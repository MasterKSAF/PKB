"""
Unit tests for RegistryServiceClient.

Tests mock generation for draft endpoints.
"""

import pytest

from app.services.registry_client import RegistryServiceClient


@pytest.fixture
def reg_client():
    client = RegistryServiceClient()
    client.mock_mode = True
    return client


# ===========================================================================
# Drafts
# ===========================================================================


class TestRegistryDrafts:
    """Tests for draft management methods."""

    @pytest.mark.asyncio
    async def test_create_draft(self, reg_client):
        """create_draft returns draft_id."""
        result = await reg_client.create_draft(
            file_key="f-abc123",
            document_key="doc-001",
            created_by="user-1",
            file_hash_sha256="abc123",
            title_hash_sha256="def456",
        )
        assert "data" in result
        data = result["data"]
        assert "id" in data
        assert data["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_get_draft(self, reg_client):
        """get_draft returns full draft info."""
        result = await reg_client.get_draft(draft_id=1)
        assert "data" in result
        data = result["data"]
        assert data["draft_id"] == 1
        assert "status" in data
        assert "file_key" in data

    @pytest.mark.asyncio
    async def test_get_draft_preview(self, reg_client):
        """get_draft_preview returns preview metadata."""
        result = await reg_client.get_draft_preview(draft_id=1)
        assert "data" in result
        data = result["data"]
        assert "draft_id" in data
        assert "preview_not_supported" in data

    @pytest.mark.asyncio
    async def test_update_draft_status(self, reg_client):
        """update_draft_status returns updated info."""
        result = await reg_client.update_draft_status(
            draft_id=1, status="previewing"
        )
        assert "data" in result
        data = result["data"]
        assert data["status"] == "previewing"

    @pytest.mark.asyncio
    async def test_update_draft_status_with_document_id(self, reg_client):
        """update_draft_status with optional document_id."""
        result = await reg_client.update_draft_status(
            draft_id=1, status="approved", document_id=100
        )
        assert "data" in result
        data = result["data"]
        assert data["document_id"] == 100

    @pytest.mark.asyncio
    async def test_delete_draft(self, reg_client):
        """delete_draft returns deletion confirmation."""
        result = await reg_client.delete_draft(draft_id=1)
        assert "data" in result
        data = result["data"]
        assert data["deleted"] is True

    @pytest.mark.asyncio
    async def test_check_uniqueness(self, reg_client):
        """check_uniqueness returns duplicate detection info."""
        result = await reg_client.check_uniqueness(
            title="Тестовый документ",
            doc_code="TEST-001",
            source_type="GOST",
        )
        assert "data" in result
        data = result["data"]
        assert "is_duplicate" in data
        assert "is_duplicate_file" in data

    @pytest.mark.asyncio
    async def test_check_uniqueness_duplicate(self, reg_client):
        """check_uniqueness returns is_duplicate flags."""
        result = await reg_client.check_uniqueness(
            title="known-duplicate-title",
        )
        assert "data" in result
        data = result["data"]
        assert isinstance(data.get("is_duplicate"), bool)

    # ------------------------------------------------------------------
    # Document status (RG-1)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_update_document_status(self, reg_client):
        """update_document_status returns updated status."""
        result = await reg_client.update_document_status(
            document_id=1, status="indexed"
        )
        assert "data" in result
        data = result["data"]
        assert data["document_id"] == 1
        assert data["status"] == "indexed"
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_update_document_status_with_updated_by(self, reg_client):
        """update_document_status with optional updated_by."""
        result = await reg_client.update_document_status(
            document_id=1, status="failed", updated_by="system"
        )
        assert "data" in result
        data = result["data"]
        assert data["status"] == "failed"

    @pytest.mark.asyncio
    async def test_update_document_status_not_found(self, reg_client):
        """update_document_status on non-existent doc returns error."""
        result = await reg_client.update_document_status(
            document_id=9999, status="indexed"
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_update_document_status_roundtrip(self, reg_client):
        """update_document_status persists in mock storage through multiple calls."""
        result1 = await reg_client.update_document_status(
            document_id=1, status="indexing"
        )
        assert result1["data"]["status"] == "indexing"

        result2 = await reg_client.update_document_status(
            document_id=1, status="indexed"
        )
        assert result2["data"]["status"] == "indexed"


# ===========================================================================
# Mock-real gap: id=0 falsy and key divergence
# ===========================================================================


class TestRegistryMockRealGap:
    """Тесты на расхождение mock-логики с реальностью."""

    @pytest.mark.asyncio
    async def test_get_draft_id_zero_not_falsy(self, reg_client):
        """После фикса: data["id"]=0 **не** falsy.

        Эндпоинт теперь использует:
        data.get("id") if data.get("id") is not None else data.get("draft_id")
        0 is not None → возвращается 0 (не draft_id).
        """
        storage = reg_client._storage
        draft = {
            "id": 0,
            "draft_id": 42,
            "file_key": "test",
            "status": "uploaded",
            "created_by": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        storage["drafts"][42] = draft

        result = await reg_client.get_draft(draft_id=42)
        assert "data" in result
        data = result["data"]

        # После фикса: id=0 возвращается корректно
        resolved_id = data.get("id") if data.get("id") is not None else data.get("draft_id")
        assert resolved_id == 0, (
            f"Expected resolved_id=0 (id is not None), "
            f"got {resolved_id}"
        )

    @pytest.mark.asyncio
    async def test_get_draft_id_zero_no_draft_id_after_fix(self, reg_client):
        """После фикса: data["id"]=0, нет "draft_id" → resolve = 0.

        Новый код: data.get("id") if data.get("id") is not None else data.get("draft_id")
        0 is not None → 0 (раньше был None из-за falsy).
        """
        storage = reg_client._storage
        draft = {
            "id": 0,
            # НЕТ "draft_id"
            "file_key": "test",
            "status": "uploaded",
            "created_by": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        storage["drafts"][99] = draft

        result = await reg_client.get_draft(draft_id=99)
        assert "data" in result
        data = result["data"]

        # После фикса: id=0 возвращается корректно (не None)
        resolved_id = data.get("id") if data.get("id") is not None else data.get("draft_id")
        assert resolved_id == 0, (
            f"After fix: expected resolved_id=0 (id is 0, not None), "
            f"got {resolved_id}"
        )

    @pytest.mark.asyncio
    async def test_get_draft_returns_id_key_not_draft_id(self, reg_client):
        """_mock_get_draft возвращает 'id', а статический mock_response — 'draft_id'.

        Эндпоинт использует: data.get("id") if id is not None else data.get("draft_id").
        Оба ключа есть → возвращается id (не draft_id).
        """
        storage = reg_client._storage
        draft = {
            "id": 100,
            "draft_id": 999,
            "file_key": "test",
            "status": "uploaded",
            "created_by": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        storage["drafts"][100] = draft

        result = await reg_client.get_draft(draft_id=100)
        data = result["data"]

        assert "id" in data, "_mock_get_draft should return 'id' key"

        # После фикса: id is not None → возвращается id (100), не draft_id fallback
        draft_id = data.get("id") if data.get("id") is not None else data.get("draft_id")
        assert draft_id == 100, f"Failed to resolve draft_id from data: {data}"
