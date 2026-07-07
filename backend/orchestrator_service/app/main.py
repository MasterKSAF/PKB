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
from app.db.base import engine
from app.db.retry_db import init_database
from app.services.task_poller import start_poller, stop_poller
from app.services.queue_drain_poller import start_queue_drain_poller, stop_queue_drain_poller


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
    # Initialise database schema with retry on transient connection errors
    await init_database()
    # Initialize OpenTelemetry
    try:
        setup_otel(app)
    except Exception as otel_err:
        logger.warning(f"OTEL init failed (non-fatal): {otel_err}")

    # Start BackgroundTaskPoller
    await start_poller()

    # Start QueueDrainPoller — фоновый диспатч queued задач
    await start_queue_drain_poller()

    # Cleanup stale locks at startup (M5: fallback if Celery Beat was down)
    try:
        from app.db.session import get_db_context
        from app.repositories.pipeline import TaskRepository

        async with get_db_context() as db:
            repo = TaskRepository(db)
            released = await repo.release_stale_locks(
                max_seconds=settings.pipeline.MAX_JOB_RUNNING_TIME
            )
            if released:
                logger.warning(
                    f"Startup: released {len(released)} stale task locks "
                    "(Celery Beat may have been down)"
                )

            # Reset active → queued: tasks orphaned by restart
            reactivated = await repo.reset_stale_active_tasks()
            if reactivated:
                logger.warning(
                    f"Startup: reset {len(reactivated)} stale active tasks to queued"
                    f" (ids: {[t.id for t in reactivated]})"
                )

            # Cleanup stale external tasks: on restart, any pending external task
            # is orphaned (the orchestrator that submitted it is gone). Delete them
            # and reset the corresponding pipeline steps so drain queue re-dispatches.
            from app.repositories.external_task_repo import ExternalTaskRepository
            ext_repo = ExternalTaskRepository(db)
            stale_ext_tasks = await ext_repo.delete_all_pending()
            if stale_ext_tasks:
                unique_pairs = set(stale_ext_tasks)
                for task_id, step_name in unique_pairs:
                    step = await repo.reset_task_step_for_fallback(
                        task_id, step_name, new_service_name="Orchestrator",
                    )
                    if step:
                        logger.warning(
                            f"Startup: reset step {step_name} for task {task_id}"
                            f" to pending (stale external task cleaned up)"
                        )
    except Exception as cleanup_err:
        logger.warning(f"Startup lock cleanup failed (non-fatal): {cleanup_err}")

    yield

    # Shutdown
    logger.info("Shutting down Orchestrator Service")
    await stop_queue_drain_poller()
    await stop_poller()
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
