from datetime import UTC, datetime, timedelta

from homehub.modules.maintenance.scheduling import (
    compute_next_due_after_completion,
    is_overdue,
)


def test_filter_next_due_by_days():
    completed = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    result = compute_next_due_after_completion(completed, None, 90, None)
    assert result.next_due_at == datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    assert result.next_due_mileage is None


def test_oil_change_next_due_date_and_mileage():
    completed = datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    result = compute_next_due_after_completion(completed, 50_000, 180, 5000)
    assert result.next_due_at == completed + timedelta(days=180)
    assert result.next_due_mileage == 55_000


def test_overdue_by_date():
    now = datetime(2026, 5, 1, tzinfo=UTC)
    due = datetime(2026, 4, 1, tzinfo=UTC)
    assert is_overdue(now, due, None, None) is True


def test_overdue_by_mileage():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert is_overdue(now, None, 55_000, 55_500) is True
