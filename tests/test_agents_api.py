"""Tests for the agent API (Road_Map Step 7)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestListAgents:
    def test_lists_default_agents(self, client):
        response = client.get("/api/agents")
        assert response.status_code == 200
        names = {agent["name"] for agent in response.json()}
        assert {"orchestrator", "research", "control"} <= names

    def test_agent_shape(self, client):
        response = client.get("/api/agents")
        first = response.json()[0]
        assert set(first.keys()) == {"name", "description", "capabilities", "tools"}


class TestListTools:
    def test_lists_default_tools(self, client):
        response = client.get("/api/agents/tools")
        assert response.status_code == 200
        names = {tool["name"] for tool in response.json()}
        assert {"list_notebooks", "search_sources", "create_note"} <= names


class TestRunAgent:
    def test_run_submits_command(self, client):
        with patch(
            "api.routers.agents.submit_command",
            return_value="command:123",
        ) as mock_submit:
            response = client.post(
                "/api/agents/run", json={"goal": "list my notebooks"}
            )

        assert response.status_code == 200
        assert response.json() == {"command_id": "command:123"}
        mock_submit.assert_called_once_with(
            "open_notebook",
            "run_agent",
            {"goal": "list my notebooks", "notebook_id": None},
        )
