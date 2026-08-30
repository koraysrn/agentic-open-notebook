"""Persona persistence (Road_Map Step 15).

A persona is a perspective: it reframes source facts for an audience without
changing them (PROJE MİMARİSİ.md).
"""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class Persona(ObjectModel):
    """A named expert perspective with a base system prompt."""

    table_name: ClassVar[str] = "persona"
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
