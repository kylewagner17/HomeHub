from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from homehub.modules.groceries.schemas import GroceryListResponse


class SyncEntityType(StrEnum):
    grocery_list = "grocery_list"


class SyncOperation(StrEnum):
    upsert = "upsert"
    delete = "delete"


class GroceryListMutationData(BaseModel):
    name: str | None = None
    revision: int = Field(ge=1)


class SyncMutation(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=64)
    entity_type: SyncEntityType
    operation: SyncOperation
    entity_id: UUID
    data: GroceryListMutationData | None = None


class SyncPushRequest(BaseModel):
    family_id: UUID
    mutations: list[SyncMutation]


class SyncPushResult(BaseModel):
    idempotency_key: str
    status: str
    entity: GroceryListResponse | None = None


class SyncPushResponse(BaseModel):
    results: list[SyncPushResult]


class SyncPullResponse(BaseModel):
    server_time: datetime
    grocery_lists: list[GroceryListResponse]


class SyncPingResponse(BaseModel):
    ok: bool = True
    server_time: datetime
