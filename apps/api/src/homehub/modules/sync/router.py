from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.groceries.repository import GroceryListsRepository
from homehub.modules.sync.repository import SyncRepository
from homehub.modules.sync.schemas import (
    SyncPingResponse,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
)
from homehub.modules.sync.service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


def _service(db: DbSession) -> SyncService:
    return SyncService(
        SyncRepository(db),
        GroceryListsRepository(db),
        FamiliesRepository(db),
    )


@router.get("/ping", response_model=SyncPingResponse)
def sync_ping(user: CurrentUser, db: DbSession) -> SyncPingResponse:
    server_time = _service(db).ping()
    return SyncPingResponse(server_time=server_time)


@router.get("/pull", response_model=SyncPullResponse)
def sync_pull(
    user: CurrentUser,
    db: DbSession,
    family_id: UUID,
    since: Annotated[datetime | None, Query()] = None,
) -> SyncPullResponse:
    return _service(db).pull(user, family_id, since)


@router.post("/push", response_model=SyncPushResponse)
def sync_push(body: SyncPushRequest, user: CurrentUser, db: DbSession) -> SyncPushResponse:
    result = _service(db).push(user, body)
    db.commit()
    return result
