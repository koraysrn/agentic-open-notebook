"""Tests for the Agent model and AgentRegistry (Road_Map Step 3)."""

import pytest

from open_notebook.agents import Agent, AgentRegistry, registry
from open_notebook.agents.definitions import DEFAULT_AGENTS


class TestAgentModel:
    def test_valid_agent(self):
        agent = Agent(name="research", description="Does research.")
        assert agent.name == "research"
        assert agent.capabilities == []
        assert agent.tools == []
        assert agent.system_prompt == ""

    def test_name_is_required_and_trimmed(self):
        assert Agent(name="  research  ", description="x").name == "research"

    def test_empty_name_is_rejected(self):
        with pytest.raises(ValueError):
            Agent(name="   ", description="x")

    def test_capabilities_and_tools_default_to_empty_lists(self):
        agent = Agent(name="report", description="x")
        assert agent.capabilities == []
        assert agent.tools == []


class TestAgentRegistry:
    def test_fresh_registry_is_empty(self):
        assert len(AgentRegistry()) == 0

    def test_register_and_get(self):
        registry = AgentRegistry()
        agent = Agent(name="research", description="d")
        registry.register(agent)
        assert registry.get("research") is agent
        assert "research" in registry

    def test_duplicate_registration_raises(self):
        registry = AgentRegistry()
        registry.register(Agent(name="research", description="d"))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(Agent(name="research", description="other"))

    def test_unregister_removes_agent(self):
        registry = AgentRegistry()
        registry.register(Agent(name="research", description="d"))
        registry.unregister("research")
        assert registry.get("research") is None
        assert len(registry) == 0

    def test_unregister_missing_name_is_noop(self):
        registry = AgentRegistry()
        registry.unregister("missing")

    def test_list_agents_returns_all(self):
        registry = AgentRegistry()
        registry.register(Agent(name="a", description="d"))
        registry.register(Agent(name="b", description="d"))
        assert {agent.name for agent in registry.list_agents()} == {"a", "b"}

    def test_select_by_capability(self):
        registry = AgentRegistry()
        registry.register(
            Agent(name="fact_checker", description="d", capabilities=["control"])
        )
        registry.register(
            Agent(name="research", description="d", capabilities=["search"])
        )
        assert [a.name for a in registry.select_by_capability("control")] == [
            "fact_checker"
        ]

    def test_clear_empties_registry(self):
        registry = AgentRegistry()
        registry.register(Agent(name="a", description="d"))
        registry.clear()
        assert len(registry) == 0


class TestDefaultRegistry:
    def test_default_registry_contains_all_defaults(self):
        assert len(registry) == len(DEFAULT_AGENTS)

    def test_default_names_match_spec(self):
        expected = {
            "orchestrator",
            "research",
            "education",
            "presentation",
            "report",
            "podcast",
            "fact_checker",
            "control",
            "persona",
            "action",
        }
        assert {agent.name for agent in registry.list_agents()} == expected

    def test_defaults_have_descriptions_and_capabilities(self):
        for agent in registry.list_agents():
            assert agent.description.strip()
            assert isinstance(agent.capabilities, list)
