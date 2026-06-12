"""
HTTP client for proxying requests to real microservices.

Gateway выступает как reverse-proxy: получает запрос от UI,
перенаправляет его в соответствующий внутренний сервис, и возвращает ответ.
"""

import asyncio
import logging
from typing import Dict, Optional

import httpx
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from gateway.config import config

logger = logging.getLogger(__name__)


def _error_response(code: str, message: str) -> dict:
    """Формат ошибки, совместимый со спецификацией Registry."""
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


# ---------------------------------------------------------------------------
# Service routing table — префикс пути → имя сервиса
# ---------------------------------------------------------------------------
SERVICE_ROUTES: Dict[str, str] = {
    # Auth Service (:8082)
    "/api/v1/auth/": "auth",
    "/api/v1/admin/": "auth",
    # Orchestrator Service (:8081)
    "/api/v1/documents/": "orchestrator",
    "/api/v1/drafts/": "orchestrator",
    "/api/v1/tasks/": "orchestrator",
    "/api/v1/monitor/": "orchestrator",
    # Query Service (:8083)
    "/api/v1/chat/": "query",
    "/api/v1/text/": "query",
    # Registry Service (:8084)
    "/api/v1/classifiers/": "registry",
    "/api/v1/terminology/": "registry",
    "/api/v1/common/": "registry",
    "/api/v1/registry/": "registry",
    # Integration Service (:8085) — зарезервировано
    "/api/v1/meridian/": "integration",
    # Analyse Service (:8089) — зарезервировано
    "/api/v1/analyse/": "analyse",
}


def resolve_service(path: str) -> Optional[str]:
    """Определяет имя сервиса по префиксу пути.

    Сопоставление гибкое:
      /api/v1/classifiers      → registry (точное совпадение)
      /api/v1/classifiers/ext  → registry (вложенный путь)
      /api/v1/system/health    → None (собственный эндпоинт Gateway)
    """
    normalized = path.rstrip("/")
    for prefix, svc in SERVICE_ROUTES.items():
        p = prefix.rstrip("/")
        if normalized == p or normalized.startswith(p + "/"):
            return svc
    return None


# ---------------------------------------------------------------------------
# Shared httpx client
# ---------------------------------------------------------------------------

_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    """Возвращает разделяемый HTTP-клиент (lazy initialisation)."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(config.request_timeout),
            follow_redirects=False,
        )
    return _client


async def close_client():
    """Закрывает HTTP-клиент при завершении приложения."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

async def check_service_health(service_name: str) -> str:
    """Проверяет health конкретного сервиса, возвращает 'ok'/'unavailable'."""
    url = config.service_urls.get(service_name)
    if not url:
        return "unavailable"
    try:
        client = get_client()
        resp = await client.get(
            f"{url}/api/v1/system/health",
            timeout=httpx.Timeout(config.health_timeout),
        )
        if resp.status_code == 200:
            return "ok"
        return "degraded"
    except (httpx.ConnectError, httpx.TimeoutException):
        return "unavailable"
    except Exception:
        logger.exception("Health check failed for %s", service_name)
        return "unavailable"


async def check_all_services_health() -> Dict[str, str]:
    """Агрегированный health-check всех сервисов."""
    services = list(config.service_urls.keys()) + ["gateway"]
    results: Dict[str, str] = {}

    async def _check(name: str):
        if name == "gateway":
            results[name] = "ok"
        else:
            results[name] = await check_service_health(name)

    tasks = [asyncio.create_task(_check(s)) for s in services]
    await asyncio.gather(*tasks)
    return results


# ---------------------------------------------------------------------------
# Proxying logic
# ---------------------------------------------------------------------------

async def proxy_request(request: Request, service_name: str) -> Response:
    """Проксирует HTTP-запрос к указанному внутреннему сервису.

    1. Определяет целевой URL (service_url + path + query_string)
    2. Копирует заголовки (с фильтрацией hop-by-hop)
    3. Читает тело запроса (bytes)
    4. Отправляет запрос через httpx
    5. Возвращает ответ клиенту (статус, заголовки, тело)
    """
    base_url = config.service_urls.get(service_name)
    if not base_url:
        return JSONResponse(
            status_code=502,
            content=_error_response(
                "BAD_GATEWAY",
                f"Сервис '{service_name}' не настроен",
            ),
        )

    # Целевой URL
    path = request.url.path
    query = request.url.query
    target_url = f"{base_url}{path}"
    if query:
        target_url += f"?{query}"

    # Hop-by-hop заголовки (RFC 7230 §6.1) — не проксируются
    hop_by_hop = {
        "connection", "keep-alive", "proxy-authenticate",
        "proxy-authorization", "te", "trailers",
        "transfer-encoding", "upgrade",
    }
    # Content-Length, Host — httpx управляет ими самостоятельно

    headers = dict(request.headers.items())
    # Удаляем hop-by-hop заголовки
    for key in list(headers.keys()):
        if key.lower() in hop_by_hop:
            del headers[key]
    # Удаляем host — httpx установит правильный
    headers.pop("host", None)

    # Читаем тело запроса
    body = await request.body()

    try:
        client = get_client()
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=502,
            content=_error_response(
                "BAD_GATEWAY",
                f"Сервис '{service_name}' недоступен ({base_url})",
            ),
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content=_error_response(
                "GATEWAY_TIMEOUT",
                f"Сервис '{service_name}' не ответил за {config.request_timeout}с",
            ),
        )
    except Exception as exc:
        logger.exception("Proxy error for %s %s", request.method, target_url)
        return JSONResponse(
            status_code=502,
            content=_error_response(
                "BAD_GATEWAY",
                f"Ошибка проксирования к сервису '{service_name}': {exc}",
            ),
        )

    # Формируем ответ
    # Исключаем transfer-encoding из ответа (FastAPI управляет этим сама)
    response_headers = dict(resp.headers)
    for key in list(response_headers.keys()):
        if key.lower() in hop_by_hop or key.lower() == "content-length":
            del response_headers[key]

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type"),
    )
