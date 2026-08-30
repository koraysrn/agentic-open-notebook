"""External system connectors for Live Sync and the Action Engine.

Connectors are isolated from the core knowledge system: they expose a small
async interface and never touch SurrealDB or domain models directly.
"""

from open_notebook.connectors.sync import (
    GoogleDriveConnector,
    SyncConnector,
    dedupe_by_content_hash,
    diff_remote_state,
)

__all__ = [
    "GoogleDriveConnector",
    "SyncConnector",
    "dedupe_by_content_hash",
    "diff_remote_state",
]
