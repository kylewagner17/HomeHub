from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from homehub.modules.maintenance.models import MaintenanceCompletion, MaintenanceItem


class MaintenanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def list_items(self, family_id: UUID, category: str | None = None) -> list[MaintenanceItem]:
        stmt = select(MaintenanceItem).where(
            MaintenanceItem.family_id == family_id,
            MaintenanceItem.deleted_at.is_(None),
        )
        if category is not None:
            stmt = stmt.where(MaintenanceItem.category == category)
        stmt = stmt.order_by(MaintenanceItem.title.asc())
        return list(self._session.scalars(stmt).all())

    def get_item(self, item_id: UUID, family_id: UUID) -> MaintenanceItem | None:
        stmt = select(MaintenanceItem).where(
            MaintenanceItem.id == item_id,
            MaintenanceItem.family_id == family_id,
            MaintenanceItem.deleted_at.is_(None),
        )
        return self._session.scalar(stmt)

    def create_item(self, row: MaintenanceItem) -> MaintenanceItem:
        self._session.add(row)
        self._session.flush()
        return row

    def soft_delete(self, row: MaintenanceItem) -> None:
        row.deleted_at = datetime.now(UTC)
        self._session.flush()

    def add_completion(self, row: MaintenanceCompletion) -> MaintenanceCompletion:
        self._session.add(row)
        self._session.flush()
        return row

    def list_completions_for_family(
        self, family_id: UUID, limit: int = 100
    ) -> list[MaintenanceCompletion]:
        stmt = (
            select(MaintenanceCompletion)
            .where(MaintenanceCompletion.family_id == family_id)
            .order_by(MaintenanceCompletion.completed_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def list_completions_for_item(
        self, item_id: UUID, family_id: UUID
    ) -> list[MaintenanceCompletion]:
        stmt = (
            select(MaintenanceCompletion)
            .where(
                MaintenanceCompletion.item_id == item_id,
                MaintenanceCompletion.family_id == family_id,
            )
            .order_by(MaintenanceCompletion.completed_at.desc())
        )
        return list(self._session.scalars(stmt).all())
