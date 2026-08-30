"""Approval API: create and act on human-approval records (Road_Map Step 19).

Actions are only executed by the background worker when an approval reaches
``status == "approved"``; this router creates and approves records but never
executes anything itself.
"""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from open_notebook.domain.approval import Approval

router = APIRouter()


class ApprovalCreate(BaseModel):
    notebook_id: Optional[str] = None
    action_type: str
    payload: str = "{}"


class ApprovalResponse(BaseModel):
    id: Optional[str]
    action_type: Optional[str]
    status: Optional[str]
    payload: Optional[str]


def _to_response(approval: Approval) -> ApprovalResponse:
    return ApprovalResponse(
        id=approval.id,
        action_type=approval.action_type,
        status=approval.status,
        payload=approval.payload,
    )


@router.get("/approvals", response_model=list[ApprovalResponse])
async def list_approvals() -> list[ApprovalResponse]:
    approvals = await Approval.get_all(order_by="updated desc")
    return [_to_response(approval) for approval in approvals]


@router.post("/approvals", response_model=ApprovalResponse)
async def create_approval(request: ApprovalCreate) -> ApprovalResponse:
    approval = Approval(
        notebook=request.notebook_id,
        action_type=request.action_type,
        payload=request.payload,
        status="pending",
    )
    await approval.save()
    return _to_response(approval)


@router.post(
    "/approvals/{approval_id}/approve", response_model=ApprovalResponse
)
async def approve_approval(approval_id: str) -> ApprovalResponse:
    approval = await Approval.get(approval_id)
    approval.status = "approved"
    await approval.save()
    return _to_response(approval)
