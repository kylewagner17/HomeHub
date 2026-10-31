from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.maintenance.schemas import (
    CompleteMaintenanceRequest,
    CreateMaintenanceItemRequest,
    MaintenanceCompletionResponse,
    MaintenanceItemResponse,
    UpdateMaintenanceItemRequest,
    UpdateStockStatusRequest,
)
from homehub.modules.maintenance.service import build_maintenance_service

router = APIRouter(prefix="/families/{family_id}/maintenance", tags=["maintenance"])


@router.get("/items", response_model=list[MaintenanceItemResponse])
def list_items(
    family_id: UUID,
    user: CurrentUser,
    db: DbSession,
    category: Annotated[str | None, Query(pattern="^(home|auto|items)$")] = None,
) -> list[MaintenanceItemResponse]:
    return build_maintenance_service(db).list_items(user, family_id, category)


@router.post("/items", response_model=MaintenanceItemResponse)
def create_item(
    family_id: UUID,
    body: CreateMaintenanceItemRequest,
    user: CurrentUser,
    db: DbSession,
) -> MaintenanceItemResponse:
    result = build_maintenance_service(db).create_item(user, family_id, body)
    db.commit()
    return result


@router.patch("/items/{item_id}", response_model=MaintenanceItemResponse)
def update_item(
    family_id: UUID,
    item_id: UUID,
    body: UpdateMaintenanceItemRequest,
    user: CurrentUser,
    db: DbSession,
) -> MaintenanceItemResponse:
    result = build_maintenance_service(db).update_item(user, family_id, item_id, body)
    db.commit()
    return result


@router.patch("/items/{item_id}/stock", response_model=MaintenanceItemResponse)
def set_stock_status(
    family_id: UUID,
    item_id: UUID,
    body: UpdateStockStatusRequest,
    user: CurrentUser,
    db: DbSession,
) -> MaintenanceItemResponse:
    result = build_maintenance_service(db).set_stock_status(user, family_id, item_id, body)
    db.commit()
    return result


@router.post("/items/{item_id}/complete", response_model=MaintenanceItemResponse)
def complete_item(
    family_id: UUID,
    item_id: UUID,
    body: CompleteMaintenanceRequest,
    user: CurrentUser,
    db: DbSession,
) -> MaintenanceItemResponse:
    result = build_maintenance_service(db).complete_item(user, family_id, item_id, body)
    db.commit()
    return result


@router.delete("/items/{item_id}", status_code=204)
def delete_item(family_id: UUID, item_id: UUID, user: CurrentUser, db: DbSession) -> None:
    build_maintenance_service(db).delete_item(user, family_id, item_id)
    db.commit()


@router.get("/history", response_model=list[MaintenanceCompletionResponse])
def list_history(
    family_id: UUID, user: CurrentUser, db: DbSession
) -> list[MaintenanceCompletionResponse]:
    return build_maintenance_service(db).list_history(user, family_id)
