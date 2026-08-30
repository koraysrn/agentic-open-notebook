"""Education Engine graph (Road_Map Step 16).

Given source content, the graph produces structured learning material: a
study plan, an explanation, a quiz, and flashcards. Output is provider-
agnostic via a Pydantic output parser.
"""

from typing import Any

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


class Question(BaseModel):
    text: str
    answer: str


class Flashcard(BaseModel):
    front: str
    back: str


class StudyPlanStep(BaseModel):
    topic: str
    minutes: int


class StudyPlan(BaseModel):
    steps: list[StudyPlanStep] = Field(default_factory=list)


class EducationMaterial(BaseModel):
    plan: StudyPlan = Field(default_factory=StudyPlan)
    explanation: str = ""
    quiz: list[Question] = Field(default_factory=list)
    flashcards: list[Flashcard] = Field(default_factory=list)


class EducationState(TypedDict, total=False):
    source_content: str
    material: EducationMaterial


async def generate_material(
    state: EducationState, config: RunnableConfig
) -> dict[str, Any]:
    """Generate study plan, explanation, quiz, and flashcards."""
    try:
        parser: PydanticOutputParser[EducationMaterial] = PydanticOutputParser(
            pydantic_object=EducationMaterial
        )
        prompt = Prompter(prompt_template="education/material", parser=parser).render(  # type: ignore[arg-type]
            data=dict(source_content=state["source_content"])
        )
        model = await provision_langchain_model(
            prompt,
            config.get("configurable", {}).get("education_model"),
            "tools",
            max_tokens=2000,
            structured=dict(type="json"),
        )
        message = await model.ainvoke(prompt)
        material = parser.parse(
            clean_thinking_content(extract_text_content(message.content))
        )
        return {"material": material}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


graph_builder = StateGraph(EducationState)
graph_builder.add_node("generate", generate_material)
graph_builder.add_edge(START, "generate")
graph_builder.add_edge("generate", END)

graph = graph_builder.compile()
