"""
ExternalTask repository — CRUD for external async task tracking.

Used by Celery tasks (to save new tasks) and BackgroundTaskPoller (to poll/update).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_task import ExternalTask


class ExternalTaskRepository:
    """Repository for ExternalTask entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        orchestrator_task_id: str,
        step_name: str,
        external_service: str,
        external_task_id: str,
        context_data: Optional[dict] = None,
    ) -> ExternalTask:
        """Create a new external task record."""
        task = ExternalTask(
            orchestrator_task_id=orchestrator_task_id,
            step_name=step_name,
            external_service=external_service,
            external_task_id=external_task_id,
            context_data=context_data,
            status="pending",
        )
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_pending_tasks(self) -> list[ExternalTask]:
        """Get all tasks still in pending status."""
        result = await self.db.execute(
            select(ExternalTask).where(ExternalTask.status == "pending")
        )
        return list(result.scalars().all())

    async def mark_completed(self, task_id: int) -> None:
        """Mark an external task as completed."""
        await self.db.execute(
            select(ExternalTask).where(ExternalTask.id == task_id)
        )
        task = await self.db.get(ExternalTask, task_id)
        if task:
            task.status = "completed"
            task.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def mark_failed(
        self, task_id: int, error_message: Optional[str] = None
    ) -> None:
        """Mark an external task as failed."""
        task = await self.db.get(ExternalTask, task_id)
        if task:
            task.status = "failed"
            task.error_message = error_message
            task.updated_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def delete(self, task_id: int) -> None:
        """Delete an external task record."""
        task = await self.db.get(ExternalTask, task_id)
        if task:
            await self.db.delete(task)
            await self.db.flush()

    async def delete_by_orchestrator_task(
        self, orchestrator_task_id: str, step_name: str
    ) -> None:
        """Delete external tasks for a given orchestrator task + step."""
        result = await self.db.execute(
            select(ExternalTask).where(
                ExternalTask.orchestrator_task_id == orchestrator_task_id,
                ExternalTask.step_name == step_name,
            )
        )
        tasks = list(result.scalars().all())
        for task in tasks:
            await self.db.delete(task)
        await self.db.flush()

    async def count_pending(self) -> int:
        """Count total pending external tasks."""
        result = await self.db.execute(
            select(func.count(ExternalTask.id)).where(
                ExternalTask.status == "pending"
            )
        )
        return result.scalar() or 0
