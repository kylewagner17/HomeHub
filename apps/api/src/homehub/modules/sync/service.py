"""Apply mobile sync mutations and serve change feeds (ADR-003, ADR-004)."""

from datetime import UTC, datetime
from uuid import UUID

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.quantity import add_quantities
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.groceries.service import GroceryListsService
from homehub.modules.maintenance.consumable_grocery import reset_consumable_after_grocery_checkoff
from homehub.modules.maintenance.repository import MaintenanceRepository
from homehub.modules.sync.repository import SyncRepository
from homehub.modules.sync.schemas import (
    SyncEntityType,
    SyncMutation,
    SyncOperation,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    SyncPushResult,
)


class SyncService:
    """Server-side sync for family-scoped grocery entities."""

    def __init__(
        self,
        sync_repo: SyncRepository,
        lists_repo: GroceryListsRepository,
        families_repo: FamiliesRepository,
    ) -> None:
        self._sync_repo = sync_repo
        self._repo = lists_repo
        self._families_repo = families_repo

    def ping(self) -> datetime:
        return datetime.now(UTC)

    def pull(self, user: User, family_id: UUID, since: datetime | None) -> SyncPullResponse:
        self._require_member(user.id, family_id)
        return SyncPullResponse(
            server_time=datetime.now(UTC),
            grocery_lists=[
                GroceryListsService.to_list_response(r)
                for r in self._repo.list_lists_for_family(family_id, since=since)
            ],
            grocery_list_items=[
                GroceryListsService.to_item_response(r)
                for r in self._repo.list_items_for_family(family_id, since=since)
            ],
            grocery_staples=[
                GroceryListsService.to_staple_response(r)
                for r in self._repo.list_staples_for_family(family_id, since=since)
            ],
            grocery_stores=[
                GroceryListsService.to_store_response(r)
                for r in self._repo.list_stores_for_family(family_id, since=since)
            ],
            grocery_store_prices=[
                GroceryListsService.to_price_response(r)
                for r in self._repo.list_prices_for_family(family_id, since=since)
            ],
        )

    def push(self, user: User, body: SyncPushRequest) -> SyncPushResponse:
        self._require_member(user.id, body.family_id)
        results: list[SyncPushResult] = []
        for mutation in body.mutations:
            results.append(self._apply_mutation(user, body.family_id, mutation))
        return SyncPushResponse(results=results)

    def _apply_mutation(
        self, user: User, family_id: UUID, mutation: SyncMutation
    ) -> SyncPushResult:
        handlers = {
            SyncEntityType.grocery_list: self._apply_grocery_list,
            SyncEntityType.grocery_list_item: self._apply_grocery_list_item,
            SyncEntityType.grocery_staple: self._apply_grocery_staple,
            SyncEntityType.grocery_store: self._apply_grocery_store,
            SyncEntityType.grocery_store_price: self._apply_grocery_store_price,
        }
        handler = handlers.get(mutation.entity_type)
        if handler is None:
            raise HomeHubError("UNSUPPORTED_ENTITY", "Unsupported entity type", status_code=400)
        return handler(user, family_id, mutation)

    def _duplicate_result(
        self, mutation: SyncMutation, family_id: UUID
    ) -> SyncPushResult:
        entity_type = mutation.entity_type
        if entity_type == SyncEntityType.grocery_list:
            row = self._repo.get_list_by_id(mutation.entity_id, family_id)
            entity = GroceryListsService.to_list_response(row) if row else None
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="duplicate",
                entity_type=entity_type,
                entity=entity,
            )
        if entity_type == SyncEntityType.grocery_list_item:
            row = self._repo.get_item_by_id(mutation.entity_id, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="duplicate",
                entity_type=entity_type,
                grocery_list_item=GroceryListsService.to_item_response(row) if row else None,
            )
        if entity_type == SyncEntityType.grocery_staple:
            row = self._repo.get_staple_by_id(mutation.entity_id, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="duplicate",
                entity_type=entity_type,
                grocery_staple=GroceryListsService.to_staple_response(row) if row else None,
            )
        if entity_type == SyncEntityType.grocery_store:
            row = self._repo.get_store_by_id(mutation.entity_id, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="duplicate",
                entity_type=entity_type,
                grocery_store=GroceryListsService.to_store_response(row) if row else None,
            )
        row = self._repo.get_price_by_id(mutation.entity_id, family_id)
        return SyncPushResult(
            idempotency_key=mutation.idempotency_key,
            status="duplicate",
            entity_type=entity_type,
            grocery_store_price=GroceryListsService.to_price_response(row) if row else None,
        )

    def _apply_grocery_list(
        self, user: User, family_id: UUID, mutation: SyncMutation
    ) -> SyncPushResult:
        if self._sync_repo.was_applied(mutation.idempotency_key):
            return self._duplicate_result(mutation, family_id)

        if mutation.operation == SyncOperation.delete:
            row = self._repo.get_list_by_id(mutation.entity_id, family_id)
            if row is None:
                self._sync_repo.record_applied(mutation.idempotency_key, family_id)
                return SyncPushResult(
                    idempotency_key=mutation.idempotency_key,
                    status="applied",
                    entity_type=mutation.entity_type,
                )
            row.deleted_at = datetime.now(UTC)
            row.revision = row.revision + 1
            self._repo.save_list(row)
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=mutation.entity_type,
                entity=GroceryListsService.to_list_response(row),
            )

        if mutation.data is None or not mutation.data.name:
            raise HomeHubError("VALIDATION_ERROR", "Missing grocery list data", status_code=422)

        if mutation.data.selected_store_id is not None:
            store = self._repo.get_store_by_id(mutation.data.selected_store_id, family_id)
            if store is None or store.deleted_at is not None:
                raise HomeHubError("NOT_FOUND", "Store not found", status_code=404)

        row = self._repo.get_list_by_id(mutation.entity_id, family_id)
        if row is None:
            row = self._repo.create_list(
                mutation.entity_id,
                family_id,
                mutation.data.name,
                user.id,
                mutation.data.revision,
                selected_store_id=mutation.data.selected_store_id,
            )
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=mutation.entity_type,
                entity=GroceryListsService.to_list_response(row),
            )

        if mutation.data.revision < row.revision:
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="conflict",
                entity_type=mutation.entity_type,
                entity=GroceryListsService.to_list_response(row),
            )

        row.name = mutation.data.name
        if mutation.data.selected_store_id is not None:
            row.selected_store_id = mutation.data.selected_store_id
        row.revision = max(mutation.data.revision, row.revision)
        if row.deleted_at is not None:
            row.deleted_at = None
        self._repo.save_list(row)
        self._sync_repo.record_applied(mutation.idempotency_key, family_id)
        return SyncPushResult(
            idempotency_key=mutation.idempotency_key,
            status="applied",
            entity_type=mutation.entity_type,
            entity=GroceryListsService.to_list_response(row),
        )

    def _apply_grocery_list_item(
        self, user: User, family_id: UUID, mutation: SyncMutation
    ) -> SyncPushResult:
        if self._sync_repo.was_applied(mutation.idempotency_key):
            return self._duplicate_result(mutation, family_id)

        if mutation.operation == SyncOperation.delete:
            row = self._repo.get_item_by_id(mutation.entity_id, family_id)
            if row is None:
                self._sync_repo.record_applied(mutation.idempotency_key, family_id)
                return SyncPushResult(
                    idempotency_key=mutation.idempotency_key,
                    status="applied",
                    entity_type=mutation.entity_type,
                )
            row.deleted_at = datetime.now(UTC)
            row.revision = row.revision + 1
            self._repo.save_item(row)
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=mutation.entity_type,
                grocery_list_item=GroceryListsService.to_item_response(row),
            )

        if mutation.data is None or not mutation.data.name or mutation.data.list_id is None:
            raise HomeHubError("VALIDATION_ERROR", "Missing list item data", status_code=422)

        parent = self._repo.get_list_by_id(mutation.data.list_id, family_id)
        if parent is None or parent.deleted_at is not None:
            raise HomeHubError("NOT_FOUND", "Grocery list not found", status_code=404)

        quantity = mutation.data.quantity or "1"
        checked = bool(mutation.data.checked) if mutation.data.checked is not None else False

        row = self._repo.get_item_by_id(mutation.entity_id, family_id)
        if row is None:
            existing = self._repo.find_active_item_by_name(
                mutation.data.list_id, family_id, mutation.data.name
            )
            if existing is not None:
                existing.quantity = add_quantities(existing.quantity, quantity)
                existing.checked = checked
                existing.revision = max(existing.revision + 1, mutation.data.revision)
                self._maybe_reset_consumable_stock(existing, checked, family_id)
                self._repo.save_item(existing)
                self._sync_repo.record_applied(mutation.idempotency_key, family_id)
                return SyncPushResult(
                    idempotency_key=mutation.idempotency_key,
                    status="applied",
                    entity_type=mutation.entity_type,
                    grocery_list_item=GroceryListsService.to_item_response(existing),
                )
            row = self._repo.create_item(
                mutation.entity_id,
                mutation.data.list_id,
                family_id,
                mutation.data.name,
                quantity,
                checked,
                mutation.data.staple_id,
                mutation.data.revision,
            )
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=mutation.entity_type,
                grocery_list_item=GroceryListsService.to_item_response(row),
            )

        if mutation.data.revision < row.revision:
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="conflict",
                entity_type=mutation.entity_type,
                grocery_list_item=GroceryListsService.to_item_response(row),
            )

        row.list_id = mutation.data.list_id
        row.name = mutation.data.name
        row.quantity = quantity
        row.checked = checked
        row.staple_id = mutation.data.staple_id
        row.revision = max(mutation.data.revision, row.revision)
        if row.deleted_at is not None:
            row.deleted_at = None
        self._maybe_reset_consumable_stock(row, checked, family_id)
        self._repo.save_item(row)
        self._sync_repo.record_applied(mutation.idempotency_key, family_id)
        return SyncPushResult(
            idempotency_key=mutation.idempotency_key,
            status="applied",
            entity_type=mutation.entity_type,
            grocery_list_item=GroceryListsService.to_item_response(row),
        )

    def _apply_grocery_staple(
        self, user: User, family_id: UUID, mutation: SyncMutation
    ) -> SyncPushResult:
        return self._apply_named_entity(
            mutation,
            family_id,
            mutation.entity_type,
            get_row=self._repo.get_staple_by_id,
            create_row=lambda: self._repo.create_staple(
                mutation.entity_id,
                family_id,
                mutation.data.name,  # type: ignore[union-attr]
                mutation.data.revision,  # type: ignore[union-attr]
            ),
            save_row=self._repo.save_staple,
            to_response=GroceryListsService.to_staple_response,
            response_field="grocery_staple",
        )

    def _apply_grocery_store(
        self, user: User, family_id: UUID, mutation: SyncMutation
    ) -> SyncPushResult:
        return self._apply_named_entity(
            mutation,
            family_id,
            mutation.entity_type,
            get_row=self._repo.get_store_by_id,
            create_row=lambda: self._repo.create_store(
                mutation.entity_id,
                family_id,
                mutation.data.name,  # type: ignore[union-attr]
                mutation.data.revision,  # type: ignore[union-attr]
            ),
            save_row=self._repo.save_store,
            to_response=GroceryListsService.to_store_response,
            response_field="grocery_store",
        )

    def _apply_grocery_store_price(
        self, user: User, family_id: UUID, mutation: SyncMutation
    ) -> SyncPushResult:
        if self._sync_repo.was_applied(mutation.idempotency_key):
            return self._duplicate_result(mutation, family_id)

        if mutation.operation == SyncOperation.delete:
            row = self._repo.get_price_by_id(mutation.entity_id, family_id)
            if row is None:
                self._sync_repo.record_applied(mutation.idempotency_key, family_id)
                return SyncPushResult(
                    idempotency_key=mutation.idempotency_key,
                    status="applied",
                    entity_type=mutation.entity_type,
                )
            row.deleted_at = datetime.now(UTC)
            row.revision = row.revision + 1
            self._repo.save_price(row)
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=mutation.entity_type,
                grocery_store_price=GroceryListsService.to_price_response(row),
            )

        if (
            mutation.data is None
            or mutation.data.store_id is None
            or not mutation.data.item_name
            or mutation.data.price_cents is None
        ):
            raise HomeHubError("VALIDATION_ERROR", "Missing store price data", status_code=422)

        store = self._repo.get_store_by_id(mutation.data.store_id, family_id)
        if store is None or store.deleted_at is not None:
            raise HomeHubError("NOT_FOUND", "Store not found", status_code=404)

        row = self._repo.get_price_by_id(mutation.entity_id, family_id)
        if row is None:
            row = self._repo.create_price(
                mutation.entity_id,
                family_id,
                mutation.data.store_id,
                mutation.data.item_name,
                mutation.data.price_cents,
                mutation.data.revision,
            )
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=mutation.entity_type,
                grocery_store_price=GroceryListsService.to_price_response(row),
            )

        if mutation.data.revision < row.revision:
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="conflict",
                entity_type=mutation.entity_type,
                grocery_store_price=GroceryListsService.to_price_response(row),
            )

        row.store_id = mutation.data.store_id
        row.item_name = mutation.data.item_name
        row.price_cents = mutation.data.price_cents
        row.revision = max(mutation.data.revision, row.revision)
        if row.deleted_at is not None:
            row.deleted_at = None
        self._repo.save_price(row)
        self._sync_repo.record_applied(mutation.idempotency_key, family_id)
        return SyncPushResult(
            idempotency_key=mutation.idempotency_key,
            status="applied",
            entity_type=mutation.entity_type,
            grocery_store_price=GroceryListsService.to_price_response(row),
        )

    def _apply_named_entity(
        self,
        mutation: SyncMutation,
        family_id: UUID,
        entity_type: SyncEntityType,
        get_row,
        create_row,
        save_row,
        to_response,
        response_field: str,
    ) -> SyncPushResult:
        if self._sync_repo.was_applied(mutation.idempotency_key):
            return self._duplicate_result(mutation, family_id)

        if mutation.operation == SyncOperation.delete:
            row = get_row(mutation.entity_id, family_id)
            if row is None:
                self._sync_repo.record_applied(mutation.idempotency_key, family_id)
                return SyncPushResult(
                    idempotency_key=mutation.idempotency_key,
                    status="applied",
                    entity_type=entity_type,
                )
            row.deleted_at = datetime.now(UTC)
            row.revision = row.revision + 1
            save_row(row)
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=entity_type,
                **{response_field: to_response(row)},
            )

        if mutation.data is None or not mutation.data.name:
            raise HomeHubError("VALIDATION_ERROR", "Missing entity data", status_code=422)

        row = get_row(mutation.entity_id, family_id)
        if row is None:
            row = create_row()
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity_type=entity_type,
                **{response_field: to_response(row)},
            )

        if mutation.data.revision < row.revision:
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="conflict",
                entity_type=entity_type,
                **{response_field: to_response(row)},
            )

        row.name = mutation.data.name
        row.revision = max(mutation.data.revision, row.revision)
        if row.deleted_at is not None:
            row.deleted_at = None
        save_row(row)
        self._sync_repo.record_applied(mutation.idempotency_key, family_id)
        return SyncPushResult(
            idempotency_key=mutation.idempotency_key,
            status="applied",
            entity_type=entity_type,
            **{response_field: to_response(row)},
        )

    def _maybe_reset_consumable_stock(self, row, checked: bool, family_id: UUID) -> None:
        if not checked or row.maintenance_item_id is None:
            return
        reset_consumable_after_grocery_checkoff(
            self._repo,
            MaintenanceRepository(self._repo.session),
            family_id,
            row.maintenance_item_id,
        )

    def _require_member(self, user_id: UUID, family_id: UUID) -> None:
        if self._families_repo.get_membership(user_id, family_id) is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)
