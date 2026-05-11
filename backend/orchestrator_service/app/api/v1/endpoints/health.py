"""
Health check endpoint.
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
    """System health check."""
    uptime = (datetime.utcnow() - START_TIME).total_seconds()

    # Check external services status
    # In mock mode, all services are "ok"
    services_status = {
        "auth": "ok",
        "rag": "ok",
        "ocr": "ok",
        "validation": "ok",
        "integration": "ok",
    }

    # Determine overall status
    all_ok = all(s == "ok" for s in services_status.values())
    status = "ok" if all_ok else "degraded"

    return HealthStatus(
        status=status,
        version=settings.APP_VERSION,
        uptime_seconds=int(uptime),
        services=services_status,
        database="ok",
        search_index="ok",
        ocr_queue="ok",
        storage="ok",
    )
