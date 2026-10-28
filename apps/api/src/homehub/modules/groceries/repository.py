from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from homehub.modules.groceries.models import GroceryList


class GroceryListsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, list_id: UUID, family_id: UUID) -> GroceryList | None:
        stmt = select(GroceryList).where(
            GroceryList.id == list_id,
            GroceryList.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def list_for_family(self, family_id: UUID, since: datetime | None = None) -> list[GroceryList]:
        stmt = select(GroceryList).where(GroceryList.family_id == family_id)
        if since is not None:
            stmt = stmt.where(GroceryList.updated_at > since)
        stmt = stmt.order_by(GroceryList.updated_at.asc())
        return list(self._session.scalars(stmt).all())

    def create(
        self,
        list_id: UUID,
        family_id: UUID,
        name: str,
        created_by: UUID,
        revision: int,
    ) -> GroceryList:
        row = GroceryList(
            id=list_id,
            family_id=family_id,
            name=name,
            revision=revision,
            created_by=created_by,
            updated_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def save(self, row: GroceryList) -> GroceryList:
        row.updated_at = datetime.now(UTC)
        self._session.flush()
        return row
