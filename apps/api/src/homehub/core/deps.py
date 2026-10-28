"""FastAPI dependencies: DB session per request and JWT-authenticated user."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session, sessionmaker

from homehub.core.errors import HomeHubError
from homehub.core.security import decode_access_token
from homehub.modules.auth.models import User
from homehub.modules.auth.repository import AuthRepository


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
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Resolve Bearer JWT to a User row; used by all protected routes."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HomeHubError("UNAUTHORIZED", "Missing or invalid authorization", status_code=401)
    token = authorization.split(" ", 1)[1].strip()
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
