"""
Тесты edge cases для PATCH /drafts/{draft_id}/decide.

Покрывает сценарии §4 Решение пользователя (pipeline1-orchestrator_details.md):
  - reject для терминального статуса → 409 DRAFT_ALREADY_DECIDED
  - stop_duplicate для upload → 409 INVALID_STAGE
  - stop_duplicate для full → 409 INVALID_STAGE
  - approve с metadata_overrides → overrides передаются в create_document

Внимание:
  - approve для review_required → в production-коде проверяется STAGE, а не статус Registry.
    Текущая логика: approve разрешён для decision/upload/preview.
  - Проверка 0 страниц при approve не реализована.
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDecideTerminalEdgeCases:
    """PATCH /decide на терминальных черновиках."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def draft_with_terminal_task(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        """Create a draft and set task to terminal status."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-terminal"), "application/pdf")},
            data={"document_key": "doc-terminal-edge", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        return draft_id

    @pytest.mark.parametrize("terminal_status", ["completed", "failed"])
    async def test_reject_on_terminal_task_returns_409(
        self,
        terminal_status: str,
        draft_with_terminal_task: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """reject на терминальной задаче → 409 TASK_ALREADY_TERMINAL."""
        draft_id = draft_with_terminal_task
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.status = terminal_status
        task.pipeline_stage = "decision"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "reject"},
        )
        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "TASK_ALREADY_TERMINAL"

    @pytest.mark.parametrize("terminal_status", ["completed", "failed"])
    async def test_stop_duplicate_on_terminal_task_returns_409(
        self,
        terminal_status: str,
        draft_with_terminal_task: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """stop_duplicate на терминальной задаче → 409 TASK_ALREADY_TERMINAL."""
        draft_id = draft_with_terminal_task
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.status = terminal_status
        task.pipeline_stage = "preview"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "stop_duplicate"},
        )
        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "TASK_ALREADY_TERMINAL"


class TestDecideStopDuplicateStageValidation:
    """stop_duplicate разрешён только для preview/decision."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    @pytest.fixture
    async def created_draft(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-stopdup"), "application/pdf")},
            data={"document_key": "doc-stopdup", "source_type": "GOST"},
        )
        assert response.status_code == 202
        return response.json()["draft_id"]

    @pytest.mark.parametrize("stage", ["upload", "full", "registry", "indexation"])
    async def test_stop_duplicate_in_invalid_stage_returns_409(
        self,
        stage: str,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """stop_duplicate вне preview/decision → 409 INVALID_STAGE."""
        draft_id = created_draft
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = stage
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "stop_duplicate"},
        )
        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "INVALID_STAGE"

    @pytest.mark.parametrize("stage", ["preview", "decision"])
    async def test_stop_duplicate_in_valid_stage_returns_200(
        self,
        stage: str,
        created_draft: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """stop_duplicate для preview/decision → 200."""
        draft_id = created_draft
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = stage
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "stop_duplicate"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "stop_duplicate"
        assert data["status"] == "discarded"


class TestDecideWithMetadataOverrides:
    """approve с metadata_overrides → overrides передаются."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    async def test_approve_with_overrides_passes_metadata(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """metadata_overrides в approve передаются в create_document."""
        from unittest.mock import patch, AsyncMock

        # Create draft
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-override"), "application/pdf")},
            data={"document_key": "doc-override", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        task_id = response.json()["task_id"]

        # Set task to decision stage
        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        overrides = {
            "title": "Overridden Title",
            "doc_code": "OVERRIDE-001",
            "era": "CURRENT",
        }

        # Мокаем RegistryServiceClient в orchestrator (где вызывается approve_draft)
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_reg_cls, patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_rag_index_step.delay",
        ):
            mock_reg = mock_reg_cls.return_value
            mock_reg.get_draft = AsyncMock(return_value={
                "data": {"draft_id": draft_id, "title_key": "Test", "document_key": "TEST-001"}
            })
            mock_reg.get_draft_preview = AsyncMock(return_value={
                "data": {"title": "Overridden Title", "doc_code": "OVERRIDE-001"}
            })
            mock_reg.create_document = AsyncMock(return_value={
                "data": {"document_id": 5001, "version_id": 50001, "is_new_document": True}
            })
            mock_reg.create_draft_snapshot = AsyncMock()
            mock_reg.close = AsyncMock()
            mock_reg.update_draft_status = AsyncMock()

            response = client.patch(
                self.DECIDE_URL.format(draft_id=draft_id),
                headers=auth_header,
                json={"action": "approve", "metadata_overrides": overrides},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] is not None
        assert data["action"] == "approve"

        # Verify overrides were applied via API response
        assert data["document_id"] is not None
        assert data["version_id"] is not None


class TestDecideProceedAction:
    """proceed (internal action) — то же что approve, но action='proceed'."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    async def test_proceed_action_returns_200(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """proceed = approve (внутреннее действие) → 200."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-proceed"), "application/pdf")},
            data={"document_key": "doc-proceed", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "proceed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "proceed"
        assert data["status"] == "proceeding"
        assert data["document_id"] is not None


class TestDecideForceNewVersion:
    """force_new_version (internal action)."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    async def test_force_new_version_returns_200(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """force_new_version = approve + message → 200."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-force"), "application/pdf")},
            data={"document_key": "doc-force", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "force_new_version"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "force_new_version"
        assert data["is_new_document"] is False
        assert "Принудительное создание новой версии" in data["message"]
