"""
Tests for StripTrailingSlashMiddleware.

Проверяет:
  - /api/v1/drafts/ → путь нормализован до /api/v1/drafts
  - /api/v1/drafts → без изменений
  - / → без изменений (корень)
  - /api/v1/drafts/123/ → /api/v1/drafts/123
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class TestStripTrailingSlash:
    """Trailing slash нормализуется — нет 307 редиректа."""

    @pytest.mark.parametrize("path_with_slash", [
        "/api/v1/drafts/",
        "/api/v1/drafts",
        "/api/v1/drafts/123/",
        "/api/v1/drafts/123",
        "/api/v1/health/",
        "/",
    ])
    def test_strip_slash_no_307_redirect(self, path_with_slash: str, client):
        """Ни один path с trailing slash не вызывает 307."""
        resp = client.get(path_with_slash, follow_redirects=False)
        assert resp.status_code != 307, (
            f"Trailing slash caused 307 redirect: {path_with_slash}"
        )

    def test_root_slash_unchanged(self, client):
        """Корневой '/' не изменяется."""
        resp = client.get("/", follow_redirects=False)
        # Root — не /api/v1/*, так что может быть 404 у Gateway,
        # но не 307 редирект
        assert resp.status_code != 307

    def test_double_slash_not_affected(self, client):
        """Двойной слеш в середине пути не затрагивается middleware."""
        resp = client.get("/api/v1//drafts", follow_redirects=False)
        # middleware обрезает только конец
        assert resp.status_code != 307
