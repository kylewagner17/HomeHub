"""FastAPI dependencies: DB session per request and JWT-authenticated user."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from homehub.core.errors import HomeHubError
from homehub.core.security import decode_access_token
from homehub.modules.auth.models import User
from homehub.modules.auth.repository import AuthRepository

# Documented in OpenAPI so Swagger UI "Authorize" sends Authorization: Bearer …
_http_bearer = HTTPBearer(auto_error=False)


def get_session_factory() -> sessionmaker[Session]:
    from homehub.main import session_factory

    return session_factory


def get_db(
    factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_http_bearer)
    ] = None,
) -> User:
    """Resolve Bearer JWT to a User row; used by all protected routes."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HomeHubError("UNAUTHORIZED", "Missing or invalid authorization", status_code=401)
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except Exception:
        raise HomeHubError("UNAUTHORIZED", "Invalid token", status_code=401) from None
    user = AuthRepository(db).get_user_by_id(user_id)
    if user is None:
        raise HomeHubError("UNAUTHORIZED", "User not found", status_code=401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
