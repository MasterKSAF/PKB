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
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict

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
)
from gateway.config import config
from gateway.routers import proxy_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, os.getenv("GATEWAY_LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gateway")

logger.info("Gateway starting — mode=%s, port=%s", config.mode, config.port)


# ---------------------------------------------------------------------------
# RBAC middleware — валидация JWT через Auth Service
# ---------------------------------------------------------------------------


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
        path = request.url.path

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
                or path == "/api/v1/system/health"
                or path == "/api/v1/system/mode"
            ):
                if not user_context["is_authenticated"]:
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

        # Permission-based checks для аутентифицированных
        if user_context["is_authenticated"]:
            permissions = user_context.get("permissions", {})

            # POST /drafts и POST /documents — can_upload_documents
            if request.method == "POST" and path in ("/api/v1/drafts", "/api/v1/documents"):
                if not permissions.get("can_upload_documents", False):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для загрузки документов",
                        ),
                    )

            # POST/PUT/DELETE /classifiers — can_manage_classifiers
            _classifier_path = path.startswith("/api/v1/classifiers") or path.startswith("/api/v1/registry/classifiers")
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and _classifier_path:
                if not permissions.get("can_manage_classifiers", False):
                    return JSONResponse(
                        status_code=403,
                        content=_error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для управления классификаторами",
                        ),
                    )

            # POST/PUT/DELETE /terminology — can_manage_terminology
            _term_path = path.startswith("/api/v1/terminology") or path.startswith("/api/v1/registry/terminology")
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

            # DELETE /documents/{id}, DELETE /drafts/{id},
            # POST /documents/{id}/reprocess, POST /documents/{id}/approve
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
            user_context.update(
                user_id=data.get("user_id"),
                full_name=data.get("full_name"),
                roles=data.get("roles", []),
                role=data.get("role"),
                permissions=data.get("permissions", {}),
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


def _error_response(code: str, message: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


def _error_code_from_status(status_code: int, detail: Any) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
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


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Gateway ready — mode=%s, host=%s, port=%s",
        config.mode, config.host, config.port,
    )
    yield
    _IDEMPOTENCY_STORE.clear()
    await close_client()
    logger.info("Gateway shut down")


# ---------------------------------------------------------------------------
# Create application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PKB Neuroassistant Gateway Service",
    version="1.1.0",
    description=(
        "Reverse-proxy для внутренних микросервисов PKB Neuroassistant. "
        "Маршрутизирует запросы от Web UI к Auth, Orchestrator, Query, Registry."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, JSONResponse):
        return exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_response(
            code=_error_code_from_status(exc.status_code, exc.detail),
            message=_extract_message(exc.detail),
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

app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allowed_origins.split(",") if config.cors_allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Собственные эндпоинты Gateway (регистрируются до catch-all роутера)
# ---------------------------------------------------------------------------


@app.get("/api/v1/system/health")
async def gateway_health():
    """Health-check с агрегированным статусом всех сервисов."""
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
        "version": "1.1.0",
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
# Proxy router — catch-all для всех /api/v1/* запросов к сервисам
# ---------------------------------------------------------------------------

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
