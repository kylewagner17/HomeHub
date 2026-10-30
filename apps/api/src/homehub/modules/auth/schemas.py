from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from homehub.modules.families.enums import FamilyRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class FamilyMembershipSummary(BaseModel):
    family_id: UUID
    family_name: str
    role: FamilyRole
    invite_code: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    memberships: list[FamilyMembershipSummary]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class DeviceTokenRequest(BaseModel):
    platform: str = Field(pattern="^(android|ios)$")
    token: str = Field(min_length=1, max_length=512)
