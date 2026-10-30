from fastapi import APIRouter

from homehub.core.deps import CurrentUser, DbSession
from homehub.modules.auth.repository import AuthRepository
from homehub.modules.auth.schemas import (
    DeviceTokenRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from homehub.modules.auth.service import AuthService
from homehub.modules.families.repository import FamiliesRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_service(db: DbSession) -> AuthService:
    return AuthService(AuthRepository(db), FamiliesRepository(db))


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: DbSession) -> TokenResponse:
    service = _auth_service(db)
    result = service.register(body)
    db.commit()
    return result


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    service = _auth_service(db)
    result = service.login(body)
    db.commit()
    return result


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser, db: DbSession) -> UserResponse:
    return _auth_service(db).me(user)


@router.put("/device-token", status_code=204)
def register_device_token(user: CurrentUser, body: DeviceTokenRequest, db: DbSession) -> None:
    _auth_service(db).register_device_token(user, body)
    db.commit()
