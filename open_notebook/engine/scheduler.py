"""Workflow scheduling helpers (Road_Map Step 22).

A schedule is a simple keyword: ``hourly``, ``daily``, or ``weekly``.
``is_due`` compares the elapsed time since ``last_run``; a workflow that has
never run is always due.
"""

from datetime import datetime, timedelta

_SCHEDULES = {
    "hourly": timedelta(hours=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


def is_due(
    schedule: str, last_run: datetime | None, now: datetime | None = None
) -> bool:
    """Return True when a workflow's schedule has elapsed since last_run."""
    if not schedule:
        return False
    if schedule not in _SCHEDULES:
        raise ValueError(f"Unknown schedule: {schedule}")
    if last_run is None:
        return True
    current = now or datetime.now()
    return current - last_run >= _SCHEDULES[schedule]
