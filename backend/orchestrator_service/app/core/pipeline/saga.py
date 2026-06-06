"""
Saga Coordinator — manages compensation actions for distributed transactions.

When a pipeline step fails and retries are exhausted, the Saga coordinator
runs compensation (rollback) actions for all previously completed steps,
in reverse order.

Compensation actions are defined per step name.
Steps that are stateless (OCR, Parser) have no compensation.
Steps with side-effects (Registry, RAG Index) have compensations.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.pipeline import PipelineRepository

logger = logging.getLogger("orchestrator.saga")


class SagaCoordinator:
    """Coordinates compensation (rollback) actions for failed pipelines.

    Each compensation is an async call that undoes the side-effect of a step:
    - registry: delete the document registry entry
    - rag_index: delete the document from the vector index
    - converter: no side-effects (pure transformation), no compensation
    - ocr / parser: no side-effects (stateless), no compensation
    """

    # Map step name -> compensation action
    # In a real system, these would be actual service client calls
    COMPENSATION_ACTIONS: dict[str, Optional[str]] = {
        "ocr": None,  # stateless — no compensation
        "parser": None,  # stateless — no compensation
        "converter": None,  # pure transformation — no compensation
        "registry": "delete_registry_document",
        "rag_index": "delete_from_vector_index",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipeline_repo = PipelineRepository(db)

    async def compensate(self, job_id: str, failed_step: str) -> None:
        """Run compensation for all completed steps before the failed one.

        Steps are compensated in reverse order.
        Steps that come AFTER the failed step are not compensated
        (they never ran).
        """
        step_logs = await self.pipeline_repo.get_step_logs_for_job(job_id)

        # Find the index of the failed step
        failed_index = None
        for log in step_logs:
            if log.step_name == failed_step:
                failed_index = log.step_index
                break

        if failed_index is None:
            logger.warning(
                f"Failed step {failed_step} not found in job {job_id}",
            )
            return

        # Collect steps that completed successfully BEFORE the failed one
        completed_steps = [
            log
            for log in step_logs
            if log.step_index < failed_index and log.status == "success"
        ]

        # Compensate in reverse order
        for log in reversed(completed_steps):
            action = self.COMPENSATION_ACTIONS.get(log.step_name)
            if action is None:
                logger.info(
                    f"Step {log.step_name} has no compensation (stateless)",
                    extra={"job_id": job_id},
                )
                continue

            try:
                await self._execute_compensation(action, log)
                await self.pipeline_repo.compensate_step_log(log.id)
                logger.info(
                    f"Compensated step {log.step_name} via {action}",
                    extra={"job_id": job_id, "step_log_id": log.id},
                )
            except Exception as e:
                logger.error(
                    f"Compensation failed for step {log.step_name}: {e}",
                    extra={"job_id": job_id, "step_log_id": log.id},
                )

        # Mark job with error info (compensation completed but pipeline failed)
        await self.pipeline_repo.set_job_error(
            job_id,
            error_code="PIPELINE_FAILED",
            error_message=f"Pipeline failed at step {failed_step}, compensations applied",
        )
        await self.pipeline_repo.update_job_status(job_id, "failed")

        logger.info(
            f"Saga compensation completed for job {job_id}",
            extra={"failed_step": failed_step, "compensated_steps": len(completed_steps)},
        )

    async def _execute_compensation(
        self, action: str, step_log
    ) -> None:
        """Execute a single compensation action.

        In production, this would call the appropriate service client.
        For now, we log the action — actual HTTP calls come when
        service clients are connected.
        """
        logger.info(
            f"Executing compensation: {action} for step {step_log.step_name}",
            extra={
                "job_id": step_log.job_id,
                "document_id": step_log.document_id,
                "action": action,
            },
        )
        # In production:
        # if action == "delete_registry_document":
        #     client = RegistryServiceClient()
        #     await client.delete_registry_document(registry_doc_id)
        # elif action == "delete_from_vector_index":
        #     client = RAGServiceClient()
        #     await client.delete_index(document_id)
        await self.db.flush()
