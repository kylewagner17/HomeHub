from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from homehub.modules.groceries.schemas import (
    GroceryListItemResponse,
    GroceryListResponse,
    GroceryStapleResponse,
    GroceryStorePriceResponse,
    GroceryStoreResponse,
)


class SyncEntityType(StrEnum):
    grocery_list = "grocery_list"
    grocery_list_item = "grocery_list_item"
    grocery_staple = "grocery_staple"
    grocery_store = "grocery_store"
    grocery_store_price = "grocery_store_price"


class SyncOperation(StrEnum):
    upsert = "upsert"
    delete = "delete"


class SyncEntityData(BaseModel):
    """Payload fields depend on entity_type; revision is always required for upserts."""

    revision: int = Field(ge=1)
    name: str | None = None
    selected_store_id: UUID | None = None
    list_id: UUID | None = None
    quantity: str | None = None
    checked: bool | None = None
    staple_id: UUID | None = None
    store_id: UUID | None = None
    item_name: str | None = None
    price_cents: int | None = None


class SyncMutation(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=64)
    entity_type: SyncEntityType
    operation: SyncOperation
    entity_id: UUID
    data: SyncEntityData | None = None


class SyncPushRequest(BaseModel):
    family_id: UUID
    mutations: list[SyncMutation]


class SyncPushResult(BaseModel):
    idempotency_key: str
    status: str
    entity_type: SyncEntityType | None = None
    entity: GroceryListResponse | None = None
    grocery_list_item: GroceryListItemResponse | None = None
    grocery_staple: GroceryStapleResponse | None = None
    grocery_store: GroceryStoreResponse | None = None
    grocery_store_price: GroceryStorePriceResponse | None = None


class SyncPushResponse(BaseModel):
    results: list[SyncPushResult]


class SyncPullResponse(BaseModel):
    server_time: datetime
    grocery_lists: list[GroceryListResponse] = Field(default_factory=list)
    grocery_list_items: list[GroceryListItemResponse] = Field(default_factory=list)
    grocery_staples: list[GroceryStapleResponse] = Field(default_factory=list)
    grocery_stores: list[GroceryStoreResponse] = Field(default_factory=list)
    grocery_store_prices: list[GroceryStorePriceResponse] = Field(default_factory=list)


class SyncPingResponse(BaseModel):
    ok: bool = True
    server_time: datetime
