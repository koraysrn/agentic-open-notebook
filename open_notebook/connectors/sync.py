"""Live Sync engine and connectors (Road_Map Steps 13-14).

The Google Drive connector lists files through the Drive API v3 using a
config-gated access token. The sync engine itself stays provider-agnostic:
``diff_remote_state`` and ``dedupe_by_content_hash`` operate on plain
snapshots.
"""

import os
from typing import Any, Protocol

import httpx

from open_notebook.exceptions import ConfigurationError, ExternalServiceError


def diff_remote_state(
    previous: dict[str, str | None], current: dict[str, str | None]
) -> dict[str, list[str]]:
    """Diff two snapshots keyed by remote file id -> version marker."""
    added = [fid for fid in current if fid not in previous]
    changed = [
        fid
        for fid in current
        if fid in previous and previous[fid] != current[fid]
    ]
    deleted = [fid for fid in previous if fid not in current]
    return {"added": added, "changed": changed, "deleted": deleted}


def dedupe_by_content_hash(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first entry per content hash (duplicate prevention)."""
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for entry in entries:
        digest = entry.get("content_hash")
        if not digest or digest in seen:
            continue
        seen.add(digest)
        result.append(entry)
    return result


class SyncConnector(Protocol):
    async def list_files(self) -> list[dict[str, Any]]:
        ...


class GoogleDriveConnector:
    """List Drive files via the Google Drive API v3."""

    provider = "google_drive"

    async def list_files(self) -> list[dict[str, Any]]:
        token = os.getenv("OPEN_NOTEBOOK_GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
        if not token:
            raise ConfigurationError(
                "Google Drive is not configured. Set "
                "OPEN_NOTEBOOK_GOOGLE_DRIVE_ACCESS_TOKEN."
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    params={
                        "fields": "files(id,name,mimeType,md5Checksum,modifiedTime)"
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code >= 400:
                    raise ExternalServiceError(
                        f"Google Drive error {response.status_code}: {response.text}"
                    )
                data = response.json()
        except httpx.HTTPError as e:
            raise ExternalServiceError(f"Google Drive request failed: {e}") from e

        files = data.get("files", []) if isinstance(data, dict) else []
        return [
            {
                "id": item["id"],
                "name": item.get("name"),
                "content_hash": item.get("md5Checksum"),
                "version": item.get("modifiedTime"),
            }
            for item in files
            if item.get("id")
        ]
