"""
Проверка исправления путей Registry и redirect_slashes в Gateway mock.

Чекает:
  - /api/v1/registry/classifiers/* — 200 (новый путь по документации)
  - /api/v1/registry/terminology/* — 200
  - /api/v1/registry/common/* — 200
  - /api/v1/registry/documents/* — 200
  - /api/v1/classifiers — 404 (старый путь больше не живёт в gateway mock)
  - /api/v1/terminology — 404
  - отсутствие 307 redirect (redirect_slashes=False)
  - /api/v1/documents, /api/v1/drafts — без редиректа
"""

import pytest
from fastapi.testclient import TestClient
from mocks.gateway import app
from mocks.auth_service.main import app as auth_app
from mocks.common import SEED_USERS

client = TestClient(app)

# ── helpers ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token():
    r = client.post("/api/v1/auth/token", json={"username": "admin@example.com", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["access_token"]

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}

# ───────────────────────────────────────────────────────────────────────────

class TestRegistryPrefixPaths:
    """Новые пути с /api/v1/registry/ должны работать."""

    BASE = "/api/v1/registry"

    def test_registry_classifiers_list(self, admin_token):
        resp = client.get(f"{self.BASE}/classifiers", headers=auth_header(admin_token))
        assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "data" in data
        assert "meta" in data

    def test_registry_classifiers_tree(self, admin_token):
        resp = client.get(f"{self.BASE}/classifiers/tree", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_registry_classifiers_create(self, admin_token):
        resp = client.post(
            f"{self.BASE}/classifiers",
            json={"classifier_system": "MKS", "code": "ZZ.TEST", "full_name": "Test", "status": "active"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201

    def test_registry_terminology_list(self, admin_token):
        resp = client.get(f"{self.BASE}/terminology", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_registry_terminology_normalize(self, admin_token):
        resp = client.get(f"{self.BASE}/terminology/normalize", params={"term": "Толщина"}, headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_registry_common_stats(self, admin_token):
        resp = client.get(f"{self.BASE}/common/stats", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_registry_common_enums(self, admin_token):
        resp = client.get(f"{self.BASE}/common/enums", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_registry_documents(self, admin_token):
        resp = client.get(f"{self.BASE}/documents", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_classifiers_validate(self, admin_token):
        resp = client.post(
            f"{self.BASE}/classifiers/validate",
            json={"code": "47"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    def test_classifiers_quarantine(self, admin_token):
        resp = client.get(f"{self.BASE}/classifiers/quarantine", headers=auth_header(admin_token))
        assert resp.status_code == 200


class TestOldPathsReturn404:
    """Старые пути без /registry/ больше не живут в gateway — 404."""

    def test_old_classifiers(self, admin_token):
        resp = client.get("/api/v1/classifiers", headers=auth_header(admin_token))
        assert resp.status_code == 404, f"expected 404, got {resp.status_code}"

    def test_old_terminology(self, admin_token):
        resp = client.get("/api/v1/terminology", headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_old_common_stats(self, admin_token):
        resp = client.get("/api/v1/common/stats", headers=auth_header(admin_token))
        assert resp.status_code == 404


class TestTrailingSlashNormalization:
    """StripTrailingSlashMiddleware обрезает / ДО роутинга.
    Запросы с / и без / работают одинаково, без единого 307.
    """

    def test_router_has_redirect_slashes_false(self):
        """redirect_slashes=False — нормализацию делает middleware."""
        assert app.router.redirect_slashes is False

    def test_registry_classifiers_with_slash_returns_200(self):
        """С trailing slash — middleware обрезает, роут срабатывает."""
        resp = client.get("/api/v1/registry/classifiers/", follow_redirects=False)
        assert resp.status_code == 200, f"expected 200, got {resp.status_code}"

    def test_registry_classifiers_without_slash_returns_200(self):
        """Без trailing slash — прямой матчинг."""
        resp = client.get("/api/v1/registry/classifiers", follow_redirects=False)
        assert resp.status_code == 200

    def test_documents_no_redirect(self):
        resp = client.get("/api/v1/documents", follow_redirects=False)
        assert resp.status_code != 307, f"expected non-307, got {resp.status_code}"

    def test_drafts_no_redirect(self):
        resp = client.get("/api/v1/drafts", follow_redirects=False)
        assert resp.status_code != 307, f"expected non-307, got {resp.status_code}"

    def test_registry_documents_no_redirect(self, admin_token):
        resp = client.get("/api/v1/registry/documents", headers=auth_header(admin_token), follow_redirects=False)
        assert resp.status_code != 307, f"expected 200, got 307 redirect"
        assert resp.status_code == 200

    def test_registry_classifiers_no_redirect(self, admin_token):
        resp = client.get("/api/v1/registry/classifiers", headers=auth_header(admin_token), follow_redirects=False)
        assert resp.status_code != 307
        assert resp.status_code == 200
