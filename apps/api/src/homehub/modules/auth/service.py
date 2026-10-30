from homehub.core.errors import HomeHubError
from homehub.core.security import create_access_token, hash_password, verify_password
from homehub.modules.auth.models import User
from homehub.modules.auth.repository import AuthRepository
from homehub.modules.auth.schemas import (
    DeviceTokenRequest,
    FamilyMembershipSummary,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from homehub.modules.families.repository import FamiliesRepository


class AuthService:
    """Registration, login, and profile with embedded family memberships."""

    def __init__(self, auth_repo: AuthRepository, families_repo: FamiliesRepository) -> None:
        self._auth_repo = auth_repo
        self._families_repo = families_repo

    def register(self, body: RegisterRequest) -> TokenResponse:
        if self._auth_repo.get_user_by_email(body.email):
            raise HomeHubError("EMAIL_TAKEN", "Email already registered", status_code=409)
        user = self._auth_repo.create_user(
            body.email, hash_password(body.password), body.display_name
        )
        return self._token_response(user)

    def login(self, body: LoginRequest) -> TokenResponse:
        user = self._auth_repo.get_user_by_email(body.email)
        if user is None or not verify_password(body.password, user.password_hash):
            raise HomeHubError("INVALID_CREDENTIALS", "Invalid email or password", status_code=401)
        return self._token_response(user)

    def me(self, user: User) -> UserResponse:
        return self._user_response(user)

    def register_device_token(self, user: User, body: DeviceTokenRequest) -> None:
        self._auth_repo.upsert_push_token(user.id, body.platform, body.token)

    def _token_response(self, user: User) -> TokenResponse:
        token = create_access_token(user.id)
        return TokenResponse(access_token=token, user=self._user_response(user))

    def _user_response(self, user: User) -> UserResponse:
        memberships = self._families_repo.list_memberships_for_user(user.id)
        return UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            memberships=[
                FamilyMembershipSummary(
                    family_id=m.family_id,
                    family_name=m.family.name,
                    role=m.role,
                    invite_code=m.family.invite_code,
                )
                for m in memberships
            ],
        )
