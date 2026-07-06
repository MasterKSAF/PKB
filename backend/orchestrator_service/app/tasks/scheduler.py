"""
Scheduled Celery tasks for pipeline housekeeping.
"""

import logging

from app.celery_app import celery_app
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.db.session import get_db_context
from app.tasks.async_utils import run_async, close_async_loop

logger = logging.getLogger("tasks.scheduler")


@celery_app.task(name="app.tasks.scheduler.cleanup_stale_tasks")
def cleanup_stale_tasks():
    """Periodic task: detect and mark stale running jobs as dead.

    Runs every 5 minutes via Celery Beat.
    """
    logger.info("Running stale job cleanup...")

    async def _cleanup():
        async with get_db_context() as db:
            orchestrator = PipelineOrchestrator(db)
            count = await orchestrator.cleanup_stale_tasks()
            return count

    try:
        cleaned = run_async(_cleanup())
        logger.info(f"Stale job cleanup complete: {cleaned} jobs marked as dead")
        return {"cleaned": cleaned}
    finally:
        close_async_loop()


@celery_app.task(name="app.tasks.scheduler.integrity_check")
def integrity_check():
    """Background integrity check for indexed documents (P2I-2)."""
    logger.info("Running background integrity check...")

    async def _check():
        from app.repositories.pipeline import TaskRepository
        from app.services.rag_client import RAGBuilderClient

        async with get_db_context() as db:
            repo = TaskRepository(db)
            tasks = await repo.get_recently_indexed_tasks(max_hours=24)

        checked = 0
        failed = 0
        for task in tasks:
            client = RAGBuilderClient()
            try:
                doc_id = str(task.document_id or task.draft_id)
                result = await client.check_index(doc_id)

                if not result.get("integrity_ok", True):
                    logger.error(
                        f"Background check failed for task {task.id} (doc={doc_id}): "
                        f"{result.get('indexed_count', 0)}/"
                        f"{result.get('expected_count', 0)}",
                    )
                    async with get_db_context() as db2:
                        repo2 = TaskRepository(db2)
                        await repo2.update_task_status(
                            task.id, status="failed",
                        )
                        await repo2.set_task_error(
                            task.id,
                            "INTEGRITY_CHECK_FAILED",
                            f"Background check: "
                            f"{result.get('indexed_count', 0)}/"
                            f"{result.get('expected_count', 0)} chunks",
                        )
                    failed += 1
                checked += 1
            except Exception as e:
                logger.warning(f"Background check error for task {task.id}: {e}")
                checked += 1
            finally:
                await client.close()

        logger.info(f"Background check: {checked} checked, {failed} failed")
        return {"checked": checked, "failed": failed}

    try:
        return run_async(_check())
    finally:
        close_async_loop()


@celery_app.task(name="app.tasks.scheduler.drain_pipeline_queue")
def drain_pipeline_queue():
    """Periodic task: process queued pipeline tasks (safety net).

    Если триггер завершения задачи не сработал, Beat scheduler
    запускает ожидающие задачи в течение 2 минут.
    """
    logger.info("Running pipeline queue drain...")

    async def _drain():
        async with get_db_context() as db:
            orchestrator = PipelineOrchestrator(db)
            await orchestrator._drain_queue()

    try:
        run_async(_drain())
        logger.info("Pipeline queue drain complete")
        return {"drained": True}
    finally:
        close_async_loop()
