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
from app.core.config import settings
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


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120, name="tasks.pipeline.indexation.run_rag_index_step")
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

        # --- Resolve document_id to int ---
        try:
            doc_id_int = int(document_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid document_id format (not an integer): {document_id}")
            raise ValueError(f"document_id must be an integer, got: {document_id}")

        # --- Fetch sections from Registry (RS-6/RS-7) ---
        try:
            from app.services.registry_client import RegistryServiceClient
            reg_client = RegistryServiceClient()
            sections_response = _run_async(
                reg_client.get_document_sections(document_id=doc_id_int)
            )
            _run_async(reg_client.close())
        except Exception as reg_err:
            logger.error(f"Failed to fetch sections from Registry: {reg_err}")
            raise

        sections_data = sections_response.get("data", {})
        sections = sections_data.get("sections", [])
        logger.info(
            f"Fetched {len(sections)} sections for doc {document_id} from Registry"
        )

        # --- RAG Builder call (POST /rag/build, RS-6/RS-7) ---
        try:
            from app.services.rag_client import RAGBuilderClient
            client = RAGBuilderClient()
            build_result = _run_async(
                client.index_document(
                    document_id=document_id,
                    sections=sections,
                )
            )

            # 202 Accepted — indexing started asynchronously
            if build_result.get("status") == "indexing":
                indexing_txn_id = build_result.get("indexing_txn_id")
                logger.info(
                    f"RAG Build started: doc={document_id} txn={indexing_txn_id}",
                )
                # Poll for final status
                status_result = _run_async(
                    client.get_build_status(document_id=document_id)
                )
            else:
                # Backward compat: some mocks may return synchronous response
                status_result = build_result

            _run_async(client.close())
        except Exception as svc_err:
            logger.error(f"RAG Builder call failed: {svc_err}")
            raise

        # Extract index stats from final status response
        chunks_count = status_result.get("chunks_count", 0)
        final_status = status_result.get("status", "indexed")
        indexed_at = status_result.get("indexed_at")

        # --- Integrity check (P2I-2) ---
        integrity_ok = True
        integrity_detail = ""
        if final_status == "failed":
            integrity_ok = False
            integrity_detail = status_result.get("errors", "RAG Build failed")
        else:
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

        # Inline check: if index returned 0 but sections existed
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

        # Check for partially_indexed (P2I-1)
        expected_count = status_result.get("chunks_count", chunks_count)
        if expected_count > 0 and chunks_count < expected_count:
            logger.warning(
                f"Partially indexed: {chunks_count}/{expected_count} chunks for doc {document_id}",
            )
            _run_async(_notify_step_completed(
                job_id, "rag_index",
                {**status_result, "status": TaskStatus.PARTIALLY_INDEXED.value}
            ))
            return_status = TaskStatus.PARTIALLY_INDEXED.value
        else:
            _run_async(_notify_step_completed(job_id, "rag_index", status_result))
            return_status = final_status

        logger.info(f"RAG Index step completed: job={job_id}")

        # Release lock on success
        try:
            r = sync_redis.from_url(settings.REDIS_URL)
            r.delete(lock_key)
            r.close()
        except Exception:
            pass

        return {
            "status": return_status,
            "step": "rag_index",
            "job_id": job_id,
            "chunks_count": chunks_count,
            "indexed_at": indexed_at,
        }

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

        # Resolve document_id to int
        try:
            doc_id_int = int(document_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid document_id format for reprocess: {document_id}")
            raise ValueError(f"document_id must be an integer, got: {document_id}")

        # Fetch sections from Registry
        try:
            from app.services.registry_client import RegistryServiceClient
            reg_client = RegistryServiceClient()
            sections_response = _run_async(
                reg_client.get_document_sections(document_id=doc_id_int)
            )
            _run_async(reg_client.close())
        except Exception as reg_err:
            logger.warning(f"Failed to fetch sections from Registry for reprocess: {reg_err}")
            sections_response = {"data": {"sections": []}}

        sections = sections_response.get("data", {}).get("sections", [])

        # Trigger re-index via RAG Builder
        rag = RAGBuilderClient()
        build_result = _run_async(
            rag.index_document(
                document_id=document_id,
                sections=sections,
            )
        )

        # Poll for final status (async contract: 202 → polling)
        if build_result.get("status") == "indexing":
            status_result = _run_async(
                rag.get_build_status(document_id=document_id)
            )
        else:
            status_result = build_result

        _run_async(rag.close())

        final_status = status_result.get("status", "indexed")
        _run_async(_notify_step_completed(task_id, "reprocess", status_result))
        logger.info(f"Reprocess completed: task={task_id} status={final_status}")
        return {"status": final_status, "step": "reprocess", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Reprocess failed: {exc}")
        _run_async(_notify_step_failed(task_id, "reprocess", "REPROCESS_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30, name="tasks.pipeline.run_activate_document_step")
def run_activate_document_step(self, document_id: int):
    """
    Background task: poll RAG Builder for async completion, then activate document.

    RAG Builder processes chunks asynchronously. This task:
    1. Calls GET /rag/build/{doc_id}/status (longpoll) until indexed/failed
    2. On indexed: calls GET /rag/build/{doc_id}/check (integrity check)
    3. On integrity_ok: PATCH /api/v1/registry/documents/{id}/status → active
    4. On still indexing/pending: retry (up to 5 times, 30s apart)
    5. On build/integrity failure: stays in "validating" (terminal for this task)
    """
    logger.info(f"Background activation for document {document_id}")
    from app.services.rag_client import RAGBuilderClient
    from app.services.registry_client import RegistryServiceClient

    try:
        rag = RAGBuilderClient()

        # Step 1: Wait for async indexing to complete via longpoll
        status_result = _run_async(rag.get_build_status(
            document_id=document_id, longpoll=15,
        ))
        final_status = status_result.get("status", "")

        if final_status == "indexed":
            # Step 2: Integrity check
            check_result = _run_async(rag.check_index(document_id=document_id))
            _run_async(rag.close())

            integrity_ok = check_result.get("integrity_ok", False)
            if integrity_ok:
                registry = RegistryServiceClient()
                _run_async(registry.update_document_status(
                    document_id=document_id,
                    status="active",
                ))
                _run_async(registry.close())
                logger.info(f"Document {document_id} activated via background task")
                return {"status": "active", "document_id": document_id}
            else:
                logger.warning(
                    f"Background activation: integrity check failed for doc {document_id}, "
                    f"staying in validating",
                    extra={"check_result": check_result},
                )
                return {"status": "integrity_failed", "document_id": document_id}

        elif final_status == "failed":
            _run_async(rag.close())
            logger.error(
                f"Background activation: RAG build failed for doc {document_id}, "
                f"staying in validating",
                extra={"status_result": status_result},
            )
            return {"status": "build_failed", "document_id": document_id}

        else:
            # Still indexing/pending or timeout — retry
            _run_async(rag.close())
            logger.info(
                f"Background activation: RAG build still in progress "
                f"(status={final_status}) for doc {document_id}, will retry",
            )
            # self.retry() raises celery.exceptions.Retry, not Exception
            raise self.retry(
                exc=Exception(f"RAG build not complete: {final_status}"),
            )

    except Exception as e:
        # Covers connectivity errors, timeouts, unexpected failures
        # Don't catch Retry from self.retry() — let it propagate to Celery
        from celery.exceptions import Retry
        if isinstance(e, Retry):
            raise
        logger.error(f"Background activation failed for doc {document_id}: {e}")
        raise self.retry(exc=e)


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
