"""
T-12: health/live vs health/ready (CM-6, service_checker).

Проверяет, что:
  - GET /api/v1/system/health/live — liveness probe (200, {"status": "ok"})
  - GET /api/v1/system/health/ready — readiness probe (200, {"status": "ok"})
  - GET /api/v1/health — минимальный health (200, {"status": "ok"})
  - GET /api/v1/system/health — агрегированный health (200, {"status": "ok"})

Контракт (common_api.md):
  - live/ready — для Kubernetes liveness/readiness probes
  - system/health — полный health check с агрегацией (для system_admin)
  - health — минимальный ответ для неаутентифицированных
"""

import os
import sys

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


class TestLivenessProbe:
    """T-12: GET /api/v1/system/health/live — liveness probe."""

    def test_live_returns_200(self):
        """Liveness probe должен возвращать 200."""
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        assert resp.status_code == 200

    def test_live_returns_status_ok(self):
        """Liveness probe — {"status": "ok"}."""
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        body = resp.json()
        assert body.get("status") == "ok"

    def test_live_no_auth_required(self):
        """Liveness probe доступен без аутентификации."""
        resp = client.get(f"{BASE}/system/health/live", follow_redirects=False)
        assert resp.status_code == 200


class TestReadinessProbe:
    """T-12: GET /api/v1/system/health/ready — readiness probe."""

    def test_ready_returns_200(self):
        """Readiness probe должен возвращать 200."""
        resp = client.get(f"{BASE}/system/health/ready", follow_redirects=False)
        assert resp.status_code == 200

    def test_ready_returns_status_ok(self):
        """Readiness probe — {"status": "ok"}."""
        resp = client.get(f"{BASE}/system/health/ready", follow_redirects=False)
        body = resp.json()
        assert body.get("status") == "ok"


class TestMinimalHealth:
    """T-12: GET /api/v1/health — минимальный health check."""

    def test_health_returns_200(self):
        """GET /api/v1/health должен возвращать 200."""
        resp = client.get(f"{BASE}/health", follow_redirects=False)
        assert resp.status_code == 200

    def test_health_returns_status_ok(self):
        """GET /api/v1/health — {"status": "ok"}."""
        resp = client.get(f"{BASE}/health", follow_redirects=False)
        body = resp.json()
        assert body.get("status") == "ok"


class TestSystemHealth:
    """T-12: GET /api/v1/system/health — агрегированный health."""

    def test_system_health_returns_200(self):
        """GET /api/v1/system/health должен возвращать 200."""
        resp = client.get(f"{BASE}/system/health", follow_redirects=False)
        assert resp.status_code == 200

    def test_system_health_contains_status(self):
        """Ответ содержит status."""
        resp = client.get(f"{BASE}/system/health", follow_redirects=False)
        body = resp.json()
        assert "status" in body
