"""
Тесты ProcessTimeMiddleware.

Сценарии:
  - Ответ содержит X-Process-Time
  - Значение — число с плавающей точкой (float)
  - Время больше 0
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


@pytest.fixture(scope="module")
def process_time_test_app():
    """Создаёт минимальное приложение с ProcessTimeMiddleware."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from gateway.main import ProcessTimeMiddleware

    api = FastAPI()
    api.add_middleware(ProcessTimeMiddleware)

    @api.get("/api/v1/test")
    async def test_endpoint():
        return {"status": "ok"}

    return TestClient(api)


class TestProcessTime:
    """ProcessTimeMiddleware — заголовок X-Process-Time."""

    def test_response_contains_process_time(self, process_time_test_app):
        """Ответ содержит X-Process-Time."""
        resp = process_time_test_app.get("/api/v1/test")
        assert "X-Process-Time" in resp.headers

    def test_process_time_is_float(self, process_time_test_app):
        """X-Process-Time — число с плавающей точкой."""
        resp = process_time_test_app.get("/api/v1/test")
        value = resp.headers.get("X-Process-Time", "")
        try:
            float(value)
        except ValueError:
            pytest.fail(f"X-Process-Time не является float: {value!r}")

    def test_process_time_greater_than_zero(self, process_time_test_app):
        """X-Process-Time > 0."""
        resp = process_time_test_app.get("/api/v1/test")
        value = float(resp.headers.get("X-Process-Time", "0"))
        assert value > 0, f"X-Process-Time должен быть > 0, получен {value}"


# ---------------------------------------------------------------------------
# Интеграционные тесты (Docker)
# ---------------------------------------------------------------------------


@pytest.mark.docker
class TestProcessTimeIntegration:
    """ProcessTime — интеграционные тесты через Docker."""

    @pytest.mark.asyncio
    async def test_process_time_in_response(self, http_client, docker_gateway_base):
        """Ответ Gateway содержит X-Process-Time."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health")
        assert "X-Process-Time" in resp.headers

    @pytest.mark.asyncio
    async def test_process_time_positive(self, http_client, docker_gateway_base):
        """X-Process-Time > 0 (Docker)."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health")
        value = float(resp.headers.get("X-Process-Time", "0"))
        assert value > 0
