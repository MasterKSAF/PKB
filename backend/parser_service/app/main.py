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
tracer_provider, _, logger = setup_observability(
    service_name="parser_service",
    otlp_endpoint=settings.otel_endpoint,
)

# === ОСТАЛЬНЫЕ ИМПОРТЫ ===
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.exception_handlers import (
    parser_service_error_handler,
    validation_error_handler,
    generic_exception_handler,
)
from app.core.exceptions import ParserServiceError
from app.core.task_store import task_store
from app.core.minio_client import minio_client
from app.dependencies import init_services, get_pipeline_service

# Событие для graceful shutdown
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения:
    - создание бакетов MinIO
    - запуск фоновой очистки задач
    - запуск воркера очереди
    - graceful shutdown
    """
    logger.info("Starting application lifespan")

    # Инициализируем сервисы (DI) с shutdown_event
    init_services(shutdown_event)
    logger.debug("Services initialized")

    # Создание бакетов в MinIO (если не существуют)
    await minio_client._ensure_bucket(settings.minio_bucket)
    await minio_client._ensure_bucket(settings.minio_image_bucket)
    logger.info(
        "MinIO buckets checked/created: %s, %s",
        settings.minio_bucket,
        settings.minio_image_bucket,
    )

    # Запуск фоновой очистки устаревших задач
    cleanup_task = asyncio.create_task(task_store.start_cleanup())
    logger.debug("Background cleanup task started")

    # Воркер очереди уже запущен в PipelineService при инициализации

    yield

    # Graceful shutdown
    logger.info("Shutting down, cancelling background tasks...")
    shutdown_event.set()
    await asyncio.sleep(5)

    # Остановка воркера очереди
    pipeline_service = get_pipeline_service()
    if pipeline_service:
        await pipeline_service.shutdown_worker()

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
    lifespan=lifespan,
)

# Инструментирование FastAPI для сбора трейсов
instrument_fastapi(app, tracer_provider)

# Подключение роутера API
app.include_router(v1_router, prefix=settings.api_prefix)

# Глобальные обработчики исключений
app.add_exception_handler(ParserServiceError, parser_service_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Возвращает оригинальный статус и детали для HTTPException."""
    logger.debug("HTTPException: %s - %s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    # Логируем только в DEBUG (без логов в INFO)
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.get("/routes")
async def list_routes():
    """Отладочный эндпоинт: список всех маршрутов."""
    routes = [{"path": route.path, "methods": list(route.methods)} for route in app.routes]
    logger.debug("Routes requested, total %d", len(routes))
    return routes