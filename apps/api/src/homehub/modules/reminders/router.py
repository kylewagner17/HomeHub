from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.reminders.repository import RemindersRepository
from homehub.modules.reminders.schemas import (
    CreateReminderRequest,
    ReminderFireLogResponse,
    ReminderResponse,
    UpdateReminderRequest,
    UserNotificationResponse,
)
from homehub.modules.reminders.service import RemindersService

reminders_router = APIRouter(prefix="/families/{family_id}/reminders", tags=["reminders"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


def _service(db: DbSession) -> RemindersService:
    return RemindersService(RemindersRepository(db), FamiliesRepository(db))


@reminders_router.get("", response_model=list[ReminderResponse])
def list_reminders(family_id: UUID, user: CurrentUser, db: DbSession) -> list[ReminderResponse]:
    return _service(db).list_reminders(user, family_id)


@reminders_router.post("", response_model=ReminderResponse)
def create_reminder(
    family_id: UUID, body: CreateReminderRequest, user: CurrentUser, db: DbSession
) -> ReminderResponse:
    result = _service(db).create_reminder(user, family_id, body)
    db.commit()
    return result


@reminders_router.patch("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    family_id: UUID,
    reminder_id: UUID,
    body: UpdateReminderRequest,
    user: CurrentUser,
    db: DbSession,
) -> ReminderResponse:
    result = _service(db).update_reminder(user, family_id, reminder_id, body)
    db.commit()
    return result


@reminders_router.delete("/{reminder_id}", status_code=204)
def delete_reminder(
    family_id: UUID, reminder_id: UUID, user: CurrentUser, db: DbSession
) -> None:
    _service(db).delete_reminder(user, family_id, reminder_id)
    db.commit()


@reminders_router.get("/history", response_model=list[ReminderFireLogResponse])
def reminder_history(
    family_id: UUID, user: CurrentUser, db: DbSession
) -> list[ReminderFireLogResponse]:
    return _service(db).list_history(user, family_id)


@notifications_router.get("", response_model=list[UserNotificationResponse])
def list_notifications(
    user: CurrentUser,
    db: DbSession,
    since: Annotated[datetime | None, Query()] = None,
) -> list[UserNotificationResponse]:
    return _service(db).list_notifications(user, since)


@notifications_router.patch("/{notification_id}/read", response_model=UserNotificationResponse)
def read_notification(
    notification_id: UUID, user: CurrentUser, db: DbSession
) -> UserNotificationResponse:
    result = _service(db).mark_notification_read(user, notification_id)
    db.commit()
    return result
