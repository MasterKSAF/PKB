"""
Integration tests for the full preview phase flow.

Tests the preview lifecycle through both the FastAPI TestClient
(draft preview endpoints) and the PipelineOrchestrator directly.

Verifies:
  - Preview start via API
  - Preview status at each phase (processing, completed)
  - Stage transition when preview_converter completes
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.fsm import TaskStage
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.pipeline import TaskRepository

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def preview_task(db_session: AsyncSession) -> dict:
    """Create a Task with all 3 preview steps for testing.

    Returns dict with {task, steps, repo} for easy access in tests.
    Data is committed so TestClient can see it.
    """
    from app.services.registry_client import RegistryServiceClient

    repo = TaskRepository(db_session)
    task = await repo.create_task(
        draft_id=200,
        pipeline_type="formation",
        total_steps=3,
    )
    await db_session.flush()

    # Pre-populate Registry mock storage with draft 200
    RegistryServiceClient._storage["drafts"][200] = {
        "draft_id": 200,
        "file_key": "drafts/200/file.pdf",
        "status": "uploaded",
        "created_by": "user-1",
        "created_at": "2026-06-08T10:00:00Z",
        "updated_at": "2026-06-08T10:00:00Z",
    }

    # Upload step (always completed immediately by orchestrator)
    upload = await repo.create_task_step(
        task_id=task.id, step_name="upload", step_index=0,
        service_name="Orchestrator",
        input_data={"file_key": "drafts/200/file.pdf"},
    )
    await repo.start_task_step(upload.id)
    await repo.complete_task_step(
        upload.id,
        output_data={"draft_id": 200, "task_id": task.id, "file_key": "drafts/200/file.pdf"},
    )

    # Preview OCR — running (simulates orchestator having started it)
    ocr = await repo.create_task_step(
        task_id=task.id, step_name="preview_ocr", step_index=1,
        service_name="OCR Service",
        input_data={"file_key": "drafts/200/file.pdf", "mode": "preview", "max_pages": 3},
    )
    await repo.start_task_step(ocr.id)

    # Preview converter — pending (waiting for OCR to finish)
    converter = await repo.create_task_step(
        task_id=task.id, step_name="preview_converter", step_index=2,
        service_name="Converter-validator",
        input_data={"file_key": "drafts/200/file.pdf", "mode": "preview"},
    )

    await db_session.commit()

    return {
        "task": task,
        "steps": {"upload": upload, "ocr": ocr, "converter": converter},
        "repo": repo,
    }


# ---------------------------------------------------------------------------
#  Preview start via API
# ---------------------------------------------------------------------------


class TestPreviewStartViaApi:
    """POST /drafts/{draft_id}/preview via TestClient."""

    async def test_start_preview_returns_accepted(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession,
    ):
        """Starting preview via API returns 202 with previewing status."""
        # Arrange: create a Task for draft_id=300
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=300, pipeline_type="formation", total_steps=3,
        )
        await db_session.commit()

        # Mock RegistryServiceClient.get_draft to return "uploaded" status
        mock_registry = AsyncMock()
        mock_registry.get_draft.return_value = {
            "data": {
                "draft_id": 300,
                "file_key": "drafts/300/file.pdf",
                "status": "uploaded",
                "created_by": "user-1",
                "created_at": "2026-06-08T10:00:00Z",
                "updated_at": "2026-06-08T10:00:00Z",
            }
        }

        with patch(
            "app.api.v1.endpoints.drafts.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_preview_step.delay",
        ):
            response = client.post(
                "/api/v1/drafts/300/preview",
                headers=auth_header,
            )

        assert response.status_code == 202
        data = response.json()
        assert data["draft_id"] == 300
        assert data["status"] == "previewing"
        assert "task_id" in data
        assert "message" in data


# ---------------------------------------------------------------------------
#  Preview status via API
# ---------------------------------------------------------------------------


class TestPreviewStatusViaApi:
    """GET /drafts/{draft_id}/preview/status via TestClient."""

    async def test_status_returns_processing_when_ocr_running(
        self, client: TestClient, auth_header: dict, preview_task: dict,
    ):
        """When preview_ocr is still running, status returns 'processing'."""
        task = preview_task["task"]

        response = client.get(
            f"/api/v1/drafts/{task.draft_id}/preview/status?longpoll=0",
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == task.draft_id
        assert data["task_id"] == task.id
        assert data["status"] == "processing"
        assert data["decision_required"] is False
        assert "progress_percent" in data

    async def test_status_returns_completed_when_all_steps_done(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession, preview_task: dict,
    ):
        """When both preview steps complete, status returns 'completed'."""
        task = preview_task["task"]
        steps = preview_task["steps"]
        repo = preview_task["repo"]

        # Complete the OCR step with output
        await repo.complete_task_step(
            steps["ocr"].id,
            output_data={
                "preview_not_supported": False,
                "pages_processed": 3,
                "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test"},
            },
        )

        # Start and complete the converter step
        await repo.start_task_step(steps["converter"].id)
        await repo.complete_task_step(
            steps["converter"].id,
            output_data={
                "validated": True,
                "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test"},
            },
        )

        # Update task stage to decision (as orchestrator would)
        await repo.update_task_status(
            task_id=task.id,
            stage=TaskStage.DECISION.value,
            progress_percent=50,
        )

        await db_session.commit()

        response = client.get(
            f"/api/v1/drafts/{task.draft_id}/preview/status?longpoll=0",
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["decision_required"] is True
        assert data["progress_percent"] == 50
        assert data["preview"] is not None
        assert data["preview"]["doc_code"] == "ГОСТ 1234-56"

    async def test_status_with_longpoll_returns_completed(
        self, client: TestClient, auth_header: dict, db_session: AsyncSession, preview_task: dict,
    ):
        """Longpoll returns 'completed' when steps finish before timeout."""
        task = preview_task["task"]
        steps = preview_task["steps"]
        repo = preview_task["repo"]

        # Complete both steps (simulating Celery tasks finishing quickly)
        await repo.complete_task_step(
            steps["ocr"].id,
            output_data={
                "preview_not_supported": False,
                "pages_processed": 3,
            },
        )
        await repo.start_task_step(steps["converter"].id)
        await repo.complete_task_step(
            steps["converter"].id,
            output_data={"validated": True, "metadata": {}},
        )
        await repo.update_task_status(
            task_id=task.id,
            stage=TaskStage.DECISION.value,
        )

        await db_session.commit()

        response = client.get(
            f"/api/v1/drafts/{task.draft_id}/preview/status?longpoll=5",
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
#  Stage transition via orchestrator
# ---------------------------------------------------------------------------


class TestPreviewStageTransition:
    """Direct PipelineOrchestrator usage for stage transitions."""

    async def test_preview_converter_completion_transitions_to_decision(
        self, db_session: AsyncSession,
    ):
        """When preview_converter completes, the task stage becomes 'decision'."""
        # Create a full preview scenario via orchestrator
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=400, pipeline_type="formation", total_steps=3,
        )

        # Create steps manually
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": "drafts/400/file.pdf"},
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 400, "task_id": task.id, "file_key": "drafts/400/file.pdf"},
        )

        ocr = await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="OCR Service",
            input_data={"file_key": "drafts/400/file.pdf", "mode": "preview", "max_pages": 3},
        )
        await repo.start_task_step(ocr.id)
        await repo.complete_task_step(
            ocr.id,
            output_data={
                "preview_not_supported": False,
                "pages_processed": 3,
                "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Partial Preview"},
            },
        )

        converter = await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
            input_data={"file_key": "drafts/400/file.pdf", "mode": "preview"},
        )
        await repo.start_task_step(converter.id)

        # Mock RegistryServiceClient
        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            orchestrator = PipelineOrchestrator(db_session)
            # Trigger the converter completion
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="preview_converter",
                input_data={"file_key": "drafts/400/file.pdf", "mode": "preview"},
                output_data={
                    "validated": True,
                    "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Partial Preview"},
                },
            )

        # Verify stage transition
        updated_task = await repo.get_task(task.id)
        assert updated_task is not None
        assert updated_task.pipeline_stage == TaskStage.DECISION.value
        assert updated_task.progress_percent == 50

        # Converter step should be completed
        all_steps = await repo.get_task_steps(task.id)
        conv_step = next(s for s in all_steps if s.step_name == "preview_converter")
        assert conv_step.status == "completed"

        # Registry should have been called to update draft status
        mock_registry.update_draft_status.assert_awaited_once_with(
            draft_id=400,
            status="ready_for_approve",
        )

    async def test_full_pipeline_preview_flow(
        self, db_session: AsyncSession,
    ):
        """End-to-end: start_pipeline → complete preview_ocr → complete converter."""
        # --- Phase 1: Start pipeline ---
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=500, pipeline_type="formation", total_steps=3,
        )

        with patch(
            "app.tasks.pipeline_formation.run_ocr_preview_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_preview_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.start_pipeline(
                draft_id=500,
                task_id=task.id,
                file_key="drafts/500/file.pdf",
                mime_type="application/pdf",
            )

        # Verify initial state
        task_after_start = await repo.get_task(task.id)
        assert task_after_start is not None
        assert task_after_start.pipeline_stage == TaskStage.PREVIEW.value
        assert task_after_start.progress_percent == 10

        # --- Phase 2: Complete preview_ocr ---
        # Find the ocr step and mark it as running (Celery would have started it)
        steps = await repo.get_task_steps(task.id)
        ocr_step = next(s for s in steps if s.step_name == "preview_ocr")
        await repo.start_task_step(ocr_step.id)

        # Mock Registry to avoid real calls
        mock_registry = AsyncMock()
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="preview_ocr",
                input_data={"file_key": "drafts/500/file.pdf", "mode": "preview", "max_pages": 3},
                output_data={
                    "preview_not_supported": False,
                    "pages_processed": 3,
                    "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test Doc"},
                },
            )

        # Verify OCR step completed
        ocr_after = await repo.get_task_steps(task.id)
        ocr = next(s for s in ocr_after if s.step_name == "preview_ocr")
        assert ocr.status == "completed"

        # --- Phase 3: Complete preview_converter ---
        conv_step = next(s for s in steps if s.step_name == "preview_converter")
        await repo.start_task_step(conv_step.id)

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_registry,
        ):
            await orchestrator.on_step_completed(
                task_id=task.id,
                step_name="preview_converter",
                input_data={"file_key": "drafts/500/file.pdf", "mode": "preview"},
                output_data={
                    "validated": True,
                    "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test Doc"},
                },
            )

        # Verify final preview state
        final_task = await repo.get_task(task.id)
        assert final_task is not None
        assert final_task.pipeline_stage == TaskStage.DECISION.value
        assert final_task.progress_percent == 50

        # Verify both steps completed
        all_steps = await repo.get_task_steps(task.id)
        conv = next(s for s in all_steps if s.step_name == "preview_converter")
        assert conv.status == "completed"

        # Registry was called
        mock_registry.update_draft_status.assert_called_with(
            draft_id=500,
            status="ready_for_approve",
        )
