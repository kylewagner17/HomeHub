"""HomeHub LAN API — modular monolith entrypoint and global exception handlers."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from homehub import __version__
from homehub.config import get_settings
from homehub.core.errors import ErrorBody, ErrorResponse, HomeHubError
from homehub.core.logging import configure_logging
from homehub.db.session import (
    check_database_connection,
    create_db_engine,
    create_session_factory,
)
from homehub.modules.auth.router import router as auth_router
from homehub.modules.calendar.router import router as calendar_router
from homehub.modules.families.router import router as families_router
from homehub.modules.groceries.router import router as groceries_lists_router
from homehub.modules.integrations.router import router as integrations_router
from homehub.modules.maintenance.router import router as maintenance_router
from homehub.modules.reminders.router import notifications_router, reminders_router
from homehub.modules.sync.router import router as sync_router
from homehub.schemas.health import HealthResponse

API_PREFIX = "/api/v1"

settings = get_settings()
configure_logging(settings.log_level)

engine = create_db_engine(settings.database_url)
session_factory = create_session_factory(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if settings.reminder_scheduler_enabled:
        from homehub.jobs.reminder_scheduler import start_reminder_scheduler

        scheduler = start_reminder_scheduler(session_factory)
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)
    engine.dispose()


app = FastAPI(title="HomeHub API", version=__version__, lifespan=lifespan)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(families_router, prefix=API_PREFIX)
app.include_router(groceries_lists_router, prefix=API_PREFIX)
app.include_router(reminders_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(maintenance_router, prefix=API_PREFIX)
app.include_router(calendar_router, prefix=API_PREFIX)
app.include_router(integrations_router, prefix=API_PREFIX)
app.include_router(sync_router, prefix=API_PREFIX)


def custom_openapi():
    """Expose Bearer JWT in Swagger UI (Authorize button)."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault(
        "securitySchemes",
        {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "access_token from POST /api/v1/auth/login (paste token only).",
            }
        },
    )
    public_suffixes = ("/auth/register", "/auth/login")
    for path, methods in schema.get("paths", {}).items():
        if path in ("/health", "/"):
            continue
        for op in methods.values():
            if not isinstance(op, dict):
                continue
            if any(path.endswith(suffix) for suffix in public_suffixes):
                continue
            op.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.exception_handler(HomeHubError)
async def homehub_error_handler(_request: Request, exc: HomeHubError) -> JSONResponse:
    body = exc.to_response().model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorBody(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
        )
    ).model_dump()
    return JSONResponse(status_code=422, content=body)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_ok = check_database_connection(engine)
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="ok" if db_ok else "unavailable",
        version=__version__,
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {"service": "homehub-api", "version": __version__, "docs": "/docs"}
