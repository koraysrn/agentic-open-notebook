"""Research API: run the research graph (Road_Map Step 12).

The research graph gathers evidence (internal search + best-effort web search),
synthesizes a draft report, and fact-checks it through the Control Layer. This
router exposes that workflow synchronously so the Research page can show a
source-cited report and per-claim verification labels.
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from open_notebook.exceptions import OpenNotebookError
from open_notebook.graphs.research import graph as research_graph

router = APIRouter()


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Research question.")

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class EvidenceResponse(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    content: str = ""


class ClaimResponse(BaseModel):
    text: str
    label: str
    confidence: float


class ResearchResponse(BaseModel):
    draft: str
    claims: list[ClaimResponse] = []
    evidence: list[EvidenceResponse] = []


def _claim_to_response(claim: Any) -> ClaimResponse:
    if isinstance(claim, dict):
        return ClaimResponse(
            text=str(claim.get("text") or ""),
            label=str(claim.get("label") or "unverified"),
            confidence=float(claim.get("confidence") or 0.0),
        )
    return ClaimResponse(
        text=getattr(claim, "text", ""),
        label=getattr(claim, "label", "unverified"),
        confidence=float(getattr(claim, "confidence", 0.0) or 0.0),
    )


@router.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest) -> ResearchResponse:
    """Run the research workflow for a question."""
    try:
        result = await research_graph.ainvoke(  # type: ignore[call-overload]
            {"question": request.question}
        )

        evidence = [
            EvidenceResponse(
                id=item.get("id") if isinstance(item, dict) else None,
                title=item.get("title") if isinstance(item, dict) else None,
                content=str(
                    (item.get("content") if isinstance(item, dict) else "") or ""
                ),
            )
            for item in result.get("evidence", [])
        ]
        claims = [_claim_to_response(c) for c in result.get("claims", [])]

        return ResearchResponse(
            draft=str(result.get("draft") or ""),
            claims=claims,
            evidence=evidence,
        )
    except OpenNotebookError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during research: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {e}")
