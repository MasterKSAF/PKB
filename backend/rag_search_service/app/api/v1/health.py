"""Health check endpoint по спецификации common_api.md."""

from __future__ import annotations

import time

from fastapi import APIRouter, status

from app.config import get_settings
from app.core.database import check_db_health
from app.models.response import HealthResponse

router = APIRouter()
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Проверка состояния сервиса. Используется Orchestrator и K8s probes.",
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    db_health = await check_db_health()

    # Статус сервиса зависит от состояния БД
    overall_status = "ok" if db_health.get("status") == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.service_version,
        uptime_seconds=int(time.time() - _start_time),
        details={"database": db_health},
    )