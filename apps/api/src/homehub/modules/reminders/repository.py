from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from homehub.modules.reminders.models import Reminder, ReminderFireLog, UserNotification


class RemindersRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def list_for_family(self, family_id: UUID) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(Reminder.family_id == family_id, Reminder.deleted_at.is_(None))
            .order_by(Reminder.next_fire_at.asc())
        )
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, reminder_id: UUID, family_id: UUID) -> Reminder | None:
        stmt = select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.family_id == family_id,
            Reminder.deleted_at.is_(None),
        )
        return self._session.scalar(stmt)

    def create(
        self,
        reminder_id: UUID,
        family_id: UUID,
        title: str,
        body: str | None,
        assignee_user_id: UUID | None,
        recurrence: str,
        next_fire_at: datetime,
        created_by: UUID,
    ) -> Reminder:
        row = Reminder(
            id=reminder_id,
            family_id=family_id,
            title=title,
            body=body,
            assignee_user_id=assignee_user_id,
            recurrence=recurrence,
            enabled=True,
            next_fire_at=next_fire_at,
            created_by=created_by,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def soft_delete(self, row: Reminder) -> None:
        row.deleted_at = datetime.now(UTC)
        row.enabled = False
        self._session.flush()

    def list_due(self, now: datetime) -> list[Reminder]:
        stmt = select(Reminder).where(
            Reminder.enabled.is_(True),
            Reminder.deleted_at.is_(None),
            Reminder.next_fire_at <= now,
        )
        return list(self._session.scalars(stmt).all())

    def add_fire_log(
        self,
        log_id: UUID,
        reminder_id: UUID,
        family_id: UUID,
        scheduled_at: datetime,
        fired_at: datetime,
        title: str,
    ) -> ReminderFireLog:
        row = ReminderFireLog(
            id=log_id,
            reminder_id=reminder_id,
            family_id=family_id,
            scheduled_at=scheduled_at,
            fired_at=fired_at,
            title=title,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def list_fire_logs_for_family(self, family_id: UUID, limit: int = 100) -> list[ReminderFireLog]:
        stmt = (
            select(ReminderFireLog)
            .where(ReminderFireLog.family_id == family_id)
            .order_by(ReminderFireLog.fired_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def add_notification(
        self,
        notification_id: UUID,
        user_id: UUID,
        family_id: UUID,
        reminder_id: UUID | None,
        title: str,
        body: str | None,
    ) -> UserNotification:
        row = UserNotification(
            id=notification_id,
            user_id=user_id,
            family_id=family_id,
            reminder_id=reminder_id,
            title=title,
            body=body,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def list_notifications_for_user(
        self, user_id: UUID, since: datetime | None, limit: int = 50
    ) -> list[UserNotification]:
        stmt = select(UserNotification).where(UserNotification.user_id == user_id)
        if since is not None:
            stmt = stmt.where(UserNotification.created_at > since)
        stmt = stmt.order_by(UserNotification.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())

    def get_notification(self, notification_id: UUID, user_id: UUID) -> UserNotification | None:
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        return self._session.scalar(stmt)
