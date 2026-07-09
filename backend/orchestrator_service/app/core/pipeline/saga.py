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
        "rag_index": "delete_from_vector_index",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)

    async def compensate(
        self, task_id: int, failed_step: str, task=None
    ) -> None:
        """Run compensation for all completed steps before the failed one,
        and also for the failed step itself if it has side-effects.

        Args:
            task_id: ID задачи
            failed_step: Имя шага, на котором произошла ошибка
            task: Объект Task (опционально). Если передан, используется для
                  получения draft_id/document_id вместо lazy-load через step.task
                  (предотвращает MissingGreenlet в async SQLAlchemy).
        """
        logger.info(
            f"Starting compensation for task after {failed_step} failure",
            extra={"task_id": task_id, "failed_step": failed_step},
        )
        steps = await self.task_repo.get_task_steps(task_id)

        # Find the index and object of the failed step
        failed_index = None
        failed_step_obj = None
        for step in steps:
            if step.step_name == failed_step:
                failed_index = step.step_index
                failed_step_obj = step
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
                await self._execute_compensation(action, step, task=task)
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

        # Also compensate the failed step itself if it has side-effects
        # (e.g. rag_index may have partial chunks that need cleanup)
        failed_action = self.COMPENSATION_ACTIONS.get(failed_step)
        if failed_action is not None and failed_step_obj is not None:
            try:
                await self._execute_compensation(failed_action, failed_step_obj, task=task)
                await self.task_repo.compensate_task_step(failed_step_obj.id)
                logger.info(
                    f"Compensated failed step {failed_step} via {failed_action}",
                    extra={"task_id": task_id, "step_id": failed_step_obj.id},
                )
            except Exception as e:
                logger.error(
                    f"Compensation failed for failed step {failed_step}: {e}",
                    extra={"task_id": task_id, "step_id": failed_step_obj.id},
                )

        # Mark task with error info
        await self.task_repo.set_task_error(
            task_id,
            error_code="PIPELINE_FAILED",
            error_message=f"Pipeline failed at step {failed_step}, compensations applied",
        )
        await self.task_repo.update_task_status(task_id, status="failed")

        # If a document was created (e.g. by approve_draft) before the pipeline failed,
        # mark it as failed so it doesn't stay in "uploaded" limbo.
        doc_id = getattr(task, 'document_id', None) if task else None
        if doc_id:
            try:
                from app.services.registry_client import RegistryServiceClient
                reg = RegistryServiceClient()
                try:
                    await reg.update_document_status(
                        document_id=doc_id,
                        status="failed",
                    )
                    logger.info(
                        f"Document {doc_id} marked as failed after pipeline failure",
                        extra={"task_id": task_id, "failed_step": failed_step},
                    )
                finally:
                    await reg.close()
            except Exception as e:
                logger.warning(
                    f"Failed to mark document {doc_id} as failed: {e}",
                    extra={"task_id": task_id},
                )

        logger.info(
            f"Saga compensation completed for task {task_id}",
            extra={"failed_step": failed_step, "compensated_steps": len(completed_steps)},
        )

    async def _execute_compensation(
        self, action: str, step, task=None
    ) -> None:
        """Execute a single compensation action synchronously.

        Вызывает API напрямую (не через Celery), чтобы гарантировать
        выполнение компенсации независимо от состояния Celery workers.

        Actions:
        - delete_registry_document  → удаление документа из Registry
        - delete_from_vector_index  → удаление чанков из векторного индекса

        Args:
            task: Объект Task (опционально). Используется для получения
                  draft_id/document_id без lazy-load через step.task,
                  который вызывает MissingGreenlet в async SQLAlchemy.
        """
        logger.info(
            f"Executing compensation: {action} for step {step.step_name}",
            extra={
                "task_id": step.task_id,
                "action": action,
            },
        )

        try:
            if action == "delete_registry_document":
                registry_doc_id = None
                if step.output_data:
                    registry_doc_id = step.output_data.get("registry_id")
                if not registry_doc_id:
                    registry_doc_id = str(
                        getattr(task, "document_id", "0") if task else "0"
                    )

                from app.services.registry_client import RegistryServiceClient
                client = RegistryServiceClient()
                try:
                    await client.delete_document(int(registry_doc_id))
                finally:
                    await client.close()

            elif action == "delete_from_vector_index":
                doc_id = None
                if step.output_data:
                    doc_id = step.output_data.get("document_id")
                if not doc_id:
                    doc_id = str(
                        getattr(task, "document_id", "0") if task else "0"
                    )

                from app.services.rag_client import RAGBuilderClient
                client = RAGBuilderClient()
                try:
                    await client.delete_index(doc_id)
                finally:
                    await client.close()

        except Exception as exc:
            logger.error(
                f"Compensation {action} failed: {exc}",
                extra={"task_id": step.task_id, "step": step.step_name},
            )
            # Пробрасываем исключение — caller решит, фатально ли это
            raise

        await self.db.flush()
