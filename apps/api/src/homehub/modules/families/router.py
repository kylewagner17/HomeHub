from uuid import UUID

from fastapi import APIRouter

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.auth.repository import AuthRepository
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.families.schemas import (
    CreateFamilyRequest,
    FamilyMemberResponse,
    FamilyResponse,
    JoinFamilyRequest,
    UpdateMemberRoleRequest,
)
from homehub.modules.families.service import FamiliesService

router = APIRouter(prefix="/families", tags=["families"])


def _families_service(db: DbSession) -> FamiliesService:
    return FamiliesService(FamiliesRepository(db), AuthRepository(db))


@router.post("", response_model=FamilyResponse)
def create_family(body: CreateFamilyRequest, user: CurrentUser, db: DbSession) -> FamilyResponse:
    result = _families_service(db).create_family(user, body)
    db.commit()
    return result


@router.post("/join", response_model=FamilyResponse)
def join_family(body: JoinFamilyRequest, user: CurrentUser, db: DbSession) -> FamilyResponse:
    result = _families_service(db).join_family(user, body)
    db.commit()
    return result


@router.get("/{family_id}", response_model=FamilyResponse)
def get_family(family_id: UUID, user: CurrentUser, db: DbSession) -> FamilyResponse:
    return _families_service(db).get_family(user, family_id)


@router.get("/{family_id}/members", response_model=list[FamilyMemberResponse])
def list_members(family_id: UUID, user: CurrentUser, db: DbSession) -> list[FamilyMemberResponse]:
    return _families_service(db).list_members(user, family_id)


@router.patch("/{family_id}/members/{member_user_id}/role", response_model=FamilyMemberResponse)
def update_member_role(
    family_id: UUID,
    member_user_id: UUID,
    body: UpdateMemberRoleRequest,
    user: CurrentUser,
    db: DbSession,
) -> FamilyMemberResponse:
    result = _families_service(db).update_member_role(user, family_id, member_user_id, body)
    db.commit()
    return result
