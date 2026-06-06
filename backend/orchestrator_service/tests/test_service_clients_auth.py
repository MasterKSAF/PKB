"""
Unit tests for AuthServiceClient.

Tests mock generation for all auth service endpoints:
  - Token validation, refresh, revoke
  - User profile (/auth/me)
  - Admin endpoints: users CRUD, roles, audit log
"""

import pytest

from app.services.auth_client import AuthServiceClient


@pytest.fixture
def auth_client():
    """Create AuthServiceClient in mock mode."""
    client = AuthServiceClient()
    # Force mock mode
    client.mock_mode = True
    return client


class TestAuthToken:
    """Tests for token-related endpoints."""

    @pytest.mark.asyncio
    async def test_validate_token(self, auth_client):
        result = await auth_client.validate_token("some-token")
        assert result["valid"] is True
        assert result["user_id"] == "u-mock-001"
        assert "email" in result
        assert "roles" in result
        assert "permissions" in result

    @pytest.mark.asyncio
    async def test_get_me(self, auth_client):
        result = await auth_client.get_me()
        assert result["user_id"] == "u-001"
        assert result["full_name"] == "Иванов Сергей Петрович"
        assert result["role"] == "engineer"
        assert "permissions" in result
        assert "available_tabs" in result
        assert result["available_tabs"] == ["chat", "search", "checks", "history"]

    @pytest.mark.asyncio
    async def test_get_me_permissions_structure(self, auth_client):
        result = await auth_client.get_me()
        perms = result["permissions"]
        assert "can_upload_documents" in perms
        assert "can_run_ocr" in perms
        assert "can_manage_users" in perms
        assert "can_manage_classifiers" in perms
        assert "can_manage_terminology" in perms
        assert "can_manage_registry" in perms


class TestAuthAdminUsers:
    """Tests for admin user management endpoints."""

    @pytest.mark.asyncio
    async def test_list_users_default(self, auth_client):
        result = await auth_client.list_users()
        assert "users" in result
        assert "meta" in result
        assert result["meta"]["total"] >= 0

    @pytest.mark.asyncio
    async def test_list_users_with_role_filter(self, auth_client):
        result = await auth_client.list_users(role="engineer")
        assert "users" in result

    @pytest.mark.asyncio
    async def test_list_users_with_search(self, auth_client):
        result = await auth_client.list_users(search="Иванов")
        assert "users" in result

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, auth_client):
        result = await auth_client.list_users(page=2, page_size=10)
        # Mock data doesn't preserve pagination params, but returns useful defaults
        assert "users" in result
        assert "meta" in result
        assert "page" in result["meta"]
        assert "page_size" in result["meta"]

    @pytest.mark.asyncio
    async def test_create_user(self, auth_client):
        result = await auth_client.create_user(
            email="new@example.com",
            full_name="Новый Пользователь",
            password="secret123",
            roles=["engineer"],
        )
        assert result["user_id"] == "u-mock-new"
        assert result["email"] == "new@example.com"
        assert result["full_name"] == "Новый Пользователь"
        assert result["roles"] == ["engineer"]

    @pytest.mark.asyncio
    async def test_get_user(self, auth_client):
        result = await auth_client.get_user("u-mock-001")
        assert result["user_id"] == "u-mock-001"
        assert "email" in result
        assert "full_name" in result
        assert "role" in result
        assert "permissions" in result

    @pytest.mark.asyncio
    async def test_get_user_all_fields(self, auth_client):
        result = await auth_client.get_user("u-test-001")
        expected_fields = [
            "user_id", "email", "full_name", "role", "role_title",
            "position", "available_tabs", "permissions",
            "is_active", "last_login_at", "created_at", "updated_at",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_update_user(self, auth_client):
        result = await auth_client.update_user("u-mock-001", {"full_name": "Обновлённый"})
        # Mock returns data with default-style name
        assert "full_name" in result
        assert result["user_id"] == "u-mock-001"

    @pytest.mark.asyncio
    async def test_patch_user(self, auth_client):
        result = await auth_client.patch_user("u-mock-001", {"full_name": "Частично обновлён"})
        assert result["full_name"] == "Частично обновлён"

    @pytest.mark.asyncio
    async def test_patch_user_merges(self, auth_client):
        """PATCH should merge provided fields."""
        result = await auth_client.patch_user("u-test-001", {"position": "Гл. инженер"})
        assert result["position"] == "Гл. инженер"
        assert result["full_name"] == "Пользователь"  # default from mock

    @pytest.mark.asyncio
    async def test_deactivate_user(self, auth_client):
        result = await auth_client.deactivate_user("u-mock-001")
        assert result["is_active"] is False
        assert "deactivated_at" in result
        assert result["user_id"] == "u-mock-001"


class TestAuthAdminRoles:
    """Tests for role management endpoints."""

    @pytest.mark.asyncio
    async def test_list_roles(self, auth_client):
        result = await auth_client.list_roles()
        assert "roles" in result
        assert len(result["roles"]) > 0

    @pytest.mark.asyncio
    async def test_list_roles_structure(self, auth_client):
        result = await auth_client.list_roles()
        role = result["roles"][0]
        for field in ("role_id", "name", "permissions", "created_at"):
            assert field in role, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_create_role(self, auth_client):
        result = await auth_client.create_role(
            name="Тестовая роль",
            permissions=["documents:read", "search"],
        )
        assert result["role_id"] == "r-mock-new"
        assert result["name"] == "Тестовая роль"
        assert "permissions" in result
        assert "created_at" in result


class TestAuthAudit:
    """Tests for audit log endpoints."""

    @pytest.mark.asyncio
    async def test_get_audit_log_default(self, auth_client):
        result = await auth_client.get_audit_log()
        assert "events" in result
        assert "meta" in result

    @pytest.mark.asyncio
    async def test_get_audit_log_with_filters(self, auth_client):
        result = await auth_client.get_audit_log(
            user_id="u-mock-001",
            action="document.upload",
            date_from="2026-01-01",
            date_to="2026-12-31",
        )
        assert "events" in result

    @pytest.mark.asyncio
    async def test_get_audit_log_with_pagination(self, auth_client):
        result = await auth_client.get_audit_log(page=1, page_size=20)
        assert "events" in result
        assert "meta" in result
        assert "page" in result["meta"]
        assert "page_size" in result["meta"]

    @pytest.mark.asyncio
    async def test_audit_event_structure(self, auth_client):
        result = await auth_client.get_audit_log()
        if result["events"]:
            event = result["events"][0]
            for field in ("event_id", "user_id", "action", "resource_type", "resource_id", "timestamp"):
                assert field in event, f"Missing field: {field}"
