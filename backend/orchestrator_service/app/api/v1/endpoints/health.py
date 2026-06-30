"""
Health check endpoint.

Per API doc — orchestrator polls GET /health of each internal service
and returns an aggregated result.
"""

import asyncio
from datetime import datetime, UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status as http_status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.base import get_db
from app.schemas.validation import HealthStatus

# Service start time for uptime calculation
START_TIME = datetime.now(UTC)

router = APIRouter()


@router.get("/system/health", response_model=HealthStatus)
async def health_check():
    """System health check — aggregated health of all internal services.

    In mock mode, all services are ``ok``.
    In real mode, polls each downstream ``/health`` with 2s timeout
    and marks ``degraded`` for failed/unreachable services.
    """
    import httpx

    uptime = (datetime.now(UTC) - START_TIME).total_seconds()

    # Mock-mode: keep legacy "all ok" behaviour.
    if settings.services.REGISTRY_SERVICE_MOCK:
        services_status = {
            "auth": "ok",
            "rag_builder": "ok",
            "rag_search": "ok",
            "ocr": "ok",
            "validation": "ok",
            "integration": "ok",
        }
    else:
        # Real mode: poll each downstream /health in parallel.
        targets: dict[str, str | None] = {
            "auth": settings.services.AUTH_SERVICE_URL if hasattr(settings.services, "AUTH_SERVICE_URL") else None,
            "rag_builder": settings.services.RAG_BUILDER_SERVICE_URL,
            "rag_search": settings.services.RAG_SEARCH_SERVICE_URL,
            "ocr": settings.services.OCR_SERVICE_URL,
            "validation": settings.services.CONVERTER_SERVICE_URL,
        }

        async def _probe(name: str, base: str | None) -> tuple[str, str]:
            if not base:
                return name, "not_configured"
            url = base.rstrip("/") + "/health"
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(url)
                return name, "ok" if resp.status_code < 500 else "degraded"
            except Exception:
                return name, "degraded"

        results = await asyncio.gather(
            *(_probe(n, b) for n, b in targets.items())
        )
        services_status = {name: state for name, state in results}
        # integration has no service URL — mark as not_configured.
        services_status["integration"] = "not_configured"

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


@router.get("/health")
async def health_check_simple():
    """Simple health check — per internal service health contract.

    Returns minimal status, service name and version.
    """
    return {
        "status": "ok",
        "service": "orchestrator",
        "version": settings.APP_VERSION,
    }


@router.get("/health/live")
async def health_live():
    """Liveness check — process is alive and responding."""
    return {"status": "alive", "service": "orchestrator-service"}


@router.get("/health/ready")
async def health_ready(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Readiness check — service is ready to accept traffic.

    Checks database connectivity (SELECT 1) and basic service state.
    Returns 503 if DB is unreachable.
    """
    uptime = (datetime.now(UTC) - START_TIME).total_seconds()
    db_status = "online"
    db_error: str | None = None
    try:
        # SELECT 1 with explicit short timeout.
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=3.0)
    except Exception as exc:
        db_status = "offline"
        db_error = str(exc)[:200]
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE

    payload: dict = {
        "status": "ready" if db_status == "online" else "not_ready",
        "uptime_seconds": int(uptime),
        "database": db_status,
    }
    if db_error:
        payload["database_error"] = db_error
    return payload
