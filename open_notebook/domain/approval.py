"""Human approval queue persistence (Road_Map Step 19).

Actions are executed only when ``status == "approved"``; the execution layer
must enforce that invariant, never the client.
"""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class Approval(ObjectModel):
    """A pending, approved, or rejected external action."""

    table_name: ClassVar[str] = "approval"
    notebook: Optional[str] = None
    action_type: Optional[str] = None
    payload: Optional[str] = None
    status: Optional[str] = None
