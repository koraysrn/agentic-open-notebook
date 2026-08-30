"""Tests for the agent supervisor graph (Road_Map Step 5).

LLM nodes are tested with a mocked ``provision_langchain_model`` and tools are
tested against a fresh registry, so no database or provider is required.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.agents.tools import ToolRegistry
from open_notebook.exceptions import InvalidInputError
from open_notebook.graphs.agent import (
    AgentState,
    Plan,
    ToolCall,
    execute_node,
    graph,
    plan_node,
    should_continue,
)


def _fake_model(*responses):
    """Return a fake model whose ainvoke yields the given message contents."""
    messages = [SimpleNamespace(content=content) for content in responses]
    model = SimpleNamespace(ainvoke=AsyncMock(side_effect=messages))
    return model


async def _dummy_tool(value: str = "ok") -> dict:
    """A fake tool for tests."""
    return {"value": value}


class TestGraphShape:
    def test_graph_has_supervisor_nodes(self):
        names = set(graph.get_graph().nodes.keys())
        assert {"plan", "execute", "decide", "finalize", "__start__", "__end__"} <= names


class TestPlanParsing:
    @pytest.mark.asyncio
    async def test_plan_node_parses_model_output(self):
        plan_payload = {
            "reasoning": "list notebooks",
            "tool_calls": [
                {"agent": "research", "tool": "list_notebooks", "args": {}, "reason": "x"}
            ],
        }
        model = _fake_model(json.dumps(plan_payload))
        with patch(
            "open_notebook.graphs.agent.provision_langchain_model",
            new=AsyncMock(return_value=model),
        ):
            result = await plan_node({"goal": "g"}, {})  # type: ignore[arg-type]

        assert result["iteration"] == 1
        assert isinstance(result["plan"], Plan)
        assert result["plan"].tool_calls[0].tool == "list_notebooks"


class TestExecuteNode:
    def _registry_with_dummy(self):
        registry = ToolRegistry()
        registry.register("dummy_tool", _dummy_tool)
        return registry

    @pytest.mark.asyncio
    async def test_execute_runs_planned_tools(self):
        registry = self._registry_with_dummy()
        state: AgentState = {
            "goal": "g",
            "plan": Plan(
                tool_calls=[ToolCall(tool="dummy_tool", args={"value": "hi"})]
            ),
        }
        with patch("open_notebook.graphs.agent.tool_registry", registry):
            result = await execute_node(state, {})  # type: ignore[arg-type]

        assert result["results"] == [
            {"tool": "dummy_tool", "args": {"value": "hi"}, "output": {"value": "hi"}}
        ]

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_raises(self):
        registry = self._registry_with_dummy()
        state: AgentState = {
            "goal": "g",
            "plan": Plan(tool_calls=[ToolCall(tool="missing", args={})]),
        }
        with patch("open_notebook.graphs.agent.tool_registry", registry):
            with pytest.raises(InvalidInputError, match="Unknown tool"):
                await execute_node(state, {})  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_execute_records_known_tool_errors_instead_of_raising(self):
        async def failing_tool(**kwargs: object) -> dict:
            raise RuntimeError("boom")

        registry = ToolRegistry()
        registry.register("failing_tool", failing_tool)
        state: AgentState = {
            "goal": "g",
            "plan": Plan(tool_calls=[ToolCall(tool="failing_tool", args={})]),
        }
        with patch("open_notebook.graphs.agent.tool_registry", registry):
            result = await execute_node(state, {})  # type: ignore[arg-type]

        assert result["results"][0]["output"] == {"error": "boom"}


class TestLoopBound:
    def test_should_continue_respects_budget(self):
        assert should_continue({"iteration": 0}) == "plan"  # type: ignore[arg-type]
        assert should_continue({"iteration": 5}) == "finalize"  # type: ignore[arg-type]
        assert should_continue({"done": True}) == "finalize"  # type: ignore[arg-type]


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_graph_completes_with_mocked_llm_and_tool(self):
        plan_payload = {
            "reasoning": "list notebooks",
            "tool_calls": [{"tool": "dummy_tool", "args": {}, "reason": "x"}],
        }
        decision_payload = {"done": True, "reasoning": "enough"}
        model = _fake_model(
            json.dumps(plan_payload),
            json.dumps(decision_payload),
            "We have one notebook.",
        )
        registry = ToolRegistry()
        registry.register("dummy_tool", _dummy_tool)

        with (
            patch(
                "open_notebook.graphs.agent.provision_langchain_model",
                new=AsyncMock(return_value=model),
            ),
            patch("open_notebook.graphs.agent.tool_registry", registry),
        ):
            result = await graph.ainvoke(  # type: ignore[call-overload]
                {"goal": "list my notebooks"}
            )

        assert result["final_answer"] == "We have one notebook."
        assert len(result["results"]) == 1
        assert result["results"][0]["tool"] == "dummy_tool"
