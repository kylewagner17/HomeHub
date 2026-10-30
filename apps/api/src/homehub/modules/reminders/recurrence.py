"""Advance reminder schedule for M4 recurrence subset (see ADR-006)."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum


class RecurrenceKind(StrEnum):
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


def normalize_recurrence(recurrence: str) -> str:
    """Map legacy `none` to `one_time` (ADR-006 follow-up)."""
    if recurrence == "none":
        return RecurrenceKind.ONE_TIME
    return recurrence


def advance_next_fire(current: datetime, recurrence: str) -> datetime | None:
    """Return the next fire time after *current*, or None when recurrence is one-shot."""
    kind = RecurrenceKind(normalize_recurrence(recurrence))
    if kind is RecurrenceKind.ONE_TIME:
        return None
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    if kind is RecurrenceKind.DAILY:
        return current + timedelta(days=1)
    if kind is RecurrenceKind.WEEKLY:
        return current + timedelta(weeks=1)
    # Monthly: same clock time, add one calendar month (clamp day when needed).
    month = current.month + 1
    year = current.year
    if month > 12:
        month = 1
        year += 1
    day = min(current.day, _days_in_month(year, month))
    return current.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=UTC)
    this_month = datetime(year, month, 1, tzinfo=UTC)
    return (next_month - this_month).days
