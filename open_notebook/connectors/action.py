"""Action Engine connectors (Road_Map Step 20).

Real connectors for Email (SMTP) and Jira (REST). Each is config-gated: it
raises ``ConfigurationError`` when its credentials are missing, and only
executes behind the human-approval invariant enforced by
``execute_approved_action``.
"""

import asyncio
import base64
import json
import os
import smtplib
from email.message import EmailMessage
from typing import Any, Protocol

import httpx

from open_notebook.domain.approval import Approval
from open_notebook.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    InvalidInputError,
)


class ActionConnector(Protocol):
    async def execute(
        self, action_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        ...


class EmailConnector:
    """Send email over SMTP (STARTTLS)."""

    def _send(self, host: str, port: int, username: str, password: str, message: EmailMessage) -> None:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            if username:
                server.login(username, password)
            server.send_message(message)

    async def execute(self, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        host = os.getenv("OPEN_NOTEBOOK_SMTP_HOST", "").strip()
        if not host:
            raise ConfigurationError(
                "Email is not configured. Set OPEN_NOTEBOOK_SMTP_HOST."
            )
        port = int(os.getenv("OPEN_NOTEBOOK_SMTP_PORT", "587"))
        username = os.getenv("OPEN_NOTEBOOK_SMTP_USERNAME", "").strip()
        password = os.getenv("OPEN_NOTEBOOK_SMTP_PASSWORD", "")

        if not payload.get("to"):
            raise InvalidInputError("Email payload requires a 'to' recipient.")

        message = EmailMessage()
        message["From"] = payload.get("from") or username
        message["To"] = payload["to"]
        message["Subject"] = payload.get("subject", "")
        message.set_content(payload.get("body", ""))

        await asyncio.to_thread(self._send, host, port, username, password, message)
        return {"status": "sent", "to": payload["to"]}


class JiraConnector:
    """Create a Jira issue via the Jira REST API (Basic auth)."""

    async def execute(self, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        base = os.getenv("OPEN_NOTEBOOK_JIRA_URL", "").strip()
        email = os.getenv("OPEN_NOTEBOOK_JIRA_EMAIL", "").strip()
        token = os.getenv("OPEN_NOTEBOOK_JIRA_API_TOKEN", "")
        if not (base and email and token):
            raise ConfigurationError(
                "Jira is not configured. Set OPEN_NOTEBOOK_JIRA_URL, "
                "OPEN_NOTEBOOK_JIRA_EMAIL and OPEN_NOTEBOOK_JIRA_API_TOKEN."
            )

        if not payload.get("project") or not payload.get("summary"):
            raise InvalidInputError("Jira payload requires 'project' and 'summary'.")

        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        fields = {
            "project": {"key": payload["project"]},
            "summary": payload["summary"],
            "issuetype": {"name": payload.get("issuetype", "Task")},
        }
        if payload.get("description"):
            fields["description"] = payload["description"]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{base.rstrip('/')}/rest/api/3/issue",
                    json={"fields": fields},
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Content-Type": "application/json",
                    },
                )
                if response.status_code >= 400:
                    raise ExternalServiceError(
                        f"Jira error {response.status_code}: {response.text}"
                    )
                data = response.json()
        except httpx.HTTPError as e:
            raise ExternalServiceError(f"Jira request failed: {e}") from e

        return {"id": data.get("id"), "key": data.get("key")}


_CONNECTORS: dict[str, ActionConnector] = {
    "jira": JiraConnector(),
    "email": EmailConnector(),
}


def get_connector(action_type: str) -> ActionConnector:
    if action_type not in _CONNECTORS:
        raise InvalidInputError(f"Unknown action type: {action_type}")
    return _CONNECTORS[action_type]


async def execute_approved_action(approval: Approval) -> dict[str, Any]:
    """Execute an approval, enforcing the human-approval invariant."""
    if approval.status != "approved":
        raise InvalidInputError("Action is not approved; refusing to execute.")

    payload = json.loads(approval.payload or "{}")
    connector = get_connector(approval.action_type or "")
    return await connector.execute(approval.action_type or "", payload)
