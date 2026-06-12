"""
Integration tests for the Gateway mock — simulates external HTTP calls.

Проверяет, что Gateway отвечает так, как ожидает checker:
  - /api/v1/registry/classifiers  → 200 (не 307, не 404)
  - /api/v1/registry/terminology  → 200
  - /api/v1/registry/documents   → 200
  - /api/v1/registry/common/*    → 200
  - /api/v1/classifiers          → 404 (старый путь не живёт)
  - /api/v1/terminology          → 404
  - Нет 307 redirect ни на одном из этих путей
  - redirect_slashes=False работает
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest
from fastapi.testclient import TestClient

import mocks.gateway

# Anonymous mode for tests
mocks.gateway.ALLOW_ANONYMOUS = True
from mocks.gateway import app

client = TestClient(app, raise_server_exceptions=False)

BASE = "/api/v1"
REG = f"{BASE}/registry"


# ===========================================================================
# New registry paths — checker шлёт эти пути по документации API
# ===========================================================================

class TestNewRegistryPaths:
    """Checker ожидает 200 на всех /api/v1/registry/* путях."""

    # ---------- classifiers ----------

    def test_classifiers_list(self):
        """GET /api/v1/registry/classifiers → 200."""
        resp = client.get(f"{REG}/classifiers", follow_redirects=False)
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code} ({resp.status_code}): {resp.text[:200]}"
        )
        assert resp.json()["data"] is not None

    def test_classifiers_list_no_trailing_slash(self):
        """GET /api/v1/registry/classifiers (без /) → 200, не 307."""
        resp = client.get(f"{REG}/classifiers", follow_redirects=False)
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code} — trailing slash causes 307 redirect!"
        )

    def test_classifiers_tree(self):
        resp = client.get(f"{REG}/classifiers/tree", follow_redirects=False)
        assert resp.status_code == 200

    def test_classifiers_create(self):
        resp = client.post(
            f"{REG}/classifiers",
            json={"classifier_system": "MKS", "code": "INTEG.TEST", "full_name": "Integration Test"},
            follow_redirects=False,
        )
        # 201 is also acceptable (created)
        assert resp.status_code in (200, 201), f"Got {resp.status_code}: {resp.text[:200]}"

    def test_classifiers_validate(self):
        resp = client.post(
            f"{REG}/classifiers/validate",
            json={"code": "47"},
            follow_redirects=False,
        )
        assert resp.status_code == 200

    def test_classifiers_quarantine(self):
        resp = client.get(f"{REG}/classifiers/quarantine", follow_redirects=False)
        assert resp.status_code == 200

    # ---------- terminology ----------

    def test_terminology_list(self):
        resp = client.get(f"{REG}/terminology", follow_redirects=False)
        assert resp.status_code == 200

    def test_terminology_normalize(self):
        resp = client.get(
            f"{REG}/terminology/normalize",
            params={"term": "ГОСТ"},
            follow_redirects=False,
        )
        assert resp.status_code == 200

    # ---------- documents ----------

    def test_registry_documents(self):
        resp = client.get(f"{REG}/documents", follow_redirects=False)
        assert resp.status_code == 200

    # ---------- common ----------

    def test_common_stats(self):
        resp = client.get(f"{REG}/common/stats", follow_redirects=False)
        assert resp.status_code == 200

    def test_common_enums(self):
        resp = client.get(f"{REG}/common/enums", follow_redirects=False)
        assert resp.status_code == 200

    # ---------- drafts (internal) ----------

    def test_registry_drafts_list(self):
        resp = client.get(f"{REG}/drafts", follow_redirects=False)
        assert resp.status_code == 200


# ===========================================================================
# Old paths (без /registry/) — checker их не шлёт, они должны отдавать 404
# ===========================================================================

class TestOldPathsReturn404:
    """Старые пути без /registry/ должны возвращать 404."""

    def test_old_classifiers(self):
        resp = client.get(f"{BASE}/classifiers", follow_redirects=False)
        assert resp.status_code == 404, (
            f"Expected 404 for old path, got {resp.status_code}"
        )

    def test_old_terminology(self):
        resp = client.get(f"{BASE}/terminology", follow_redirects=False)
        assert resp.status_code == 404

    def test_old_common_stats(self):
        resp = client.get(f"{BASE}/common/stats", follow_redirects=False)
        assert resp.status_code == 404


# ===========================================================================
# Trailing slash — проверяем, что нет 307 redirect
# ===========================================================================

class TestNoTrailingSlashRedirect:
    """redirect_slashes=False — ни один запрос не должен вернуть 307."""

    def test_redirect_slashes_is_false(self):
        assert app.router.redirect_slashes is False

    REGISTRY_PATHS = [
        "/api/v1/registry/classifiers",
        "/api/v1/registry/terminology",
        "/api/v1/registry/documents",
        "/api/v1/registry/common/stats",
        "/api/v1/registry/common/enums",
        "/api/v1/registry/drafts",
        "/api/v1/documents",
        "/api/v1/drafts",
    ]

    @pytest.mark.parametrize("path", REGISTRY_PATHS)
    def test_no_307_on_any_path(self, path: str):
        """Ни один из этих путей не должен возвращать 307."""
        resp = client.get(path, follow_redirects=False)
        assert resp.status_code != 307, (
            f"Path {path} returned 307 redirect! "
            f"Location: {resp.headers.get('location', 'N/A')}"
        )


# ===========================================================================
# Response format — checker ожидает {data, meta} формат
# ===========================================================================

class TestResponseFormat:
    """Ответы должны содержать data и meta (если применимо)."""

    def test_registry_classifiers_format(self):
        resp = client.get(f"{REG}/classifiers", follow_redirects=False)
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body, "Response missing 'data' field"
        assert "meta" in body, "Paginated response missing 'meta' field"

    def test_registry_documents_format(self):
        resp = client.get(f"{REG}/documents", follow_redirects=False)
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body

    def test_error_format_404(self):
        """404 ответ — старый путь без /registry/ должен вернуть 404.
        В моке (без catch-all роутера) формат может быть {"detail": ...},
        в реальном Gateway — единый формат {"error": {"code": ..., "message": ...}}.
        """
        resp = client.get(f"{BASE}/classifiers", follow_redirects=False)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


# ===========================================================================
# External call simulation — как будто checker стучится к серверу
# ===========================================================================

class TestExternalCallSimulation:
    """Симуляция внешних вызовов: checker отправляет запросы по документации API
    и ожидает 200, а не 307/404."""

    CHECKER_PATHS = [
        # (method, path, expected_status, json_body)
        ("GET",    "/api/v1/registry/classifiers",                  200, None),
        ("GET",    "/api/v1/registry/classifiers/tree",             200, None),
        ("POST",   "/api/v1/registry/classifiers",                  201,
         {"classifier_system": "MKS", "code": "EXT.CHECK", "full_name": "Checker Test"}),
        ("GET",    "/api/v1/registry/terminology",                  200, None),
        ("GET",    "/api/v1/registry/documents",                    200, None),
        ("GET",    "/api/v1/registry/common/stats",                 200, None),
        ("GET",    "/api/v1/registry/common/enums",                 200, None),
        ("POST",   "/api/v1/registry/classifiers/validate",         200,
         {"code": "47"}),
        ("GET",    "/api/v1/registry/classifiers/quarantine",       200, None),
        ("POST",   "/api/v1/registry/drafts",                       201,
         {"file_key": "ext-test.pdf", "document_key": "ext-doc-001"}),
    ]

    @pytest.mark.parametrize("method,path,expected_status,body", CHECKER_PATHS)
    def test_checker_paths(self, method: str, path: str, expected_status: int, body: dict):
        """Проверяем, что checker получает ожидаемый статус, а не 307 или 404."""
        resp = client.request(
            method=method,
            url=path,
            json=body,
            follow_redirects=False,
        )
        assert resp.status_code == expected_status, (
            f"[{method} {path}] Expected {expected_status}, "
            f"got {resp.status_code}: {resp.text[:200]}"
        )

    def test_checker_gets_no_redirect_on_any_path(self):
        """Ни один из checker-путей не должен вернуть 307."""
        for method, path, _, body in self.CHECKER_PATHS:
            resp = client.request(
                method=method,
                url=path,
                json=body,
                follow_redirects=False,
            )
            assert resp.status_code != 307, (
                f"[{method} {path}] Got 307 redirect! "
                f"Location: {resp.headers.get('location', 'N/A')}"
            )
