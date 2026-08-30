"""Workflow persistence (Road_Map Step 21).

``definition`` is a JSON string whose steps reference only registered agent
and tool names — arbitrary code never executes.
"""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class Workflow(ObjectModel):
    """A named, schedulable composition of agents and tools."""

    table_name: ClassVar[str] = "workflow"
    name: Optional[str] = None
    definition: Optional[str] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None
    last_run_at: Optional[str] = None
