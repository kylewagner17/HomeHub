from datetime import UTC, datetime
from uuid import UUID

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.groceries.service import GroceryListsService
from homehub.modules.sync.repository import SyncRepository
from homehub.modules.sync.schemas import (
    SyncMutation,
    SyncOperation,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
    SyncPushResult,
)


class SyncService:
    def __init__(
        self,
        sync_repo: SyncRepository,
        lists_repo: GroceryListsRepository,
        families_repo: FamiliesRepository,
    ) -> None:
        self._sync_repo = sync_repo
        self._lists_repo = lists_repo
        self._families_repo = families_repo

    def ping(self) -> datetime:
        return datetime.now(UTC)

    def pull(self, user: User, family_id: UUID, since: datetime | None) -> SyncPullResponse:
        self._require_member(user.id, family_id)
        rows = self._lists_repo.list_for_family(family_id, since=since)
        return SyncPullResponse(
            server_time=datetime.now(UTC),
            grocery_lists=[GroceryListsService._to_response(r) for r in rows],
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
        if mutation.entity_type.value != "grocery_list":
            raise HomeHubError("UNSUPPORTED_ENTITY", "Unsupported entity type", status_code=400)

        if self._sync_repo.was_applied(mutation.idempotency_key):
            row = self._lists_repo.get_by_id(mutation.entity_id, family_id)
            entity = GroceryListsService._to_response(row) if row else None
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key, status="duplicate", entity=entity
            )

        if mutation.operation == SyncOperation.delete:
            row = self._lists_repo.get_by_id(mutation.entity_id, family_id)
            if row is None:
                self._sync_repo.record_applied(mutation.idempotency_key, family_id)
                return SyncPushResult(
                    idempotency_key=mutation.idempotency_key, status="applied", entity=None
                )
            row.deleted_at = datetime.now(UTC)
            row.revision = row.revision + 1
            self._lists_repo.save(row)
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity=GroceryListsService._to_response(row),
            )

        if mutation.data is None or not mutation.data.name:
            raise HomeHubError("VALIDATION_ERROR", "Missing grocery list data", status_code=422)

        row = self._lists_repo.get_by_id(mutation.entity_id, family_id)
        if row is None:
            row = self._lists_repo.create(
                mutation.entity_id,
                family_id,
                mutation.data.name,
                user.id,
                mutation.data.revision,
            )
            self._sync_repo.record_applied(mutation.idempotency_key, family_id)
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="applied",
                entity=GroceryListsService._to_response(row),
            )

        if mutation.data.revision < row.revision:
            return SyncPushResult(
                idempotency_key=mutation.idempotency_key,
                status="conflict",
                entity=GroceryListsService._to_response(row),
            )

        row.name = mutation.data.name
        row.revision = max(mutation.data.revision, row.revision)
        if row.deleted_at is not None:
            row.deleted_at = None
        self._lists_repo.save(row)
        self._sync_repo.record_applied(mutation.idempotency_key, family_id)
        return SyncPushResult(
            idempotency_key=mutation.idempotency_key,
            status="applied",
            entity=GroceryListsService._to_response(row),
        )

    def _require_member(self, user_id: UUID, family_id: UUID) -> None:
        if self._families_repo.get_membership(user_id, family_id) is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)
