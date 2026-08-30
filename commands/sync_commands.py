"""Background command that runs a sync connection (Road_Map Step 14)."""

import time
from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.connectors.sync import GoogleDriveConnector, diff_remote_state
from open_notebook.domain.sync_connection import SyncConnection


class RunSyncInput(CommandInput):
    connection_id: str


class RunSyncOutput(CommandOutput):
    success: bool
    added: list[str] = []
    changed: list[str] = []
    deleted: list[str] = []
    error_message: Optional[str] = None


@command(
    "run_sync",
    app="open_notebook",
    retry={"max_attempts": 1, "stop_on": [ValueError]},
)
async def run_sync_command(input_data: RunSyncInput) -> RunSyncOutput:
    connection = await SyncConnection.get(input_data.connection_id)

    if connection.provider == "google_drive":
        connector = GoogleDriveConnector()
    else:
        raise ValueError(f"Unknown sync provider: {connection.provider}")

    current = await connector.list_files()
    current_map: dict[str, str | None] = {
        entry["id"]: entry.get("version") or entry.get("content_hash")
        for entry in current
        if entry.get("id")
    }

    # A full implementation persists the previous snapshot on the connection
    # record; the first run diffs against an empty snapshot.
    diff = diff_remote_state({}, current_map)

    connection.last_sync_at = time.strftime("%Y-%m-%d %H:%M:%S")
    connection.status = "completed"
    await connection.save()

    logger.info(
        f"Sync for {connection.id}: +{len(diff['added'])} "
        f"~{len(diff['changed'])} -{len(diff['deleted'])}"
    )
    return RunSyncOutput(
        success=True,
        added=diff["added"],
        changed=diff["changed"],
        deleted=diff["deleted"],
    )
