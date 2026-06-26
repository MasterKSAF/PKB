"""
Catch-all router for the Gateway reverse-proxy.

Перенаправляет запросы от Web UI к соответствующим внутренним сервисам
на основе path-pattern маршрутизации. Собственные эндпоинты Gateway
(/system/health, /system/mode) регистрируются на уровне app
и имеют приоритет над catch-all.

Маршрутизация учитывает HTTP-метод и выполняет URL-трансформацию
для Registry (документы/черновики: /api/v1/documents/* → /api/v1/registry/documents/*).
"""

import logging
import re

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from gateway.client import proxy_request, resolve_service, is_deprecated_integration_route

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Catch-all router — проксирует все /api/v1/* запросы к сервисам
# ---------------------------------------------------------------------------

proxy_router = APIRouter()


# Паттерн для нечислового draft_id в draft-путях
_INVALID_DRAFT_PATH_RE = re.compile(
    r"^/api/v1/drafts/(?!\d+)([^/]+)(?:/tasks|/preview(?:/status)?|/decide|/metadata)?$"
)


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
    """Проксирует запрос к внутреннему сервису по path-pattern маршруту."""
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

    # Новая сигнатура: resolve_service(method, path) → (service_name, target_path) | None
    result = resolve_service(request.method, full_path)

    if not result:
        # Проверка на нечисловой draft_id — даём внятную ошибку вместо 404
        if _INVALID_DRAFT_PATH_RE.search(full_path):
            return JSONResponse(
                status_code=400,
                content=_error(
                    "INVALID_DRAFT_ID",
                    f"draft_id должен быть числовым: {request.method} {full_path}",
                ),
            )
        return JSONResponse(
            status_code=404,
            content=_error(
                "NOT_FOUND",
                f"Маршрут не найден: {request.method} {full_path}",
            ),
        )

    service_name, target_path = result
    return await proxy_request(request, service_name, target_path)
