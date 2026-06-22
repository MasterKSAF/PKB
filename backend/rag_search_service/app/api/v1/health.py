"""Health check endpoint по спецификации common_api.md."""

from __future__ import annotations

import time

from fastapi import APIRouter, status

from app.config import get_settings
from app.core.database import check_db_health
from app.core.logging import get_logger
from app.core.reranking import RerankingError, get_reranker
from app.models.response import HealthResponse

router = APIRouter()
_start_time = time.time()
logger = get_logger("api.health")


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

    details: dict = {"database": db_health}

    if settings.reranker_base_url:
        try:
            reranker = get_reranker()
            await reranker.rerank("", [], top_n=0)
            details["reranker"] = {"status": "ok", "model": reranker.get_model_name()}
        except RerankingError:
            details["reranker"] = {"status": "unavailable"}
        except Exception as e:
            logger.debug("TEI health probe failed: %s", e)
            details["reranker"] = {"status": "unavailable"}

    overall_status = "ok" if db_health.get("status") == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.service_version,
        uptime_seconds=int(time.time() - _start_time),
        details=details,
    )
