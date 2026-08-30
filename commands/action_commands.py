"""Background command that executes an approved action (Road_Map Step 20)."""

from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.connectors.action import execute_approved_action
from open_notebook.domain.approval import Approval


class ExecuteActionInput(CommandInput):
    approval_id: str


class ExecuteActionOutput(CommandOutput):
    success: bool
    result: dict = {}
    error_message: Optional[str] = None


@command(
    "execute_action",
    app="open_notebook",
    retry={"max_attempts": 1, "stop_on": [ValueError]},
)
async def execute_action_command(
    input_data: ExecuteActionInput,
) -> ExecuteActionOutput:
    approval = await Approval.get(input_data.approval_id)
    result = await execute_approved_action(approval)

    approval.status = "executed"
    await approval.save()
    logger.info(f"Executed action approval {approval.id}")
    return ExecuteActionOutput(success=True, result=result)
