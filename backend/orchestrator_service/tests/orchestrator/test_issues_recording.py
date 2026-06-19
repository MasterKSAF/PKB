"""
Tests: quality notifications recording to pipeline.draft_notifications (T-4).

Verifies that:
  1. TaskRepository.save_notifications() writes to DB
  2. TaskRepository.get_task_notifications() retrieves them
  3. TaskRepository.has_critical_notifications() detects critical
  4. Orchestrator._on_preview_completed() saves notifications from quality data
"""

import pytest
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import TaskRepository
from app.core.pipeline.orchestrator import PipelineOrchestrator


class TestSaveNotifications:
    """Direct repository tests for DraftNotification."""

    async def test_save_and_retrieve(self, db_session: AsyncSession):
        """Save notifications then retrieve them."""
        repo = TaskRepository(db_session)

        # Create a task first
        task = await repo.create_task(
            draft_id=1, pipeline_type="formation", total_steps=3
        )
        task_id = task.id

        notifications = [
            {"service": "ocr", "code": "low_confidence_pages",
             "message": "3 pages with low confidence", "severity": "warning"},
            {"service": "ocr", "code": "missing_pages",
             "message": "Page 5 missing", "severity": "critical"},
        ]

        saved = await repo.save_notifications(task_id, draft_id=1, notifications=notifications)
        assert len(saved) == 2

        retrieved = await repo.get_task_notifications(task_id)
        assert len(retrieved) == 2
        assert retrieved[0].service == "ocr"
        assert retrieved[0].severity == "warning"
        assert retrieved[1].severity == "critical"

    async def test_has_critical(self, db_session: AsyncSession):
        """has_critical_notifications returns True when critical exists."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=2, pipeline_type="formation", total_steps=3
        )
        task_id = task.id

        # No notifications yet
        assert await repo.has_critical_notifications(task_id) is False

        # Add warning only
        await repo.save_notifications(
            task_id=task_id, draft_id=2,
            notifications=[
                {"service": "parser", "code": "low_quality",
                 "message": "Quality 0.7", "severity": "warning"},
            ],
        )
        assert await repo.has_critical_notifications(task_id) is False

        # Add critical
        await repo.save_notifications(
            task_id=task_id, draft_id=2,
            notifications=[
                {"service": "parser", "code": "very_low_quality",
                 "message": "Quality 0.3", "severity": "critical"},
            ],
        )
        assert await repo.has_critical_notifications(task_id) is True

    async def test_empty_notifications(self, db_session: AsyncSession):
        """Empty notifications list saves nothing."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=3, pipeline_type="formation", total_steps=3
        )

        saved = await repo.save_notifications(task.id, draft_id=3, notifications=[])
        assert len(saved) == 0

        retrieved = await repo.get_task_notifications(task.id)
        assert len(retrieved) == 0


class TestNotificationsFromQualityData:
    """Check that quality data in step output is processed."""

    async def test_orchestrator_saves_notifications(self, db_session: AsyncSession):
        """Orchestrator._on_preview_completed saves notifications."""
        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=10, pipeline_type="formation", total_steps=3
        )

        # Create preview steps with quality data
        from app.models.pipeline import TaskStep
        ocr_step = TaskStep(
            task_id=task.id,
            step_name="preview_ocr",
            step_index=1,
            service_name="OCR Service",
            status="completed",
            input_data={"file_key": "f-test", "mode": "preview", "draft_id": 10},
            output_data={
                "preview_not_supported": False,
                "pages_processed": 3,
                "metadata": {"doc_code": "GOST 1234", "title": "Test"},
                "quality": {
                    "score": 0.55,
                    "notifications": [
                        {"code": "low_quality", "message": "Score 0.55",
                         "severity": "critical"},
                    ],
                },
            },
        )
        db_session.add(ocr_step)
        converter_step = TaskStep(
            task_id=task.id,
            step_name="preview_converter",
            step_index=2,
            service_name="Converter-validator",
            status="pending",
        )
        db_session.add(converter_step)
        await db_session.flush()

        # Run _on_preview_completed
        steps = await repo.get_task_steps(task.id)
        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator._on_preview_completed(task, steps, converter_output={})

        # Check notifications saved
        notifications = await repo.get_task_notifications(task.id)
        assert len(notifications) >= 1
        assert any(n.code == "low_quality" for n in notifications)
