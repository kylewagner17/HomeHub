from uuid import UUID, uuid4

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.models import GroceryList
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.groceries.schemas import (
    CreateGroceryListRequest,
    GroceryListResponse,
    UpdateGroceryListRequest,
)


class GroceryListsService:
    def __init__(
        self,
        lists_repo: GroceryListsRepository,
        families_repo: FamiliesRepository,
    ) -> None:
        self._lists_repo = lists_repo
        self._families_repo = families_repo

    def list_lists(self, user: User, family_id: UUID) -> list[GroceryListResponse]:
        self._require_member(user.id, family_id)
        rows = self._lists_repo.list_for_family(family_id)
        return [self._to_response(r) for r in rows if r.deleted_at is None]

    def create_list(
        self, user: User, family_id: UUID, body: CreateGroceryListRequest
    ) -> GroceryListResponse:
        self._require_member(user.id, family_id)
        row = self._lists_repo.create(uuid4(), family_id, body.name, user.id, revision=1)
        return self._to_response(row)

    def update_list(
        self, user: User, family_id: UUID, list_id: UUID, body: UpdateGroceryListRequest
    ) -> GroceryListResponse:
        self._require_member(user.id, family_id)
        row = self._lists_repo.get_by_id(list_id, family_id)
        if row is None or row.deleted_at is not None:
            raise HomeHubError("NOT_FOUND", "Grocery list not found", status_code=404)
        if body.revision < row.revision:
            raise HomeHubError(
                "CONFLICT",
                "Server has newer revision",
                status_code=409,
                details={"server": self._to_response(row).model_dump(mode="json")},
            )
        row.name = body.name
        row.revision = max(body.revision, row.revision)
        self._lists_repo.save(row)
        return self._to_response(row)

    def _require_member(self, user_id: UUID, family_id: UUID) -> None:
        if self._families_repo.get_membership(user_id, family_id) is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)

    @staticmethod
    def _to_response(row: GroceryList) -> GroceryListResponse:
        return GroceryListResponse(
            id=row.id,
            family_id=row.family_id,
            name=row.name,
            revision=row.revision,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )
