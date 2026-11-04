from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from homehub.modules.calendar.models import CalendarEvent


class CalendarRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_visible_in_range(
        self,
        family_id: UUID,
        user_id: UUID,
        range_start: datetime,
        range_end: datetime,
    ) -> list[CalendarEvent]:
        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.family_id == family_id,
                CalendarEvent.deleted_at.is_(None),
                CalendarEvent.starts_at < range_end,
                CalendarEvent.ends_at > range_start,
                or_(
                    CalendarEvent.visibility == "family",
                    CalendarEvent.owner_user_id == user_id,
                ),
            )
            .order_by(CalendarEvent.starts_at.asc())
        )
        return list(self._session.scalars(stmt))

    def get_event(self, event_id: UUID, family_id: UUID) -> CalendarEvent | None:
        stmt = select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.family_id == family_id,
            CalendarEvent.deleted_at.is_(None),
        )
        return self._session.scalar(stmt)

    def list_active_for_family(self, family_id: UUID) -> list[CalendarEvent]:
        stmt = select(CalendarEvent).where(
            CalendarEvent.family_id == family_id,
            CalendarEvent.deleted_at.is_(None),
        )
        return list(self._session.scalars(stmt))

    def create(self, row: CalendarEvent) -> CalendarEvent:
        self._session.add(row)
        self._session.flush()
        return row

    def save(self, row: CalendarEvent) -> CalendarEvent:
        self._session.add(row)
        self._session.flush()
        return row
