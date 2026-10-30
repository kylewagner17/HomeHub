from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReminderResponse(BaseModel):
    id: UUID
    family_id: UUID
    title: str
    body: str | None
    assignee_user_id: UUID | None
    recurrence: str
    enabled: bool
    next_fire_at: datetime
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class CreateReminderRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=2000)
    assignee_user_id: UUID | None = None
    recurrence: str = Field(default="one_time", pattern="^(one_time|none|daily|weekly|monthly)$")
    next_fire_at: datetime

    @field_validator("recurrence")
    @classmethod
    def normalize_recurrence(cls, value: str) -> str:
        return "one_time" if value == "none" else value


class UpdateReminderRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=2000)
    assignee_user_id: UUID | None = None
    recurrence: str | None = Field(
        default=None, pattern="^(one_time|none|daily|weekly|monthly)$"
    )
    next_fire_at: datetime | None = None
    enabled: bool | None = None

    @field_validator("recurrence")
    @classmethod
    def normalize_recurrence(cls, value: str | None) -> str | None:
        if value == "none":
            return "one_time"
        return value


class ReminderFireLogResponse(BaseModel):
    id: UUID
    reminder_id: UUID
    family_id: UUID
    scheduled_at: datetime
    fired_at: datetime
    title: str


class UserNotificationResponse(BaseModel):
    id: UUID
    family_id: UUID
    reminder_id: UUID | None
    title: str
    body: str | None
    created_at: datetime
    read_at: datetime | None
