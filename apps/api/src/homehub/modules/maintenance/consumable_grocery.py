"""Push household consumables onto grocery lists when stock is low/out (ADR-007)."""

from uuid import UUID, uuid4

from homehub.modules.groceries.models import GroceryListItem
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.maintenance.models import MaintenanceItem


class StockStatus:
    IN_STOCK = "in_stock"
    LOW = "low"
    OUT = "out"


def sync_grocery_lists_for_stock(
    grocery_repo: GroceryListsRepository,
    maintenance_row: MaintenanceItem,
) -> None:
    """Mirror maintenance consumable stock onto every active grocery list in the family."""
    if maintenance_row.category != "items":
        return

    status = maintenance_row.stock_status or StockStatus.IN_STOCK
    lists = [
        lst
        for lst in grocery_repo.list_lists_for_family(maintenance_row.family_id)
        if lst.deleted_at is None
    ]

    if status in (StockStatus.LOW, StockStatus.OUT):
        urgent = status == StockStatus.OUT
        for lst in lists:
            row = _find_linked_item(
                grocery_repo, lst.id, maintenance_row.family_id, maintenance_row.id
            )
            if row is None:
                row = grocery_repo.find_active_item_by_name(
                    lst.id, maintenance_row.family_id, maintenance_row.title
                )
                if row is not None:
                    row.maintenance_item_id = maintenance_row.id
                    row.urgent_out = urgent
                    row.checked = False
                    row.revision = row.revision + 1
                    grocery_repo.save_item(row)
                    continue
                grocery_repo.create_item(
                    uuid4(),
                    lst.id,
                    maintenance_row.family_id,
                    maintenance_row.title,
                    "1",
                    False,
                    None,
                    1,
                    maintenance_item_id=maintenance_row.id,
                    urgent_out=urgent,
                )
            else:
                row.urgent_out = urgent
                row.checked = False
                row.revision = row.revision + 1
                grocery_repo.save_item(row)
        return

    if status == StockStatus.IN_STOCK:
        for row in _all_linked_items(grocery_repo, maintenance_row.family_id, maintenance_row.id):
            row.urgent_out = False
            row.revision = row.revision + 1
            grocery_repo.save_item(row)


def reset_consumable_after_grocery_checkoff(
    grocery_repo: GroceryListsRepository,
    maintenance_repo,
    family_id: UUID,
    maintenance_item_id: UUID,
) -> None:
    """Checked off on a grocery list → household item back to in stock."""
    row = maintenance_repo.get_item(maintenance_item_id, family_id)
    if row is None or row.category != "items":
        return
    row.stock_status = StockStatus.IN_STOCK
    for linked in _all_linked_items(grocery_repo, family_id, maintenance_item_id):
        linked.urgent_out = False
        linked.revision = linked.revision + 1
        grocery_repo.save_item(linked)


def _find_linked_item(
    grocery_repo: GroceryListsRepository,
    list_id: UUID,
    family_id: UUID,
    maintenance_item_id: UUID,
) -> GroceryListItem | None:
    for row in grocery_repo.list_active_items_for_list(list_id, family_id):
        if row.maintenance_item_id == maintenance_item_id:
            return row
    return None


def _all_linked_items(
    grocery_repo: GroceryListsRepository,
    family_id: UUID,
    maintenance_item_id: UUID,
) -> list[GroceryListItem]:
    return [
        row
        for row in grocery_repo.list_items_for_family(family_id)
        if row.maintenance_item_id == maintenance_item_id and row.deleted_at is None
    ]
