"""
Orchestrator Service - FastAPI application.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.otel import setup_otel
from app.core.trace import get_trace_id, set_trace_id, set_user_id, reset_trace_id
from app.db.base import engine, Base
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup, dispose engine on shutdown."""
    # Startup
    setup_logging(debug=settings.DEBUG)
    logger = logging.getLogger("orchestrator.main")
    logger.info(
        "Starting Orchestrator Service",
        extra={
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "db": settings.DATABASE_URL[:30] + "...",
        },
    )
    async with engine.begin() as conn:
        # Ensure pipeline schema exists
        if settings.DATABASE_URL.startswith("sqlite"):
            # SQLite: attach in-memory database as pipeline schema
            try:
                await conn.execute(text("ATTACH DATABASE ':memory:' AS pipeline"))
            except Exception:
                pass  # already attached
        else:
            # PostgreSQL: create schema if not exists
            try:
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS pipeline"))
            except Exception:
                pass  # non-fatal
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    # Initialize OpenTelemetry
    try:
        setup_otel(app)
    except Exception as otel_err:
        logger.warning(f"OTEL init failed (non-fatal): {otel_err}")
    yield
    # Shutdown
    logger.info("Shutting down Orchestrator Service")
    await engine.dispose()


def create_application() -> FastAPI:
    """Create FastAPI application instance."""
    application = FastAPI(
        title="Orchestrator Service API",
        description="Единая точка входа для публичного API Нейроассистента ПКБ",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trace ID middleware
    application.add_middleware(BaseHTTPMiddleware, dispatch=trace_middleware)

    # Include API router
    application.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX,
    )

    @application.get("/")
    async def root():
        return {
            "service": "orchestrator-service",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return application


async def trace_middleware(request, call_next):
    """Middleware: inject trace ID from header or generate new one."""
    trace_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID")
    set_trace_id(trace_id)
    # Propagate X-User-ID from Gateway (CM-5)
    user_id = request.headers.get("X-User-ID")
    if user_id:
        set_user_id(user_id)
    response = await call_next(request)
    response.headers["X-Trace-ID"] = get_trace_id()
    reset_trace_id()
    return response


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
