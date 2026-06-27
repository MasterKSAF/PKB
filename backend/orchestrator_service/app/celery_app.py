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
}

if __name__ == "__main__":
    celery_app.start()
