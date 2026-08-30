"""Control Layer: evidence and citation verification (Road_Map Step 8).

The verification graph splits an answer into atomic claims and labels each
claim with one of the four information types from PROJE MİMARİSİ.md:

    verified   — directly supported by the provided evidence.
    external   — grounded in general world knowledge, not the evidence.
    inferred   — a reasoned conclusion drawn from the evidence.
    unverified — unsupported by both evidence and general knowledge.

The graph is a single LLM node for now; contradiction detection and
hallucination scoring build on top of this in Steps 9 and 10.
"""

from typing import Any, Literal

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.exceptions import OpenNotebookError
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content

ClaimLabel = Literal["verified", "external", "inferred", "unverified"]


class Claim(BaseModel):
    """One atomic claim extracted from an answer, with its verification label."""

    text: str = Field(description="The claim text.")
    label: ClaimLabel = Field(description="Verification label.")
    evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence ids supporting the claim."
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score in [0, 1]."
    )


class VerificationResult(BaseModel):
    claims: list[Claim] = Field(default_factory=list)


class ControlState(TypedDict, total=False):
    answer: str
    evidence: list[dict[str, Any]]
    claims: list[Claim]


async def verify_node(
    state: ControlState, config: RunnableConfig
) -> dict[str, Any]:
    """Extract and label claims from an answer against the given evidence."""
    try:
        parser: PydanticOutputParser[VerificationResult] = PydanticOutputParser(
            pydantic_object=VerificationResult
        )
        prompt = Prompter(prompt_template="control/verify", parser=parser).render(  # type: ignore[arg-type]
            data=dict(
                answer=state["answer"],
                evidence=state.get("evidence", []),
            )
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("verifier_model"),
            "tools",
            max_tokens=2000,
            structured=dict(type="json"),
        )
        message = await model.ainvoke(prompt)
        result = parser.parse(
            clean_thinking_content(extract_text_content(message.content))
        )
        return {"claims": result.claims}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


graph_builder = StateGraph(ControlState)
graph_builder.add_node("verify", verify_node)
graph_builder.add_edge(START, "verify")
graph_builder.add_edge("verify", END)

graph = graph_builder.compile()


class Contradiction(BaseModel):
    """A pair of conflicting statements found across evidence items."""

    statement_a: str = Field(description="First conflicting statement.")
    evidence_a_ids: list[str] = Field(
        default_factory=list, description="Evidence ids for the first statement."
    )
    statement_b: str = Field(description="Second conflicting statement.")
    evidence_b_ids: list[str] = Field(
        default_factory=list, description="Evidence ids for the second statement."
    )
    reasoning: str = Field(default="", description="Why the two conflict.")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score in [0, 1]."
    )


class ContradictionResult(BaseModel):
    contradictions: list[Contradiction] = Field(default_factory=list)


class ContradictionState(TypedDict, total=False):
    evidence: list[dict[str, Any]]
    contradictions: list[Contradiction]


async def contradiction_node(
    state: ContradictionState, config: RunnableConfig
) -> dict[str, Any]:
    """Detect contradictory statements across the provided evidence."""
    try:
        parser: PydanticOutputParser[ContradictionResult] = PydanticOutputParser(
            pydantic_object=ContradictionResult
        )
        prompt = Prompter(prompt_template="control/contradiction", parser=parser).render(  # type: ignore[arg-type]
            data=dict(evidence=state.get("evidence", []))
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("verifier_model"),
            "tools",
            max_tokens=2000,
            structured=dict(type="json"),
        )
        message = await model.ainvoke(prompt)
        result = parser.parse(
            clean_thinking_content(extract_text_content(message.content))
        )
        return {"contradictions": result.contradictions}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


contradiction_builder = StateGraph(ContradictionState)
contradiction_builder.add_node("detect", contradiction_node)
contradiction_builder.add_edge(START, "detect")
contradiction_builder.add_edge("detect", END)

contradiction_graph = contradiction_builder.compile()


class HallucinationCheck(BaseModel):
    """Best-effort hallucination signal for an answer against evidence."""

    supported: bool = Field(
        description="True if the answer is supported by the provided evidence."
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score in [0, 1]."
    )
    reasoning: str = Field(default="", description="Why the verdict was reached.")


class HallucinationState(TypedDict, total=False):
    answer: str
    evidence: list[dict[str, Any]]
    check: HallucinationCheck


async def hallucination_node(
    state: HallucinationState, config: RunnableConfig
) -> dict[str, Any]:
    """Judge whether an answer is supported by the provided evidence.

    This is deliberately a best-effort signal, not a deterministic guarantee:
    LLM-as-judge can itself err, so callers must treat ``supported=False`` as
    a prompt to re-check rather than as ground truth.
    """
    try:
        parser: PydanticOutputParser[HallucinationCheck] = PydanticOutputParser(
            pydantic_object=HallucinationCheck
        )
        prompt = Prompter(prompt_template="control/hallucination", parser=parser).render(  # type: ignore[arg-type]
            data=dict(answer=state["answer"], evidence=state.get("evidence", []))
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("verifier_model"),
            "tools",
            max_tokens=500,
            structured=dict(type="json"),
        )
        message = await model.ainvoke(prompt)
        check = parser.parse(
            clean_thinking_content(extract_text_content(message.content))
        )
        return {"check": check}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


hallucination_builder = StateGraph(HallucinationState)
hallucination_builder.add_node("judge", hallucination_node)
hallucination_builder.add_edge(START, "judge")
hallucination_builder.add_edge("judge", END)

hallucination_graph = hallucination_builder.compile()
