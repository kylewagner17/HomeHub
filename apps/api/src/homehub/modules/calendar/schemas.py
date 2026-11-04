from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CalendarEventResponse(BaseModel):
    id: UUID
    family_id: UUID
    owner_user_id: UUID
    title: str
    description: str | None
    location: str | None
    starts_at: datetime
    ends_at: datetime
    all_day: bool
    timezone: str | None
    visibility: str
    external_provider: str | None
    external_uid: str | None
    created_at: datetime
    updated_at: datetime


class CreateCalendarEventRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=500)
    starts_at: datetime
    ends_at: datetime
    all_day: bool = False
    timezone: str | None = Field(default=None, max_length=64)
    visibility: str = Field(default="family", pattern="^(personal|family)$")


class UpdateCalendarEventRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    all_day: bool | None = None
    timezone: str | None = Field(default=None, max_length=64)
    visibility: str | None = Field(default=None, pattern="^(personal|family)$")


class ImportIcalRequest(BaseModel):
    ics_text: str = Field(min_length=10)


class ImportGoogleRequest(BaseModel):
    time_min: datetime
    time_max: datetime


class CalendarImportResult(BaseModel):
    imported: int
    skipped_duplicates: int


class GoogleOAuthCodeRequest(BaseModel):
    code: str = Field(min_length=1)
    redirect_uri: str = Field(min_length=1)


class GoogleConnectionStatus(BaseModel):
    connected: bool


class GoogleAuthorizeResponse(BaseModel):
    authorize_url: str | None
