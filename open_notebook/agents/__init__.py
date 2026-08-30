"""Agent Engine: agent abstraction, registry, and tool access.

This package is the embedded, additive agent layer described in ADR-008.
It consumes the existing domain models, graphs, and API; it never rewrites
them. Agents are registered metadata objects; execution is orchestrated by
the supervisor graph in ``open_notebook/graphs/agent.py`` (Road_Map Step 5).
"""

from open_notebook.agents.agent import Agent
from open_notebook.agents.registry import AgentRegistry, registry
from open_notebook.agents.tools import ToolRegistry, tool_registry

__all__ = [
    "Agent",
    "AgentRegistry",
    "registry",
    "ToolRegistry",
    "tool_registry",
]
