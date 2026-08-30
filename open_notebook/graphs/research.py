"""Research workflow graph (Road_Map Step 12).

The graph chains: gather evidence (internal search + best-effort web search)
→ synthesize a draft report → fact-check the draft against the evidence using
the Control Layer. The result is a source-cited report plus per-claim
verification labels.
"""

import operator
from typing import Annotated, Any

from ai_prompter import Prompter
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from open_notebook.agents.web import web_search
from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.notebook import text_search
from open_notebook.exceptions import ConfigurationError, OpenNotebookError
from open_notebook.graphs.control import Claim
from open_notebook.graphs.control import verify_node as control_verify_node
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content


class ResearchState(TypedDict, total=False):
    question: str
    evidence: Annotated[list[dict[str, Any]], operator.add]
    draft: str
    claims: list[Claim]


async def gather_node(
    state: ResearchState, config: RunnableConfig
) -> dict[str, Any]:
    """Collect evidence from internal search and, if configured, web search."""
    try:
        evidence: list[dict[str, Any]] = []

        internal = await text_search(
            state["question"], 5, source=True, note=True
        )
        for item in internal or []:
            if isinstance(item, dict):
                evidence.append(
                    {
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "content": (
                            item.get("full_text") or item.get("content") or ""
                        )[:500],
                    }
                )

        # Web research is opt-in: an unconfigured provider must not fail the
        # whole run — the report simply relies on the internal knowledge base.
        try:
            external = await web_search(state["question"], limit=3)
            for item in external:
                evidence.append(
                    {
                        "id": item.get("url") or item.get("id") or "web",
                        "title": item.get("title") or "web",
                        "content": str(
                            item.get("snippet") or item.get("content") or ""
                        )[:500],
                    }
                )
        except ConfigurationError:
            pass

        return {"evidence": evidence}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def synthesize_node(
    state: ResearchState, config: RunnableConfig
) -> dict[str, Any]:
    """Write a source-cited draft report from the gathered evidence."""
    try:
        prompt = Prompter(prompt_template="research/synthesize").render(
            data=dict(question=state["question"], evidence=state.get("evidence", []))
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("research_model"),
            "tools",
            max_tokens=2000,
        )
        message = await model.ainvoke(prompt)
        return {
            "draft": clean_thinking_content(extract_text_content(message.content))
        }
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def fact_check_node(
    state: ResearchState, config: RunnableConfig
) -> dict[str, Any]:
    """Verify the draft against the evidence via the Control Layer."""
    result = await control_verify_node(
        {"answer": state.get("draft", ""), "evidence": state.get("evidence", [])},
        config,
    )
    return {"claims": result["claims"]}


graph_builder = StateGraph(ResearchState)
graph_builder.add_node("gather", gather_node)
graph_builder.add_node("synthesize", synthesize_node)
graph_builder.add_node("fact_check", fact_check_node)
graph_builder.add_edge(START, "gather")
graph_builder.add_edge("gather", "synthesize")
graph_builder.add_edge("synthesize", "fact_check")
graph_builder.add_edge("fact_check", END)

graph = graph_builder.compile()
