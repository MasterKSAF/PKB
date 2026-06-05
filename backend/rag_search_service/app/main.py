"""FastAPI-приложение RAG Search Service."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import get_settings
from app.core.database import close_db_pool, init_db_pool
from app.core.logging import setup_logging
from app.core.middleware import add_request_logging_middleware
from app.models.response import ErrorDetail, ErrorResponse

# Инициализируем логирование первым делом
logger = setup_logging()
settings = get_settings()

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: инициализация и очистка ресурсов."""
    logger.info(
        "Starting %s v%s on port %d",
        settings.service_name,
        settings.service_version,
        settings.service_port,
    )
    
    # Инициализируем пул БД
    try:
        await init_db_pool()
        logger.info("Database pool initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database pool: %s", e)
        # Продолжаем запуск, health check покажет ошибку
    
    logger.info("Service ready")

    yield

    logger.info("Shutting down %s", settings.service_name)
    
    # Закрываем пул БД
    await close_db_pool()
    
    logger.info("Shutdown complete")


app = FastAPI(
    title="RAG Search Service",
    description="Гибридный поиск релевантных чанков (dense + sparse + RRF). Внутренний сервис.",
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS для локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware — логирует каждый запрос (вход, выход, ошибки)
add_request_logging_middleware(app)


# --- Exception handlers (согласно common_api.md) ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="Internal server error",
                details={"type": type(exc).__name__},
            )
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=str(exc),
                details={},
            )
        ).model_dump(),
    )


# --- Подключаем роутеры ---

app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
        "docs": "/docs",
    }