"""Activity API: a merged stream of recent agent runs and approvals."""

from typing import Any

from fastapi import APIRouter

from open_notebook.domain.agent_run import AgentRun
from open_notebook.domain.approval import Approval

router = APIRouter()


@router.get("/activity")
async def recent_activity() -> dict[str, Any]:
    runs = await AgentRun.get_all(order_by="updated desc")
    approvals = await Approval.get_all(order_by="updated desc")

    items: list[dict[str, Any]] = []
    for run in runs[:20]:
        items.append(
            {
                "kind": "agent_run",
                "id": run.id,
                "agent": run.agent,
                "status": run.status,
                "goal": run.goal,
            }
        )
    for approval in approvals[:20]:
        items.append(
            {
                "kind": "approval",
                "id": approval.id,
                "action_type": approval.action_type,
                "status": approval.status,
            }
        )
    return {"items": items}
