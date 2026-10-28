import secrets
from uuid import UUID

from homehub.core.errors import HomeHubError
from homehub.modules.auth.models import User
from homehub.modules.auth.repository import AuthRepository
from homehub.modules.families.enums import FamilyRole
from homehub.modules.families.models import FamilyMembership
from homehub.modules.families.repository import FamiliesRepository
from homehub.modules.families.schemas import (
    CreateFamilyRequest,
    FamilyMemberResponse,
    FamilyResponse,
    JoinFamilyRequest,
    UpdateMemberRoleRequest,
)


class FamiliesService:
    """Family (node) lifecycle: create, join via invite, roles (ADR-002)."""

    def __init__(self, families_repo: FamiliesRepository, auth_repo: AuthRepository) -> None:
        self._families_repo = families_repo
        self._auth_repo = auth_repo

    def create_family(self, user: User, body: CreateFamilyRequest) -> FamilyResponse:
        # Creator becomes admin; joiners default to member (see ADR-002).
        invite_code = secrets.token_urlsafe(6).upper().replace("-", "")[:10]
        family = self._families_repo.create_family(body.name, invite_code)
        self._families_repo.add_membership(user.id, family.id, FamilyRole.admin)
        return FamilyResponse(id=family.id, name=family.name, invite_code=family.invite_code)

    def join_family(self, user: User, body: JoinFamilyRequest) -> FamilyResponse:
        family = self._families_repo.get_family_by_invite_code(body.invite_code)
        if family is None:
            raise HomeHubError("INVALID_INVITE", "Invite code not found", status_code=404)
        existing = self._families_repo.get_membership(user.id, family.id)
        if existing is not None:
            raise HomeHubError("ALREADY_MEMBER", "Already in this family", status_code=409)
        self._families_repo.add_membership(user.id, family.id, FamilyRole.member)
        return FamilyResponse(id=family.id, name=family.name, invite_code=family.invite_code)

    def get_family(self, user: User, family_id: UUID) -> FamilyResponse:
        self._require_membership(user.id, family_id)
        family = self._families_repo.get_family_by_id(family_id)
        if family is None:
            raise HomeHubError("NOT_FOUND", "Family not found", status_code=404)
        return FamilyResponse(id=family.id, name=family.name, invite_code=family.invite_code)

    def list_members(self, user: User, family_id: UUID) -> list[FamilyMemberResponse]:
        self._require_membership(user.id, family_id)
        rows = self._families_repo.list_memberships_for_family(family_id)
        result: list[FamilyMemberResponse] = []
        for row in rows:
            member_user = self._auth_repo.get_user_by_id(row.user_id)
            if member_user is None:
                continue
            result.append(
                FamilyMemberResponse(
                    user_id=member_user.id,
                    display_name=member_user.display_name,
                    email=member_user.email,
                    role=row.role,
                )
            )
        return result

    def update_member_role(
        self, actor: User, family_id: UUID, target_user_id: UUID, body: UpdateMemberRoleRequest
    ) -> FamilyMemberResponse:
        actor_membership = self._require_membership(actor.id, family_id)
        if actor_membership.role != FamilyRole.admin:
            raise HomeHubError("FORBIDDEN", "Only admins can change roles", status_code=403)
        updated = self._families_repo.update_member_role(family_id, target_user_id, body.role)
        if updated is None:
            raise HomeHubError("NOT_FOUND", "Member not found in family", status_code=404)
        target = self._auth_repo.get_user_by_id(target_user_id)
        if target is None:
            raise HomeHubError("NOT_FOUND", "User not found", status_code=404)
        return FamilyMemberResponse(
            user_id=target.id,
            display_name=target.display_name,
            email=target.email,
            role=updated.role,
        )

    def _require_membership(self, user_id: UUID, family_id: UUID) -> FamilyMembership:
        membership = self._families_repo.get_membership(user_id, family_id)
        if membership is None:
            raise HomeHubError("FORBIDDEN", "Not a member of this family", status_code=403)
        return membership
