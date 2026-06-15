from time import monotonic

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag_builder.core.config import settings
from rag_builder.db.session import get_session

router = APIRouter(tags=["health"])

_STARTED_AT_MONOTONIC = monotonic()


@router.get(
    "/health",
    summary="Состояние сервиса",
    description=(
        "Единый health-check по контракту common_api.md. "
        "Проверяет доступность сервиса и базы данных через SQL-запрос `SELECT 1`."
    ),
    responses={
        200: {
            "description": (
                "Состояние сервиса в едином формате. "
                "`status=ok` если БД доступна, `status=degraded` если зависимость недоступна."
            )
        }
    },
)
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str | int]:
    logger.debug("GET /health")
    status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        status = "degraded"
        logger.exception("Health check dependency failure service={}", settings.service_name)

    return {
        "status": status,
        "service": settings.service_name,
        "version": settings.app_version,
        "uptime_seconds": int(monotonic() - _STARTED_AT_MONOTONIC),
    }
