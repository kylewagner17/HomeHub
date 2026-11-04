from typing import Annotated

from fastapi import APIRouter, Query

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.calendar.schemas import (
    GoogleAuthorizeResponse,
    GoogleConnectionStatus,
    GoogleOAuthCodeRequest,
)
from homehub.modules.calendar.service import build_calendar_service
from homehub.modules.integrations.google_calendar import (
    build_google_authorize_url,
    google_oauth_configured,
)

router = APIRouter(prefix="/integrations/google", tags=["integrations"])


@router.get("/authorize-url", response_model=GoogleAuthorizeResponse)
def google_authorize_url(
    user: CurrentUser,
    redirect_uri: Annotated[str, Query(min_length=1)],
) -> GoogleAuthorizeResponse:
    _ = user
    if not google_oauth_configured():
        return GoogleAuthorizeResponse(authorize_url=None)
    url = build_google_authorize_url(redirect_uri, state="homehub")
    return GoogleAuthorizeResponse(authorize_url=url)


@router.post("/connect")
def connect_google(
    body: GoogleOAuthCodeRequest,
    user: CurrentUser,
    db: DbSession,
) -> GoogleConnectionStatus:
    build_calendar_service(db).connect_google(user, body.code, body.redirect_uri)
    db.commit()
    return GoogleConnectionStatus(connected=True)


@router.get("/status", response_model=GoogleConnectionStatus)
def google_status(user: CurrentUser, db: DbSession) -> GoogleConnectionStatus:
    connected = build_calendar_service(db).google_connected(user)
    return GoogleConnectionStatus(connected=connected)
