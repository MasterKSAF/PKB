"""
HTTP client for proxying requests to real microservices.

Gateway выступает как reverse-proxy: получает запрос от UI,
перенаправляет его в соответствующий внутренний сервис, и возвращает ответ.

Маршрутизация — по шаблону пути (path-pattern), а не по префиксу.
Для Registry пути трансформируются: /api/v1/documents/* → /api/v1/registry/documents/*.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

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
# Route rule — шаблон пути → сервис
# ---------------------------------------------------------------------------

# Символ для обозначения "любой метод"
ALL_METHODS = "*"


@dataclass
class RouteEntry:
    """Одно правило маршрутизации.

    Сопоставляет HTTP-метод и путь с именем внутреннего сервиса.
    При необходимости преобразует исходный путь в целевой (например,
    для Registry: /api/v1/documents/{id} → /api/v1/registry/documents/{id}).
    """

    methods: Set[str]
    """Допустимые HTTP-методы (например {'GET'}, {'POST','PUT'}) или {'*'} для любых."""

    path_regex: str
    """Регулярное выражение для сопоставления с путём запроса."""

    service: str
    """Имя целевого сервиса (ключ в config.service_urls)."""

    transform: Optional[Callable[[str], str]] = None
    """Опциональная функция преобразования пути.
    Если не задана, используется исходный путь без изменений."""

    _compiled: Optional[re.Pattern] = field(init=False, default=None, repr=False)

    def __post_init__(self):
        self._compiled = re.compile(self.path_regex)

    def match(self, method: str, path: str) -> bool:
        """Проверяет, подходит ли правило для данного запроса."""
        if ALL_METHODS not in self.methods:
            if method.upper() not in {m.upper() for m in self.methods}:
                return False
        return bool(self._compiled.match(path))

    def apply(self, path: str) -> str:
        """Применяет трансформацию пути (если задана) или возвращает исходный."""
        if self.transform:
            return self.transform(path)
        return path


# ---------------------------------------------------------------------------
# Таблица маршрутов — детализирована до уровня конкретных путей
# ---------------------------------------------------------------------------
# Порядок имеет значение: более специфичные правила идут раньше.
# Сначала документы и черновики (разделение Registry/Orchestrator),
# затем общие префиксы других сервисов.

ROUTE_TABLE: List[RouteEntry] = [
    # ── Registry: черновики (чтение) ──────────────────────────────────────
    RouteEntry(
        {"GET"}, r"^/api/v1/drafts(?:/\d+(?:/preview)?)?$", "registry",
        transform=lambda p: p.replace("/api/v1/drafts", "/api/v1/registry/drafts", 1),
    ),

    # ── Orchestrator: черновики (управление/пайплайн) ─────────────────────
    RouteEntry({"POST"}, r"^/api/v1/drafts$", "orchestrator"),
    RouteEntry({"POST"}, r"^/api/v1/drafts/\d+/preview$", "orchestrator"),
    RouteEntry({"GET"}, r"^/api/v1/drafts/\d+/preview/status$", "orchestrator"),
    RouteEntry({"PATCH"}, r"^/api/v1/drafts/\d+/decide$", "orchestrator"),
    RouteEntry({"PATCH"}, r"^/api/v1/drafts/\d+/metadata$", "orchestrator"),
    RouteEntry({"DELETE"}, r"^/api/v1/drafts/\d+$", "orchestrator"),
    RouteEntry({"GET"}, r"^/api/v1/drafts/\d+/tasks$", "orchestrator"),

    # ── Registry: документы (CRUD + чтение) ──────────────────────────────
    RouteEntry(
        {"GET", "PUT", "PATCH", "DELETE"}, r"^/api/v1/documents/\d+$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/sections$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    # pages listing: /documents/{id}/pages (exact) and /documents/{id}/pages/{page}(/...) 
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/pages(?:/.*)?$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/file$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/history$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/parameters$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/versions$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/\d+/succession$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),

    # ── Registry: документы — массовые/спец. операции ────────────────────
    # search — особый случай: Registry endpoint /api/v1/registry/search
    RouteEntry(
        {"GET", "POST"}, r"^/api/v1/documents/search$", "registry",
        transform=lambda _: "/api/v1/registry/search",
    ),
    RouteEntry(
        {"GET"}, r"^/api/v1/documents/export$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"POST"}, r"^/api/v1/documents/import$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),
    RouteEntry(
        {"POST"}, r"^/api/v1/documents/check-uniqueness$", "registry",
        transform=lambda p: p.replace("/api/v1/documents", "/api/v1/registry/documents", 1),
    ),

    # ── Orchestrator: документы — deprecated + пайплайн ─────────────────
    # POST /api/v1/documents — deprecated (OR-11), возвращает 410
    RouteEntry({"POST"}, r"^/api/v1/documents$", "orchestrator"),
    RouteEntry({"GET"}, r"^/api/v1/documents/\d+/status$", "orchestrator"),
    RouteEntry({"GET"}, r"^/api/v1/documents/queue$", "orchestrator"),
    RouteEntry({"GET"}, r"^/api/v1/documents/\d+/errors$", "orchestrator"),
    RouteEntry({"POST"}, r"^/api/v1/documents/\d+/versions$", "orchestrator"),
    RouteEntry({"POST"}, r"^/api/v1/documents/\d+/reprocess$", "orchestrator"),
    RouteEntry({"GET"}, r"^/api/v1/documents/\d+/tasks$", "orchestrator"),

    # ── Registry: прямой доступ /api/v1/registry/* ────────────────────────
    RouteEntry({ALL_METHODS}, r"^/api/v1/registry(?:/.*)?$", "registry"),

    # ── Задачи (tasks) — только Orchestrator ─────────────────────────────
    RouteEntry({ALL_METHODS}, r"^/api/v1/tasks(?:/.*)?$", "orchestrator"),

    # ── Другие сервисы (без изменений) ───────────────────────────────────
    RouteEntry({ALL_METHODS}, r"^/api/v1/auth(?:/.*)?$", "auth"),
    RouteEntry({ALL_METHODS}, r"^/api/v1/admin(?:/.*)?$", "auth"),
    RouteEntry({ALL_METHODS}, r"^/api/v1/chat(?:/.*)?$", "query"),
    RouteEntry({ALL_METHODS}, r"^/api/v1/text(?:/.*)?$", "query"),
    RouteEntry({ALL_METHODS}, r"^/api/v1/analyse(?:/.*)?$", "analyse"),
    RouteEntry({ALL_METHODS}, r"^/api/v1/rag(?:/.*)?$", "rag_search"),
]


DEPRECATED_INTEGRATION_PREFIXES = (
    "/api/v1/meridian",
    "/api/v1/files",
    "/api/v1/external",
)


def is_deprecated_integration_route(path: str) -> bool:
    """True для legacy-маршрутов снятого Integration Service."""
    normalized = path.rstrip("/")
    for prefix in DEPRECATED_INTEGRATION_PREFIXES:
        p = prefix.rstrip("/")
        if normalized == p or normalized.startswith(p + "/"):
            return True
    return False


# ---------------------------------------------------------------------------
# resolve_service — поиск маршрута по методу + пути
# ---------------------------------------------------------------------------

def resolve_service(method: str, path: str) -> Optional[Tuple[str, str]]:
    """Определяет сервис и целевой путь для запроса.

    Возвращает (имя_сервиса, целевой_путь) или None если маршрут не найден.

    В отличие от старой версии, учитывает HTTP-метод и выполняет
    преобразование пути (для Registry: документы → /api/v1/registry/*).
    """
    normalized = path.rstrip("/") if path != "/" else "/"

    for entry in ROUTE_TABLE:
        if entry.match(method, normalized):
            target = entry.apply(normalized)
            return entry.service, target

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

async def proxy_request(request: Request, service_name: str, target_path: Optional[str] = None) -> Response:
    """Проксирует HTTP-запрос к указанному внутреннему сервису.

    Args:
        request: Исходный запрос.
        service_name: Имя целевого сервиса (ключ в config.service_urls).
        target_path: Целевой путь (если None, используется оригинальный path).
                     Нужен для URL-трансформации (Registry: /api/v1/documents → /api/v1/registry/documents).

    1. Определяет целевой URL (service_url + target_path + query_string)
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

    # Целевой путь: либо переданный (с трансформацией), либо исходный
    path_to_use = target_path if target_path is not None else (
        request.url.path.rstrip("/") if request.url.path != "/" else "/"
    )
    query = request.url.query
    target_url = f"{base_url}{path_to_use}"
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

    # Проброс корреляционных заголовков (P11-2 / CM-5)
    for hdr in ("X-Request-ID", "X-Trace-ID"):
        val = getattr(request.state, hdr.lower().replace("-", "_"), None)
        if val:
            headers[hdr] = val
    # X-User-ID после JWT-валидации
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        headers["X-User-ID"] = str(user_id)
    # X-Draft-ID / X-Document-ID / X-Version-ID из пути
    for hdr in ("X-Draft-ID", "X-Document-ID", "X-Version-ID"):
        val = getattr(request.state, hdr.lower().replace("-", "_"), None)
        if val is not None:
            headers[hdr] = str(val)

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
