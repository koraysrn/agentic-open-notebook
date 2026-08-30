"""Education API: generate study material via the Education Engine graph.

Given pasted source content, the graph produces structured learning material:
a study plan, an explanation, a quiz, and flashcards.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from open_notebook.exceptions import OpenNotebookError
from open_notebook.graphs.education import graph as education_graph

router = APIRouter()


class EducationRequest(BaseModel):
    source_content: str = Field(
        ..., min_length=1, description="Source text to build study material from."
    )

    @field_validator("source_content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_content must not be blank")
        return value


class QuestionResponse(BaseModel):
    text: str
    answer: str


class FlashcardResponse(BaseModel):
    front: str
    back: str


class StudyPlanStepResponse(BaseModel):
    topic: str
    minutes: int


class EducationResponse(BaseModel):
    explanation: str
    plan: list[StudyPlanStepResponse] = []
    quiz: list[QuestionResponse] = []
    flashcards: list[FlashcardResponse] = []


def _to_response(material: Any) -> EducationResponse:
    """Normalize either a pydantic EducationMaterial or a plain dict."""
    if isinstance(material, dict):
        plan = material.get("plan")
        steps = plan.get("steps", []) if isinstance(plan, dict) else (plan or [])
        explanation = str(material.get("explanation") or "")
        quiz = material.get("quiz") or []
        flashcards = material.get("flashcards") or []
    else:
        plan = getattr(material, "plan", None)
        steps = getattr(plan, "steps", []) if plan else []
        explanation = str(getattr(material, "explanation", "") or "")
        quiz = getattr(material, "quiz", []) or []
        flashcards = getattr(material, "flashcards", []) or []

    def _text(obj: Any, field: str) -> str:
        if isinstance(obj, dict):
            return str(obj.get(field) or "")
        return str(getattr(obj, field, "") or "")

    return EducationResponse(
        explanation=explanation,
        plan=[
            StudyPlanStepResponse(
                topic=_text(step, "topic"),
                minutes=int(
                    (step.get("minutes") if isinstance(step, dict) else getattr(step, "minutes", 0))
                    or 0
                ),
            )
            for step in steps
        ],
        quiz=[
            QuestionResponse(text=_text(q, "text"), answer=_text(q, "answer"))
            for q in quiz
        ],
        flashcards=[
            FlashcardResponse(front=_text(f, "front"), back=_text(f, "back"))
            for f in flashcards
        ],
    )


@router.post("/education/material", response_model=EducationResponse)
async def generate_material(request: EducationRequest) -> EducationResponse:
    """Generate a study plan, explanation, quiz, and flashcards."""
    try:
        result = await education_graph.ainvoke(
            {"source_content": request.source_content}
        )
        material = result.get("material")
        if material is None:
            return EducationResponse(explanation="")
        return _to_response(material)
    except OpenNotebookError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during education generation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Education generation failed: {e}"
        )
