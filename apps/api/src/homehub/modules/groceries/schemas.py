from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GroceryListResponse(BaseModel):
    id: UUID
    family_id: UUID
    name: str
    selected_store_id: UUID | None = None
    revision: int
    updated_at: datetime
    deleted_at: datetime | None = None


class GroceryListItemResponse(BaseModel):
    id: UUID
    list_id: UUID
    family_id: UUID
    name: str
    quantity: str
    checked: bool
    staple_id: UUID | None = None
    maintenance_item_id: UUID | None = None
    urgent_out: bool = False
    revision: int
    updated_at: datetime
    deleted_at: datetime | None = None


class GroceryStapleResponse(BaseModel):
    id: UUID
    family_id: UUID
    name: str
    revision: int
    updated_at: datetime
    deleted_at: datetime | None = None


class GroceryStoreResponse(BaseModel):
    id: UUID
    family_id: UUID
    name: str
    external_provider: str | None = None
    external_store_id: str | None = None
    address_line: str | None = None
    revision: int
    updated_at: datetime
    deleted_at: datetime | None = None


class GroceryStorePriceResponse(BaseModel):
    id: UUID
    family_id: UUID
    store_id: UUID
    item_name: str
    price_cents: int
    revision: int
    updated_at: datetime
    deleted_at: datetime | None = None


class CreateGroceryListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UpdateGroceryListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    revision: int = Field(ge=1)
    selected_store_id: UUID | None = None


class GroceryEstimateResponse(BaseModel):
    store_id: UUID
    list_id: UUID
    total_cents: int
    missing_item_names: list[str]
