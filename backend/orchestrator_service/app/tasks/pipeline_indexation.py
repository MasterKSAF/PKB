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
from app.core.fsm import TaskStatus
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

    Uses Redis advisory lock (P2I-7) to prevent double indexing.
    In production: calls RAG Builder Service to chunk text.
    Has side-effects, so Saga compensation needed.
    """
    lock_key = f"indexation:lock:{document_id}"
    lock_ttl = 3600  # 1 hour max

    try:
        # Try to acquire advisory lock via Redis
        import redis as sync_redis
        r = sync_redis.from_url(settings.REDIS_URL)
        acquired = r.setnx(lock_key, "1")
        if acquired:
            r.expire(lock_key, lock_ttl)
        r.close()

        if not acquired:
            logger.warning(
                f"Indexation already in progress for document {document_id}, "
                f"skipping (advisory lock held)",
            )
            return {"status": "skipped", "reason": "lock_held", "document_id": document_id}

        logger.info(f"RAG Index step started: job={job_id} doc={document_id}")

        # --- Real RAG Builder call (not mock) ---
        try:
            from app.services.rag_client import RAGBuilderClient
            client = RAGBuilderClient()
            result = _run_async(client.index_document(document_id=document_id))
            _run_async(client.close())
        except Exception as svc_err:
            logger.error(f"RAG Builder call failed: {svc_err}")
            raise

        # Check for partially_indexed (P2I-1)
        indexed_count = result.get("indexed_count", 0)
        expected_count = result.get("expected_count", indexed_count)

        # --- Integrity check (P2I-2) ---
        integrity_ok = True
        integrity_detail = ""
        try:
            rag_check = RAGBuilderClient()
            check_result = _run_async(rag_check.check_index(document_id=document_id))
            _run_async(rag_check.close())
            integrity_ok = check_result.get("integrity_ok", True)
            if not integrity_ok:
                integrity_detail = (
                    f"Integrity check failed: "
                    f"indexed={check_result.get('indexed_count', 0)}/"
                    f"expected={check_result.get('expected_count', 0)}"
                )
                logger.error(integrity_detail, extra={"document_id": document_id})
        except Exception as integrity_err:
            logger.warning(
                f"Integrity check call failed (non-fatal): {integrity_err}",
                extra={"document_id": document_id},
            )

        # Inline check: if index returned 0 but expected > 0
        if expected_count > 0 and indexed_count == 0:
            integrity_ok = False
            integrity_detail = (
                f"Index integrity check failed: 0/{expected_count} chunks indexed"
            )

        if not integrity_ok:
            error_msg = integrity_detail or "Integrity check failed"
            logger.error(error_msg, extra={"document_id": document_id,
                                           "job_id": job_id})
            _run_async(_notify_step_failed(
                job_id, "rag_index",
                "INTEGRITY_CHECK_FAILED",
                error_msg,
            ))
            # Release lock
            try:
                r = sync_redis.from_url(settings.REDIS_URL)
                r.delete(lock_key)
                r.close()
            except Exception:
                pass
            return {
                "status": "failed",
                "step": "rag_index",
                "job_id": job_id,
                "error_code": "INTEGRITY_CHECK_FAILED",
                "error_message": error_msg,
            }

        if expected_count > 0 and indexed_count < expected_count:
            logger.warning(
                f"Partially indexed: {indexed_count}/{expected_count} chunks for doc {document_id}",
            )
            _run_async(_notify_step_completed(
                job_id, "rag_index",
                {**result, "status": TaskStatus.PARTIALLY_INDEXED.value}
            ))
        else:
            _run_async(_notify_step_completed(job_id, "rag_index", result))

        logger.info(f"RAG Index step completed: job={job_id}")

        # Release lock on success
        try:
            r = sync_redis.from_url(settings.REDIS_URL)
            r.delete(lock_key)
            r.close()
        except Exception:
            pass

        status = TaskStatus.PARTIALLY_INDEXED.value if (
            expected_count > 0 and indexed_count < expected_count
        ) else "completed"
        return {"status": status, "step": "rag_index", "job_id": job_id,
                "indexed_count": indexed_count, "expected_count": expected_count}

    except Exception as exc:
        logger.error(f"RAG Index step failed: {exc}")
        # Release lock on failure too
        try:
            r = sync_redis.from_url(settings.REDIS_URL)
            r.delete(lock_key)
            r.close()
        except Exception:
            pass
        _run_async(
            _notify_step_failed(job_id, "rag_index", "RAG_INDEX_ERROR", str(exc))
        )
        raise self.retry(exc=exc)


async def _notify_step_completed(job_id: str, step_name: str, result: dict):
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_completed(job_id, step_name, result)


@celery_app.task(
    bind=True, max_retries=2, default_retry_delay=30,
    name="tasks.pipeline.run_reprocess_step"
)
def run_reprocess_step(self, task_id: int, document_id: str):
    """
    Reprocess a document (P2I-9).

    Triggers re-indexation of an already-processed document.
    """
    logger.info(f"Reprocess step started: task={task_id} doc={document_id}")
    try:
        from app.services.rag_client import RAGBuilderClient
        client = RAGBuilderClient()
        # Delete existing index first
        _run_async(client.delete_index(document_id))
        _run_async(client.close())

        # Trigger re-index via RAG Builder
        rag = RAGBuilderClient()
        result = _run_async(rag.index_document(document_id=document_id))
        _run_async(rag.close())

        _run_async(_notify_step_completed(task_id, "reprocess", result))
        logger.info(f"Reprocess completed: task={task_id}")
        return {"status": "completed", "step": "reprocess", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Reprocess failed: {exc}")
        _run_async(_notify_step_failed(task_id, "reprocess", "REPROCESS_ERROR", str(exc)))
        raise self.retry(exc=exc)


async def _notify_step_failed(
    job_id: str, step_name: str, error_code: str, error_message: str
):
    async with get_db_context() as db:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_failed(job_id, step_name, error_code, error_message)
