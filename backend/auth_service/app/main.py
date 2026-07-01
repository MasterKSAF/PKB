import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.v1 import audit, auth, internal, roles, users
from app.core.config import settings
from app.core.logger import get_logger
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal

try:
    from telemetry_lib.telemetry import instrument_fastapi, setup_observability
    _tracer_provider, _meter_provider, _ = setup_observability("auth-service", settings.otel_endpoint)
    _otel_enabled = True
except Exception:
    from app.core.logger import setup_logging
    setup_logging()
    _otel_enabled = False

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await init_db(db)
    logger.info("Auth Service started (env=%s)", settings.env)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Сервис аутентификации, ролей, доступов и аудита.",
    lifespan=lifespan,
)

if _otel_enabled:
    instrument_fastapi(app, _tracer_provider)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        content = {"error": detail}
    else:
        content = {"error": {"code": "ERROR", "message": str(detail), "details": {}}}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Внутренняя ошибка сервера", "details": {}}},
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(roles.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(internal.router, prefix="/api/v1")


from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse)
@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="auth_service", version="1.0.0")
