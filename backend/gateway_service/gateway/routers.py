"""
Catch-all router for the Gateway reverse-proxy.

Перенаправляет запросы от Web UI к соответствующим внутренним сервисам
на основе префикса пути. Собственные эндпоинты Gateway (/system/health,
/system/mode) регистрируются на уровне app и имеют приоритет над catch-all.
"""

import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from gateway.client import proxy_request, resolve_service, is_deprecated_integration_route

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Catch-all router — проксирует все /api/v1/* запросы к сервисам
# ---------------------------------------------------------------------------

proxy_router = APIRouter()


def _error(code: str, message: str) -> dict:
    """Формат ошибки, совместимый со спецификацией Registry."""
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


@proxy_router.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def gateway_catch_all(request: Request, path: str) -> Response:
    """Проксирует запрос к внутреннему сервису на основе префикса пути."""
    full_path = f"/api/v1/{path}"

    if is_deprecated_integration_route(full_path):
        return JSONResponse(
            status_code=410,
            content=_error(
                "SERVICE_REMOVED",
                "Integration Service отключён; маршруты "
                "meridian/files/external недоступны",
            ),
        )

    service_name = resolve_service(full_path)

    if not service_name:
        return JSONResponse(
            status_code=404,
            content=_error(
                "NOT_FOUND",
                f"Маршрут не найден: {request.method} {full_path}",
            ),
        )

    return await proxy_request(request, service_name)
