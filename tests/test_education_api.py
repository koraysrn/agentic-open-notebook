"""Tests for the education API (Road_Map Step 16 + UI wiring)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestGenerateMaterial:
    def test_returns_material(self, client):
        material = {
            "explanation": "Explains the topic.",
            "plan": {"steps": [{"topic": "Intro", "minutes": 5}]},
            "quiz": [{"text": "Q?", "answer": "A"}],
            "flashcards": [{"front": "F", "back": "B"}],
        }
        with patch(
            "api.routers.education.education_graph.ainvoke",
            return_value={"material": material},
        ) as mock_graph:
            response = client.post(
                "/api/education/material", json={"source_content": "content"}
            )

        assert response.status_code == 200
        body = response.json()
        assert body["explanation"] == "Explains the topic."
        assert body["plan"] == [{"topic": "Intro", "minutes": 5}]
        assert body["quiz"] == [{"text": "Q?", "answer": "A"}]
        assert body["flashcards"] == [{"front": "F", "back": "B"}]
        mock_graph.assert_awaited_once_with({"source_content": "content"})

    def test_handles_missing_material(self, client):
        with patch(
            "api.routers.education.education_graph.ainvoke",
            return_value={},
        ):
            response = client.post(
                "/api/education/material", json={"source_content": "content"}
            )

        assert response.status_code == 200
        assert response.json()["explanation"] == ""

    def test_rejects_empty_content(self, client):
        response = client.post(
            "/api/education/material", json={"source_content": ""}
        )
        assert response.status_code == 422
