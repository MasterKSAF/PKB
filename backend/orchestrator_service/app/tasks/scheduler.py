"""
Scheduled Celery tasks for pipeline housekeeping.
"""

import asyncio
import logging

from app.celery_app import celery_app
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.db.session import get_db_context

logger = logging.getLogger("tasks.scheduler")


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.scheduler.cleanup_stale_jobs")
def cleanup_stale_jobs():
    """Periodic task: detect and mark stale running jobs as dead.

    Runs every 5 minutes via Celery Beat.
    """
    logger.info("Running stale job cleanup...")

    async def _cleanup():
        async with get_db_context() as db:
            orchestrator = PipelineOrchestrator(db)
            count = await orchestrator.cleanup_stale_jobs()
            return count

    cleaned = _run_async(_cleanup())
    logger.info(f"Stale job cleanup complete: {cleaned} jobs marked as dead")
    return {"cleaned": cleaned}
