"""
Тесты StripTrailingSlashMiddleware.

Сценарии:
  - /api/v1/drafts/ → путь нормализован до /api/v1/drafts
  - /api/v1/drafts → без изменений
  - / → без изменений (корень)
  - /api/v1/drafts/123/ → /api/v1/drafts/123

Unit-тесты через TestClient с изолированным middleware + интеграционные.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


@pytest.fixture(scope="module")
def strip_slash_test_app():
    """Создаёт минимальное приложение с StripTrailingSlashMiddleware."""
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient

    # Копируем middleware
    from gateway.main import StripTrailingSlashMiddleware

    api = FastAPI(redirect_slashes=False)
    api.add_middleware(StripTrailingSlashMiddleware)

    @api.get("/api/v1/drafts")
    async def drafts_list():
        return {"path": "/api/v1/drafts"}

    @api.get("/api/v1/drafts/123")
    async def draft_detail():
        return {"path": "/api/v1/drafts/123"}

    @api.get("/")
    async def root():
        return {"path": "/"}

    return TestClient(api)


class TestStripTrailingSlash:
    """StripTrailingSlashMiddleware — нормализация trailing slash."""

    def test_trailing_slash_normalized(self, strip_slash_test_app):
        """/api/v1/drafts/ → нормализован до /api/v1/drafts."""
        resp = strip_slash_test_app.get("/api/v1/drafts/", follow_redirects=False)
        assert resp.status_code == 200, (
            f"Trailing slash должен нормализоваться, "
            f"получен {resp.status_code}: {resp.text[:100]}"
        )
        data = resp.json()
        assert data.get("path") == "/api/v1/drafts"

    def test_no_trailing_slash_unchanged(self, strip_slash_test_app):
        """/api/v1/drafts → без изменений (200)."""
        resp = strip_slash_test_app.get("/api/v1/drafts", follow_redirects=False)
        assert resp.status_code == 200
        assert resp.json().get("path") == "/api/v1/drafts"

    def test_root_unchanged(self, strip_slash_test_app):
        """/ → без изменений."""
        resp = strip_slash_test_app.get("/", follow_redirects=False)
        assert resp.status_code == 200
        assert resp.json().get("path") == "/"

    def test_deep_trailing_slash_normalized(self, strip_slash_test_app):
        """/api/v1/drafts/123/ → /api/v1/drafts/123."""
        resp = strip_slash_test_app.get("/api/v1/drafts/123/", follow_redirects=False)
        assert resp.status_code == 200
        assert resp.json().get("path") == "/api/v1/drafts/123"


# ---------------------------------------------------------------------------
# Интеграционные тесты (Docker)
# ---------------------------------------------------------------------------


@pytest.mark.docker
class TestStripSlashIntegration:
    """StripTrailingSlash — интеграционные тесты через Docker."""

    @pytest.mark.asyncio
    async def test_no_307_redirect(self, http_client, docker_gateway_base):
        """Запросы с trailing slash не должны возвращать 307."""
        for path in ["/api/v1/drafts/", "/api/v1/drafts/123/",
                      "/api/v1/documents/", "/api/v1/documents/1/",
                      "/api/v1/registry/classifiers/"]:
            resp = await http_client.get(
                f"{docker_gateway_base}{path}",
                follow_redirects=False,
            )
            assert resp.status_code != 307, (
                f"Path {path} вернул 307! Location: {resp.headers.get('location', 'N/A')}"
            )

    @pytest.mark.asyncio
    async def test_health_with_slash(self, http_client, docker_gateway_base):
        """/api/v1/health/ → 200 (middleware обрезал slash)."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/health/",
            follow_redirects=False,
        )
        assert resp.status_code == 200
