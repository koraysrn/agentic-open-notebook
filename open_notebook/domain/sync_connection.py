"""Live Sync connection persistence (Road_Map Step 13).

The OAuth token is stored encrypted at rest; the API layer must never return
``oauth_token_encrypted`` to clients.
"""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class SyncConnection(ObjectModel):
    """A connection between a notebook and an external source system."""

    table_name: ClassVar[str] = "sync_connection"
    provider: Optional[str] = None
    notebook: Optional[str] = None
    oauth_token_encrypted: Optional[str] = None
    last_sync_at: Optional[str] = None
    status: Optional[str] = None
