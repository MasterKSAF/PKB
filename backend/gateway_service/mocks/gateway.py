"""
Gateway Mock — unified entry point (nginx emulation).
Combines all 5 routers on a single port 8081 with:
- CORS (all origins)
- RBAC (JWT validation, anonymous fallback)
- Idempotency-Key support for POST /documents and POST /chat
- X-Process-Time header
- Lifespan context manager
"""

import asyncio
import json
import os
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

# ---------------------------------------------------------------------------
# Track generated access tokens for RBAC lookup
# ---------------------------------------------------------------------------
import mocks.auth_service.main as auth_mod
from mocks.auth_service.main import router as auth_router
from mocks.common import SEED_USERS, utcnow
from mocks.orchestrator_service.main import router as orch_router
from mocks.query_service.main import router as query_router
from mocks.registry_service.main import main_router as registry_router
from mocks.registry_service.main import registry_docs_router

_ACCESS_TOKEN_USER: Dict[str, str] = {}  # access_token -> user_id
_MOCK_USERS: Dict[str, dict] = {u["user_id"]: u for u in SEED_USERS}

_orig_make_token = auth_mod._make_token


def _patched_make_token(user_id: str) -> dict:
    result = _orig_make_token(user_id)
    _ACCESS_TOKEN_USER[result["access_token"]] = user_id
    return result


auth_mod._make_token = _patched_make_token


# ---------------------------------------------------------------------------
# RBAC middleware
# ---------------------------------------------------------------------------


class RBACMiddleware(BaseHTTPMiddleware):
    """Validates JWT Bearer token (mock) and attaches user context.

    - Missing/invalid token → allowed as anonymous (backward compat)
    - Valid token → user info from seed data attached to request.state.user
    """

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")

        user_context: Dict[str, Any] = {
            "user_id": None,
            "roles": [],
            "role": None,
            "permissions": {},
            "is_authenticated": False,
            "is_anonymous": True,
        }

        if auth.startswith("Bearer "):
            token = auth[7:]
            user_id = _ACCESS_TOKEN_USER.get(token)
            if user_id and user_id in _MOCK_USERS:
                user = _MOCK_USERS[user_id]
                user_context.update(
                    user_id=user_id,
                    roles=user.get("roles", []),
                    role=user.get("role"),
                    permissions=user.get("permissions", {}),
                    is_authenticated=True,
                    is_anonymous=False,
                )

        request.state.user = user_context
        return await call_next(request)


# ---------------------------------------------------------------------------
# Idempotency-Key middleware
# ---------------------------------------------------------------------------

_IDEMPOTENCY_STORE: Dict[str, dict] = {}
_IDEMPOTENCY_TTL = 3600
_IDEMPOTENCY_PREFIXES = ("/api/v1/documents", "/api/v1/chat")


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Caches POST responses for /api/v1/documents* and /api/v1/chat*
    when Idempotency-Key header is provided."""

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST":
            return await call_next(request)
        path = request.url.path
        if not path.startswith(_IDEMPOTENCY_PREFIXES):
            return await call_next(request)
        key = request.headers.get("Idempotency-Key", "")
        if not key:
            return await call_next(request)

        cached = _IDEMPOTENCY_STORE.get(key)
        if cached is not None:
            return JSONResponse(
                status_code=cached["status_code"],
                content=cached["body"],
                headers={"Idempotency-Key-Repeated": "true"},
            )

        response = await call_next(request)
        if response.status_code < 500:
            try:
                body = await asyncio.gather(response.body())
                body_json = (
                    json.loads(body[0]) if isinstance(body[0], bytes) else body[0]
                )
            except Exception:
                try:
                    body_json = json.loads(str(response.body))
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
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    _IDEMPOTENCY_STORE.clear()
    _ACCESS_TOKEN_USER.clear()


# ---------------------------------------------------------------------------
# Create application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PKB Neuroassistant Mock Gateway",
    version="1.0.0",
    description="Mock gateway combining all services on a single port",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------

app.add_middleware(ProcessTimeMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router includes
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(orch_router)
app.include_router(query_router)
app.include_router(registry_router)
app.include_router(registry_docs_router, prefix="/api/v1/registry")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Direct run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8081)
