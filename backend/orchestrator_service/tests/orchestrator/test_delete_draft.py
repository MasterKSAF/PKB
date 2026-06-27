"""
Тесты DELETE /drafts/{draft_id}.

Покрывает сценарии §8 Удаление черновика (pipeline1-orchestrator_details.md):
  - Статус uploaded → 204
  - Статус previewing → 204
  - Статус ready_for_approve → 204
  - Статус approved → 204 (документ сохраняется)
  - Несуществующий черновик → 404

Внимание:
  - DELETE /drafts — прокси в Registry (RegistryServiceClient.delete_draft)
  - DELETE возвращает 204 No Content (или 200 с телом)
  - MinIO объект не удаляется (TTL 30 дней)
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDeleteDraft:
    """DELETE /api/v1/drafts/{draft_id} — основные сценарии."""

    DELETE_URL = "/api/v1/drafts/{draft_id}"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def created_draft(
        self, client: TestClient, auth_header: dict
    ) -> int:
        """Create a draft via API."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF delete test " * 50), "application/pdf")},
            data={"document_key": "doc-delete-test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    async def test_delete_draft_returns_204(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
    ):
        """Удаление существующего черновика → 204 No Content (или 200 с телом)."""
        response = client.delete(
            self.DELETE_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        # DELETE может вернуть 204 (без тела) или 200 (с телом)
        assert response.status_code in (200, 204)
        if response.status_code == 200:
            data = response.json()
            assert data["draft_id"] == created_draft
            assert "deleted_at" in data

    async def test_delete_draft_twice_returns_204_or_404(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
    ):
        """Повторное удаление — черновик уже удалён."""
        # Первое удаление
        resp1 = client.delete(
            self.DELETE_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        assert resp1.status_code in (200, 204)

        # Второе удаление
        resp2 = client.delete(
            self.DELETE_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        # Registry может вернуть 404 (уже удалён) или 204 (идимпотентность)
        assert resp2.status_code in (200, 204, 404)

    async def test_delete_nonexistent_draft_returns_404(
        self,
        client: TestClient,
        auth_header: dict,
    ):
        """Несуществующий черновик → 404."""
        response = client.delete(
            self.DELETE_URL.format(draft_id=99999),
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_delete_after_draft_creation_succeeds(
        self,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
    ):
        """Удаление черновика после создания — успешный ответ."""
        response = client.delete(
            self.DELETE_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        assert response.status_code in (200, 204)

        # RegistryServiceClient.delete_draft помечает черновик как удалённый
        # (но не обязательно меняет pipeline.tasks.deleted_at)


class TestDeleteDraftInVariousStatuses:
    """DELETE /drafts при разных статусах черновика."""

    DELETE_URL = "/api/v1/drafts/{draft_id}"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.mark.parametrize("status", [
        "uploaded", "previewing", "ready_for_approve", "discarded", "approved",
    ])
    async def test_delete_draft_in_any_status_returns_204(
        self,
        status: str,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Черновик в любом статусе → 204 при удалении."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-del"), "application/pdf")},
            data={"document_key": f"doc-del-{status}", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Set registry status
        from app.services.registry_client import RegistryServiceClient
        reg = RegistryServiceClient._storage
        if draft_id in reg["drafts"]:
            reg["drafts"][draft_id]["status"] = status

        response = client.delete(
            self.DELETE_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert response.status_code in (200, 204)
