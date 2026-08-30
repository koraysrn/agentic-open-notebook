"""The Agent model: a named, capability-tagged AI component.

An ``Agent`` is pure metadata — identity, capabilities, allowed tools, and a
base system prompt. It holds no executable logic; that belongs to the
orchestration layer (see ``open_notebook/graphs/agent.py``).
"""

from pydantic import BaseModel, Field, field_validator


class Agent(BaseModel):
    """A registered agent: a specialized component with a task and tools."""

    name: str = Field(description="Unique identifier for the agent (slug).")
    description: str = Field(
        description="What the agent does, in one or two sentences."
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Capability tags used for registry selection.",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Names of the tools this agent is allowed to call.",
    )
    system_prompt: str = Field(
        default="",
        description="Base system prompt that shapes the agent's behavior.",
    )

    @field_validator("name")
    @classmethod
    def _name_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Agent name cannot be empty")
        return value
