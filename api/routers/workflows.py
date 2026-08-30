"""Workflow API: list, create, and run workflow definitions (Road_Map Steps 21-22)."""

import json
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from surreal_commands import submit_command

from open_notebook.agents import tool_registry
from open_notebook.domain.workflow import Workflow
from open_notebook.engine.workflow import validate_definition

router = APIRouter()


class WorkflowCreate(BaseModel):
    name: str
    definition: str = '{"steps": []}'
    schedule: Optional[str] = None
    enabled: bool = True


class WorkflowResponse(BaseModel):
    id: Optional[str]
    name: Optional[str]
    definition: Optional[str]
    schedule: Optional[str]
    enabled: Optional[bool]
    last_run_at: Optional[str]


class RunWorkflowResponse(BaseModel):
    command_id: str


def _to_response(workflow: Workflow) -> WorkflowResponse:
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        definition=workflow.definition,
        schedule=workflow.schedule,
        enabled=workflow.enabled,
        last_run_at=workflow.last_run_at,
    )


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows() -> list[WorkflowResponse]:
    workflows = await Workflow.get_all(order_by="updated desc")
    return [_to_response(workflow) for workflow in workflows]


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowCreate) -> WorkflowResponse:
    definition = json.loads(request.definition)
    validate_definition(definition, set(tool_registry.list_tools()))

    workflow = Workflow(
        name=request.name,
        definition=request.definition,
        schedule=request.schedule,
        enabled=request.enabled,
    )
    await workflow.save()
    return _to_response(workflow)


@router.post(
    "/workflows/{workflow_id}/run", response_model=RunWorkflowResponse
)
async def run_workflow(workflow_id: str) -> RunWorkflowResponse:
    import commands.workflow_commands  # noqa: F401

    command_id = submit_command(
        "open_notebook",
        "run_workflow",
        {"workflow_id": workflow_id},
    )
    return RunWorkflowResponse(command_id=str(command_id))
