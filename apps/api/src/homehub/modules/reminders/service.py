from datetime import UTC, datetime
from uuid import UUID, uuid4

from homehub.config import get_settings
from homehub.core.errors import HomeHubError
from homehub.jobs.push_dispatch import send_push_to_users
from homehub.modules.auth.models import User
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.reminders.models import Reminder
from homehub.modules.reminders.recurrence import (
    RecurrenceKind,
    advance_next_fire,
    normalize_recurrence,
)
from homehub.modules.reminders.repository import RemindersRepository
from homehub.modules.reminders.schemas import (
    CreateReminderRequest,
    ReminderFireLogResponse,
    ReminderResponse,
    UpdateReminderRequest,
    UserNotificationResponse,
)


class RemindersService:
    """Family reminders CRUD, in-app notifications, and due processing for the scheduler."""

    def __init__(
        self,
        reminders_repo: RemindersRepository,
        families_repo: FamiliesRepository,
    ) -> None:
        self._repo = reminders_repo
        self._families_repo = families_repo

    def list_reminders(self, user: User, family_id: UUID) -> list[ReminderResponse]:
        self._require_member(user.id, family_id)
        return [self._to_reminder_response(r) for r in self._repo.list_for_family(family_id)]

    def create_reminder(
        self, user: User, family_id: UUID, body: CreateReminderRequest
    ) -> ReminderResponse:
        self._require_member(user.id, family_id)
        if body.assignee_user_id is not None:
            self._require_member(body.assignee_user_id, family_id)
        next_fire = self._ensure_aware_utc(body.next_fire_at)
        row = self._repo.create(
            uuid4(),
            family_id,
            body.title.strip(),
            body.body,
            body.assignee_user_id,
            body.recurrence,
            next_fire,
            user.id,
        )
        return self._to_reminder_response(row)

    def update_reminder(
        self, user: User, family_id: UUID, reminder_id: UUID, body: UpdateReminderRequest
    ) -> ReminderResponse:
        self._require_member(user.id, family_id)
        row = self._repo.get_by_id(reminder_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Reminder not found", status_code=404)
        if body.title is not None:
            row.title = body.title.strip()
        if body.body is not None:
            row.body = body.body
        if body.assignee_user_id is not None:
            self._require_member(body.assignee_user_id, family_id)
            row.assignee_user_id = body.assignee_user_id
        if body.recurrence is not None:
            row.recurrence = body.recurrence
        if body.next_fire_at is not None:
            row.next_fire_at = self._ensure_aware_utc(body.next_fire_at)
        if body.enabled is not None:
            row.enabled = body.enabled
        return self._to_reminder_response(row)

    def delete_reminder(self, user: User, family_id: UUID, reminder_id: UUID) -> None:
        self._require_member(user.id, family_id)
        row = self._repo.get_by_id(reminder_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Reminder not found", status_code=404)
        self._repo.soft_delete(row)

    def list_history(self, user: User, family_id: UUID) -> list[ReminderFireLogResponse]:
        self._require_member(user.id, family_id)
        logs = self._repo.list_fire_logs_for_family(family_id)
        return [
            ReminderFireLogResponse(
                id=log.id,
                reminder_id=log.reminder_id,
                family_id=log.family_id,
                scheduled_at=log.scheduled_at,
                fired_at=log.fired_at,
                title=log.title,
            )
            for log in logs
        ]

    def list_notifications(
        self, user: User, since: datetime | None
    ) -> list[UserNotificationResponse]:
        if since is not None:
            since = self._ensure_aware_utc(since)
        rows = self._repo.list_notifications_for_user(user.id, since)
        return [self._to_notification_response(r) for r in rows]

    def mark_notification_read(self, user: User, notification_id: UUID) -> UserNotificationResponse:
        row = self._repo.get_notification(notification_id, user.id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Notification not found", status_code=404)
        if row.read_at is None:
            row.read_at = datetime.now(UTC)
        return self._to_notification_response(row)

    def sync_maintenance_due_reminder(
        self,
        *,
        family_id: UUID,
        created_by: UUID,
        existing_reminder_id: UUID | None,
        title: str,
        body: str | None,
        due_at: datetime | None,
    ) -> UUID | None:
        """Create/update/disable a one-time reminder tied to a maintenance due date."""
        if due_at is None:
            if existing_reminder_id is not None:
                row = self._repo.get_by_id(existing_reminder_id, family_id)
                if row is not None and row.deleted_at is None:
                    row.enabled = False
            return existing_reminder_id

        due_at = self._ensure_aware_utc(due_at)
        if existing_reminder_id is not None:
            row = self._repo.get_by_id(existing_reminder_id, family_id)
            if row is not None and row.deleted_at is None:
                row.title = title
                row.body = body
                row.recurrence = RecurrenceKind.ONE_TIME
                row.next_fire_at = due_at
                row.enabled = True
                return row.id

        row = self._repo.create(
            uuid4(),
            family_id,
            title,
            body,
            None,
            RecurrenceKind.ONE_TIME,
            due_at,
            created_by,
        )
        return row.id

    def process_due_reminders(self, now: datetime) -> int:
        """Fire all due reminders; called by the background scheduler."""
        now = self._ensure_aware_utc(now)
        settings = get_settings()
        due_rows = self._repo.list_due(now)
        for reminder in due_rows:
            self._fire_one(reminder, now, settings)
        return len(due_rows)

    def _fire_one(self, reminder: Reminder, now: datetime, settings) -> None:
        scheduled_at = reminder.next_fire_at
        user_ids = self._target_user_ids(reminder)
        self._repo.add_fire_log(
            uuid4(),
            reminder.id,
            reminder.family_id,
            scheduled_at,
            now,
            reminder.title,
        )
        for user_id in user_ids:
            self._repo.add_notification(
                uuid4(),
                user_id,
                reminder.family_id,
                reminder.id,
                reminder.title,
                reminder.body,
            )
        send_push_to_users(
            self._repo.session,
            settings,
            user_ids,
            reminder.title,
            reminder.body,
        )
        next_at = advance_next_fire(scheduled_at, reminder.recurrence)
        if next_at is None or normalize_recurrence(reminder.recurrence) == RecurrenceKind.ONE_TIME:
            reminder.enabled = False
        else:
            reminder.next_fire_at = next_at

    def _target_user_ids(self, reminder: Reminder) -> list[UUID]:
        if reminder.assignee_user_id is not None:
            return [reminder.assignee_user_id]
        memberships = self._families_repo.list_memberships_for_family(reminder.family_id)
        return [m.user_id for m in memberships]

    def _require_member(self, user_id: UUID, family_id: UUID) -> None:
        if self._families_repo.get_membership(user_id, family_id) is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)

    @staticmethod
    def _ensure_aware_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    @staticmethod
    def _to_reminder_response(row: Reminder) -> ReminderResponse:
        return ReminderResponse(
            id=row.id,
            family_id=row.family_id,
            title=row.title,
            body=row.body,
            assignee_user_id=row.assignee_user_id,
            recurrence=normalize_recurrence(row.recurrence),
            enabled=row.enabled,
            next_fire_at=row.next_fire_at,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_notification_response(row) -> UserNotificationResponse:
        return UserNotificationResponse(
            id=row.id,
            family_id=row.family_id,
            reminder_id=row.reminder_id,
            title=row.title,
            body=row.body,
            created_at=row.created_at,
            read_at=row.read_at,
        )
