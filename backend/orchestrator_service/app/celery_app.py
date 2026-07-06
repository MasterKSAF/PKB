"""
Celery application instance for pipeline task execution.

Configured to use Redis as both broker and result backend.
Task routes separate heavy and light tasks into different queues.
"""

import logging

from celery import Celery

from app.core.config import settings

logger = logging.getLogger("orchestrator.celery")

celery_app = Celery(
    "orchestrator_pipeline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.pipeline_formation",
        "app.tasks.pipeline_indexation",
        "app.tasks.compensation",
        "app.tasks.scheduler",
    ],
)

# Task routing: different queues for different workloads
celery_app.conf.task_routes = {
    "tasks.pipeline.*": {"queue": "pipeline"},
    "tasks.compensation.*": {"queue": "saga"},
}

logger.info(
    "Celery initialized",
    extra={
        "celery_app": celery_app.main,
        "broker": settings.CELERY_BROKER_URL,
        "backend": settings.CELERY_RESULT_BACKEND,
        "queues": ["celery", "pipeline", "saga"],
        "tasks": [
            "tasks.pipeline.run_ocr_preview_step",
            "tasks.pipeline.run_parser_preview_step",
            "tasks.pipeline.run_converter_preview_step",
            "tasks.pipeline.run_converter_full_step",
            "tasks.pipeline.run_registry_step",
            "tasks.pipeline.indexation.run_rag_index_step",
            "tasks.pipeline.indexation.run_reprocess_step",
            "tasks.compensation.delete_registry_document",
            "app.tasks.scheduler.cleanup_stale_jobs",
        ],
    },
)

# Task serialization
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

# Task execution settings
celery_app.conf.task_track_started = True
celery_app.conf.task_acks_late = True  # Re-deliver if worker crashes
celery_app.conf.worker_prefetch_multiplier = 1  # One task at a time per worker

# Schedule cleanup of stale jobs every 5 minutes
celery_app.conf.beat_schedule = {
    "cleanup-stale-jobs": {
        "task": "app.tasks.scheduler.cleanup_stale_jobs",
        "schedule": 300.0,  # every 5 minutes
    },
    "drain-pipeline-queue": {
        "task": "app.tasks.scheduler.drain_pipeline_queue",
        "schedule": 120.0,  # every 2 minutes
    },
}

# ── Worker startup: release stale locks held by this worker ──────────
@celery_app.on_after_finalize.connect
def _release_locks_on_startup(**kwargs):
    """Release stale DB locks held by previous instance of this worker.

    Fires once in the main process before any tasks are consumed.
    Only runs in production (skipped under pytest).
    """
    import sys
    if "pytest" in sys.modules:
        return  # skip during tests

    import os
    from app.repositories.pipeline import TaskRepository
    from app.db.session import get_db_context

    worker_id = os.environ.get("CELERY_WORKER_ID", f"worker-{os.getpid()}")

    async def _cleanup():
        async with get_db_context() as db:
            repo = TaskRepository(db)
            count = await repo.release_locks_by_worker(worker_id)
            if count:
                logger.info(
                    "Released stale locks on worker startup",
                    extra={"worker_id": worker_id, "count": count},
                )
            return count

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_cleanup())
    finally:
        loop.close()


if __name__ == "__main__":
    celery_app.start()
