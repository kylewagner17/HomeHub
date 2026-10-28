from uuid import UUID

from fastapi import APIRouter

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.groceries.schemas import (
    CreateGroceryListRequest,
    GroceryListResponse,
    UpdateGroceryListRequest,
)
from homehub.modules.groceries.service import GroceryListsService

router = APIRouter(prefix="/families/{family_id}/grocery-lists", tags=["groceries"])


def _service(db: DbSession) -> GroceryListsService:
    return GroceryListsService(GroceryListsRepository(db), FamiliesRepository(db))


@router.get("", response_model=list[GroceryListResponse])
def list_grocery_lists(
    family_id: UUID, user: CurrentUser, db: DbSession
) -> list[GroceryListResponse]:
    return _service(db).list_lists(user, family_id)


@router.post("", response_model=GroceryListResponse)
def create_grocery_list(
    family_id: UUID, body: CreateGroceryListRequest, user: CurrentUser, db: DbSession
) -> GroceryListResponse:
    result = _service(db).create_list(user, family_id, body)
    db.commit()
    return result


@router.patch("/{list_id}", response_model=GroceryListResponse)
def update_grocery_list(
    family_id: UUID,
    list_id: UUID,
    body: UpdateGroceryListRequest,
    user: CurrentUser,
    db: DbSession,
) -> GroceryListResponse:
    result = _service(db).update_list(user, family_id, list_id, body)
    db.commit()
    return result
