"""Agent API: expose the agent and tool registries, and submit agent runs."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field
from surreal_commands import submit_command

from open_notebook.agents import registry as agent_registry
from open_notebook.agents import tool_registry

router = APIRouter()


class AgentInfo(BaseModel):
    name: str
    description: str
    capabilities: list[str]
    tools: list[str]


class ToolInfo(BaseModel):
    name: str
    description: str


class AgentRunRequest(BaseModel):
    goal: str = Field(..., description="The user goal to orchestrate.")
    notebook_id: Optional[str] = None


class AgentRunResponse(BaseModel):
    command_id: str


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """List all registered agents and their metadata."""
    return [
        AgentInfo(
            name=agent.name,
            description=agent.description,
            capabilities=agent.capabilities,
            tools=agent.tools,
        )
        for agent in agent_registry.list_agents()
    ]


@router.get("/agents/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """List all registered agent tools."""
    entries: list[ToolInfo] = []
    for name in tool_registry.list_tools():
        tool = tool_registry.get(name)
        entries.append(
            ToolInfo(
                name=name,
                description=(tool.__doc__ or "").strip() if tool else "",
            )
        )
    return entries


@router.post("/agents/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    """Submit an agent run to the background worker."""
    # Import the module so the command is registered before submission.
    import commands.agent_commands  # noqa: F401

    command_id = submit_command(
        "open_notebook",
        "run_agent",
        {"goal": request.goal, "notebook_id": request.notebook_id},
    )
    return AgentRunResponse(command_id=str(command_id))
