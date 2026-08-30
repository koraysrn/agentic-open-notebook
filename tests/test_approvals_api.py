"""Tests for the approval API (Road_Map Step 19)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from open_notebook.domain.approval import Approval


@pytest.fixture
def client():
    return TestClient(app)


class TestListApprovals:
    def test_lists_approvals(self, client):
        approval = Approval(
            id="approval:1",
            action_type="jira",
            status="pending",
            payload="{}",
        )
        with patch(
            "open_notebook.domain.base.ObjectModel.get_all",
            new=AsyncMock(return_value=[approval]),
        ):
            response = client.get("/api/approvals")

        assert response.status_code == 200
        assert response.json()[0]["action_type"] == "jira"


class TestCreateApproval:
    def test_creates_pending_approval(self, client):
        with patch(
            "open_notebook.domain.base.ObjectModel.save",
            new=AsyncMock(return_value=None),
        ):
            response = client.post(
                "/api/approvals",
                json={"action_type": "email", "payload": "{}"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "pending"
        assert response.json()["action_type"] == "email"


class TestApproveApproval:
    def test_approves_approval(self, client):
        approval = Approval(
            id="approval:1",
            action_type="jira",
            status="pending",
            payload="{}",
        )
        with (
            patch(
                "open_notebook.domain.approval.Approval.get",
                new=AsyncMock(return_value=approval),
            ),
            patch(
                "open_notebook.domain.base.ObjectModel.save",
                new=AsyncMock(return_value=None),
            ),
        ):
            response = client.post("/api/approvals/approval:1/approve")

        assert response.status_code == 200
        assert approval.status == "approved"
        assert response.json()["status"] == "approved"
