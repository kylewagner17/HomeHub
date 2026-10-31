"""Next-due rules for maintenance items (ADR-007)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class NextDueResult:
    next_due_at: datetime | None
    next_due_mileage: int | None


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def compute_next_due_after_completion(
    completed_at: datetime,
    mileage_at_completion: int | None,
    interval_days: int | None,
    interval_miles: int | None,
) -> NextDueResult:
    """Compute next due date/mileage from a completion event."""
    completed_at = ensure_utc(completed_at)
    next_due_at = None
    if interval_days is not None and interval_days > 0:
        next_due_at = completed_at + timedelta(days=interval_days)
    next_due_mileage = None
    if (
        interval_miles is not None
        and interval_miles > 0
        and mileage_at_completion is not None
    ):
        next_due_mileage = mileage_at_completion + interval_miles
    return NextDueResult(next_due_at=next_due_at, next_due_mileage=next_due_mileage)


def is_overdue(
    now: datetime,
    next_due_at: datetime | None,
    next_due_mileage: int | None,
    current_mileage: int | None,
) -> bool:
    now = ensure_utc(now)
    if next_due_at is not None and ensure_utc(next_due_at) <= now:
        return True
    if (
        next_due_mileage is not None
        and current_mileage is not None
        and current_mileage >= next_due_mileage
    ):
        return True
    return False
