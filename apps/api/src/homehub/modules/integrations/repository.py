from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from homehub.modules.integrations.models import UserCalendarConnection


class IntegrationsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_connection(self, user_id: UUID, provider: str) -> UserCalendarConnection | None:
        stmt = select(UserCalendarConnection).where(
            UserCalendarConnection.user_id == user_id,
            UserCalendarConnection.provider == provider,
        )
        return self._session.scalar(stmt)

    def upsert_connection(self, row: UserCalendarConnection) -> UserCalendarConnection:
        existing = self.get_connection(row.user_id, row.provider)
        if existing:
            existing.access_token = row.access_token
            existing.refresh_token = row.refresh_token
            existing.expires_at = row.expires_at
            self._session.flush()
            return existing
        self._session.add(row)
        self._session.flush()
        return row
