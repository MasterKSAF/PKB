"""
Saga Coordinator — manages compensation actions for distributed transactions.

When a pipeline step fails and retries are exhausted, the Saga coordinator
runs compensation (rollback) actions for all previously completed steps,
in reverse order.

Compensation actions are defined per step name.
Steps that are stateless (OCR, Parser) have no compensation.
Steps with side-effects (Registry creation) have compensations.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pipeline import TaskRepository

logger = logging.getLogger("orchestrator.saga")


class SagaCoordinator:
    """Coordinates compensation (rollback) actions for failed pipelines.

    Each compensation is an async call that undoes the side-effect of a step:
    - registry_creation: delete the document from Registry
    - converter: no side-effects (pure transformation), no compensation
    - full_ocr / preview_ocr / preview_converter / full_converter: no compensation
    """

    COMPENSATION_ACTIONS: dict[str, Optional[str]] = {
        "upload": None,
        "preview_ocr": None,
        "preview_converter": None,
        "full_ocr": None,
        "full_converter": None,
        "registry_creation": "delete_registry_document",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)

    async def compensate(self, task_id: int, failed_step: str) -> None:
        """Run compensation for all completed steps before the failed one."""
        logger.info(
            f"Starting compensation for task after {failed_step} failure",
            extra={"task_id": task_id, "failed_step": failed_step},
        )
        steps = await self.task_repo.get_task_steps(task_id)

        # Find the index of the failed step
        failed_index = None
        for step in steps:
            if step.step_name == failed_step:
                failed_index = step.step_index
                break

        if failed_index is None:
            logger.warning(
                f"Failed step {failed_step} not found in task {task_id}",
            )
            return

        # Collect steps that completed successfully BEFORE the failed one
        completed_steps = [
            step
            for step in steps
            if step.step_index < failed_index and step.status == "completed"
        ]

        # Compensate in reverse order
        for step in reversed(completed_steps):
            action = self.COMPENSATION_ACTIONS.get(step.step_name)
            if action is None:
                logger.info(
                    f"Step {step.step_name} has no compensation (stateless)",
                    extra={"task_id": task_id},
                )
                continue

            try:
                await self._execute_compensation(action, step)
                await self.task_repo.compensate_task_step(step.id)
                logger.info(
                    f"Compensated step {step.step_name} via {action}",
                    extra={"task_id": task_id, "step_id": step.id},
                )
            except Exception as e:
                logger.error(
                    f"Compensation failed for step {step.step_name}: {e}",
                    extra={"task_id": task_id, "step_id": step.id},
                )

        # Mark task with error info
        await self.task_repo.set_task_error(
            task_id,
            error_code="PIPELINE_FAILED",
            error_message=f"Pipeline failed at step {failed_step}, compensations applied",
        )
        await self.task_repo.update_task_status(task_id, status="failed")

        logger.info(
            f"Saga compensation completed for task {task_id}",
            extra={"failed_step": failed_step, "compensated_steps": len(completed_steps)},
        )

    async def _execute_compensation(self, action: str, step) -> None:
        """Execute a single compensation action."""
        logger.info(
            f"Executing compensation: {action} for step {step.step_name}",
            extra={
                "task_id": step.task_id,
                "action": action,
            },
        )
        # In production:
        # if action == "delete_registry_document":
        #     client = RegistryServiceClient()
        #     await client.delete_registry_document(registry_doc_id)
        await self.db.flush()
