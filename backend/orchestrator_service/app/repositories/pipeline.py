"""
Task repository — CRUD operations for Task and TaskStep.

Manages the lifecycle of pipeline task execution records.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import Task, TaskStep
from app.core.fsm import TaskStatus
from app.core.fsm import TaskStage


class TaskRepository:
    """Repository for Task and TaskStep entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Task
    # ------------------------------------------------------------------

    async def count_active_tasks(self) -> int:
        """Count tasks that are currently active (not in terminal state)."""
        result = await self.db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.deleted_at.is_(None),
                    Task.status == TaskStatus.ACTIVE.value,
                )
            )
        )
        return result.scalar() or 0

    async def create_task(
        self,
        draft_id: int,
        pipeline_type: str,
        total_steps: int,
        priority: int = 5,
    ) -> Task:
        """Create a new pipeline task."""
        task = Task(
            draft_id=draft_id,
            pipeline_type=pipeline_type,
            status="active",
            pipeline_stage=TaskStage.UPLOAD.value,
            priority=priority,
            total_steps=total_steps,
            current_step_index=0,
            progress_percent=0,
        )
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID (excludes soft-deleted)."""
        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_task_for_update(self, task_id: int) -> Optional[Task]:
        """Get task with FOR UPDATE lock (excludes soft-deleted)."""
        result = await self.db.execute(
            select(Task)
            .where(
                Task.id == task_id,
                Task.deleted_at.is_(None),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def update_task_status(
        self,
        task_id: int,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        step_name: Optional[str] = None,
        step_index: Optional[int] = None,
        progress_percent: Optional[int] = None,
    ) -> Optional[Task]:
        """Update task status and optionally current step info."""
        task = await self.get_task_for_update(task_id)
        if task is None:
            return None
        if status is not None:
            task.status = status
        if stage is not None:
            task.pipeline_stage = stage
        if step_name is not None:
            task.current_step_name = step_name
        if step_index is not None:
            task.current_step_index = step_index
        if progress_percent is not None:
            task.progress_percent = progress_percent
        if status == "active" and task.started_at is None:
            task.started_at = datetime.now(timezone.utc)
        if status in ("completed", "failed"):
            task.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return task

    async def lock_task(self, task_id: int, worker_id: str) -> Optional[Task]:
        """Lock a task for exclusive processing by a worker."""
        task = await self.get_task_for_update(task_id)
        if task is None:
            return None
        task.locked_by = worker_id
        task.locked_at = datetime.now(timezone.utc)
        await self.db.flush()
        return task

    async def unlock_task(self, task_id: int) -> Optional[Task]:
        """Release lock on a task."""
        task = await self.get_task_for_update(task_id)
        if task is None:
            return None
        task.locked_by = None
        task.locked_at = None
        await self.db.flush()
        return task

    async def get_stale_running_tasks(
        self, max_running_seconds: int = 3600
    ) -> list[Task]:
        """Find tasks that have been running too long."""
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_running_seconds)
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.status == "active",
                    Task.started_at < threshold,
                    Task.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_stale_pending_steps(
        self, max_pending_seconds: int = 30
    ) -> list[TaskStep]:
        """Find steps stuck in pending state (P3S-1)."""
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_pending_seconds)
        result = await self.db.execute(
            select(TaskStep).where(
                and_(
                    TaskStep.status == "pending",
                    TaskStep.created_at < threshold,
                    TaskStep.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_stale_running_steps(
        self, max_running_seconds: int = 600
    ) -> list[TaskStep]:
        """Find steps stuck in running state (B2).

        Steps in 'running' longer than max_running_seconds are candidates
        for health check — the service may have hung or crashed.
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_running_seconds)
        result = await self.db.execute(
            select(TaskStep).where(
                and_(
                    TaskStep.status == "running",
                    TaskStep.started_at < threshold,
                    TaskStep.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_absolute_timeout_tasks(
        self, max_hours: int = 48
    ) -> list[Task]:
        """Find tasks exceeding absolute timeout (P3S-1).

        Also returns completed indexation tasks for background integrity check (P2I-2).
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(hours=max_hours)
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.status == "active",
                    Task.created_at < threshold,
                    Task.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_stale_running_steps_for_hard_kill(
        self, max_execution_seconds: int = 1800
    ) -> list[TaskStep]:
        """Find running steps exceeding absolute execution timeout (H1).

        Unlike get_stale_running_steps, this ignores health-check and returns
        steps that must be killed regardless of service liveness.
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_execution_seconds)
        result = await self.db.execute(
            select(TaskStep).where(
                and_(
                    TaskStep.status == "running",
                    TaskStep.started_at < threshold,
                    TaskStep.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_stale_running_steps_for_hard_kill(
        self, max_execution_seconds: int = 1800
    ) -> list[TaskStep]:
        """Find running steps exceeding absolute execution timeout (H1).

        Unlike get_stale_running_steps, this ignores health-check and
        directly returns steps that must be killed.
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_execution_seconds)
        result = await self.db.execute(
            select(TaskStep).where(
                and_(
                    TaskStep.status == "running",
                    TaskStep.started_at < threshold,
                    TaskStep.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_stale_validation_tasks(
        self, max_validating_seconds: int = 7200
    ) -> list[Task]:
        """Find indexation tasks where rag_index completed but activation stuck (C2).

        These are tasks where:
        - pipeline_type == 'indexation'
        - status == 'active'
        - TaskStep 'rag_index' is 'completed'
        - No 'activate' step completed
        - Task started_at is older than max_validating_seconds
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_validating_seconds)

        # Subquery: find tasks that have a completed rag_index step
        rag_completed = (
            select(TaskStep.task_id)
            .where(
                and_(
                    TaskStep.step_name == "rag_index",
                    TaskStep.status == "completed",
                    TaskStep.deleted_at.is_(None),
                )
            )
        ).scalar_subquery()

        # Subquery: find tasks that have a completed activate step
        activate_completed = (
            select(TaskStep.task_id)
            .where(
                and_(
                    TaskStep.step_name == "activate",
                    TaskStep.status == "completed",
                    TaskStep.deleted_at.is_(None),
                )
            )
        ).scalar_subquery()

        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.pipeline_type == "indexation",
                    Task.status == "active",
                    Task.id.in_(rag_completed),
                    Task.id.not_in(activate_completed),
                    Task.started_at < threshold,
                    Task.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_recently_indexed_tasks(
        self, max_hours: int = 24
    ) -> list[Task]:
        """Get tasks that completed indexation recently (P2I-2 background check)."""
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(hours=max_hours)
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.pipeline_type == "indexation",
                    Task.status.in_(["completed", "partially_indexed"]),
                    Task.completed_at >= threshold,
                    Task.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def set_task_error(
        self, task_id: int, error_code: str, error_message: str
    ) -> Optional[Task]:
        """Record an error on a task."""
        task = await self.get_task_for_update(task_id)
        if task is None:
            return None
        task.error_code = error_code
        task.error_message = error_message
        task.retry_count = task.retry_count + 1
        await self.db.flush()
        return task

    # ------------------------------------------------------------------
    # TaskStep
    # ------------------------------------------------------------------

    async def create_task_step(
        self,
        task_id: int,
        step_name: str,
        step_index: int,
        service_name: str,
        input_data: Optional[dict] = None,
    ) -> TaskStep:
        """Create a task step entry (status: pending)."""
        step = TaskStep(
            task_id=task_id,
            step_name=step_name,
            step_index=step_index,
            service_name=service_name,
            status="pending",
            input_data=input_data,
        )
        self.db.add(step)
        await self.db.flush()
        return step

    async def start_task_step(self, step_id: int) -> Optional[TaskStep]:
        """Mark step as running."""
        result = await self.db.execute(
            select(TaskStep)
            .where(TaskStep.id == step_id)
            .with_for_update()
        )
        step = result.scalar_one_or_none()
        if step is None:
            return None
        step.status = "running"
        step.started_at = datetime.now(timezone.utc)
        await self.db.flush()
        return step

    async def complete_task_step(
        self,
        step_id: int,
        output_data: Optional[dict] = None,
    ) -> Optional[TaskStep]:
        """Mark step as completed successfully."""
        result = await self.db.execute(
            select(TaskStep)
            .where(TaskStep.id == step_id)
            .with_for_update()
        )
        step = result.scalar_one_or_none()
        if step is None:
            return None
        step.status = "completed"
        step.completed_at = datetime.now(timezone.utc)
        if output_data is not None:
            step.output_data = output_data
        await self.db.flush()
        return step

    async def fail_task_step(
        self,
        step_id: int,
        error_code: str,
        error_message: str,
    ) -> Optional[TaskStep]:
        """Mark step as failed."""
        result = await self.db.execute(
            select(TaskStep)
            .where(TaskStep.id == step_id)
            .with_for_update()
        )
        step = result.scalar_one_or_none()
        if step is None:
            return None
        step.status = "failed"
        step.completed_at = datetime.now(timezone.utc)
        step.error_code = error_code
        step.error_message = error_message
        await self.db.flush()
        return step

    async def compensate_task_step(self, step_id: int) -> Optional[TaskStep]:
        """Mark step as compensated."""
        result = await self.db.execute(
            select(TaskStep)
            .where(TaskStep.id == step_id)
            .with_for_update()
        )
        step = result.scalar_one_or_none()
        if step is None:
            return None
        step.status = "compensated"
        await self.db.flush()
        return step

    async def release_stale_locks(self, max_seconds: int = 3600) -> list[Task]:
        """Release locks on tasks that have been locked too long (M4).

        Returns the list of released tasks (with locked_by/locked_at info
        for logging).
        """
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(seconds=max_seconds)
        result = await self.db.execute(
            select(Task).where(
                and_(
                    Task.locked_at.is_not(None),
                    Task.locked_at < threshold,
                    Task.deleted_at.is_(None),
                )
            )
        )
        stale_locks = list(result.scalars().all())
        released = []
        for task in stale_locks:
            released.append({
                "id": task.id,
                "locked_by": task.locked_by,
                "locked_at": task.locked_at,
            })
            task.locked_by = None
            task.locked_at = None
        if stale_locks:
            await self.db.flush()
        return released

    async def get_task_steps(self, task_id: int) -> list[TaskStep]:
        """Get all steps for a task, ordered by step index (excludes soft-deleted)."""
        result = await self.db.execute(
            select(TaskStep)
            .where(
                TaskStep.task_id == task_id,
                TaskStep.deleted_at.is_(None),
            )
            .order_by(TaskStep.step_index)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # DraftNotification
    # ------------------------------------------------------------------

    async def save_notifications(
        self, task_id: int, draft_id: int, notifications: list[dict]
    ) -> list["DraftNotification"]:
        """Save quality notifications for a draft from Parser/OCR.

        Each notification dict:
            service (str): "ocr" | "parser"
            code (str): "low_quality", "missing_pages", etc.
            message (str): human-readable description
            severity (str): "critical" | "warning" | "info"
        """
        from app.models.pipeline import DraftNotification

        saved = []
        for n in notifications:
            notif = DraftNotification(
                task_id=task_id,
                draft_id=draft_id,
                service=n.get("service", "unknown"),
                code=n.get("code", "unknown"),
                message=n.get("message", ""),
                severity=n.get("severity", "warning"),
            )
            self.db.add(notif)
            saved.append(notif)
        if saved:
            await self.db.flush()
        return saved

    async def get_task_notifications(self, task_id: int) -> list["DraftNotification"]:
        """Get all notifications for a task."""
        from app.models.pipeline import DraftNotification

        result = await self.db.execute(
            select(DraftNotification).where(DraftNotification.task_id == task_id)
        )
        return list(result.scalars().all())

    async def has_critical_notifications(self, task_id: int) -> bool:
        """Check if task has any critical notifications."""
        from app.models.pipeline import DraftNotification

        result = await self.db.execute(
            select(DraftNotification).where(
                DraftNotification.task_id == task_id,
                DraftNotification.severity == "critical",
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None
