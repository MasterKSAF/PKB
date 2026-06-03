"""
Pipeline 2 (Indexation) Celery tasks.

Pipeline 2 runs after Pipeline 1 completes successfully.
It indexes the document into the vector search index (RAG).

Steps:
1. RAG Index — chunk document, generate embeddings, store in pgvector
"""

import asyncio
import logging

from app.celery_app import celery_app
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.db.session import get_db_context

logger = logging.getLogger("tasks.pipeline_2")


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120, name="tasks.pipeline.run_rag_index_step")
def run_rag_index_step(self, job_id: str, document_id: str):
    """
    Step 1: RAG Index — chunk document and store embeddings.

    In production: calls RAG Builder Service to chunk text,
    generate embeddings, and store in pgvector.

    Has side-effects (writes to vector DB), so Saga compensation needed.
    """
    try:
        logger.info(f"RAG Index step started: job={job_id} doc={document_id}")

        # Mock: simulate indexing
        mock_result = {
            "document_id": document_id,
            "chunks_indexed": 42,
            "status": "indexed",
        }

        _run_async(_notify_step_completed(job_id, "rag_index", mock_result))

        logger.info(f"RAG Index step completed: job={job_id}")
        return {"status": "completed", "step": "rag_index", "job_id": job_id}

    except Exception as exc:
        logger.error(f"RAG Index step failed: {exc}")
        _run_async(
            _notify_step_failed(job_id, "rag_index", "RAG_INDEX_ERROR", str(exc))
        )
        raise self.retry(exc=exc)


async def _notify_step_completed(job_id: str, step_name: str, result: dict):
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_completed(job_id, step_name, result)


async def _notify_step_failed(
    job_id: str, step_name: str, error_code: str, error_message: str
):
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_failed(job_id, step_name, error_code, error_message)
