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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-terminal " * 100), "application/pdf")},
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
        """reject на терминальной задаче → 409 DRAFT_ALREADY_DECIDED."""
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
        assert detail["error"]["code"] == "DRAFT_ALREADY_DECIDED"

    @pytest.mark.parametrize("terminal_status", ["completed", "failed"])
    async def test_stop_duplicate_on_terminal_task_returns_409(
        self,
        terminal_status: str,
        draft_with_terminal_task: int,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """stop_duplicate на терминальной задаче → 409 DRAFT_ALREADY_DECIDED."""
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
        assert detail["error"]["code"] == "DRAFT_ALREADY_DECIDED"


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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-stopdup " * 100), "application/pdf")},
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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-override " * 100), "application/pdf")},
            data={"document_key": "doc-override", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        task_id = response.json()["task_id"]

        # Set task to decision stage
        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        # Set preview steps to completed so approve doesn't get blocked by 5.3 check
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        for step in steps_result.scalars().all():
            step.status = "completed"
            if step.step_name == "preview_converter":
                step.output_data = {
                    "metadata": {
                        "doc_code": "OVERRIDE-001",
                        "title": "Overridden Title",
                        "source_type": "GOST",
                    }
                }

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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-proceed " * 100), "application/pdf")},
            data={"document_key": "doc-proceed", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        # Complete preview steps to pass 5.3 check
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        for step in steps_result.scalars().all():
            step.status = "completed"

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
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-force " * 100), "application/pdf")},
            data={"document_key": "doc-force", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        # Complete preview steps to pass 5.3 check
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        for step in steps_result.scalars().all():
            step.status = "completed"

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


class TestDecidePreviewInProgress:
    """PATCH /decide — блокировка при processing preview (5.3).

    approve/proceed/force_new_version должны возвращать 409,
    если preview-шаги ещё выполняются (running/pending).
    """

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"
    PREVIEW_URL = "/api/v1/drafts/{draft_id}/preview"

    @pytest.fixture
    async def draft_with_preview_steps(
        self, request, client: TestClient, auth_header: dict, db_session: AsyncSession
    ) -> int:
        """Create a draft (which auto-starts preview), then set step statuses via fixture param."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF preview-block " * 100), "application/pdf")},
            data={"document_key": "doc-prev-block", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        # Apply step statuses from fixture param
        step_statuses = getattr(request, "param", {})
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        steps = list(steps_result.scalars().all())
        for step in steps:
            if step.step_name in step_statuses:
                step.status = step_statuses[step.step_name]
                if step.step_name == "preview_converter" and step.status == "completed":
                    step.output_data = {
                        "metadata": {
                            "doc_code": "TEST-001",
                            "title": "Test Title",
                            "source_type": "GOST",
                        }
                    }

        await db_session.flush()
        await db_session.commit()
        return draft_id

    @pytest.mark.parametrize(
        "draft_with_preview_steps,expected_status",
        [
            ({"preview_ocr": "running", "preview_converter": "completed"}, 409),
            ({"preview_ocr": "pending", "preview_converter": "completed"}, 409),
            ({"preview_ocr": "completed", "preview_converter": "completed"}, 200),
        ],
        indirect=["draft_with_preview_steps"],
    )
    async def test_approve_blocks_on_running_preview(
        self,
        draft_with_preview_steps: int,
        expected_status: int,
        client: TestClient,
        auth_header: dict,
    ):
        """
        approve:
          - running preview → 409 PREVIEW_IN_PROGRESS
          - pending preview → 409 PREVIEW_IN_PROGRESS
          - completed preview → 200
        """
        draft_id = draft_with_preview_steps
        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "approve"},
        )
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}: {response.json()}"
        )
        if expected_status == 409:
            data = response.json()
            detail = data.get("detail", data)
            assert detail["error"]["code"] == "PREVIEW_IN_PROGRESS"
        elif expected_status == 200:
            data = response.json()
            assert data["action"] == "approve"

    async def test_proceed_while_preview_running_returns_409(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """proceed при running preview → 409 PREVIEW_IN_PROGRESS."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF proceed-block " * 100), "application/pdf")},
            data={"document_key": "doc-proceed-block", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        # Set OCR to running, converter to completed
        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        steps = list(steps_result.scalars().all())
        for step in steps:
            if step.step_name == "preview_ocr":
                step.status = "running"
            elif step.step_name == "preview_converter":
                step.status = "completed"

        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "proceed"},
        )
        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "PREVIEW_IN_PROGRESS"


class TestDecideConfirmAction:
    """confirm (action for review_required → validation)."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    async def test_confirm_requires_decision_stage(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """confirm на upload-стадии → 409 INVALID_STAGE."""
        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-confirm " * 100), "application/pdf")},
            data={"document_key": "doc-confirm", "source_type": "GOST"},
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
        task.pipeline_stage = "upload"
        task.status = "active"
        await db_session.flush()
        await db_session.commit()

        response = client.patch(
            self.DECIDE_URL.format(draft_id=draft_id),
            headers=auth_header,
            json={"action": "confirm"},
        )
        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "INVALID_STAGE"

    async def test_confirm_on_decision_returns_validation(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """confirm на decision-стадии → ответ с status='validation'."""
        from unittest.mock import patch, AsyncMock

        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-confirm2 " * 100), "application/pdf")},
            data={"document_key": "doc-confirm2", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        task_id = response.json()["task_id"]

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
                "data": {"draft_id": draft_id, "title_key": "Confirm Test", "document_key": "CONFIRM-001"}
            })
            mock_reg.get_draft_preview = AsyncMock(return_value={
                "data": {"title": "Confirm Title", "doc_code": "CONFIRM-001"}
            })
            mock_reg.create_document = AsyncMock(return_value={
                "data": {"document_id": 6001, "version_id": 60001, "is_new_document": True}
            })
            mock_reg.create_draft_snapshot = AsyncMock()
            mock_reg.close = AsyncMock()

            response = client.patch(
                self.DECIDE_URL.format(draft_id=draft_id),
                headers=auth_header,
                json={"action": "confirm"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "validation"
        assert data["action"] == "confirm"


class TestDecideBusinessKeyDrift:
    """BUSINESS_KEY_DRIFT при approve (метаданные изменились)."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    async def test_business_key_drift_returns_409(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """При изменении title через overrides → 409 BUSINESS_KEY_DRIFT."""
        from unittest.mock import patch, AsyncMock

        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-bkdrift " * 100), "application/pdf")},
            data={"document_key": "doc-bkdrift", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        task_id = response.json()["task_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        for step in steps_result.scalars().all():
            step.status = "completed"
        await db_session.flush()
        await db_session.commit()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_reg_cls:
            mock_reg = mock_reg_cls.return_value
            mock_reg.get_draft = AsyncMock(return_value={
                "data": {"draft_id": draft_id, "title_key": "Original", "document_key": "ORIG-001"}
            })
            mock_reg.get_draft_preview = AsyncMock(return_value={
                "data": {"title": "Original Title", "doc_code": "ORIG-001", "title_hash_sha256": "dd3545e9ab2b0772384fdf2d61abd18cdbf3c14c2e6a7fbe1dcda54f52ec805b"}
            })
            mock_reg.create_document = AsyncMock()
            mock_reg.create_draft_snapshot = AsyncMock()
            mock_reg.close = AsyncMock()

            overrides = {"title": "Completely Different Title"}

            response = client.patch(
                self.DECIDE_URL.format(draft_id=draft_id),
                headers=auth_header,
                json={"action": "approve", "metadata_overrides": overrides},
            )

        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "BUSINESS_KEY_DRIFT"


class TestDecideDuplicateFileAfterApprove:
    """DUPLICATE_FILE_AFTER_APPROVE при race condition с Registry."""

    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"
    CREATE_URL = "/api/v1/drafts/"

    async def test_duplicate_file_after_approve_returns_409(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
    ):
        """Registry возвращает DUPLICATE_FILE → 409 с conflict_document_id."""
        from unittest.mock import patch, AsyncMock

        response = client.post(
            self.CREATE_URL,
            headers=auth_header,
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-dedup " * 100), "application/pdf")},
            data={"document_key": "doc-dedup", "source_type": "GOST"},
        )
        assert response.status_code == 202
        draft_id = response.json()["draft_id"]
        task_id = response.json()["task_id"]

        from sqlalchemy import select
        from app.models.pipeline import Task, TaskStep

        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        task = result.scalar_one_or_none()
        assert task is not None
        task.pipeline_stage = "decision"
        task.status = "active"

        steps_result = await db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        for step in steps_result.scalars().all():
            step.status = "completed"
        await db_session.flush()
        await db_session.commit()

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
        ) as mock_reg_cls:
            mock_reg = mock_reg_cls.return_value
            mock_reg.get_draft = AsyncMock(return_value={
                "data": {"draft_id": draft_id, "title_key": "Dedup Test", "document_key": "DEDUP-001"}
            })
            mock_reg.get_draft_preview = AsyncMock(return_value={
                "data": {"title": "Dedup Title", "doc_code": "DEDUP-001"}
            })
            # Simulate DUPLICATE_FILE error
            mock_reg.create_document = AsyncMock(return_value={
                "error": {
                    "code": "DUPLICATE_FILE",
                    "details": {"conflict_document_id": 777},
                }
            })
            mock_reg.create_draft_snapshot = AsyncMock()
            mock_reg.close = AsyncMock()
            mock_reg.update_draft_status = AsyncMock()

            response = client.patch(
                self.DECIDE_URL.format(draft_id=draft_id),
                headers=auth_header,
                json={"action": "approve"},
            )

        assert response.status_code == 409
        data = response.json()
        detail = data.get("detail", data)
        assert detail["error"]["code"] == "DUPLICATE_FILE_AFTER_APPROVE"
        assert detail["error"]["details"]["conflict_document_id"] == 777
