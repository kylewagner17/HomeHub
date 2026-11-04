from datetime import UTC, datetime
from uuid import uuid4

from homehub.modules.calendar.dedupe import is_duplicate_event
from homehub.modules.calendar.ical import ParsedIcalEvent, parse_ics_events, serialize_events_to_ics
from homehub.modules.calendar.models import CalendarEvent


def test_parse_ics_vevent():
    ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:abc@x
SUMMARY:Test
DTSTART:20260102T100000Z
DTEND:20260102T110000Z
END:VEVENT
END:VCALENDAR"""
    events = parse_ics_events(ics)
    assert len(events) == 1
    assert events[0].uid == "abc@x"
    assert events[0].title == "Test"


def test_serialize_roundtrip_shape():
    ev = ParsedIcalEvent(
        uid="u1",
        title="Hi",
        description=None,
        location=None,
        starts_at=datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 2, 11, 0, tzinfo=UTC),
        all_day=False,
    )
    text = serialize_events_to_ics([ev])
    assert "BEGIN:VEVENT" in text
    assert "SUMMARY:Hi" in text


def test_dedupe_by_external_uid():
    existing = CalendarEvent(
        id=uuid4(),
        family_id=uuid4(),
        owner_user_id=uuid4(),
        title="X",
        description=None,
        location=None,
        starts_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 13, 0, tzinfo=UTC),
        all_day=False,
        timezone=None,
        visibility="family",
        external_provider="ical",
        external_uid="same-uid",
        created_by=None,
    )
    assert is_duplicate_event(
        existing,
        title="Different",
        starts_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
        ends_at=datetime(2026, 5, 1, 13, 0, tzinfo=UTC),
        external_provider="ical",
        external_uid="same-uid",
    )
