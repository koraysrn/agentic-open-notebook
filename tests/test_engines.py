"""Tests for the sync, adaptive, workflow, action, persona, and security engines."""

from unittest.mock import patch

import pytest

from open_notebook.agents.tools import ToolRegistry
from open_notebook.connectors.action import execute_approved_action, get_connector
from open_notebook.connectors.sync import dedupe_by_content_hash, diff_remote_state
from open_notebook.domain.approval import Approval
from open_notebook.domain.persona import Persona
from open_notebook.engine.adaptive import select_weak_subjects
from open_notebook.engine.persona import build_persona_prompt
from open_notebook.engine.workflow import run_definition, validate_definition
from open_notebook.exceptions import ConfigurationError, InvalidInputError
from open_notebook.utils.security import redact_secret


class TestSyncEngine:
    def test_diff_remote_state(self):
        previous: dict[str, str | None] = {"a": "v1", "b": "v1"}
        current: dict[str, str | None] = {"b": "v2", "c": "v1"}
        diff = diff_remote_state(previous, current)
        assert diff == {"added": ["c"], "changed": ["b"], "deleted": ["a"]}

    def test_dedupe_by_content_hash(self):
        entries = [
            {"id": "1", "content_hash": "h"},
            {"id": "2", "content_hash": "h"},
            {"id": "3", "content_hash": "other"},
        ]
        result = dedupe_by_content_hash(entries)
        assert [e["id"] for e in result] == ["1", "3"]


class TestAdaptiveLearning:
    def test_select_weak_subjects(self):
        progress = [
            {"subject": "sql", "score": 0.4},
            {"subject": "sql", "score": 0.5},
            {"subject": "indexes", "score": 0.9},
        ]
        assert select_weak_subjects(progress) == ["sql"]

    def test_ignores_missing_scores(self):
        assert select_weak_subjects([{"subject": "x"}]) == []


class TestWorkflowEngine:
    def _registry_with_dummy(self):
        registry = ToolRegistry()

        async def dummy_tool(value: str = "ok"):
            return {"value": value}

        registry.register("dummy_tool", dummy_tool)
        return registry

    def test_validate_definition_accepts_registered_tools(self):
        validate_definition(
            {"steps": [{"tool": "dummy_tool", "args": {}}]}, {"dummy_tool"}
        )

    def test_validate_definition_rejects_unknown_tool(self):
        with pytest.raises(InvalidInputError, match="Unknown tool"):
            validate_definition({"steps": [{"tool": "missing"}]}, {"dummy_tool"})

    def test_validate_definition_rejects_empty_steps(self):
        with pytest.raises(InvalidInputError, match="steps"):
            validate_definition({"steps": []}, set())

    @pytest.mark.asyncio
    async def test_run_definition_executes_tools(self):
        registry = self._registry_with_dummy()
        with patch("open_notebook.engine.workflow.tool_registry", registry):
            result = await run_definition(
                {"steps": [{"tool": "dummy_tool", "args": {"value": "hi"}}]}
            )
        assert result == [
            {"tool": "dummy_tool", "output": {"value": "hi"}}
        ]


class TestActionEngine:
    def test_get_connector_rejects_unknown_type(self):
        with pytest.raises(InvalidInputError, match="Unknown action type"):
            get_connector("unknown")

    @pytest.mark.asyncio
    async def test_execute_refuses_unapproved(self):
        approval = Approval(action_type="jira", payload="{}", status="pending")
        with pytest.raises(InvalidInputError, match="not approved"):
            await execute_approved_action(approval)

    @pytest.mark.asyncio
    async def test_execute_approved_unconfigured_connector_raises(self):
        approval = Approval(action_type="jira", payload="{}", status="approved")
        with pytest.raises(ConfigurationError, match="Jira"):
            await execute_approved_action(approval)


class TestPersonaEngine:
    def test_build_persona_prompt_combines(self):
        persona = Persona(name="investor", system_prompt="You are an investor.")
        assert build_persona_prompt(persona, "Analyze risk.") == (
            "You are an investor.\n\nTask:\nAnalyze risk."
        )

    def test_build_persona_prompt_without_prompt(self):
        persona = Persona(name="investor")
        assert build_persona_prompt(persona, "Analyze risk.") == "Analyze risk."


class TestSecurity:
    def test_redact_secret(self):
        assert redact_secret("abcdef") == "abcd****"
        assert redact_secret("ab") == "****"
        assert redact_secret("") == ""
        assert redact_secret(None) == ""
