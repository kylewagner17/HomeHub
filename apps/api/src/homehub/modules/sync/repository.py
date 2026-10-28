from uuid import UUID

from sqlalchemy.orm import Session

from homehub.modules.sync.models import AppliedMutation


class SyncRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def was_applied(self, idempotency_key: str) -> bool:
        return self._session.get(AppliedMutation, idempotency_key) is not None

    def record_applied(self, idempotency_key: str, family_id: UUID) -> None:
        self._session.add(AppliedMutation(idempotency_key=idempotency_key, family_id=family_id))
        self._session.flush()
