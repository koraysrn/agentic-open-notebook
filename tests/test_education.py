"""Tests for the Education Engine graph (Road_Map Step 16)."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.graphs.education import EducationMaterial, generate_material, graph


def _fake_model(content: str):
    return SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content=content)))


class TestEducationGraph:
    def test_graph_has_generate_node(self):
        names = set(graph.get_graph().nodes.keys())
        assert {"generate", "__start__", "__end__"} <= names

    @pytest.mark.asyncio
    async def test_generate_material_parses_output(self):
        payload = {
            "plan": {"steps": [{"topic": "SQL", "minutes": 20}]},
            "explanation": "Databases store data.",
            "quiz": [{"text": "What is SQL?", "answer": "A query language."}],
            "flashcards": [{"front": "SQL", "back": "Structured Query Language"}],
        }
        model = _fake_model(json.dumps(payload))
        with patch(
            "open_notebook.graphs.education.provision_langchain_model",
            new=AsyncMock(return_value=model),
        ):
            result = await generate_material({"source_content": "x"}, {})  # type: ignore[arg-type]

        assert isinstance(result["material"], EducationMaterial)
        assert result["material"].plan.steps[0].topic == "SQL"
        assert result["material"].quiz[0].text == "What is SQL?"
