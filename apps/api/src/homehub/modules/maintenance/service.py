from datetime import UTC, datetime
from uuid import UUID, uuid4

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.maintenance.consumable_grocery import (
    StockStatus,
    sync_grocery_lists_for_stock,
)
from homehub.modules.maintenance.kinds import (
    KINDS_BY_CATEGORY,
    MaintenanceCategory,
    MaintenanceItemKind,
    default_interval_miles,
    requires_mileage_fields,
)
from homehub.modules.maintenance.models import MaintenanceCompletion, MaintenanceItem
from homehub.modules.maintenance.repository import MaintenanceRepository
from homehub.modules.maintenance.scheduling import (
    compute_next_due_after_completion,
    ensure_utc,
    is_overdue,
)
from homehub.modules.maintenance.schemas import (
    CompleteMaintenanceRequest,
    CreateMaintenanceItemRequest,
    MaintenanceCompletionResponse,
    MaintenanceItemResponse,
    UpdateMaintenanceItemRequest,
    UpdateStockStatusRequest,
)
from homehub.modules.reminders.repository import RemindersRepository
from homehub.modules.reminders.service import RemindersService


class MaintenanceService:
    """Maintenance items, completion history, and linked due reminders."""

    def __init__(
        self,
        maintenance_repo: MaintenanceRepository,
        families_repo: FamiliesRepository,
        reminders_service: RemindersService,
        grocery_repo: GroceryListsRepository,
    ) -> None:
        self._repo = maintenance_repo
        self._families_repo = families_repo
        self._reminders = reminders_service
        self._grocery_repo = grocery_repo

    def list_items(
        self, user: User, family_id: UUID, category: str | None
    ) -> list[MaintenanceItemResponse]:
        self._require_member(user.id, family_id)
        rows = self._repo.list_items(family_id, category)
        now = datetime.now(UTC)
        return [self._to_item_response(row, now) for row in rows]

    def create_item(
        self, user: User, family_id: UUID, body: CreateMaintenanceItemRequest
    ) -> MaintenanceItemResponse:
        self._require_member(user.id, family_id)
        category, item_kind = self._parse_kind(body.category, body.item_kind)
        if category is MaintenanceCategory.ITEMS:
            row = MaintenanceItem(
                id=uuid4(),
                family_id=family_id,
                category=category.value,
                item_kind=item_kind.value,
                title=body.title.strip(),
                notes=body.notes,
                stock_status=StockStatus.IN_STOCK,
                created_by=user.id,
            )
            self._repo.create_item(row)
            return self._to_item_response(row, datetime.now(UTC))

        interval_miles = body.interval_miles
        if interval_miles is None and category is MaintenanceCategory.AUTO:
            interval_miles = default_interval_miles(item_kind)
        self._validate_mileage_on_create(body, item_kind)

        row = MaintenanceItem(
            id=uuid4(),
            family_id=family_id,
            category=category.value,
            item_kind=item_kind.value,
            title=body.title.strip(),
            notes=body.notes,
            interval_days=None,
            interval_miles=interval_miles,
            mileage_at_last_service=body.mileage_at_last_service,
            previous_service_mileage=body.previous_service_mileage,
            current_mileage=body.current_mileage,
            next_due_at=ensure_utc(body.next_due_at) if body.next_due_at else None,
            created_by=user.id,
        )
        self._repo.create_item(row)
        row.reminder_id = self._sync_reminder(row, user.id)
        now = datetime.now(UTC)
        return self._to_item_response(row, now)

    def update_item(
        self, user: User, family_id: UUID, item_id: UUID, body: UpdateMaintenanceItemRequest
    ) -> MaintenanceItemResponse:
        self._require_member(user.id, family_id)
        row = self._repo.get_item(item_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Maintenance item not found", status_code=404)
        if body.title is not None:
            row.title = body.title.strip()
        if body.notes is not None:
            row.notes = body.notes
        if body.interval_miles is not None:
            row.interval_miles = body.interval_miles
        if body.next_due_at is not None:
            row.next_due_at = ensure_utc(body.next_due_at)
        if body.current_mileage is not None:
            row.current_mileage = body.current_mileage
        row.reminder_id = self._sync_reminder(row, user.id)
        return self._to_item_response(row, datetime.now(UTC))

    def set_stock_status(
        self, user: User, family_id: UUID, item_id: UUID, body: UpdateStockStatusRequest
    ) -> MaintenanceItemResponse:
        self._require_member(user.id, family_id)
        row = self._repo.get_item(item_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Maintenance item not found", status_code=404)
        if row.category != MaintenanceCategory.ITEMS.value:
            raise HomeHubError(
                "VALIDATION_ERROR",
                "Stock status applies to household items only",
                status_code=422,
            )
        row.stock_status = body.stock_status
        sync_grocery_lists_for_stock(self._grocery_repo, row)
        return self._to_item_response(row, datetime.now(UTC))

    def complete_item(
        self, user: User, family_id: UUID, item_id: UUID, body: CompleteMaintenanceRequest
    ) -> MaintenanceItemResponse:
        self._require_member(user.id, family_id)
        row = self._repo.get_item(item_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Maintenance item not found", status_code=404)
        item_kind = MaintenanceItemKind(row.item_kind)
        completed_at = ensure_utc(body.completed_at)
        mileage = body.mileage_at_completion
        if requires_mileage_fields(item_kind) and mileage is None:
            raise HomeHubError(
                "VALIDATION_ERROR",
                "Mileage at completion is required for this item",
                status_code=422,
            )

        previous_mileage = body.previous_service_mileage
        if previous_mileage is None:
            previous_mileage = row.mileage_at_last_service

        next_due = compute_next_due_after_completion(
            completed_at,
            mileage,
            None,
            row.interval_miles,
        )
        if body.next_due_at is not None:
            row.next_due_at = ensure_utc(body.next_due_at)
        else:
            row.next_due_at = next_due.next_due_at
        row.next_due_mileage = next_due.next_due_mileage

        completion = MaintenanceCompletion(
            id=uuid4(),
            item_id=row.id,
            family_id=family_id,
            completed_at=completed_at,
            mileage_at_completion=mileage,
            previous_service_mileage=previous_mileage,
            next_due_at=row.next_due_at,
            next_due_mileage=row.next_due_mileage,
            notes=body.notes,
        )
        self._repo.add_completion(completion)

        row.last_completed_at = completed_at
        row.previous_service_mileage = previous_mileage
        row.mileage_at_last_service = mileage
        if mileage is not None:
            row.current_mileage = mileage
        row.reminder_id = self._sync_reminder(row, user.id)
        return self._to_item_response(row, datetime.now(UTC))

    def delete_item(self, user: User, family_id: UUID, item_id: UUID) -> None:
        self._require_member(user.id, family_id)
        row = self._repo.get_item(item_id, family_id)
        if row is None:
            raise HomeHubError("NOT_FOUND", "Maintenance item not found", status_code=404)
        if row.reminder_id is not None:
            self._reminders.sync_maintenance_due_reminder(
                family_id=family_id,
                created_by=user.id,
                existing_reminder_id=row.reminder_id,
                title=row.title,
                body=None,
                due_at=None,
            )
        self._repo.soft_delete(row)

    def list_history(
        self, user: User, family_id: UUID
    ) -> list[MaintenanceCompletionResponse]:
        self._require_member(user.id, family_id)
        rows = self._repo.list_completions_for_family(family_id)
        return [self._to_completion_response(r) for r in rows]

    def _sync_reminder(self, row: MaintenanceItem, user_id: UUID) -> UUID | None:
        title = f"Maintenance: {row.title}"
        body_parts: list[str] = []
        if row.next_due_mileage is not None:
            body_parts.append(f"Due at {row.next_due_mileage:,} mi")
        body = " · ".join(body_parts) if body_parts else row.notes
        reminder_id = self._reminders.sync_maintenance_due_reminder(
            family_id=row.family_id,
            created_by=user_id,
            existing_reminder_id=row.reminder_id,
            title=title,
            body=body,
            due_at=row.next_due_at,
        )
        return reminder_id

    def _parse_kind(
        self, category_raw: str, kind_raw: str
    ) -> tuple[MaintenanceCategory, MaintenanceItemKind]:
        try:
            category = MaintenanceCategory(category_raw)
            item_kind = MaintenanceItemKind(kind_raw)
        except ValueError as exc:
            raise HomeHubError(
                "VALIDATION_ERROR", "Invalid category or item kind", status_code=422
            ) from exc
        if item_kind not in KINDS_BY_CATEGORY[category]:
            raise HomeHubError(
                "VALIDATION_ERROR",
                f"Item kind {item_kind.value} is not valid for {category.value}",
                status_code=422,
            )
        return category, item_kind

    @staticmethod
    def _validate_mileage_on_create(
        body: CreateMaintenanceItemRequest, item_kind: MaintenanceItemKind
    ) -> None:
        if not requires_mileage_fields(item_kind):
            return
        if body.mileage_at_last_service is None and body.next_due_at is None:
            return

    def _require_member(self, user_id: UUID, family_id: UUID) -> None:
        if self._families_repo.get_membership(user_id, family_id) is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)

    def _to_item_response(self, row: MaintenanceItem, now: datetime) -> MaintenanceItemResponse:
        return MaintenanceItemResponse(
            id=row.id,
            family_id=row.family_id,
            category=row.category,
            item_kind=row.item_kind,
            title=row.title,
            notes=row.notes,
            last_completed_at=row.last_completed_at,
            next_due_at=row.next_due_at,
            interval_days=row.interval_days,
            interval_miles=row.interval_miles,
            mileage_at_last_service=row.mileage_at_last_service,
            previous_service_mileage=row.previous_service_mileage,
            next_due_mileage=row.next_due_mileage,
            current_mileage=row.current_mileage,
            reminder_id=row.reminder_id,
            stock_status=(
                row.stock_status if row.category == MaintenanceCategory.ITEMS.value else None
            ),
            overdue=is_overdue(
                now, row.next_due_at, row.next_due_mileage, row.current_mileage
            ),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_completion_response(row: MaintenanceCompletion) -> MaintenanceCompletionResponse:
        return MaintenanceCompletionResponse(
            id=row.id,
            item_id=row.item_id,
            family_id=row.family_id,
            completed_at=row.completed_at,
            mileage_at_completion=row.mileage_at_completion,
            previous_service_mileage=row.previous_service_mileage,
            next_due_at=row.next_due_at,
            next_due_mileage=row.next_due_mileage,
            notes=row.notes,
            created_at=row.created_at,
        )


def build_maintenance_service(session) -> MaintenanceService:
    families_repo = FamiliesRepository(session)
    reminders = RemindersService(RemindersRepository(session), families_repo)
    return MaintenanceService(
        MaintenanceRepository(session),
        families_repo,
        reminders,
        GroceryListsRepository(session),
    )
