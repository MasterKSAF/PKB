"""
Health check endpoint.

Per API doc — orchestrator polls GET /health of each internal service
and returns an aggregated result.
"""

from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.validation import HealthStatus

# Service start time for uptime calculation
START_TIME = datetime.utcnow()

router = APIRouter()


@router.get("/system/health", response_model=HealthStatus)
async def health_check():
    """System health check — aggregated health of all internal services.

    In mock mode, all services are ``ok``.
    """
    uptime = (datetime.utcnow() - START_TIME).total_seconds()

    services_status = {
        "auth": "ok",
        "rag_builder": "ok",
        "rag_search": "ok",
        "ocr": "ok",
        "validation": "ok",
        "integration": "ok",
    }

    all_ok = all(s == "ok" for s in services_status.values())
    status = "ok" if all_ok else "degraded"

    return HealthStatus(
        status=status,
        version=settings.APP_VERSION,
        uptime_seconds=int(uptime),
        services=services_status,
        database="online",
        search_index="ready",
        ocr_queue="idle",
        storage="online",
    )
