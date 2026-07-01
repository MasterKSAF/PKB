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
from fastapi.responses import JSONResponse, StreamingResponse

from gateway.client import proxy_request, resolve_service, is_deprecated_integration_route
from gateway.minio_proxy import fetch_from_minio
from gateway.config import config as gw_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Catch-all router — проксирует все /api/v1/* запросы к сервисам
# ---------------------------------------------------------------------------

proxy_router = APIRouter()


# ── MinIO proxy — отдаёт файлы напрямую из S3 ─────────────────────────
@proxy_router.api_route("/api/v1/files/{file_key:path}", methods=["GET"])
async def gateway_file_proxy(request: Request, file_key: str) -> Response:
    """Прокси GET /api/v1/files/{file_key} напрямую из MinIO (без integration service).

    Определяет bucket MinIO по префиксу ключа:
      - previews/* → images
      - иначе → documents
    """
    bucket = gw_config.minio_image_bucket if file_key.startswith("previews/") else gw_config.minio_bucket
    try:
        minio_response = await fetch_from_minio(file_key, bucket=bucket)
        content_type = minio_response.headers.get("content-type", "application/octet-stream")
        content_disposition = minio_response.headers.get("content-disposition", "inline")

        return StreamingResponse(
            content=minio_response.iter_bytes(),
            status_code=minio_response.status_code,
            media_type=content_type,
            headers={
                "Content-Disposition": content_disposition,
                "Content-Length": minio_response.headers.get("content-length", ""),
                "Accept-Ranges": "bytes",
            },
        )
    except Exception as exc:
        logger.warning(f"MinIO proxy error for {file_key}: {exc}")
        return JSONResponse(
            status_code=404,
            content=_error(
                "FILE_NOT_FOUND",
                f"Файл {file_key} не найден в MinIO.",
            ),
        )


# ── Catch-all reverse-proxy ────────────────────────────────────────────
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
