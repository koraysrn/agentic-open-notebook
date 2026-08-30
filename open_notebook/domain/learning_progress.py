"""Adaptive learning progress persistence (Road_Map Step 17)."""

from typing import ClassVar, Optional

from open_notebook.domain.base import ObjectModel


class LearningProgress(ObjectModel):
    """A record of a learner's performance on a subject within a notebook."""

    table_name: ClassVar[str] = "learning_progress"
    notebook: Optional[str] = None
    subject: Optional[str] = None
    score: Optional[float] = None
    weak_topics: Optional[list[str]] = None
