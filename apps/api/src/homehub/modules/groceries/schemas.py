from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GroceryListResponse(BaseModel):
    id: UUID
    family_id: UUID
    name: str
    revision: int
    updated_at: datetime
    deleted_at: datetime | None = None


class CreateGroceryListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UpdateGroceryListRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    revision: int = Field(ge=1)
