from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from homehub.modules.auth.models import User


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self._session.get(User, user_id)

    def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self._session.scalar(stmt)

    def create_user(self, email: str, password_hash: str, display_name: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash, display_name=display_name)
        self._session.add(user)
        self._session.flush()
        return user
