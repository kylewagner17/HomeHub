from uuid import UUID

from pydantic import BaseModel, Field

from homehub.modules.families.enums import FamilyRole


class CreateFamilyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class JoinFamilyRequest(BaseModel):
    invite_code: str = Field(min_length=4, max_length=16)


class UpdateMemberRoleRequest(BaseModel):
    role: FamilyRole


class FamilyResponse(BaseModel):
    id: UUID
    name: str
    invite_code: str


class FamilyMemberResponse(BaseModel):
    user_id: UUID
    display_name: str
    email: str
    role: FamilyRole
