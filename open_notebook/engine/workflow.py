"""Workflow Engine (Road_Map Steps 21-22).

A workflow definition is a JSON object with a ``steps`` list; each step names
a registered tool and optional args. Only registered tool names can run, so a
stored definition can never execute arbitrary code.
"""

from typing import Any

from open_notebook.agents import tool_registry
from open_notebook.exceptions import InvalidInputError


def validate_definition(
    definition: dict[str, Any], available_tools: set[str]
) -> None:
    """Raise ``InvalidInputError`` if any step references an unknown tool."""
    steps = definition.get("steps")
    if not isinstance(steps, list) or not steps:
        raise InvalidInputError(
            "Workflow definition must contain a non-empty 'steps' list."
        )
    for step in steps:
        if not isinstance(step, dict):
            raise InvalidInputError("Each workflow step must be an object.")
        tool = step.get("tool")
        if not tool:
            raise InvalidInputError("Each workflow step must name a 'tool'.")
        if tool not in available_tools:
            raise InvalidInputError(f"Unknown tool in workflow: {tool}")


async def run_definition(
    definition: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate and execute a workflow's tool steps in order."""
    validate_definition(definition, set(tool_registry.list_tools()))

    results: list[dict[str, Any]] = []
    for step in definition["steps"]:
        tool = tool_registry.get(step["tool"])
        if tool is None:
            raise InvalidInputError(f"Unknown tool: {step['tool']}")
        args = step.get("args") or {}
        output = await tool(**args)
        results.append({"tool": step["tool"], "output": output})
    return results
