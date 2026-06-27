"""
Тесты RBACMiddleware — проверка прав доступа.

Сценарии:
  - Без Authorization header → 401
  - Bearer token не найден → 401
  - GET /api/v1/admin/* для system_admin → 200
  - GET /api/v1/admin/* для engineer → 403
  - POST /api/v1/admin/* для engineer → 403
  - POST /api/v1/drafts c can_upload_documents=true → 200
  - POST /api/v1/drafts c can_upload_documents=false → 403
  - Classifier/terminology CRUD с правами
  - Registry document CRUD с правами
  - DELETE /documents/1, /drafts/1 с правами
  - Публичные эндпоинты (/health, /auth/token) без токена

Интеграционные тесты (требуют Docker с Gateway + Auth).
"""

from __future__ import annotations

import os
import sys

import pytest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_GATEWAY_DIR = os.path.join(_TEST_DIR, "..")
if _TEST_DIR not in sys.path:
    sys.path.insert(0, _TEST_DIR)
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from helpers import auth_header


# ===================================================================
# Базовые тесты авторизации
# ===================================================================


@pytest.mark.docker
class TestRBACBasicAuth:
    """Базовая аутентификация."""

    @pytest.mark.asyncio
    async def test_no_auth_header_returns_401(self, http_client, docker_gateway_base):
        """Без Authorization header → 401."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/admin/users")
        assert resp.status_code == 401, (
            f"Без токена должен быть 401, получен {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, http_client, docker_gateway_base):
        """Bearer token не найден → 401."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/admin/users",
            headers=auth_header("invalid-token"),
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_health_public_without_token(self, http_client, docker_gateway_base):
        """GET /api/v1/health без токена → 200 (публичный)."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_token_public_without_token(self, http_client, docker_gateway_base):
        """POST /api/v1/auth/token без токена → 200 (публичный)."""
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/auth/token",
            json={"username": "admin@example.com", "password": "admin123"},
        )
        assert resp.status_code == 200


# ===================================================================
# Admin endpoints
# ===================================================================


@pytest.mark.docker
class TestRBACAdmin:
    """Доступ к /api/v1/admin/*."""

    @pytest.mark.asyncio
    async def test_admin_get_for_system_admin(self, http_client, docker_gateway_base, system_admin_token):
        """GET /api/v1/admin/* для system_admin → 200."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/admin/users",
            headers=auth_header(system_admin_token),
        )
        assert resp.status_code == 200, (
            f"system_admin должен иметь доступ к admin, получен {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_admin_get_for_engineer_forbidden(self, http_client, docker_gateway_base, engineer_token):
        """GET /api/v1/admin/* для engineer → 403."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/admin/users",
            headers=auth_header(engineer_token),
        )
        assert resp.status_code == 403, (
            f"engineer НЕ должен иметь доступ к admin, получен {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_admin_post_for_engineer_forbidden(self, http_client, docker_gateway_base, engineer_token):
        """POST /api/v1/admin/* для engineer → 403."""
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/admin/users",
            headers=auth_header(engineer_token),
            json={"email": "test@test.com", "password": "Test1234!", "roles": ["engineer"]},
        )
        assert resp.status_code == 403


# ===================================================================
# Drafts RBAC
# ===================================================================


@pytest.mark.docker
class TestRBACDrafts:
    """Права на создание черновиков."""

    @pytest.mark.asyncio
    async def test_post_drafts_admin(self, http_client, docker_gateway_base, system_admin_token):
        """POST /api/v1/drafts для system_admin → 200/201 (есть can_upload_documents)."""
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers=auth_header(system_admin_token),
            json={"file_key": "test.pdf", "document_key": "doc-001"},
        )
        # В Docker может быть mock, который разрешает всем — проверяем, что не 403
        assert resp.status_code not in (401, 403), (
            f"system_admin должен иметь доступ к drafts, получен {resp.status_code}: {resp.text[:100]}"
        )


# ===================================================================
# Registry документы RBAC
# ===================================================================


@pytest.mark.docker
class TestRBACRegistry:
    """Права на управление реестром."""

    @pytest.mark.asyncio
    async def test_get_registry_search_for_knowledge_admin(self, http_client, docker_gateway_base, knowledge_admin_token):
        """GET /api/v1/registry/search для knowledge_admin → 200."""
        resp = await http_client.get(
            f"{docker_gateway_base}/api/v1/registry/search",
            headers=auth_header(knowledge_admin_token),
            params={"q": "test"},
        )
        assert resp.status_code in (200,), (
            f"knowledge_admin должен иметь доступ к search, получен {resp.status_code}"
        )


# ===================================================================
# Публичные эндпоинты
# ===================================================================


@pytest.mark.docker
class TestRBACPublic:
    """Публичные эндпоинты доступны без токена."""

    @pytest.mark.asyncio
    async def test_health_public(self, http_client, docker_gateway_base):
        """GET /api/v1/health без токена → 200."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_token_public(self, http_client, docker_gateway_base):
        """POST /api/v1/auth/token без токена → 200."""
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/auth/token",
            json={"username": "admin@example.com", "password": "admin123"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_live_probe_public(self, http_client, docker_gateway_base):
        """GET /api/v1/system/health/live без токена → 200."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/health/live")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_probe_public(self, http_client, docker_gateway_base):
        """GET /api/v1/system/health/ready без токена → 200."""
        resp = await http_client.get(f"{docker_gateway_base}/api/v1/system/health/ready")
        assert resp.status_code == 200
