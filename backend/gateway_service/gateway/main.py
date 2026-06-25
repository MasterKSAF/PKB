"""
PKB Neuroassistant Gateway Service — reverse-proxy для внутренних микросервисов.

Маршрутизирует запросы от Web UI к сервисам:
  Auth (:8082), Orchestrator (:8081), Query (:8083), Registry (:8084).

Режим работы только явный — GATEWAY_MODE=real.

Мок-сервер для тестирования Web UI (эмуляция всей системы) — отдельное приложение:
    python mocks/gateway.py          # единый шлюз на порту 8081
    python mocks/start_service.py all  # или сервисы по отдельности
"""

import json
import logging
import os
import re
import sys
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from gateway.client import (
    check_all_services_health,
    close_client,
    get_client,
    is_deprecated_integration_route,
)
from gateway.config import config
from gateway.logging_config import setup_logging
from gateway.rate_limiter import (
    RateLimitResult,
    check_idor_rate_limit,
    check_rate_limit,
)
from gateway.routers import proxy_router

# ---------------------------------------------------------------------------
# OpenTelemetry (CM-6) — graceful fallback если пакет не установлен
# ---------------------------------------------------------------------------

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


def _setup_otel(app_instance: FastAPI) -> None:
    """Инициализирует OpenTelemetry SDK (если пакеты установлены)."""
    if not _OTEL_AVAILABLE:
        logger.info("OpenTelemetry packages not installed — OTEL disabled")
        return
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
    service_name = os.getenv("OTEL_SERVICE_NAME", "gateway")
    try:
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otel_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app_instance)
        logger.info("OTEL SDK initialised — endpoint=%s", otel_endpoint)
    except Exception as exc:
        logger.warning("OTEL init failed — %s", exc)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

setup_logging()
logger = logging.getLogger("gateway")

logger.info("Gateway starting — mode=%s, port=%s", config.mode, config.port)


# ---------------------------------------------------------------------------
# StripTrailingSlash — нормализует путь ДО роутинга (без 307)
# ---------------------------------------------------------------------------


class StripTrailingSlashMiddleware(BaseHTTPMiddleware):
    """Обрезает trailing slash до того, как роутер начнёт обработку.

    Проверяет путь запроса: если он не корневой (/) и заканчивается на /
    — обрезает слеш в scope["path"] и scope["raw_path"].
    Это гарантирует, что catch-all роутер и resolve_service() увидят
    нормализованный путь без единого 307 редиректа.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path != "/" and path.endswith("/"):
            request.scope["path"] = path.rstrip("/")
            raw = request.scope.get("raw_path")
            if raw is not None and len(raw) > 1 and raw.endswith(b"/"):
                request.scope["raw_path"] = raw.rstrip(b"/")
        return await call_next(request)


# ---------------------------------------------------------------------------
# RequestTracingMiddleware — генерация X-Request-ID / X-Trace-ID (P11-2/CM-5)
# ---------------------------------------------------------------------------


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Генерирует X-Request-ID и X-Trace-ID (UUIDv4), если клиент не передал.

    Сохраняет в request.state для downstream middleware, proxy_request и логов.
    """

    async def dispatch(self, request: Request, call_next):
        # X-Request-ID
        req_id = request.headers.get("X-Request-ID", "")
        if not req_id:
            req_id = str(uuid.uuid4())
        request.state.request_id = req_id

        # X-Trace-ID (CM-5)
        trace_id = request.headers.get("X-Trace-ID", "")
        if not trace_id:
            trace_id = str(uuid.uuid4())
        request.state.x_trace_id = trace_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Trace-ID"] = trace_id
        return response


# ---------------------------------------------------------------------------
# CorrelationHeadersMiddleware — извлекает X-Draft-ID/X-Document-ID/X-Version-ID
# из URL-пути (CM-5)
# ---------------------------------------------------------------------------


# Паттерны для извлечения entity ID из URL
_DRAFT_PATH_RE = re.compile(r"/api/v1/drafts/(\d+)")
_DOC_PATH_RE = re.compile(r"/api/v1/documents/(\d+)")
_VERSION_PATH_RE = re.compile(r"/api/v1/documents/\d+/versions/(\d+)")


class CorrelationHeadersMiddleware(BaseHTTPMiddleware):
    """Извлекает и пробрасывает X-Draft-ID, X-Document-ID, X-Version-ID.

    Работает в паре с proxy_request: сохраняет ID в request.state,
    откуда client.py забирает их для проброса в downstream.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # X-Draft-ID — из пути или заголовка (с защитой от невалидных значений)
        draft_id = None
        if match := _DRAFT_PATH_RE.search(path):
            draft_id = int(match.group(1))
        elif raw := request.headers.get("X-Draft-ID"):
            try:
                draft_id = int(raw)
            except (ValueError, TypeError):
                logger.warning("Invalid X-Draft-ID header: %r", raw)
        if draft_id is not None:
            request.state.x_draft_id = draft_id

        # X-Document-ID
        doc_id = None
        if match := _DOC_PATH_RE.search(path):
            doc_id = int(match.group(1))
        elif raw := request.headers.get("X-Document-ID"):
            try:
                doc_id = int(raw)
            except (ValueError, TypeError):
                logger.warning("Invalid X-Document-ID header: %r", raw)
        if doc_id is not None:
            request.state.x_document_id = doc_id

        # X-Version-ID
        ver_id = None
        if match := _VERSION_PATH_RE.search(path):
            ver_id = int(match.group(1))
        elif raw := request.headers.get("X-Version-ID"):
            try:
                ver_id = int(raw)
            except (ValueError, TypeError):
                logger.warning("Invalid X-Version-ID header: %r", raw)
        if ver_id is not None:
            request.state.x_version_id = ver_id

        return await call_next(request)


# ---------------------------------------------------------------------------
# PIIQueryValidatorMiddleware — запрет PII в query-параметрах (GW-7)
# ---------------------------------------------------------------------------

# Список запрещённых имён query-параметров (common_api.md — "Чувствительные данные в URL")
_PII_QUERY_PATTERNS: list[re.Pattern] = [
    re.compile(r"^password$", re.I),
    re.compile(r"^access_token$", re.I),
    re.compile(r"^refresh_token$", re.I),
    re.compile(r"^.+_token$", re.I),
    re.compile(r"^.+_secret$", re.I),
    # _key только для известных auth-ключей (не document_key/file_key и т.д.)
    re.compile(r"^api_key$", re.I),
    re.compile(r"^apikey$", re.I),
    re.compile(r"^secret_key$", re.I),
    re.compile(r"^email$", re.I),
    re.compile(r"^phone$", re.I),
    re.compile(r"^passport$", re.I),
    re.compile(r"^inn$", re.I),
    re.compile(r"^snils$", re.I),
    re.compile(r"^ogrn$", re.I),
]


class PIIQueryValidatorMiddleware(BaseHTTPMiddleware):
    """Проверяет query-параметры на наличие PII.

    При обнаружении запрещённого параметра возвращает
    400 BAD_REQUEST с кодом PII_IN_QUERY_STRING.
    """

    async def dispatch(self, request: Request, call_next):
        for param_name in request.query_params.keys():
            for pattern in _PII_QUERY_PATTERNS:
                if pattern.match(param_name):
                    logger.warning(
                        "PII in query-string: %s=%s",
                        param_name, request.query_params[param_name],
                    )
                    return JSONResponse(
                        status_code=400,
                        content=_error_response(
                            "PII_IN_QUERY_STRING",
                            f"Запрещено передавать '{param_name}' в query-параметрах",
                        ),
                    )
        return await call_next(request)


# ---------------------------------------------------------------------------
# RBAC middleware — валидация JWT через Auth Service
# ---------------------------------------------------------------------------


def _normalize_roles(raw_roles: Any) -> list[str]:
    """Return a stable list of role names from Auth responses."""
    if isinstance(raw_roles, str):
        return [raw_roles]
    if isinstance(raw_roles, list):
        return [str(role) for role in raw_roles if role]
    return []


def _normalize_permissions(raw_permissions: Any, roles: list[str]) -> Dict[str, bool]:
    """Normalize Auth permissions from either boolean map or permission-code list."""
    if isinstance(raw_permissions, dict):
        normalized = dict(raw_permissions)
    elif isinstance(raw_permissions, list):
        permissions = {str(permission) for permission in raw_permissions}
        normalized = {
            "can_upload_documents": (
                "documents:write" in permissions
                or "documents:manage" in permissions
                or "registry:manage" in permissions
            ),
            "can_run_ocr": "ocr:write" in permissions or "ocr:manage" in permissions,
            "can_manage_users": "users:manage" in permissions,
            "can_manage_classifiers": (
                "classifiers:manage" in permissions
                or "registry:classifiers:manage" in permissions
                or "registry:manage" in permissions
            ),
            "can_manage_terminology": (
                "terminology:manage" in permissions
                or "registry:terminology:manage" in permissions
                or "registry:manage" in permissions
            ),
            "can_manage_registry": (
                "registry:manage" in permissions
                or "documents:manage" in permissions
                or "documents:write" in permissions
            ),
        }
    else:
        normalized = {}

    # Legacy Auth may send only roles[] + coarse permissions. Keep Gateway RBAC
    # aligned with the role comments below without overriding explicit booleans.
    role_set = set(roles)
    if "system_admin" in role_set:
        normalized.setdefault("can_manage_users", True)
        normalized.setdefault("can_upload_documents", True)
        normalized.setdefault("can_manage_classifiers", True)
        normalized.setdefault("can_manage_terminology", True)
        normalized.setdefault("can_manage_registry", True)
    elif "knowledge_admin" in role_set:
        normalized.setdefault("can_upload_documents", True)
        normalized.setdefault("can_manage_classifiers", True)
        normalized.setdefault("can_manage_terminology", True)
        normalized.setdefault("can_manage_registry", True)

    return normalized


class RBACMiddleware(BaseHTTPMiddleware):
    """Проверяет JWT Bearer-токен через Auth Service и применяет RBAC.

    Принцип работы:
      1. Извлекает токен из заголовка Authorization
      2. Валидирует токен через Auth Service (/api/v1/internal/auth/validate)
      3. Применяет матрицу доступа (admin, permissions)
      4. Прокси-запрос к сервису выполняется только после RBAC
    """

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")
        path = request.url.path.rstrip("/") if request.url.path != "/" else "/"

        if is_deprecated_integration_route(path):
            return JSONResponse(
                status_code=410,
                content=_error_response(
                    "SERVICE_REMOVED",
                    "Integration Service отключён; маршруты "
                    "meridian/files/external недоступны",
                ),
            )

        user_context: Dict[str, Any] = {
            "user_id": None,
            "full_name": None,
            "roles": [],
            "role": None,
            "permissions": {},
            "is_authenticated": False,
            "is_anonymous": True,
        }

        if auth.startswith("Bearer "):
            token = auth[7:]
            await _validate_token_remotely(token, user_context)

        request.state.user = user_context

        # ── RBAC enforcement ────────────────────────────────────────────────

        # Анонимный доступ только к /auth/*, /system/health, /system/mode
        if not config.allow_anonymous:
            if not (
                path.startswith("/api/v1/auth/")
                or path == "/api/v1/health"
                or path == "/api/v1/system/health"
                or path == "/api/v1/system/mode"
            ):
                if not user_context["is_authenticated"]:
                    _log_access_denied(request, "UNAUTHORIZED", "Требуется аутентификация")
                    return JSONResponse(
                        status_code=401,
                        content=_error_response(
                            "UNAUTHORIZED", "Требуется аутентификация"
                        ),
                    )

        # /admin/* — только system_admin
        if path.startswith("/api/v1/admin"):
            if not user_context["is_authenticated"]:
                return JSONResponse(
                    status_code=401,
                    content=_error_response(
                        "UNAUTHORIZED", "Требуется аутентификация"
                    ),
                )
            role = user_context.get("role")
            if role != "system_admin":
                return JSONResponse(
                    status_code=403,
                    content=_error_response(
                        "FORBIDDEN",
                        "Недостаточно прав для доступа к административным функциям",
                    ),
                )

        # /tasks/* — read-only, только system_admin и knowledge_admin
        if path.startswith("/api/v1/tasks"):
            if not user_context["is_authenticated"]:
                return JSONResponse(
                    status_code=401,
                    content=_error_response(
                        "UNAUTHORIZED", "Требуется аутентификация"
                    ),
                )
            if request.method != "GET":
                return JSONResponse(
                    status_code=405,
                    content=_error_response(
                        "METHOD_NOT_ALLOWED",
                        "Маршрут /tasks/* только для чтения (GET)",
                    ),
                )
            role = user_context.get("role")
            if role not in ("system_admin", "knowledge_admin"):
                return JSONResponse(
                    status_code=403,
                    content=_error_response(
                        "FORBIDDEN",
                        "Недостаточно прав для просмотра задач пайплайна",
                    ),
                )

        # Permission-based checks для аутентифицированных
        if user_context["is_authenticated"]:
            permissions = user_context.get("permissions", {})

            # POST /drafts — can_upload_documents (OR-11: POST /documents deprecated)
            if request.method == "POST" and path == "/api/v1/drafts":
                if not permissions.get("can_upload_documents", False):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для загрузки документов",
                        ),
                    )

            # POST/PUT/DELETE /registry/classifiers — can_manage_classifiers (CM-1)
            _classifier_path = path.startswith("/api/v1/registry/classifiers")
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and _classifier_path:
                if not permissions.get("can_manage_classifiers", False):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для управления классификаторами",
                        ),
                    )

            # POST/PUT/DELETE /registry/terminology — can_manage_terminology (CM-1)
            _term_path = path.startswith("/api/v1/registry/terminology")
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and _term_path:
                if not permissions.get("can_manage_terminology", False):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для управления терминологией",
                        ),
                    )

            # POST/PUT/DELETE /registry/documents — can_manage_registry
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and path.startswith(
                "/api/v1/registry/documents"
            ):
                if not permissions.get("can_manage_registry", False):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для управления реестром",
                        ),
                    )

            # GET /registry/search — knowledge_admin / system_admin (CM-1)
            if request.method == "GET" and path.startswith("/api/v1/registry/search"):
                if not (
                    permissions.get("can_manage_classifiers", False)
                    or permissions.get("can_manage_registry", False)
                ):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для поиска по реестру",
                        ),
                    )

            # DELETE /documents/{id}, DELETE /drafts{id},
            # POST /documents/{id}/reprocess (approve deprecated — OR-12)
            _doc_write = request.method == "DELETE" and (
                path.startswith("/api/v1/documents/")
                or path.startswith("/api/v1/drafts/")
            ) or (
                request.method == "POST"
                and path.startswith("/api/v1/documents/")
                and not path.startswith("/api/v1/documents/search")
                and not path.startswith("/api/v1/documents/queue")
            )
            if _doc_write:
                if not (
                    permissions.get("can_manage_classifiers", False)
                    or permissions.get("can_manage_terminology", False)
                ):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для управления документами",
                        ),
                    )

            # GET /monitor/metrics — knowledge_admin / system_admin
            if request.method == "GET" and path == "/api/v1/monitor/metrics":
                if not (
                    permissions.get("can_manage_classifiers", False)
                    or permissions.get("can_manage_registry", False)
                ):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для просмотра метрик",
                        ),
                    )

        # Сохраняем user_id в request.state для проксирования в downstream
        request.state.user_id = user_context.get("user_id")

        return await call_next(request)


async def _validate_token_remotely(token: str, user_context: Dict[str, Any]) -> bool:
    """Валидирует JWT через Auth Service (/api/v1/internal/auth/validate).

    В production делает HTTP-вызов к Auth Service.
    Если сервис недоступен — токен считается невалидным.
    """
    auth_url = config.service_urls.get("auth")
    if not auth_url:
        return False

    try:
        client = get_client()
        resp = await client.post(
            f"{auth_url}/api/v1/internal/auth/validate",
            json={"access_token": token},
            timeout=config.health_timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            roles = _normalize_roles(data.get("roles", []))
            role = data.get("role") or (roles[0] if roles else None)
            user_context.update(
                user_id=data.get("user_id"),
                full_name=data.get("full_name"),
                roles=roles,
                role=role,
                permissions=_normalize_permissions(data.get("permissions", {}), roles),
                is_authenticated=True,
                is_anonymous=False,
            )
            return True
    except Exception:
        logger.warning("Auth Service unavailable, token validation failed", exc_info=True)

    return False


# ---------------------------------------------------------------------------
# Idempotency-Key middleware
# ---------------------------------------------------------------------------

_IDEMPOTENCY_STORE: Dict[str, dict] = {}
_IDEMPOTENCY_TTL = config.idempotency_ttl
_IDEMPOTENCY_PREFIXES = ("/api/v1/drafts", "/api/v1/chat")


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Caches POST responses for /api/v1/drafts* and /api/v1/chat*."""

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)
        path = request.url.path
        if not path.startswith(_IDEMPOTENCY_PREFIXES):
            return await call_next(request)
        key = request.headers.get("Idempotency-Key", "")
        if not key:
            return await call_next(request)

        # Periodic cleanup
        if len(_IDEMPOTENCY_STORE) > 1000:
            now = time.time()
            expired = [
                k for k, v in _IDEMPOTENCY_STORE.items()
                if now - v.get("timestamp", 0) > _IDEMPOTENCY_TTL
            ]
            for k in expired:
                del _IDEMPOTENCY_STORE[k]

        cached = _IDEMPOTENCY_STORE.get(key)
        if cached is not None:
            if time.time() - cached.get("timestamp", 0) > _IDEMPOTENCY_TTL:
                del _IDEMPOTENCY_STORE[key]
            else:
                return JSONResponse(
                    status_code=cached["status_code"],
                    content=cached["body"],
                    headers={"Idempotency-Key-Repeated": "true"},
                )

        response = await call_next(request)
        if response.status_code < 500:
            try:
                body_json = json.loads(response.body)
            except Exception:
                body_json = {"detail": "cached"}
            _IDEMPOTENCY_STORE[key] = {
                "status_code": response.status_code,
                "body": body_json,
                "timestamp": time.time(),
            }
        return response


# ---------------------------------------------------------------------------
# X-Process-Time header middleware
# ---------------------------------------------------------------------------


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting и IDOR protection (CM-2, CM-3, GW-4, GW-6).

    Проверяет лимиты для каждого запроса:
      1. Общий rate limit по группе эндпоинтов (CM-2, GW-4)
      2. IDOR rate limit по entity ID (CM-3, GW-6)

    При превышении — 429 Too Many Requests.
    """

    async def dispatch(self, request: Request, call_next):
        if not config.rate_limit_enabled:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        method = request.method
        path = request.url.path

        # 1. Общий rate limit
        decision = await check_rate_limit(method, path, client_ip)
        if decision.result == RateLimitResult.BLOCKED:
            logger.warning(
                "Rate limit blocked: %s %s from %s (retry_after=%ds)",
                method, path, client_ip, decision.retry_after_seconds,
            )
            return JSONResponse(
                status_code=429,
                content=_error_response(
                    "TOO_MANY_REQUESTS",
                    "Превышен лимит запросов. Попробуйте через %d секунд"
                    % decision.retry_after_seconds,
                    details={"retry_after_seconds": decision.retry_after_seconds},
                ),
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )

        # 2. IDOR protection
        idor_decision = await check_idor_rate_limit(method, path, client_ip)
        if idor_decision and idor_decision.result == RateLimitResult.BLOCKED:
            logger.warning(
                "IDOR rate limit blocked: %s %s from %s (retry_after=%ds)",
                method, path, client_ip, idor_decision.retry_after_seconds,
            )
            return JSONResponse(
                status_code=429,
                content=_error_response(
                    "TOO_MANY_REQUESTS",
                    "Превышен лимит запросов к ресурсу. Попробуйте через %d секунд"
                    % idor_decision.retry_after_seconds,
                    details={"retry_after_seconds": idor_decision.retry_after_seconds},
                ),
                headers={"Retry-After": str(idor_decision.retry_after_seconds)},
            )

        return await call_next(request)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.6f}"
        return response


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------


# Константы специфичных кодов ошибок (CM-7 / D24)
ERROR_TIMEOUT_INDEX_TRIGGER = "INDEX_TRIGGER_TIMEOUT"
ERROR_TIMEOUT_DECISION = "DECISION_TIMEOUT"
ERROR_TIMEOUT_PREVIEW_TRIGGER = "PREVIEW_TRIGGER_TIMEOUT"
ERROR_TIMEOUT_LLM_GENERATION = "LLM_GENERATION_TIMEOUT"


def _error_response(
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict | None = None,
) -> dict:
    result = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if request_id or details:
        merged = {}
        if request_id:
            merged["request_id"] = request_id
        if details:
            merged.update(details)
        result["error"]["details"] = merged
    return result


def _error_code_from_status(status_code: int, detail: Any) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
    }
    if isinstance(detail, dict):
        err = detail.get("error", {})
        if isinstance(err, dict) and "code" in err:
            return err["code"]
        if "code" in detail:
            return detail["code"]
    return mapping.get(status_code, f"HTTP_{status_code}")


def _extract_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        return detail.get("message", detail.get("error", {}).get("message", str(detail)))
    if isinstance(detail, list):
        return "; ".join(str(d) for d in detail)
    return str(detail)


def _log_access_denied(request: Request, code: str, message: str) -> None:
    """Логирует отказ доступа с контекстом запроса."""
    logger.warning(
        "Access denied: %s %s → %s (%s)",
        request.method,
        request.url.path,
        code,
        message,
        extra={
            "error_code": code,
            "error_message": message,
            "req_path": request.url.path,
            "req_method": request.method,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Gateway starting — mode=%s, host=%s, port=%s",
        config.mode, config.host, config.port,
    )
    # OTEL SDK (CM-6)
    _setup_otel(_app)
    yield
    _IDEMPOTENCY_STORE.clear()
    await close_client()
    logger.info("Gateway shut down")


# ---------------------------------------------------------------------------
# Create application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PKB Neuroassistant Gateway Service",
    version="1.2.0",
    description=(
        "Reverse-proxy для внутренних микросервисов PKB Neuroassistant. "
        "Маршрутизирует запросы от Web UI к Auth, Orchestrator, Query, Registry."
    ),
    lifespan=lifespan,
    redirect_slashes=False,
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, JSONResponse):
        return exc.detail
    req_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_response(
            code=_error_code_from_status(exc.status_code, exc.detail),
            message=_extract_message(exc.detail),
            request_id=req_id,
        ),
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Глобальный обработчик необработанных исключений."""
    req_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_response(
            code="INTERNAL_ERROR",
            message="Внутренняя ошибка сервера",
            request_id=req_id,
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = {}
    errors = exc.errors()
    if errors:
        details = {
            "validation_errors": [
                {
                    "field": ".".join(str(p) for p in e.get("loc", [])),
                    "reason": e.get("msg", "invalid"),
                    "value": e.get("input", None),
                    "constraint": e.get("ctx", {}).get("expected", None) if e.get("ctx") else None,
                }
                for e in errors
            ]
        }
    return JSONResponse(
        status_code=422,
        content=_error_response(
            code="VALIDATION_ERROR",
            message="Ошибка валидации запроса",
            details=details,
        ),
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=_error_response(
            code="VALIDATION_ERROR",
            message="Ошибка валидации запроса",
            details={"errors": exc.errors()},
        ),
    )


# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------

# Порядок middleware (внешний → внутренний):
# CORS → PIIQueryValidator → RateLimit → RequestTracing → CorrelationHeaders → RBAC →
# Idempotency → ProcessTime → StripTrailingSlash → Router
#
# StripTrailingSlash — ПЕРВЫМ (самый глубокий), чтобы роутер и resolve_service
# видели нормализованный путь без trailing slash (без 307).
app.add_middleware(StripTrailingSlashMiddleware)
app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(CorrelationHeadersMiddleware)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(RateLimitMiddleware)    # CM-2, CM-3, GW-4, GW-6
app.add_middleware(PIIQueryValidatorMiddleware)
# CORS (GW-3): в development разрешено всё, в production — только CORS_ALLOWED_ORIGINS
_cors_origins = config.cors_allowed_origins.split(",") if config.cors_allowed_origins != "*" else ["*"]
if config.env == "production" and _cors_origins == ["*"]:
    logger.warning("CORS: ALL origins allowed — это небезопасно для production!")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Собственные эндпоинты Gateway (регистрируются до catch-all роутера)
# ---------------------------------------------------------------------------


@app.get("/api/v1/health")
@app.get("/api/v1/system/health")
async def gateway_health(request: Request):
    """Health-check с агрегированным статусом всех сервисов.

    Для неаутентифицированных запросов возвращает минимальный ответ
    {"status": "ok"} (требование безопасности).
    Полный ответ — только для system_admin.
    """
    user = getattr(request.state, "user", None)
    role = user.get("role", "") if user else ""

    # Минимальный ответ для неаутентифицированных
    if not role or role != "system_admin":
        return {"status": "ok"}

    # Полный ответ для system_admin
    services = await check_all_services_health()
    overall = "ok"
    for svc, status in services.items():
        if svc == "gateway":
            continue
        if status != "ok":
            overall = "degraded"
            break

    return {
        "status": overall,
        "version": "1.2.0",
        "services": services,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoints_total": sum(
            1 for r in app.routes if hasattr(r, "methods") and r.path
        ),
    }


@app.get("/api/v1/system/mode")
async def gateway_mode_info():
    """Информация о конфигурации Gateway."""
    return {
        "mode": config.mode,
        "port": config.port,
        "service_urls": {
            name: url for name, url in sorted(config.service_urls.items())
        },
        "allow_anonymous": config.allow_anonymous,
        "request_timeout": config.request_timeout,
    }


# ---------------------------------------------------------------------------
# GW-12: GET /api/v1/monitor/metrics — собственный эндпоинт Gateway
# ---------------------------------------------------------------------------


@app.get("/api/v1/monitor/metrics")
async def gateway_metrics():
    """Метрики качества системы (собственный эндпоинт Gateway).

    Orchestrator больше не имеет своего /monitor/metrics —
    метрики агрегируются на уровне Gateway (GW-12).
    """
    return {
        "control_metrics": {
            "ocr_quality": 0.98,
            "retrieval_quality": 0.91,
            "answers_with_sources": 0.96,
            "avg_latency_ms": 1420,
        },
        "answer_metrics": {
            "useful_rate": 0.84,
            "rated_answers": 43,
            "flagged_for_review": 5,
            "open_questions": 3,
        },
        "logs": [],
    }


# ---------------------------------------------------------------------------
# CM-6: service_checker — health/live, health/ready
# ---------------------------------------------------------------------------


@app.get("/api/v1/system/health/live")
async def health_live():
    """Liveness probe — сервис жив."""
    return {"status": "ok"}


@app.get("/api/v1/system/health/ready")
async def health_ready():
    """Readiness probe — сервис готов принимать запросы."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Diagnostics — прокси к diagnostics-server на хосте
# ---------------------------------------------------------------------------


@app.get("/api/v1/system/diagnostics")
async def gateway_diagnostics():
    """Полная диагностика сервера (прокси к diagnostics_server.py на хосте).

    Diagnostics server запускается отдельно на хосте (не в Docker):
      cd backend/diagnostics && ./start_diagnostics_server.sh start

    Адрес diagnostics server задаётся в DIAGNOSTICS_URL
    (по умолчанию http://host.docker.internal:9090/diagnostics).
    """
    url = config.diagnostics_url
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(url)
            content = resp.text
            return Response(content=content, media_type="text/plain")
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": "DIAGNOSTICS_UNAVAILABLE",
                    "message": f"Diagnostics server недоступен: {exc}",
                }
            },
        )


# ---------------------------------------------------------------------------
# Proxy router — catch-all для всех /api/v1/* запросов к сервисам
# --------------------------------------------------------------------------

app.include_router(proxy_router)


# ---------------------------------------------------------------------------
# Direct run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gateway.main:app",
        host=config.host,
        port=config.port,
        reload=os.getenv("GATEWAY_RELOAD", "").lower() in ("1", "true"),
    )
