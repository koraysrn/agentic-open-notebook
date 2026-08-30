"""Integrations API: list available connectors and sync connections."""

from typing import Any

from fastapi import APIRouter

from open_notebook.domain.sync_connection import SyncConnection

router = APIRouter()

_AVAILABLE_CONNECTORS = [
    {"kind": "sync", "name": "google_drive"},
    {"kind": "action", "name": "jira"},
    {"kind": "action", "name": "email"},
]


@router.get("/integrations")
async def list_integrations() -> dict[str, Any]:
    connections = await SyncConnection.get_all(order_by="updated desc")
    return {
        "connectors": _AVAILABLE_CONNECTORS,
        "connections": [
            {
                "id": connection.id,
                "provider": connection.provider,
                "status": connection.status,
                "last_sync_at": connection.last_sync_at,
            }
            for connection in connections
        ],
    }
