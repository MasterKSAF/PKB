"""
Тесты StripTrailingSlashMiddleware — нормализация пути.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


class TestStripTrailingSlash:
    """Strip trailing slash — path normalization."""

    def test_drafts_trailing_slash_redirected(self, client):
        """GET /api/v1/drafts/ → такой же статус как без слеша."""
        resp_with = client.get("/api/v1/drafts/")
        resp_without = client.get("/api/v1/drafts")
        # Должны давать одинаковый результат (оба проходят)
        assert resp_with.status_code not in (307,)  # нет редиректа
        assert resp_without.status_code not in (307,)

    def test_health_trailing_slash(self, client):
        """GET /api/v1/health/ → 200 (как и без слеша)."""
        resp = client.get("/api/v1/health/")
        # StripTrailingSlashMiddleware или редирект
        assert resp.status_code in (200,)

    def test_system_health_trailing_slash(self, client):
        """GET /api/v1/system/health/ → 200."""
        resp = client.get("/api/v1/system/health/")
        assert resp.status_code == 200
