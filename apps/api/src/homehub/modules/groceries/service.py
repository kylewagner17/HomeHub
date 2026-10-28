from uuid import UUID, uuid4

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.estimate import estimate_total_cents
from homehub.modules.groceries.models import (
    GroceryList,
    GroceryListItem,
    GroceryStaple,
    GroceryStore,
    GroceryStorePrice,
)
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.groceries.schemas import (
    CreateGroceryListRequest,
    GroceryEstimateResponse,
    GroceryListItemResponse,
    GroceryListResponse,
    GroceryStapleResponse,
    GroceryStorePriceResponse,
    GroceryStoreResponse,
    UpdateGroceryListRequest,
)


class GroceryListsService:
    """REST grocery lists and cart estimate; sync uses SyncService with the same revision rules."""

    def __init__(
        self,
        lists_repo: GroceryListsRepository,
        families_repo: FamiliesRepository,
    ) -> None:
        self._repo = lists_repo
        self._families_repo = families_repo

    def list_lists(self, user: User, family_id: UUID) -> list[GroceryListResponse]:
        self._require_member(user.id, family_id)
        rows = self._repo.list_lists_for_family(family_id)
        return [self.to_list_response(r) for r in rows if r.deleted_at is None]

    def create_list(
        self, user: User, family_id: UUID, body: CreateGroceryListRequest
    ) -> GroceryListResponse:
        self._require_member(user.id, family_id)
        row = self._repo.create_list(uuid4(), family_id, body.name, user.id, revision=1)
        return self.to_list_response(row)

    def update_list(
        self, user: User, family_id: UUID, list_id: UUID, body: UpdateGroceryListRequest
    ) -> GroceryListResponse:
        self._require_member(user.id, family_id)
        row = self._repo.get_list_by_id(list_id, family_id)
        if row is None or row.deleted_at is not None:
            raise HomeHubError("NOT_FOUND", "Grocery list not found", status_code=404)
        if body.revision < row.revision:
            raise HomeHubError(
                "CONFLICT",
                "Server has newer revision",
                status_code=409,
                details={"server": self.to_list_response(row).model_dump(mode="json")},
            )
        if body.selected_store_id is not None:
            store = self._repo.get_store_by_id(body.selected_store_id, family_id)
            if store is None or store.deleted_at is not None:
                raise HomeHubError("NOT_FOUND", "Store not found", status_code=404)
        row.name = body.name
        row.selected_store_id = body.selected_store_id
        row.revision = max(body.revision, row.revision)
        self._repo.save_list(row)
        return self.to_list_response(row)

    def estimate_list(
        self, user: User, family_id: UUID, list_id: UUID, store_id: UUID
    ) -> GroceryEstimateResponse:
        self._require_member(user.id, family_id)
        row = self._repo.get_list_by_id(list_id, family_id)
        if row is None or row.deleted_at is not None:
            raise HomeHubError("NOT_FOUND", "Grocery list not found", status_code=404)
        store = self._repo.get_store_by_id(store_id, family_id)
        if store is None or store.deleted_at is not None:
            raise HomeHubError("NOT_FOUND", "Store not found", status_code=404)

        items = self._repo.list_active_items_for_list(list_id, family_id)
        lines = [(i.name, i.quantity) for i in items]
        prices = self._repo.list_prices_for_store(store_id, family_id)
        # Latest revision wins per item name (case-insensitive).
        price_map: dict[str, int] = {}
        for price in sorted(prices, key=lambda p: (p.item_name.lower(), p.revision)):
            if price.deleted_at is None:
                price_map[price.item_name.strip().lower()] = price.price_cents

        total, missing = estimate_total_cents(lines, price_map)
        return GroceryEstimateResponse(
            store_id=store_id,
            list_id=list_id,
            total_cents=total,
            missing_item_names=missing,
        )

    def _require_member(self, user_id: UUID, family_id: UUID) -> None:
        if self._families_repo.get_membership(user_id, family_id) is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)

    @staticmethod
    def to_list_response(row: GroceryList) -> GroceryListResponse:
        return GroceryListResponse(
            id=row.id,
            family_id=row.family_id,
            name=row.name,
            selected_store_id=row.selected_store_id,
            revision=row.revision,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def to_item_response(row: GroceryListItem) -> GroceryListItemResponse:
        return GroceryListItemResponse(
            id=row.id,
            list_id=row.list_id,
            family_id=row.family_id,
            name=row.name,
            quantity=row.quantity,
            checked=row.checked,
            staple_id=row.staple_id,
            revision=row.revision,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def to_staple_response(row: GroceryStaple) -> GroceryStapleResponse:
        return GroceryStapleResponse(
            id=row.id,
            family_id=row.family_id,
            name=row.name,
            revision=row.revision,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def to_store_response(row: GroceryStore) -> GroceryStoreResponse:
        return GroceryStoreResponse(
            id=row.id,
            family_id=row.family_id,
            name=row.name,
            external_provider=row.external_provider,
            external_store_id=row.external_store_id,
            address_line=row.address_line,
            revision=row.revision,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def to_price_response(row: GroceryStorePrice) -> GroceryStorePriceResponse:
        return GroceryStorePriceResponse(
            id=row.id,
            family_id=row.family_id,
            store_id=row.store_id,
            item_name=row.item_name,
            price_cents=row.price_cents,
            revision=row.revision,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )

    # Legacy alias for sync module
    _to_response = to_list_response
