"""Google Calendar OAuth and event fetch via httpx (no google-auth package)."""

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote, urlencode

import httpx

from homehub.config import get_settings
from homehub.core.errors import HomeHubError


def google_oauth_configured() -> bool:
    settings = get_settings()
    return bool(settings.google_oauth_client_id and settings.google_oauth_client_secret)


def build_google_authorize_url(redirect_uri: str, state: str) -> str:
    settings = get_settings()
    if not settings.google_oauth_client_id:
        raise HomeHubError(
            code="GOOGLE_NOT_CONFIGURED",
            message="Google Calendar import is not configured on the server",
            status_code=503,
        )
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_google_code(code: str, redirect_uri: str) -> dict[str, Any]:
    settings = get_settings()
    if not google_oauth_configured():
        raise HomeHubError(
            code="GOOGLE_NOT_CONFIGURED",
            message="Google Calendar import is not configured on the server",
            status_code=503,
        )
    response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30.0,
    )
    if response.status_code != 200:
        raise HomeHubError(
            code="GOOGLE_OAUTH_FAILED",
            message="Could not exchange Google authorization code",
            status_code=400,
            details={"status": response.status_code},
        )
    return response.json()


def refresh_google_access_token(refresh_token: str) -> dict[str, Any]:
    settings = get_settings()
    response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )
    if response.status_code != 200:
        raise HomeHubError(
            code="GOOGLE_TOKEN_REFRESH_FAILED",
            message="Could not refresh Google access token",
            status_code=400,
        )
    return response.json()


def list_importable_calendar_ids(access_token: str) -> list[str]:
    """Calendars the user shows in Google Calendar (not just primary)."""
    response = httpx.get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"minAccessRole": "reader"},
        timeout=30.0,
    )
    if response.status_code != 200:
        raise HomeHubError(
            code="GOOGLE_CALENDAR_LIST_FAILED",
            message="Could not list Google calendars",
            status_code=400,
            details={"status": response.status_code},
        )
    items = response.json().get("items") or []
    calendar_ids: list[str] = []
    for row in items:
        if row.get("deleted"):
            continue
        # Unchecked calendars in Google sidebar are skipped (often where shared family items live).
        if row.get("selected") is False:
            continue
        calendar_ids.append(row["id"])
    return calendar_ids or ["primary"]


def _fetch_events_for_calendar(
    access_token: str,
    calendar_id: str,
    time_min: datetime,
    time_max: datetime,
) -> list[dict[str, Any]]:
    encoded_id = quote(calendar_id, safe="")
    base_url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_id}/events"
    params: dict[str, str] = {
        "timeMin": time_min.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "timeMax": time_max.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "2500",
        "showDeleted": "false",
    }
    collected: list[dict[str, Any]] = []
    while True:
        response = httpx.get(
            base_url,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=60.0,
        )
        if response.status_code != 200:
            detail: dict[str, Any] = {
                "status": response.status_code,
                "calendar_id": calendar_id,
            }
            try:
                detail["google_error"] = response.json()
            except Exception:
                detail["body"] = response.text[:500]
            raise HomeHubError(
                code="GOOGLE_CALENDAR_FETCH_FAILED",
                message="Could not fetch Google Calendar events",
                status_code=400,
                details=detail,
            )
        payload = response.json()
        for item in payload.get("items") or []:
            if item.get("status") == "cancelled":
                continue
            if item.get("eventType") == "workingLocation":
                continue
            collected.append(item)
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
        params["pageToken"] = page_token
    return collected


def fetch_google_calendar_events(
    access_token: str,
    time_min: datetime,
    time_max: datetime,
) -> list[tuple[str, dict[str, Any]]]:
    """Return (calendar_id, event) for all selected Google calendars in the time window."""
    merged: list[tuple[str, dict[str, Any]]] = []
    for calendar_id in list_importable_calendar_ids(access_token):
        for item in _fetch_events_for_calendar(access_token, calendar_id, time_min, time_max):
            merged.append((calendar_id, item))
    return merged


def google_event_to_fields(
    item: dict[str, Any],
) -> tuple[str, datetime, datetime, bool, str | None]:
    title = item.get("summary") or "Untitled"
    start = item.get("start") or {}
    end = item.get("end") or {}
    if "date" in start:
        d = datetime.fromisoformat(start["date"]).replace(tzinfo=UTC)
        end_raw = end.get("date") or start["date"]
        end_d = datetime.fromisoformat(end_raw).replace(tzinfo=UTC)
        return title, d, end_d, True, item.get("description")
    if "dateTime" not in start:
        raise ValueError("Event missing start time")
    start_dt = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
    end_raw = end.get("dateTime") or start.get("dateTime")
    end_dt = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
    return title, start_dt, end_dt, False, item.get("description")


def external_uid_for_google_event(calendar_id: str, item: dict[str, Any]) -> str | None:
    event_id = item.get("id")
    if not event_id:
        return None
    return f"{calendar_id}:{event_id}"


def expires_at_from_token_payload(payload: dict[str, Any]) -> datetime | None:
    expires_in = payload.get("expires_in")
    if not expires_in:
        return None
    return datetime.now(UTC) + timedelta(seconds=int(expires_in))
