from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MaintenanceItemResponse(BaseModel):
    id: UUID
    family_id: UUID
    category: str
    item_kind: str
    title: str
    notes: str | None
    last_completed_at: datetime | None
    next_due_at: datetime | None
    interval_days: int | None
    interval_miles: int | None
    mileage_at_last_service: int | None
    previous_service_mileage: int | None
    next_due_mileage: int | None
    current_mileage: int | None
    reminder_id: UUID | None
    stock_status: str | None
    overdue: bool
    created_at: datetime
    updated_at: datetime


class CreateMaintenanceItemRequest(BaseModel):
    category: str = Field(pattern="^(home|auto|items)$")
    item_kind: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    interval_miles: int | None = Field(default=None, ge=1, le=500_000)
    next_due_at: datetime | None = None
    mileage_at_last_service: int | None = Field(default=None, ge=0, le=2_000_000)
    previous_service_mileage: int | None = Field(default=None, ge=0, le=2_000_000)
    current_mileage: int | None = Field(default=None, ge=0, le=2_000_000)


class UpdateStockStatusRequest(BaseModel):
    stock_status: str = Field(pattern="^(in_stock|low|out)$")


class UpdateMaintenanceItemRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    interval_miles: int | None = Field(default=None, ge=1, le=500_000)
    next_due_at: datetime | None = None
    current_mileage: int | None = Field(default=None, ge=0, le=2_000_000)


class CompleteMaintenanceRequest(BaseModel):
    completed_at: datetime
    next_due_at: datetime | None = None
    mileage_at_completion: int | None = Field(default=None, ge=0, le=2_000_000)
    previous_service_mileage: int | None = Field(default=None, ge=0, le=2_000_000)
    notes: str | None = Field(default=None, max_length=2000)


class MaintenanceCompletionResponse(BaseModel):
    id: UUID
    item_id: UUID
    family_id: UUID
    completed_at: datetime
    mileage_at_completion: int | None
    previous_service_mileage: int | None
    next_due_at: datetime | None
    next_due_mileage: int | None
    notes: str | None
    created_at: datetime
