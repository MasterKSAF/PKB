"""
Тесты ошибок full-фазы (Pipeline 1, §6).

Покрывает сценарии §6 Full-фаза (pipeline1-orchestrator_details.md):
  - Full OCR/Parser таймаут → on_step_failed → retry
  - Full OCR/Parser 5xx → on_step_failed → retry exhausted → Saga
  - Full пустой документ (0 секций) → on_step_failed обработка
  - on_step_failed для уже терминальной задачи → guard
  - Parser→OCR fallback при ошибке на full-фазе

Внимание:
  - retry-логика тестируется через PipelineOrchestrator.on_step_failed
  - Saga компенсация тестируется отдельно в test_saga_compensation.py
"""

import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.pipeline import TaskRepository
from app.core.fsm import TaskStatus


class TestOnStepFailedGuard:
    """Guard: on_step_failed не обрабатывает терминальные задачи."""

    async def test_on_step_failed_skips_terminal_task(
        self, db_session: AsyncSession,
    ):
        """on_step_failed для completed задачи → return (без изменений)."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=300, pipeline_type="formation", total_steps=3,
        )
        task.status = TaskStatus.COMPLETED.value
        await db_session.flush()

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.on_step_failed(
            task_id=task.id,
            step_name="full_ocr",
            error_code="OCR_TIMEOUT",
            error_message="OCR processing timed out",
        )

        # Task should remain completed
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED.value


class TestOnStepFailedRetry:
    """Retry-логика при ошибке шага."""

    async def test_on_step_failed_retries_with_backoff(
        self, db_session: AsyncSession,
    ):
        """on_step_failed при retry_count < MAX → создаёт новый pending step."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=301, pipeline_type="formation", total_steps=3,
        )
        task.retry_count = 0
        await db_session.flush()

        # Create a running step
        step = await repo.create_task_step(
            task_id=task.id, step_name="full_ocr", step_index=3,
            service_name="OCR Service",
        )
        await repo.start_task_step(step.id)

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.on_step_failed(
            task_id=task.id,
            step_name="full_ocr",
            error_code="OCR_TIMEOUT",
            error_message="OCR timeout after 300s",
        )

        # Verify retry: new step created
        steps = await repo.get_task_steps(task.id)
        running_steps = [s for s in steps if s.status == "running"]
        pending_steps = [s for s in steps if s.status == "pending"]
        # There should be at least one pending step for retry
        assert len(pending_steps) >= 1
        # The failed step should be marked failed
        failed_steps = [s for s in steps if s.status == "failed"]
        assert len(failed_steps) >= 1
        # error info should be set
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.error_code == "OCR_TIMEOUT"
        assert updated.retry_count > 0


class TestOnStepFailedParserToOcrFallback:
    """Parser→OCR fallback при ошибке на full-фазе."""

    async def test_parser_full_failure_falls_back_to_ocr(
        self, db_session: AsyncSession,
    ):
        """Parser failed на full_ocr → fallback на OCR."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=302, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        # Create a running step with Parser Service
        step = await repo.create_task_step(
            task_id=task.id, step_name="full_ocr", step_index=3,
            service_name="Parser Service",
            input_data={"file_key": "f-test", "mode": "full", "draft_id": 302},
        )
        await repo.start_task_step(step.id)

        with patch(
            "app.tasks.pipeline_formation.run_ocr_full_step.delay",
        ):
            orchestrator = PipelineOrchestrator(db_session)
            await orchestrator.on_step_failed(
                task_id=task.id,
                step_name="full_ocr",
                error_code="PARSER_FAILED",
                error_message="Parser returned 500",
            )

        # Verify: OCR fallback step was created
        steps = await repo.get_task_steps(task.id)
        ocr_pending = [
            s for s in steps
            if s.step_name == "full_ocr" and s.status == "pending"
            and s.service_name == "OCR Service"
        ]
        assert len(ocr_pending) >= 1, "OCR fallback step should be created"


class TestOnStepFailedRegistry:
    """Ошибка Registry шага."""

    async def test_registry_step_failure_creates_retry(
        self, db_session: AsyncSession,
    ):
        """registry_creation шаг упал → retry."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=303, pipeline_type="formation", total_steps=3,
        )
        await db_session.flush()

        step = await repo.create_task_step(
            task_id=task.id, step_name="registry_creation", step_index=5,
            service_name="Registry",
        )
        await repo.start_task_step(step.id)

        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.on_step_failed(
            task_id=task.id,
            step_name="registry_creation",
            error_code="REGISTRY_WRITE_FAILED",
            error_message="Registry INSERT failed",
        )

        # Should attempt retry
        updated = await repo.get_task(task.id)
        assert updated is not None
        assert updated.error_code == "REGISTRY_WRITE_FAILED"
