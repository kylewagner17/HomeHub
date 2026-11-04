"""Duplicate detection for calendar import (ADR-008)."""

from datetime import UTC, datetime, timedelta

from homehub.modules.calendar.models import CalendarEvent


def normalize_title(title: str) -> str:
    return " ".join(title.strip().lower().split())


def starts_match(a: datetime, b: datetime, tolerance: timedelta = timedelta(minutes=1)) -> bool:
    aa = a.astimezone(UTC) if a.tzinfo else a.replace(tzinfo=UTC)
    bb = b.astimezone(UTC) if b.tzinfo else b.replace(tzinfo=UTC)
    return abs(aa - bb) <= tolerance


def is_duplicate_event(
    existing: CalendarEvent,
    *,
    title: str,
    starts_at: datetime,
    ends_at: datetime,
    external_provider: str | None,
    external_uid: str | None,
) -> bool:
    if existing.deleted_at is not None:
        return False
    if external_uid and existing.external_uid and external_provider:
        if (
            existing.external_uid == external_uid
            and existing.external_provider == external_provider
        ):
            return True
    return (
        normalize_title(existing.title) == normalize_title(title)
        and starts_match(existing.starts_at, starts_at)
        and starts_match(existing.ends_at, ends_at, tolerance=timedelta(minutes=1))
    )
