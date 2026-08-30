"""Supervisor graph for the Agent Engine (ADR-008, Road_Map Step 5).

The graph is a bounded plan → execute → decide loop:

    plan      — an LLM turns the user goal into concrete tool calls.
    execute   — runs each planned tool against the tool registry.
    decide    — an LLM decides whether enough evidence was gathered.
    finalize  — an LLM synthesizes a final answer from the results.

The loop is bounded by ``MAX_ITERATIONS`` so an unbounded tool loop is
structurally impossible. Every LLM call goes through
``provision_langchain_model()`` and is wrapped with ``classify_error()``.
"""

import operator
from typing import Annotated, Any

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from loguru import logger
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.agents import registry as agent_registry
from open_notebook.agents import tool_registry
from open_notebook.ai.provision import provision_langchain_model
from open_notebook.exceptions import InvalidInputError, OpenNotebookError
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content

MAX_ITERATIONS = 5


class ToolCall(BaseModel):
    """One planned tool invocation."""

    agent: str | None = Field(
        default=None, description="Agent responsible for this step (optional)."
    )
    tool: str = Field(description="Name of the registered tool to call.")
    args: dict[str, Any] = Field(
        default_factory=dict, description="Keyword arguments for the tool."
    )
    reason: str = Field(default="", description="Why this call advances the goal.")


class Plan(BaseModel):
    """The planner's output for a single iteration."""

    reasoning: str = Field(default="", description="One-line plan rationale.")
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="Tools to call this iteration."
    )


class Decision(BaseModel):
    """The decider's output after execution."""

    done: bool = Field(description="True when enough evidence was gathered.")
    reasoning: str = Field(default="")


class AgentState(TypedDict, total=False):
    goal: str
    iteration: int
    plan: Plan
    results: Annotated[list[dict[str, Any]], operator.add]
    done: bool
    final_answer: str


def _available_agents() -> list[dict[str, Any]]:
    return [
        {
            "name": agent.name,
            "description": agent.description,
            "capabilities": agent.capabilities,
        }
        for agent in agent_registry.list_agents()
    ]


def _available_tools() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for name in tool_registry.list_tools():
        tool = tool_registry.get(name)
        entries.append(
            {
                "name": name,
                "description": (tool.__doc__ or "").strip() if tool else "",
            }
        )
    return entries


async def plan_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """Produce a bounded plan of tool calls for the current goal."""
    try:
        parser: PydanticOutputParser[Plan] = PydanticOutputParser(
            pydantic_object=Plan
        )
        prompt = Prompter(prompt_template="agent/plan", parser=parser).render(  # type: ignore[arg-type]
            data=dict(
                goal=state["goal"],
                agents=_available_agents(),
                tools=_available_tools(),
                results=state.get("results", []),
                iteration=state.get("iteration", 0),
            )
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("planner_model"),
            "tools",
            max_tokens=2000,
            structured=dict(type="json"),
        )
        message = await model.ainvoke(prompt)
        plan = parser.parse(
            clean_thinking_content(extract_text_content(message.content))
        )
        return {"plan": plan, "iteration": state.get("iteration", 0) + 1}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def execute_node(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    """Execute every planned tool call, collecting JSON-safe results.

    Unknown tool names are a safety invariant and still raise. A *known* tool
    that fails at runtime (unconfigured web search, a hallucinated argument from
    a small local model, etc.) is recorded as an error entry instead of
    aborting the whole run — the decide/finalize nodes can still synthesize a
    useful answer from whatever succeeded.
    """
    results: list[dict[str, Any]] = []
    for call in state.get("plan", Plan()).tool_calls:
        tool = tool_registry.get(call.tool)
        if tool is None:
            raise InvalidInputError(f"Unknown tool: {call.tool}")
        try:
            output = await tool(**call.args)
        except Exception as e:
            logger.warning(f"Tool '{call.tool}' failed: {e}")
            output = {"error": str(e)}
        results.append({"tool": call.tool, "args": call.args, "output": output})
    return {"results": results}


async def decide_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """Decide whether the gathered results are sufficient to answer."""
    try:
        parser: PydanticOutputParser[Decision] = PydanticOutputParser(
            pydantic_object=Decision
        )
        prompt = Prompter(prompt_template="agent/decide", parser=parser).render(  # type: ignore[arg-type]
            data=dict(
                goal=state["goal"],
                results=state.get("results", []),
                iteration=state.get("iteration", 0),
            )
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("planner_model"),
            "tools",
            max_tokens=500,
            structured=dict(type="json"),
        )
        message = await model.ainvoke(prompt)
        decision = parser.parse(
            clean_thinking_content(extract_text_content(message.content))
        )
        return {"done": decision.done}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def finalize_node(
    state: AgentState, config: RunnableConfig
) -> dict[str, Any]:
    """Synthesize a final answer from the collected tool results."""
    try:
        prompt = Prompter(prompt_template="agent/finalize").render(
            data=dict(goal=state["goal"], results=state.get("results", []))
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("final_answer_model"),
            "tools",
            max_tokens=2000,
        )
        message = await model.ainvoke(prompt)
        return {
            "final_answer": clean_thinking_content(
                extract_text_content(message.content)
            )
        }
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


def should_continue(state: AgentState) -> str:
    """Route to finalize once done or when the iteration budget is spent."""
    if state.get("done") or state.get("iteration", 0) >= MAX_ITERATIONS:
        return "finalize"
    return "plan"


graph_builder = StateGraph(AgentState)
graph_builder.add_node("plan", plan_node)
graph_builder.add_node("execute", execute_node)
graph_builder.add_node("decide", decide_node)
graph_builder.add_node("finalize", finalize_node)
graph_builder.add_edge(START, "plan")
graph_builder.add_edge("plan", "execute")
graph_builder.add_edge("execute", "decide")
graph_builder.add_conditional_edges(
    "decide", should_continue, {"plan": "plan", "finalize": "finalize"}
)
graph_builder.add_edge("finalize", END)

graph = graph_builder.compile()
