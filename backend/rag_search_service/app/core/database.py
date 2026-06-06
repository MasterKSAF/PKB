"""Управление пулом подключений к PostgreSQL через asyncpg."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import asyncpg
import numpy as np

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("database")

_pool: asyncpg.Pool | None = None


async def _register_vector_types(conn: asyncpg.Connection) -> None:
    """Регистрация типов pgvector для корректной работы asyncpg."""
    # Кодек для преобразования Python list/numpy array ↔ PostgreSQL vector
    await conn.set_type_codec(
        "vector",
        encoder=_vector_encoder,
        decoder=_vector_decoder,
        schema="public",
        format="text",
    )


def _vector_encoder(value: list[float] | np.ndarray) -> str:
    """Преобразование Python list/numpy array в строку pgvector."""
    if isinstance(value, np.ndarray):
        value = value.tolist()
    return "[" + ",".join(str(v) for v in value) + "]"


def _vector_decoder(value: str) -> list[float]:
    """Преобразование строки pgvector в Python list."""
    return [float(v) for v in value.strip("[]").split(",")]


async def init_db_pool() -> asyncpg.Pool:
    """Создать пул подключений при старте сервиса."""
    global _pool
    settings = get_settings()

    if _pool is not None and not _pool.is_closing():
        return _pool

    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.postgres_pool_min,
            max_size=settings.postgres_pool_max,
            init=_register_vector_types,
        )
        logger.info(
            "DB pool created: host=%s, db=%s, min=%d, max=%d",
            settings.postgres_host,
            settings.postgres_db,
            settings.postgres_pool_min,
            settings.postgres_pool_max,
        )
        return _pool
    except Exception as e:
        logger.error("Failed to create DB pool: %s", e)
        raise


async def close_db_pool() -> None:
    """Закрыть пул подключений при остановке сервиса."""
    global _pool
    if _pool is not None and not _pool.is_closing():
        await _pool.close()
        logger.info("DB pool closed")
    _pool = None


def get_pool() -> asyncpg.Pool:
    """Получить текущий пул подключений."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db_pool() first.")
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    """Контекстный менеджер для получения соединения из пула."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def check_db_health() -> dict[str, Any]:
    """Проверка доступности БД для health check."""
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                # Проверяем наличие необходимых схем
                schemas = await conn.fetch(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('registry', 'rag')"
                )
                schema_names = {row["schema_name"] for row in schemas}
                missing = {"registry", "rag"} - schema_names
                
                if missing:
                    return {
                        "status": "degraded",
                        "detail": f"Missing schemas: {', '.join(missing)}"
                    }
                return {"status": "ok", "detail": "DB connection OK"}
    except Exception as e:
        logger.error("DB health check failed: %s", e)
        return {"status": "error", "detail": str(e)}

    return {"status": "error", "detail": "unexpected result"}