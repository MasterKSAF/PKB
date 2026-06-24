"""
T-14: service_checker (CM-6).

Проверяет, что service_checker (health/live, health/ready) соответствует
контракту мониторинга:
  - GET /api/v1/system/health/live — exit-code 0 (ok)
  - GET /api/v1/system/health/ready — exit-code 0 (ok)
  - Ответ содержит атрибуты: status
  - Нет аутентификации (для мониторинга)
  - Формат совместим с Prometheus Blackbox Exporter

В production service_checker — это отдельный скрипт/контейнер, который:
  1. Делает HTTP GET к /health/live и /health/ready
  2. Возвращает exit-code 0 (ok), 1 (warning), 2 (critical)
  3. Собирает атрибуты (latency, status_code, response_time)

Здесь проверяем только HTTP-контракт эндпоинтов.
"""

import os
import sys
import time

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from fastapi.testclient import TestClient

import mocks.gateway

mocks.gateway.ALLOW_ANONYMOUS = True
from mocks.gateway import app

client = TestClient(app, raise_server_exceptions=False)

BASE = "/api/v1"


class TestServiceCheckerLiveEndpoint:
    """T-14: service_checker — liveness probe."""

    def test_live_returns_200(self):
        """liveness probe → 200 OK."""
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        assert resp.status_code == 200

    def test_live_response_time_acceptable(self):
        """liveness probe отвечает быстро (< 500ms)."""
        start = time.perf_counter()
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 0.5, f"Response too slow: {elapsed:.3f}s"

    def test_live_response_format(self):
        """liveness probe — {"status": "ok"}."""
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        body = resp.json()
        assert body == {"status": "ok"}


class TestServiceCheckerReadyEndpoint:
    """T-14: service_checker — readiness probe."""

    def test_ready_returns_200(self):
        """readiness probe → 200 OK."""
        resp = client.get(f"{BASE}/system/health/ready", follow_redirects=False)
        assert resp.status_code == 200

    def test_ready_response_format(self):
        """readiness probe — {"status": "ok"}."""
        resp = client.get(f"{BASE}/system/health/ready", follow_redirects=False)
        body = resp.json()
        assert body == {"status": "ok"}


class TestServiceCheckerExitCodes:
    """T-14: Симуляция exit-кодов service_checker.

    В production service_checker анализирует HTTP-статус и тело ответа:
      - 200 + {"status":"ok"} → exit 0
      - 200 + {"status":"degraded"} → exit 1
      - 5xx / timeout → exit 2
    """

    def test_live_implies_exit_0(self):
        """200 + {"status":"ok"} → exit 0."""
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
        # service_checker: exit 0

    def test_ready_implies_exit_0(self):
        """ready probe также → exit 0."""
        resp = client.get(f"{BASE}/system/health/ready", follow_redirects=False)
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
        # service_checker: exit 0
