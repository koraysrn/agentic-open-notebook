"""Agent run persistence for the Agent Engine (ADR-008, Road_Map Step 6).

An ``AgentRun`` records one orchestrated supervisor run so the caller can
observe status, store the serialized state (``state_json``), and read the
final answer. It is an ``ObjectModel`` like every other persisted domain type.
"""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class AgentRun(ObjectModel):
    """A single orchestrated agent run."""

    table_name: ClassVar[str] = "agent_run"
    notebook: Optional[str] = None
    agent: Optional[str] = None
    status: Optional[str] = None
    goal: Optional[str] = None
    state_json: Optional[str] = None
    final_answer: Optional[str] = None
