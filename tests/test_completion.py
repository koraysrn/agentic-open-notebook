"""Tests for connectors, scheduling, and the workflows/users/integrations APIs."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from open_notebook.connectors.action import EmailConnector, JiraConnector
from open_notebook.connectors.sync import GoogleDriveConnector
from open_notebook.engine.scheduler import is_due
from open_notebook.exceptions import ConfigurationError


@pytest.fixture
def client():
    return TestClient(app)


class TestScheduler:
    def test_never_run_is_due(self):
        assert is_due("daily", None) is True

    def test_not_due_yet(self):
        last = datetime.now() - timedelta(hours=1)
        assert is_due("daily", last) is False

    def test_due_after_elapsed(self):
        last = datetime.now() - timedelta(days=2)
        assert is_due("daily", last) is True

    def test_unknown_schedule_raises(self):
        with pytest.raises(ValueError, match="Unknown schedule"):
            is_due("monthly", None)


class TestConnectorsUnconfigured:
    @pytest.mark.asyncio
    async def test_email_unconfigured(self, monkeypatch):
        monkeypatch.delenv("OPEN_NOTEBOOK_SMTP_HOST", raising=False)
        with pytest.raises(ConfigurationError):
            await EmailConnector().execute("email", {"to": "a@b.c"})

    @pytest.mark.asyncio
    async def test_jira_unconfigured(self, monkeypatch):
        monkeypatch.delenv("OPEN_NOTEBOOK_JIRA_URL", raising=False)
        with pytest.raises(ConfigurationError):
            await JiraConnector().execute("jira", {"project": "P", "summary": "s"})

    @pytest.mark.asyncio
    async def test_drive_unconfigured(self, monkeypatch):
        monkeypatch.delenv("OPEN_NOTEBOOK_GOOGLE_DRIVE_ACCESS_TOKEN", raising=False)
        with pytest.raises(ConfigurationError):
            await GoogleDriveConnector().list_files()


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.text = str(payload)
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        return self._response

    async def get(self, *args, **kwargs):
        return self._response


class TestConnectorsConfigured:
    @pytest.mark.asyncio
    async def test_jira_creates_issue(self, monkeypatch):
        monkeypatch.setenv("OPEN_NOTEBOOK_JIRA_URL", "https://jira.example.com")
        monkeypatch.setenv("OPEN_NOTEBOOK_JIRA_EMAIL", "a@b.c")
        monkeypatch.setenv("OPEN_NOTEBOOK_JIRA_API_TOKEN", "tok")
        fake_client = _FakeClient(
            _FakeResponse(201, {"id": "10001", "key": "PROJ-1"})
        )
        with patch(
            "open_notebook.connectors.action.httpx.AsyncClient",
            return_value=fake_client,
        ):
            result = await JiraConnector().execute(
                "jira", {"project": "PROJ", "summary": "Do the thing"}
            )
        assert result["key"] == "PROJ-1"

    @pytest.mark.asyncio
    async def test_drive_lists_files(self, monkeypatch):
        monkeypatch.setenv("OPEN_NOTEBOOK_GOOGLE_DRIVE_ACCESS_TOKEN", "tok")
        fake_client = _FakeClient(
            _FakeResponse(
                200,
                {
                    "files": [
                        {"id": "f1", "name": "a.pdf", "md5Checksum": "h", "modifiedTime": "t"}
                    ]
                },
            )
        )
        with patch(
            "open_notebook.connectors.sync.httpx.AsyncClient",
            return_value=fake_client,
        ):
            result = await GoogleDriveConnector().list_files()
        assert result[0]["id"] == "f1"


class TestWorkflowsApi:
    def test_create_rejects_unknown_tool(self, client):
        response = client.post(
            "/api/workflows",
            json={"name": "bad", "definition": '{"steps": [{"tool": "missing"}]}'},
        )
        assert response.status_code == 400

    def test_create_accepts_registered_tool(self, client):
        with patch(
            "open_notebook.domain.base.ObjectModel.save",
            new=AsyncMock(return_value=None),
        ):
            response = client.post(
                "/api/workflows",
                json={
                    "name": "good",
                    "definition": '{"steps": [{"tool": "list_notebooks"}]}',
                },
            )
        assert response.status_code == 200
        assert response.json()["name"] == "good"


class TestUsersApi:
    def test_create_rejects_invalid_role(self, client):
        response = client.post(
            "/api/users", json={"email": "a@b.c", "role": "superuser"}
        )
        assert response.status_code == 400

    def test_create_accepts_valid_user(self, client):
        with patch(
            "open_notebook.domain.base.ObjectModel.save",
            new=AsyncMock(return_value=None),
        ):
            response = client.post(
                "/api/users", json={"email": "a@b.c", "role": "admin"}
            )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


class TestIntegrationsApi:
    def test_lists_connectors(self, client):
        with patch(
            "open_notebook.domain.base.ObjectModel.get_all",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get("/api/integrations")
        assert response.status_code == 200
        names = {c["name"] for c in response.json()["connectors"]}
        assert {"google_drive", "jira", "email"} <= names
