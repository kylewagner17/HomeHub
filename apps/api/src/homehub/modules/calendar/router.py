from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.calendar.schemas import (
    CalendarEventResponse,
    CalendarImportResult,
    CreateCalendarEventRequest,
    ImportGoogleRequest,
    ImportIcalRequest,
    UpdateCalendarEventRequest,
)
from homehub.modules.calendar.service import build_calendar_service

router = APIRouter(prefix="/families/{family_id}/calendar", tags=["calendar"])


@router.get("/events", response_model=list[CalendarEventResponse])
def list_events(
    family_id: UUID,
    user: CurrentUser,
    db: DbSession,
    start: Annotated[datetime, Query(description="Range start (ISO8601)")],
    end: Annotated[datetime, Query(description="Range end (ISO8601)")],
) -> list[CalendarEventResponse]:
    return build_calendar_service(db).list_events(user, family_id, start, end)


@router.post("/events", response_model=CalendarEventResponse)
def create_event(
    family_id: UUID,
    body: CreateCalendarEventRequest,
    user: CurrentUser,
    db: DbSession,
) -> CalendarEventResponse:
    result = build_calendar_service(db).create_event(user, family_id, body)
    db.commit()
    return result


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
def update_event(
    family_id: UUID,
    event_id: UUID,
    body: UpdateCalendarEventRequest,
    user: CurrentUser,
    db: DbSession,
) -> CalendarEventResponse:
    result = build_calendar_service(db).update_event(user, family_id, event_id, body)
    db.commit()
    return result


@router.delete("/events/{event_id}", status_code=204)
def delete_event(
    family_id: UUID,
    event_id: UUID,
    user: CurrentUser,
    db: DbSession,
) -> None:
    build_calendar_service(db).delete_event(user, family_id, event_id)
    db.commit()


@router.post("/import/ical", response_model=CalendarImportResult)
def import_ical(
    family_id: UUID,
    body: ImportIcalRequest,
    user: CurrentUser,
    db: DbSession,
) -> CalendarImportResult:
    result = build_calendar_service(db).import_ical(user, family_id, body.ics_text)
    db.commit()
    return result


@router.post("/import/google", response_model=CalendarImportResult)
def import_google(
    family_id: UUID,
    body: ImportGoogleRequest,
    user: CurrentUser,
    db: DbSession,
) -> CalendarImportResult:
    result = build_calendar_service(db).import_google(
        user, family_id, body.time_min, body.time_max
    )
    db.commit()
    return result


@router.get("/export/ical")
def export_ical(
    family_id: UUID,
    user: CurrentUser,
    db: DbSession,
    start: Annotated[datetime, Query()],
    end: Annotated[datetime, Query()],
) -> PlainTextResponse:
    text = build_calendar_service(db).export_ical(user, family_id, start, end)
    return PlainTextResponse(content=text, media_type="text/calendar")
