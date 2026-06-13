"""
Главный модуль FastAPI приложения.

Подключает роутеры, глобальные обработчики ошибок, lifespan менеджер.
"""
import asyncio
from contextlib import asynccontextmanager

# === НАСТРОЙКА OBSERVABILITY В ПЕРВУЮ ОЧЕРЕДЬ ===
from app.core.telemetry import setup_observability, instrument_fastapi
from app.config import settings

# Настраиваем OpenTelemetry
tracer_provider, meter_provider, logger = setup_observability(
    service_name="parser_service",
    otlp_endpoint=settings.otel_endpoint
)

# === ОСТАЛЬНЫЕ ИМПОРТЫ ===
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.router import router as v1_router
from app.api.v2.router import router as v2_router
from app.core.exception_handlers import (
    parser_service_error_handler,
    validation_error_handler,
    generic_exception_handler
)
from app.core.exceptions import ParserServiceError
from app.core.task_state_storage import task_store
from app.core.minio_client import minio_client
from app.api.v1.endpoints import process as v1_process
from app.api.v2.endpoints import process as v2_process

shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения:
    - создание бакетов MinIO
    - запуск фоновой очистки задач
    - graceful shutdown
    """
    logger.debug("Starting application lifespan")
    v1_process.set_shutdown_event(shutdown_event)
    v2_process.set_shutdown_event(shutdown_event)

    # Создание бакетов в MinIO (если не существуют)
    await minio_client._ensure_bucket(settings.minio_bucket)
    await minio_client._ensure_bucket(settings.minio_image_bucket)
    logger.info("MinIO buckets checked/created", extra={
        "buckets": f"{settings.minio_bucket}, {settings.minio_image_bucket}"
    })

    # Запуск фоновой очистки устаревших задач
    cleanup_task = asyncio.create_task(task_store.start_cleanup())
    logger.debug("Background cleanup task started")

    yield

    # Graceful shutdown
    logger.info("Shutting down, cancelling background tasks...")
    shutdown_event.set()
    await asyncio.sleep(10)

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.debug("Cleanup task cancelled")

    await asyncio.sleep(2)
    logger.info("Shutdown complete")


app = FastAPI(
    title="Parser Service",
    description="Внутренний сервис парсинга документов из MinIO",
    version="2.0.0",
    lifespan=lifespan
)

# Инструментирование FastAPI для сбора трейсов
instrument_fastapi(app, tracer_provider)


# Подключение роутеров API версий
app.include_router(v1_router, prefix=settings.api_prefix)
app.include_router(v2_router, prefix="/api/v2")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Возвращает оригинальный статус и детали для HTTPException."""
    logger.debug(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Глобальные обработчики исключений (кастомные и общие)
app.add_exception_handler(ParserServiceError, parser_service_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Логируется только на DEBUG уровне (в соответствии с требованиями).
    """
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.get("/routes")
async def list_routes():
    """Отладочный эндпоинт: список всех маршрутов."""
    routes = [{"path": route.path, "methods": list(route.methods)} for route in app.routes]
    logger.debug(f"Routes requested, total {len(routes)}")
    return routes