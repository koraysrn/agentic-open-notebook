"""Tests for the research workflow graph (Road_Map Step 12)."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.exceptions import ConfigurationError
from open_notebook.graphs.control import Claim
from open_notebook.graphs.research import (
    fact_check_node,
    gather_node,
    graph,
    synthesize_node,
)


def _fake_model(content: str):
    return SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content=content)))


class TestResearchGraphShape:
    def test_graph_has_research_nodes(self):
        names = set(graph.get_graph().nodes.keys())
        assert {"gather", "synthesize", "fact_check", "__start__", "__end__"} <= names


class TestGatherNode:
    @pytest.mark.asyncio
    async def test_gathers_internal_evidence_and_skips_unconfigured_web(self):
        internal: list[dict[str, Any]] = [
            {"id": "source:1", "title": "A", "full_text": "body", "content": None}
        ]
        with (
            patch(
                "open_notebook.graphs.research.text_search",
                new=AsyncMock(return_value=internal),
            ),
            patch(
                "open_notebook.graphs.research.web_search",
                new=AsyncMock(side_effect=ConfigurationError("not configured")),
            ),
        ):
            result = await gather_node({"question": "q"}, {})  # type: ignore[arg-type]

        assert result["evidence"] == [
            {"id": "source:1", "title": "A", "content": "body"}
        ]

    @pytest.mark.asyncio
    async def test_gathers_external_evidence_when_configured(self):
        internal: list[dict[str, Any]] = []
        external = [{"url": "https://x", "title": "W", "snippet": "snippet"}]
        with (
            patch(
                "open_notebook.graphs.research.text_search",
                new=AsyncMock(return_value=internal),
            ),
            patch(
                "open_notebook.graphs.research.web_search",
                new=AsyncMock(return_value=external),
            ),
        ):
            result = await gather_node({"question": "q"}, {})  # type: ignore[arg-type]

        assert result["evidence"][0]["id"] == "https://x"
        assert result["evidence"][0]["content"] == "snippet"


class TestSynthesizeNode:
    @pytest.mark.asyncio
    async def test_produces_draft(self):
        model = _fake_model("A sourced report.")
        with patch(
            "open_notebook.graphs.research.provision_langchain_model",
            new=AsyncMock(return_value=model),
        ):
            result = await synthesize_node({"question": "q", "evidence": []}, {})  # type: ignore[arg-type]

        assert result["draft"] == "A sourced report."


class TestFactCheckNode:
    @pytest.mark.asyncio
    async def test_returns_claims_from_control_layer(self):
        claims = [Claim(text="x", label="verified", confidence=0.9)]
        with patch(
            "open_notebook.graphs.research.control_verify_node",
            new=AsyncMock(return_value={"claims": claims}),
        ):
            result = await fact_check_node(
                {"draft": "draft", "evidence": []}, {}  # type: ignore[arg-type]
            )

        assert result["claims"] == claims


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_research_flow_completes(self):
        internal = [
            {"id": "source:1", "title": "A", "full_text": "body", "content": None}
        ]
        claims = [Claim(text="x", label="verified", confidence=0.9)]
        model = _fake_model("Report with source:1.")
        with (
            patch(
                "open_notebook.graphs.research.text_search",
                new=AsyncMock(return_value=internal),
            ),
            patch(
                "open_notebook.graphs.research.web_search",
                new=AsyncMock(side_effect=ConfigurationError("not configured")),
            ),
            patch(
                "open_notebook.graphs.research.provision_langchain_model",
                new=AsyncMock(return_value=model),
            ),
            patch(
                "open_notebook.graphs.research.control_verify_node",
                new=AsyncMock(return_value={"claims": claims}),
            ),
        ):
            result = await graph.ainvoke({"question": "is this still valid?"})  # type: ignore[call-overload]

        assert result["draft"] == "Report with source:1."
        assert result["evidence"][0]["id"] == "source:1"
        assert result["claims"][0].label == "verified"
