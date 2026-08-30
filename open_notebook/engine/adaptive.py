"""Adaptive learning helpers (Road_Map Step 17)."""

from collections import defaultdict
from typing import Any


def select_weak_subjects(
    progress: list[dict[str, Any]], threshold: float = 0.6
) -> list[str]:
    """Return subjects whose average score is below ``threshold``.

    ``progress`` entries are expected to look like
    ``{"subject": str, "score": float}`` (the LearningProgress projection).
    Subjects without any numeric scores are ignored.
    """
    totals: dict[str, list[float]] = defaultdict(list)
    for record in progress:
        subject = record.get("subject")
        score = record.get("score")
        if subject and isinstance(score, (int, float)):
            totals[subject].append(score)

    weak = []
    for subject, scores in totals.items():
        average = sum(scores) / len(scores)
        if average < threshold:
            weak.append(subject)
    return sorted(weak)
