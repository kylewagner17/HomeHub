from datetime import UTC, datetime
from uuid import UUID, uuid4

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.calendar.dedupe import is_duplicate_event
from homehub.modules.calendar.ical import ParsedIcalEvent, parse_ics_events, serialize_events_to_ics
from homehub.modules.calendar.models import CalendarEvent
from homehub.modules.calendar.repository import CalendarRepository
from homehub.modules.calendar.schemas import (
    CalendarEventResponse,
    CalendarImportResult,
    CreateCalendarEventRequest,
    UpdateCalendarEventRequest,
)
from homehub.modules.families.enums import FamilyRole
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.integrations.google_calendar import (
    exchange_google_code,
    expires_at_from_token_payload,
    external_uid_for_google_event,
    fetch_google_calendar_events,
    google_event_to_fields,
    google_oauth_configured,
    refresh_google_access_token,
)
from homehub.modules.integrations.models import UserCalendarConnection
from homehub.modules.integrations.repository import IntegrationsRepository


class CalendarService:
    """Family calendar CRUD and non-destructive external import."""

    def __init__(
        self,
        calendar_repo: CalendarRepository,
        families_repo: FamiliesRepository,
        integrations_repo: IntegrationsRepository,
    ) -> None:
        self._calendar = calendar_repo
        self._families = families_repo
        self._integrations = integrations_repo

    def list_events(
        self,
        user: User,
        family_id: UUID,
        range_start: datetime,
        range_end: datetime,
    ) -> list[CalendarEventResponse]:
        membership = self._require_member(user.id, family_id)
        _ = membership
        rows = self._calendar.list_visible_in_range(family_id, user.id, range_start, range_end)
        return [self._to_response(row) for row in rows]

    def create_event(
        self, user: User, family_id: UUID, body: CreateCalendarEventRequest
    ) -> CalendarEventResponse:
        self._require_member(user.id, family_id)
        self._validate_range(body.starts_at, body.ends_at)
        row = CalendarEvent(
            id=uuid4(),
            family_id=family_id,
            owner_user_id=user.id,
            title=body.title.strip(),
            description=body.description,
            location=body.location,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            all_day=body.all_day,
            timezone=body.timezone,
            visibility=body.visibility,
            external_provider=None,
            external_uid=None,
            created_by=user.id,
        )
        self._calendar.create(row)
        return self._to_response(row)

    def update_event(
        self,
        user: User,
        family_id: UUID,
        event_id: UUID,
        body: UpdateCalendarEventRequest,
    ) -> CalendarEventResponse:
        membership = self._require_member(user.id, family_id)
        row = self._calendar.get_event(event_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Calendar event not found", status_code=404)
        self._require_edit(row, user.id, membership.role)
        if body.title is not None:
            row.title = body.title.strip()
        if body.description is not None:
            row.description = body.description
        if body.location is not None:
            row.location = body.location
        if body.starts_at is not None:
            row.starts_at = body.starts_at
        if body.ends_at is not None:
            row.ends_at = body.ends_at
        if body.all_day is not None:
            row.all_day = body.all_day
        if body.timezone is not None:
            row.timezone = body.timezone
        if body.visibility is not None:
            row.visibility = body.visibility
        self._validate_range(row.starts_at, row.ends_at)
        self._calendar.save(row)
        return self._to_response(row)

    def delete_event(self, user: User, family_id: UUID, event_id: UUID) -> None:
        membership = self._require_member(user.id, family_id)
        row = self._calendar.get_event(event_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Calendar event not found", status_code=404)
        self._require_edit(row, user.id, membership.role)
        row.deleted_at = datetime.now(UTC)
        self._calendar.save(row)

    def import_ical(
        self, user: User, family_id: UUID, ics_text: str
    ) -> CalendarImportResult:
        self._require_member(user.id, family_id)
        parsed = parse_ics_events(ics_text)
        return self._import_parsed(user, family_id, parsed, provider="ical")

    def import_google(
        self, user: User, family_id: UUID, time_min: datetime, time_max: datetime
    ) -> CalendarImportResult:
        self._require_member(user.id, family_id)
        access_token = self._google_access_token(user.id)
        raw = fetch_google_calendar_events(access_token, time_min, time_max)
        parsed: list[ParsedIcalEvent] = []
        for calendar_id, item in raw:
            try:
                title, start, end, all_day, description = google_event_to_fields(item)
            except ValueError:
                continue
            parsed.append(
                ParsedIcalEvent(
                    uid=external_uid_for_google_event(calendar_id, item),
                    title=title,
                    description=description,
                    location=item.get("location"),
                    starts_at=start,
                    ends_at=end,
                    all_day=all_day,
                )
            )
        return self._import_parsed(user, family_id, parsed, provider="google")

    def export_ical(
        self,
        user: User,
        family_id: UUID,
        range_start: datetime,
        range_end: datetime,
    ) -> str:
        rows = self.list_events(user, family_id, range_start, range_end)
        parsed = [
            ParsedIcalEvent(
                uid=str(row.id),
                title=row.title,
                description=row.description,
                location=row.location,
                starts_at=row.starts_at,
                ends_at=row.ends_at,
                all_day=row.all_day,
            )
            for row in rows
        ]
        return serialize_events_to_ics(parsed)

    def connect_google(self, user: User, code: str, redirect_uri: str) -> None:
        if not google_oauth_configured():
            raise HomeHubError(
                code="GOOGLE_NOT_CONFIGURED",
                message="Google Calendar import is not configured on the server",
                status_code=503,
            )
        payload = exchange_google_code(code, redirect_uri)
        row = UserCalendarConnection(
            id=uuid4(),
            user_id=user.id,
            provider="google",
            access_token=str(payload["access_token"]),
            refresh_token=payload.get("refresh_token"),
            expires_at=expires_at_from_token_payload(payload),
        )
        self._integrations.upsert_connection(row)

    def google_connected(self, user: User) -> bool:
        return self._integrations.get_connection(user.id, "google") is not None

    def _import_parsed(
        self,
        user: User,
        family_id: UUID,
        events: list[ParsedIcalEvent],
        *,
        provider: str,
    ) -> CalendarImportResult:
        existing = self._calendar.list_active_for_family(family_id)
        imported = 0
        skipped = 0
        for ev in events:
            if any(
                is_duplicate_event(
                    row,
                    title=ev.title,
                    starts_at=ev.starts_at,
                    ends_at=ev.ends_at,
                    external_provider=provider,
                    external_uid=ev.uid,
                )
                for row in existing
            ):
                skipped += 1
                continue
            row = CalendarEvent(
                id=uuid4(),
                family_id=family_id,
                owner_user_id=user.id,
                title=ev.title,
                description=ev.description,
                location=ev.location,
                starts_at=ev.starts_at,
                ends_at=ev.ends_at,
                all_day=ev.all_day,
                timezone=None,
                visibility="family",
                external_provider=provider,
                external_uid=ev.uid,
                created_by=user.id,
            )
            self._calendar.create(row)
            existing.append(row)
            imported += 1
        return CalendarImportResult(imported=imported, skipped_duplicates=skipped)

    def _google_access_token(self, user_id: UUID) -> str:
        conn = self._integrations.get_connection(user_id, "google")
        if conn is None:
            raise HomeHubError(
                code="GOOGLE_NOT_CONNECTED",
                message="Connect Google Calendar before importing",
                status_code=400,
            )
        now = datetime.now(UTC)
        if conn.expires_at and conn.expires_at <= now:
            if not conn.refresh_token:
                raise HomeHubError(
                    code="GOOGLE_RECONNECT_REQUIRED",
                    message=(
                        "Google access expired. Connect again via POST "
                        "/api/v1/integrations/google/connect with a new authorization code."
                    ),
                    status_code=400,
                )
            payload = refresh_google_access_token(conn.refresh_token)
            conn.access_token = str(payload["access_token"])
            conn.expires_at = expires_at_from_token_payload(payload)
            self._integrations.upsert_connection(conn)
        return conn.access_token

    def _require_member(self, user_id: UUID, family_id: UUID):
        membership = self._families.get_membership(user_id, family_id)
        if membership is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)
        return membership

    @staticmethod
    def _require_edit(row: CalendarEvent, user_id: UUID, role: FamilyRole) -> None:
        if row.owner_user_id != user_id and role != FamilyRole.admin:
            raise HomeHubError("FORBIDDEN", "Cannot edit this event", status_code=403)

    @staticmethod
    def _validate_range(starts_at: datetime, ends_at: datetime) -> None:
        if ends_at <= starts_at:
            raise HomeHubError(
                code="INVALID_RANGE",
                message="Event end must be after start",
                status_code=422,
            )

    @staticmethod
    def _to_response(row: CalendarEvent) -> CalendarEventResponse:
        return CalendarEventResponse(
            id=row.id,
            family_id=row.family_id,
            owner_user_id=row.owner_user_id,
            title=row.title,
            description=row.description,
            location=row.location,
            starts_at=row.starts_at,
            ends_at=row.ends_at,
            all_day=row.all_day,
            timezone=row.timezone,
            visibility=row.visibility,
            external_provider=row.external_provider,
            external_uid=row.external_uid,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


def build_calendar_service(session) -> CalendarService:
    return CalendarService(
        CalendarRepository(session),
        FamiliesRepository(session),
        IntegrationsRepository(session),
    )
