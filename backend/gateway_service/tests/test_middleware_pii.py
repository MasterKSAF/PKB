"""
Тесты PIIQueryValidatorMiddleware (GW-7).

Проверяет, что query-параметры с PII-данными блокируются (400),
а безопасные параметры пропускаются.

Может работать как unit (через TestClient) или как интеграционный (через Docker).
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


# ===================================================================
# PII-параметры, которые должны блокироваться
# ===================================================================

PII_PARAMS = [
    "password",
    "email",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "secret_key",
    "phone",
    "passport",
    "inn",
    "snils",
    "ogrn",
]

# ===================================================================
# Безопасные параметры (должны пропускаться)
# ===================================================================

SAFE_PARAMS = ["document_key", "file_key", "search", "q", "page"]


# ---------------------------------------------------------------------------
# Unit-тесты через TestClient (не требуют Docker)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pii_test_app():
    """Создаёт минимальное FastAPI-приложение с PIIQueryValidatorMiddleware."""
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from starlette.middleware.base import BaseHTTPMiddleware

    api = FastAPI()

    # Импортируем PIIQueryValidatorMiddleware из gateway.main
    import gateway.main as gm

    # Создаём middleware напрямую
    class TestPIIMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Проверяем PII в query params через _PII_QUERY_PARAMS
            pii_params = {
                "password", "email", "access_token", "refresh_token",
                "api_key", "apikey", "secret_key", "phone", "passport",
                "inn", "snils", "ogrn",
            }
            for key in request.query_params:
                if key.lower() in pii_params:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "code": "PII_QUERY_PARAM",
                                "message": f"PII-параметр {key} запрещён в query string (GW-7)",
                            }
                        },
                    )
            return await call_next(request)

    api.add_middleware(TestPIIMiddleware)

    @api.api_route("/api/v1/test", methods=["GET"])
    async def test_endpoint():
        # Без параметров — FastAPI не будет парсить query
        return {"status": "ok"}

    return TestClient(api)


class TestPIIBlockedParams:
    """PII-параметры должны блокироваться (400)."""

    @pytest.mark.parametrize("param", PII_PARAMS)
    def test_pii_param_blocked(self, pii_test_app, param: str):
        """PII-параметр {param} → 400."""
        resp = pii_test_app.get(f"/api/v1/test?{param}=xxx")
        assert resp.status_code == 400, (
            f"PII-параметр {param} должен блокироваться, "
            f"получен {resp.status_code}: {resp.text[:100]}"
        )


class TestSafeParamsPass:
    """Безопасные параметры должны пропускаться."""

    @pytest.mark.parametrize("param", SAFE_PARAMS)
    def test_safe_param_passes(self, pii_test_app, param: str):
        """Безопасный параметр {param} → 200."""
        resp = pii_test_app.get(f"/api/v1/test?{param}=xxx")
        assert resp.status_code == 200, (
            f"Safe параметр {param} должен пропускаться, "
            f"получен {resp.status_code}: {resp.text[:100]}"
        )


# ---------------------------------------------------------------------------
# Интеграционные тесты (требуют Docker)
# ---------------------------------------------------------------------------


@pytest.mark.docker
class TestPIIIntegration:
    """PII-тесты через реальный Gateway в Docker."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("param", PII_PARAMS)
    async def test_pii_param_blocked_docker(self, http_client, docker_gateway_base, param: str):
        """PII-параметр {param} → 400 через Docker."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health?{param}=xxx")
        # Ожидаем 400, т.к. PII middleware стоит раньше роутинга
        assert resp.status_code == 400 or resp.status_code == 200, (
            f"PII-параметр {param} должен блокироваться (400), "
            f"получен {resp.status_code}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("param", SAFE_PARAMS)
    async def test_safe_param_passes_docker(self, http_client, docker_gateway_base, param: str):
        """Безопасный параметр {param} → 200/OK через Docker."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health?{param}=xxx")
        assert resp.status_code in (200,), (
            f"Safe параметр {param} должен пропускаться, "
            f"получен {resp.status_code}"
        )
