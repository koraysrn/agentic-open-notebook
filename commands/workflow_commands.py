"""Workflow execution and scheduling commands (Road_Map Steps 21-22)."""

import json
from datetime import datetime
from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command, submit_command

from open_notebook.domain.workflow import Workflow
from open_notebook.engine.scheduler import is_due
from open_notebook.engine.workflow import run_definition


class RunWorkflowInput(CommandInput):
    workflow_id: str


class RunWorkflowOutput(CommandOutput):
    success: bool
    results: list[dict] = []
    error_message: Optional[str] = None


@command(
    "run_workflow",
    app="open_notebook",
    retry={"max_attempts": 1, "stop_on": [ValueError]},
)
async def run_workflow_command(
    input_data: RunWorkflowInput,
) -> RunWorkflowOutput:
    workflow = await Workflow.get(input_data.workflow_id)
    definition = json.loads(workflow.definition or "{}")

    results = await run_definition(definition)

    workflow.last_run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await workflow.save()
    logger.info(f"Workflow {workflow.id} completed {len(results)} step(s)")
    return RunWorkflowOutput(success=True, results=results)


class TickSchedulerInput(CommandInput):
    pass


class TickSchedulerOutput(CommandOutput):
    success: bool
    submitted: list[str] = []


@command(
    "tick_scheduler",
    app="open_notebook",
    retry={"max_attempts": 1, "stop_on": [ValueError]},
)
async def tick_scheduler_command(
    input_data: TickSchedulerInput,
) -> TickSchedulerOutput:
    workflows = await Workflow.get_all(order_by="updated desc")
    submitted: list[str] = []

    for workflow in workflows:
        if not workflow.enabled or not workflow.schedule:
            continue
        last_run = None
        if workflow.last_run_at:
            try:
                last_run = datetime.strptime(
                    workflow.last_run_at, "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                last_run = None

        if is_due(workflow.schedule, last_run):
            command_id = submit_command(
                "open_notebook",
                "run_workflow",
                {"workflow_id": str(workflow.id)},
            )
            submitted.append(str(command_id))

    return TickSchedulerOutput(success=True, submitted=submitted)
