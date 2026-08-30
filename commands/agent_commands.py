"""Background command that runs the agent supervisor graph (Road_Map Step 7).

The command is fire-and-forget from the API's perspective: it persists an
``AgentRun`` record, invokes the bounded supervisor graph, updates the run
with the outcome, and returns a structured ``CommandOutput``.
"""

import json
import time
from typing import Any, Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.domain.agent_run import AgentRun
from open_notebook.exceptions import ConfigurationError
from open_notebook.graphs.agent import graph


class RunAgentInput(CommandInput):
    goal: str
    notebook_id: Optional[str] = None


class RunAgentOutput(CommandOutput):
    success: bool
    agent_run_id: Optional[str] = None
    final_answer: Optional[str] = None
    results: list[dict[str, Any]] = []
    error_message: Optional[str] = None


@command(
    "run_agent",
    app="open_notebook",
    retry={
        "max_attempts": 3,
        "wait_strategy": "exponential_jitter",
        "wait_min": 1,
        "wait_max": 30,
        "stop_on": [ValueError, ConfigurationError],
        "retry_log_level": "debug",
    },
)
async def run_agent_command(input_data: RunAgentInput) -> RunAgentOutput:
    """Run the supervisor for a goal and persist the outcome."""
    start = time.time()

    run = AgentRun(
        notebook=input_data.notebook_id,
        agent="orchestrator",
        status="running",
        goal=input_data.goal,
    )
    await run.save()

    try:
        result = await graph.ainvoke(  # type: ignore[call-overload]
            {"goal": input_data.goal}
        )
        final_answer = result.get("final_answer") or ""
        results = result.get("results") or []

        run.status = "completed"
        run.final_answer = final_answer
        run.state_json = json.dumps({"results": results})
        await run.save()

        logger.info(f"Agent run {run.id} completed in {time.time() - start:.2f}s")
        return RunAgentOutput(
            success=True,
            agent_run_id=run.id,
            final_answer=final_answer,
            results=results,
        )
    except Exception as e:
        logger.error(f"Agent run {run.id} failed after {time.time() - start:.2f}s: {e}")
        try:
            run.status = "failed"
            run.final_answer = str(e)
            await run.save()
        except Exception as save_error:
            logger.warning(f"Failed to persist failed agent run state: {save_error}")
        # Re-raise so surreal-commands applies its retry/stop_on policy.
        raise
