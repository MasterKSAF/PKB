"""
Тесты state validation для POST /drafts/{draft_id}/preview.

Покрывает сценарии §1 Preview-фаза: запуск (pipeline1-orchestrator_details.md):
  - Статус previewing без Idempotency-Key → 409 PREVIEW_ALREADY_RUNNING
  - Статус ready_for_approve → 409 CONFLICT
  - Статус discarded → 409 CONFLICT
  - Статус approved → 409 CONFLICT
  - Черновик не найден → 404 NOT_FOUND

Внимание:
  - В production-коде start_preview проверяет registry.drafts.status,
    а не pipeline.tasks.pipeline_stage.
  - Идемпотентность по Idempotency-Key для preview не реализована
    (в документации упомянута как P1-19, но не реализована).
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPreviewStateValidation:
    """POST /api/v1/drafts/{draft_id}/preview — state validation."""

    CREATE_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"

    @pytest.fixture
    def created_draft(self, client: TestClient, auth_header: dict) -> int:
        """Create a draft via API."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 50), "application/pdf")},
            data={"document_key": "doc-preview-state", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    async def test_preview_already_running_returns_409(
        self, created_draft: int, client: TestClient, auth_header: dict,
        db_session: AsyncSession,
    ):
        """Повторный preview → 409 PREVIEW_ALREADY_RUNNING, если есть running steps.

        После первого preview steps создаются со статусом 'pending'.
        Меняем статус step на 'running' через DB, чтобы симулировать
        реально выполняющийся preview.
        """
        # First preview — запускаем (создаёт steps)
        resp1 = client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        assert resp1.status_code == 202

        # Меняем статус step на running через DB
        from sqlalchemy import select
        from app.models.pipeline import TaskStep

        steps_result = await db_session.execute(
            select(TaskStep).where(
                TaskStep.step_name == "preview_ocr"
            )
        )
        steps = list(steps_result.scalars().all())
        for step in steps:
            step.status = "running"
        if steps:
            await db_session.flush()
            await db_session.commit()

        # Second preview — должен быть 409, т.к. есть running step
        resp2 = client.post(
            self.PREVIEW_URL.format(draft_id=created_draft),
            headers=auth_header,
        )
        assert resp2.status_code == 409, (
            f"Expected 409, got {resp2.status_code}: {resp2.text}"
        )
        data = resp2.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "PREVIEW_ALREADY_RUNNING"

    def test_preview_not_found_returns_404(
        self, client: TestClient, auth_header: dict
    ):
        """Несуществующий черновик → 404 NOT_FOUND."""
        response = client.post(
            self.PREVIEW_URL.format(draft_id=99999),
            headers=auth_header,
        )
        assert response.status_code == 404
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "NOT_FOUND"

    def test_preview_for_nonexistent_task_returns_404(
        self, client: TestClient, auth_header: dict
    ):
        """Черновик есть в Registry, но нет задачи в оркестраторе → 404.

        Registry mock возвращает draft при любом draft_id. Но если Task
        не создан, start_preview вернёт 404.
        """
        response = client.post(
            self.PREVIEW_URL.format(draft_id=42),
            headers=auth_header,
        )
        assert response.status_code == 404
        data = response.json()
        detail = data.get("detail", data)
        assert "error" in detail
        assert detail["error"]["code"] == "NOT_FOUND"


class TestPreviewWithRegistryStatus:
    """POST /preview с различными статусами в Registry.

    start_preview проверяет draft_data.get('status') == 'uploaded'.
    Если статус другой — возвращает 409.
    """

    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def draft_in_status(self, status: str, client, auth_header, db_session):
        """Create a draft and set its registry status."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 50), "application/pdf")},
            data={"document_key": "doc-status-test", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        # Update Registry mock storage status
        from app.services.registry_client import RegistryServiceClient
        reg_storage = RegistryServiceClient._storage
        if draft_id in reg_storage["drafts"]:
            reg_storage["drafts"][draft_id]["status"] = status

        return draft_id

    @pytest.mark.parametrize("status,expected_code,expected_error", [
        ("previewing", 409, "CONFLICT"),
        ("ready_for_approve", 409, "CONFLICT"),
        ("discarded", 409, "CONFLICT"),
        ("approved", 409, "CONFLICT"),
    ])
    async def test_preview_with_non_uploaded_status_returns_409(
        self,
        status: str,
        expected_code: int,
        expected_error: str,
        client: TestClient,
        auth_header: dict,
        db_session,
    ):
        """Если статус черновика в Registry не 'uploaded' → 409."""
        # Create a draft first
        create_resp = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF mock " * 50), "application/pdf")},
            data={"document_key": f"doc-status-{status}", "source_type": "GOST"},
        )
        assert create_resp.status_code == 202
        draft_id = create_resp.json()["draft_id"]

        # Update Registry status
        from app.services.registry_client import RegistryServiceClient
        reg_storage = RegistryServiceClient._storage
        reg_storage["drafts"][draft_id]["status"] = status

        # Try preview
        response = client.post(
            self.PREVIEW_URL.format(draft_id=draft_id),
            headers=auth_header,
        )
        assert response.status_code == expected_code, (
            f"status={status}: expected {expected_code}, got {response.status_code}"
        )
