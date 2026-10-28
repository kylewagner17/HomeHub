from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from homehub.modules.families.enums import FamilyRole
from homehub.modules.families.models import Family, FamilyMembership


class FamiliesRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_family_by_id(self, family_id: UUID) -> Family | None:
        return self._session.get(Family, family_id)

    def get_family_by_invite_code(self, invite_code: str) -> Family | None:
        stmt = select(Family).where(Family.invite_code == invite_code.upper())
        return self._session.scalar(stmt)

    def create_family(self, name: str, invite_code: str) -> Family:
        family = Family(name=name, invite_code=invite_code.upper())
        self._session.add(family)
        self._session.flush()
        return family

    def add_membership(self, user_id: UUID, family_id: UUID, role: FamilyRole) -> FamilyMembership:
        membership = FamilyMembership(user_id=user_id, family_id=family_id, role=role)
        self._session.add(membership)
        self._session.flush()
        return membership

    def get_membership(self, user_id: UUID, family_id: UUID) -> FamilyMembership | None:
        stmt = select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
        return self._session.scalar(stmt)

    def list_memberships_for_family(self, family_id: UUID) -> list[FamilyMembership]:
        stmt = select(FamilyMembership).where(FamilyMembership.family_id == family_id)
        return list(self._session.scalars(stmt).all())

    def list_memberships_for_user(self, user_id: UUID) -> list[FamilyMembership]:
        stmt = (
            select(FamilyMembership)
            .where(FamilyMembership.user_id == user_id)
            .options(joinedload(FamilyMembership.family))
        )
        return list(self._session.scalars(stmt).unique().all())

    def update_member_role(
        self, family_id: UUID, user_id: UUID, role: FamilyRole
    ) -> FamilyMembership | None:
        membership = self.get_membership(user_id, family_id)
        if membership is None:
            return None
        membership.role = role
        self._session.flush()
        return membership
