"""Tests for the research API (Road_Map Step 12 + UI wiring)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestRunResearch:
    def test_returns_draft_claims_and_evidence(self, client):
        result = {
            "draft": "A sourced report.",
            "claims": [{"text": "claim", "label": "verified", "confidence": 0.9}],
            "evidence": [{"id": "src:1", "title": "S", "content": "body"}],
        }
        with patch(
            "api.routers.research.research_graph.ainvoke",
            return_value=result,
        ) as mock_graph:
            response = client.post("/api/research", json={"question": "what?"})

        assert response.status_code == 200
        body = response.json()
        assert body["draft"] == "A sourced report."
        assert body["claims"][0]["label"] == "verified"
        assert body["evidence"][0]["id"] == "src:1"
        mock_graph.assert_awaited_once_with({"question": "what?"})

    def test_rejects_empty_question(self, client):
        response = client.post("/api/research", json={"question": "   "})
        assert response.status_code == 422

    def test_handles_claims_as_pydantic_objects(self, client):
        from open_notebook.graphs.control import Claim

        result = {
            "draft": "draft",
            "claims": [Claim(text="t", label="external", confidence=0.5)],
            "evidence": [],
        }
        with patch(
            "api.routers.research.research_graph.ainvoke",
            return_value=result,
        ):
            response = client.post("/api/research", json={"question": "q"})

        assert response.status_code == 200
        assert response.json()["claims"][0] == {
            "text": "t",
            "label": "external",
            "confidence": 0.5,
        }
