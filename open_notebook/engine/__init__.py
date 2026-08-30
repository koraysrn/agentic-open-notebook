"""Application engines built on the Open Notebook core.

These engines are additive layers (ADR-008): they consume domain models and
tools, and never rewrite core behaviour.
"""

from open_notebook.engine.adaptive import select_weak_subjects
from open_notebook.engine.persona import build_persona_prompt
from open_notebook.engine.workflow import run_definition, validate_definition

__all__ = [
    "build_persona_prompt",
    "run_definition",
    "select_weak_subjects",
    "validate_definition",
]
