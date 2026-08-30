"""In-memory agent registry.

The registry is intentionally simple: it stores ``Agent`` metadata and offers
lookup/selection primitives. Tool *execution* is not its concern — the
supervisor resolves tool names against the tool registry (Road_Map Step 4)
at run time.
"""

from open_notebook.agents.agent import Agent
from open_notebook.agents.definitions import DEFAULT_AGENTS


class AgentRegistry:
    """A name-keyed collection of available agents."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Add an agent. Duplicate names are rejected to keep routing
        deterministic."""
        if agent.name in self._agents:
            raise ValueError(f"Agent already registered: {agent.name}")
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> None:
        """Remove an agent by name; missing names are a no-op."""
        self._agents.pop(name, None)

    def get(self, name: str) -> Agent | None:
        """Return the agent registered under ``name``, or ``None``."""
        return self._agents.get(name)

    def list_agents(self) -> list[Agent]:
        """Return all registered agents (insertion order)."""
        return list(self._agents.values())

    def select_by_capability(self, capability: str) -> list[Agent]:
        """Return agents that declare the given capability tag."""
        return [
            agent
            for agent in self._agents.values()
            if capability in agent.capabilities
        ]

    def clear(self) -> None:
        """Remove every agent (primarily for tests)."""
        self._agents.clear()

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: object) -> bool:
        return name in self._agents


def build_default_registry() -> AgentRegistry:
    """Build a registry pre-populated with the default agent set."""
    registry = AgentRegistry()
    for agent in DEFAULT_AGENTS:
        registry.register(agent)
    return registry


# The process-wide registry used by the orchestration layer.
registry = build_default_registry()
