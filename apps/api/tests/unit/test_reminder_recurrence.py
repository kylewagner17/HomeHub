from datetime import UTC, datetime

from homehub.modules.reminders.recurrence import RecurrenceKind, advance_next_fire


def test_daily_advances_one_day():
    start = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
    nxt = advance_next_fire(start, RecurrenceKind.DAILY)
    assert nxt == datetime(2026, 1, 16, 9, 0, tzinfo=UTC)


def test_weekly_advances_seven_days():
    start = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
    nxt = advance_next_fire(start, RecurrenceKind.WEEKLY)
    assert nxt == datetime(2026, 1, 22, 9, 0, tzinfo=UTC)


def test_one_time_returns_none():
    start = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
    assert advance_next_fire(start, RecurrenceKind.ONE_TIME) is None


def test_legacy_none_treated_as_one_time():
    start = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
    assert advance_next_fire(start, "none") is None


def test_monthly_clamps_end_of_month():
    start = datetime(2026, 1, 31, 8, 30, tzinfo=UTC)
    nxt = advance_next_fire(start, RecurrenceKind.MONTHLY)
    assert nxt == datetime(2026, 2, 28, 8, 30, tzinfo=UTC)
