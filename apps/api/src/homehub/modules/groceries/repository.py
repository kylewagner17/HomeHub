from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from homehub.modules.groceries.models import (
    GroceryList,
    GroceryListItem,
    GroceryStaple,
    GroceryStore,
    GroceryStorePrice,
)


class GroceryListsRepository:
    """Family-scoped grocery entities (lists, items, staples, stores, prices)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    # --- lists ---

    def get_list_by_id(self, list_id: UUID, family_id: UUID) -> GroceryList | None:
        stmt = select(GroceryList).where(
            GroceryList.id == list_id,
            GroceryList.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def list_lists_for_family(
        self, family_id: UUID, since: datetime | None = None
    ) -> list[GroceryList]:
        stmt = select(GroceryList).where(GroceryList.family_id == family_id)
        if since is not None:
            stmt = stmt.where(GroceryList.updated_at > since)
        stmt = stmt.order_by(GroceryList.updated_at.asc())
        return list(self._session.scalars(stmt).all())

    def create_list(
        self,
        list_id: UUID,
        family_id: UUID,
        name: str,
        created_by: UUID,
        revision: int,
        selected_store_id: UUID | None = None,
    ) -> GroceryList:
        row = GroceryList(
            id=list_id,
            family_id=family_id,
            name=name,
            selected_store_id=selected_store_id,
            revision=revision,
            created_by=created_by,
            updated_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def save_list(self, row: GroceryList) -> GroceryList:
        row.updated_at = datetime.now(UTC)
        self._session.flush()
        return row

    # Backward-compatible aliases used by M2 code paths
    get_by_id = get_list_by_id
    list_for_family = list_lists_for_family
    create = create_list
    save = save_list

    # --- list items ---

    def get_item_by_id(self, item_id: UUID, family_id: UUID) -> GroceryListItem | None:
        stmt = select(GroceryListItem).where(
            GroceryListItem.id == item_id,
            GroceryListItem.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def list_items_for_family(
        self, family_id: UUID, since: datetime | None = None
    ) -> list[GroceryListItem]:
        stmt = select(GroceryListItem).where(GroceryListItem.family_id == family_id)
        if since is not None:
            stmt = stmt.where(GroceryListItem.updated_at > since)
        stmt = stmt.order_by(GroceryListItem.updated_at.asc())
        return list(self._session.scalars(stmt).all())

    def list_active_items_for_list(self, list_id: UUID, family_id: UUID) -> list[GroceryListItem]:
        stmt = select(GroceryListItem).where(
            GroceryListItem.list_id == list_id,
            GroceryListItem.family_id == family_id,
            GroceryListItem.deleted_at.is_(None),
        )
        return list(self._session.scalars(stmt).all())

    def find_active_item_by_name(
        self, list_id: UUID, family_id: UUID, name: str
    ) -> GroceryListItem | None:
        target = name.strip().lower()
        for row in self.list_active_items_for_list(list_id, family_id):
            if row.name.strip().lower() == target:
                return row
        return None

    def create_item(
        self,
        item_id: UUID,
        list_id: UUID,
        family_id: UUID,
        name: str,
        quantity: str,
        checked: bool,
        staple_id: UUID | None,
        revision: int,
        maintenance_item_id: UUID | None = None,
        urgent_out: bool = False,
    ) -> GroceryListItem:
        row = GroceryListItem(
            id=item_id,
            list_id=list_id,
            family_id=family_id,
            name=name,
            quantity=quantity,
            checked=checked,
            staple_id=staple_id,
            maintenance_item_id=maintenance_item_id,
            urgent_out=urgent_out,
            revision=revision,
            updated_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def save_item(self, row: GroceryListItem) -> GroceryListItem:
        row.updated_at = datetime.now(UTC)
        self._session.flush()
        return row

    # --- staples ---

    def get_staple_by_id(self, staple_id: UUID, family_id: UUID) -> GroceryStaple | None:
        stmt = select(GroceryStaple).where(
            GroceryStaple.id == staple_id,
            GroceryStaple.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def list_staples_for_family(
        self, family_id: UUID, since: datetime | None = None
    ) -> list[GroceryStaple]:
        stmt = select(GroceryStaple).where(GroceryStaple.family_id == family_id)
        if since is not None:
            stmt = stmt.where(GroceryStaple.updated_at > since)
        stmt = stmt.order_by(GroceryStaple.updated_at.asc())
        return list(self._session.scalars(stmt).all())

    def create_staple(
        self, staple_id: UUID, family_id: UUID, name: str, revision: int
    ) -> GroceryStaple:
        row = GroceryStaple(
            id=staple_id,
            family_id=family_id,
            name=name,
            revision=revision,
            updated_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def save_staple(self, row: GroceryStaple) -> GroceryStaple:
        row.updated_at = datetime.now(UTC)
        self._session.flush()
        return row

    # --- stores ---

    def get_store_by_id(self, store_id: UUID, family_id: UUID) -> GroceryStore | None:
        stmt = select(GroceryStore).where(
            GroceryStore.id == store_id,
            GroceryStore.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def get_store_by_external(
        self, family_id: UUID, provider: str, external_store_id: str
    ) -> GroceryStore | None:
        stmt = select(GroceryStore).where(
            GroceryStore.family_id == family_id,
            GroceryStore.external_provider == provider,
            GroceryStore.external_store_id == external_store_id,
        )
        return self._session.scalar(stmt)

    def list_stores_for_family(
        self, family_id: UUID, since: datetime | None = None
    ) -> list[GroceryStore]:
        stmt = select(GroceryStore).where(GroceryStore.family_id == family_id)
        if since is not None:
            stmt = stmt.where(GroceryStore.updated_at > since)
        stmt = stmt.order_by(GroceryStore.updated_at.asc())
        return list(self._session.scalars(stmt).all())

    def create_store(
        self,
        store_id: UUID,
        family_id: UUID,
        name: str,
        revision: int,
        *,
        external_provider: str | None = None,
        external_store_id: str | None = None,
        address_line: str | None = None,
    ) -> GroceryStore:
        row = GroceryStore(
            id=store_id,
            family_id=family_id,
            name=name,
            external_provider=external_provider,
            external_store_id=external_store_id,
            address_line=address_line,
            revision=revision,
            updated_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def save_store(self, row: GroceryStore) -> GroceryStore:
        row.updated_at = datetime.now(UTC)
        self._session.flush()
        return row

    # --- store prices ---

    def get_price_by_id(self, price_id: UUID, family_id: UUID) -> GroceryStorePrice | None:
        stmt = select(GroceryStorePrice).where(
            GroceryStorePrice.id == price_id,
            GroceryStorePrice.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def list_prices_for_family(
        self, family_id: UUID, since: datetime | None = None
    ) -> list[GroceryStorePrice]:
        stmt = select(GroceryStorePrice).where(GroceryStorePrice.family_id == family_id)
        if since is not None:
            stmt = stmt.where(GroceryStorePrice.updated_at > since)
        stmt = stmt.order_by(GroceryStorePrice.updated_at.asc())
        return list(self._session.scalars(stmt).all())

    def find_price_for_item_name(
        self, store_id: UUID, family_id: UUID, item_name: str
    ) -> GroceryStorePrice | None:
        target = item_name.strip().lower()
        rows = self.list_prices_for_store(store_id, family_id)
        matches = [row for row in rows if row.item_name.strip().lower() == target]
        if not matches:
            return None
        return max(matches, key=lambda row: row.revision)

    def list_prices_for_store(self, store_id: UUID, family_id: UUID) -> list[GroceryStorePrice]:
        stmt = select(GroceryStorePrice).where(
            GroceryStorePrice.store_id == store_id,
            GroceryStorePrice.family_id == family_id,
            GroceryStorePrice.deleted_at.is_(None),
        )
        return list(self._session.scalars(stmt).all())

    def create_price(
        self,
        price_id: UUID,
        family_id: UUID,
        store_id: UUID,
        item_name: str,
        price_cents: int,
        revision: int,
    ) -> GroceryStorePrice:
        row = GroceryStorePrice(
            id=price_id,
            family_id=family_id,
            store_id=store_id,
            item_name=item_name,
            price_cents=price_cents,
            revision=revision,
            updated_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def save_price(self, row: GroceryStorePrice) -> GroceryStorePrice:
        row.updated_at = datetime.now(UTC)
        self._session.flush()
        return row
