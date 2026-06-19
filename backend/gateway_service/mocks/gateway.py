"""
Gateway Mock — unified entry point (nginx emulation).
Combines all 5 routers on a single port 8081 with:
- CORS (all origins)
- RBAC (JWT validation, anonymous fallback)
- Idempotency-Key support for POST /drafts and POST /chat
- X-Process-Time header
- Lifespan context manager
- Unified error format (Registry spec)

Routing map (see docs/gateway_service_api.md):
- /api/v1/auth/*, /api/v1/admin/*      → Auth handlers
- /api/v1/documents/*, /api/v1/drafts/*,
    /api/v1/tasks/*, /api/v1/monitor/*  → Orchestrator handlers
- /api/v1/chat/*, /api/v1/text/*        → Query handlers
- /api/v1/classifiers/*, /api/v1/terminology/*,
    /api/v1/common/*, /api/v1/registry/documents/* → Registry handlers
- /api/v1/health                         → Gateway (own)
- /api/v1/system/health                  → Gateway (alias)

Все данные — в едином пространстве имён (mocks.common).
Никакого разделения на сервисы, никакой синхронизации.
"""

import json
import logging
import os
import re
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

from mocks.common import SEED_USERS, error_response, utcnow, _access_token_map
from mocks.handlers import auth_router, orch_router, query_router, registry_router

_MOCK_USERS: Dict[int, dict] = {u["user_id"]: u for u in SEED_USERS}

# ---------------------------------------------------------------------------
# Test mode flag — при True анонимные запросы пропускаются
# (используется в тестах, чтобы не переписывать каждый вызов с токеном)
# ---------------------------------------------------------------------------
ALLOW_ANONYMOUS = False


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

logger = logging.getLogger("gateway")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Логгирует все входящие запросы и статус ответа."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        qs = request.url.query
        full_path = f"{path}?{qs}" if qs else path
        logger.info(">>> %s %s", method, full_path)
        response = await call_next(request)
        logger.info("<<< %s %s → %s", method, full_path, response.status_code)
        return response


class StripTrailingSlashMiddleware(BaseHTTPMiddleware):
    """Обрезает trailing slash ДО того, как FastAPI начнёт роутинг.
    Checker шлёт запросы С trailing slash, а роуты определены БЕЗ слеша.
    Корневой путь / не трогаем.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path != "/" and path.endswith("/"):
            request.scope["path"] = path.rstrip("/")
            raw = request.scope.get("raw_path")
            if raw is not None and len(raw) > 1 and raw.endswith(b"/"):
                request.scope["raw_path"] = raw.rstrip(b"/")
        return await call_next(request)


class PIIQueryValidatorMiddleware(BaseHTTPMiddleware):
    """Запрет PII в query-параметрах (GW-7)."""

    _PII_PATTERNS = [
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

    async def dispatch(self, request: Request, call_next):
        for param_name in request.query_params.keys():
            for pattern in self._PII_PATTERNS:
                if pattern.match(param_name):
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "PII_IN_QUERY_STRING",
                                "message": f"Запрещено передавать '{param_name}' в query-параметрах",
                            }
                        },
                    )
        return await call_next(request)


class RBACMiddleware(BaseHTTPMiddleware):
    """Validates JWT Bearer token (mock) and attaches user context.

    - Missing/invalid token → 401 for /admin/*, anonymous for others
    - Valid token → user info from seed data attached to request.state.user
    - Blocks /admin/* paths for non-system_admin users
    """ 

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")
        path = request.url.path.rstrip("/") if request.url.path != "/" else "/"

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
            user_id = _access_token_map.get(token)
            if user_id and user_id in _MOCK_USERS:
                user = _MOCK_USERS[user_id]
                user_context.update(
                    user_id=user_id,
                    full_name=user.get("full_name"),
                    roles=user.get("roles", []),
                    role=user.get("role"),
                    permissions=user.get("permissions", {}),
                    is_authenticated=True,
                    is_anonymous=False,
                )

        request.state.user = user_context

        # RBAC enforcement
        if ALLOW_ANONYMOUS:
            pass
        else:
            if not (
                    path.startswith("/api/v1/auth/") or path == "/api/v1/system/health" or path == "/api/v1/health"
                ):
                if not user_context["is_authenticated"]:
                    return JSONResponse(
                        status_code=401,
                        content=error_response(
                            "UNAUTHORIZED", "Требуется аутентификация"
                        ),
                    )

        # /admin/* — только system_admin
        if path.startswith("/api/v1/admin"):
            if not user_context["is_authenticated"]:
                return JSONResponse(
                    status_code=401,
                    content=error_response("UNAUTHORIZED", "Требуется аутентификация"),
                )
            role = user_context.get("role")
            if role != "system_admin":
                return JSONResponse(
                    status_code=403,
                    content=error_response(
                        "FORBIDDEN",
                        "Недостаточно прав для доступа к административным функциям",
                    ),
                )

        # ────────────────────────────────────────────────────────
        # Если пользователь аутентифицирован — проверяем permissions
        # на write-операции. Анонимные запросы пропускаем (fallback).
        # ────────────────────────────────────────────────────────
        if user_context["is_authenticated"]:
            permissions = user_context.get("permissions", {})

            # POST /drafts — can_upload_documents (OR-11: POST /documents deprecated)
            if request.method == "POST" and path == "/api/v1/drafts":
                if not permissions.get("can_upload_documents", False):
                    return JSONResponse(
                        status_code=403,
                        content=error_response(
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
                        content=error_response(
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
                        content=error_response(
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
                        content=error_response(
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
                        content=error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для поиска по реестру",
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
                        content=error_response(
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
                        content=error_response(
                            "FORBIDDEN",
                            "Недостаточно прав для просмотра метрик",
                        ),
                    )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Idempotency-Key middleware
# ---------------------------------------------------------------------------

_IDEMPOTENCY_STORE: Dict[str, dict] = {}
_IDEMPOTENCY_TTL = 3600
_IDEMPOTENCY_PREFIXES = ("/api/v1/drafts", "/api/v1/chat")


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)
        path = request.url.path
        if not path.startswith(_IDEMPOTENCY_PREFIXES):
            return await call_next(request)
        key = request.headers.get("Idempotency-Key", "")
        if not key:
            return await call_next(request)

        # Cleanup expired entries periodically
        if len(_IDEMPOTENCY_STORE) > 1000:
            now = time.time()
            expired = [k for k, v in _IDEMPOTENCY_STORE.items()
                       if now - v.get("timestamp", 0) > _IDEMPOTENCY_TTL]
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


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.6f}"
        return response


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    _IDEMPOTENCY_STORE.clear()
    _access_token_map.clear()


# ---------------------------------------------------------------------------
# Create application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PKB Neuroassistant Mock Gateway",
    version="1.0.0",
    description="Mock gateway combining all services on a single port",
    lifespan=lifespan,
    redirect_slashes=False,
)


# ---------------------------------------------------------------------------
# Exception handlers — unified error format
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, JSONResponse):
        return exc.detail
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
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
        content=error_response(
            code="VALIDATION_ERROR",
            message="Ошибка валидации запроса",
            details=details,
        ),
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_ERROR",
            message="Ошибка валидации запроса",
            details={"errors": exc.errors()},
        ),
    )


def _error_code_from_status(status_code: int, detail: any) -> str:
    """Map HTTP status to error code."""
    if isinstance(detail, dict):
        err = detail.get("error", {})
        if isinstance(err, dict) and "code" in err:
            return err["code"]
        if "code" in detail:
            return detail["code"]
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
    return mapping.get(status_code, f"HTTP_{status_code}")


def _extract_message(detail: any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        return detail.get(
            "message", detail.get("error", {}).get("message", str(detail))
        )
    if isinstance(detail, list):
        parts = [str(d) for d in detail]
        return "; ".join(parts)
    return str(detail)


# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------

app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(PIIQueryValidatorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StripTrailingSlashMiddleware)
app.add_middleware(RequestLogMiddleware)


# ---------------------------------------------------------------------------
# Health check — регистрируется ДО router includes, чтобы иметь приоритет
# ---------------------------------------------------------------------------


@app.get("/api/v1/health")
@app.get("/api/v1/system/health")
async def gateway_health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "services": {
            "auth": "ok",
            "orchestrator": "ok",
            "query": "ok",
            "registry": "ok",
            "gateway": "ok",
        },
        "timestamp": utcnow(),
        "endpoints_total": sum(
            1 for r in app.routes if hasattr(r, "methods") and r.path
        ),
    }


@app.get("/api/v1/monitor/metrics")
async def mock_metrics():
    """Метрики качества — собственный эндпоинт Gateway (GW-12)."""
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


@app.get("/api/v1/system/health/live")
async def health_live():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/api/v1/system/health/ready")
async def health_ready():
    """Readiness probe."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Router includes
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(orch_router)
app.include_router(query_router)
app.include_router(registry_router, prefix="/api/v1/registry")


# ---------------------------------------------------------------------------
# Direct run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8081)
