"""Persona Engine (Road_Map Step 15).

A persona is a perspective: it changes how information is framed, never the
underlying facts. ``build_persona_prompt`` composes the persona's system
prompt with a task prompt so callers can route any generation through a
persona without rewriting the source content.
"""

from open_notebook.domain.persona import Persona


def build_persona_prompt(persona: Persona, task: str) -> str:
    """Combine a persona's perspective with a task prompt."""
    persona_part = (persona.system_prompt or "").strip()
    task_part = task.strip()
    if not persona_part:
        return task_part
    if not task_part:
        return persona_part
    return f"{persona_part}\n\nTask:\n{task_part}"
