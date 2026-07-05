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
from app.repositories.external_task_repo import ExternalTaskRepository

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
    Step 1: RAG Index — submit to RAG Builder, then exit.

    Uses Redis advisory lock (P2I-7) to prevent double indexing.
    BackgroundTaskPoller handles waiting for completion and notifying the orchestrator.
    """
    lock_key = f"indexation:lock:{document_id}"
    lock_ttl = 3600  # 1 hour max

    try:
        # Try to acquire advisory lock via Redis (atomic SET NX EX — P2I-7)
        import redis as sync_redis
        r = sync_redis.from_url(settings.REDIS_URL)
        acquired = r.set(lock_key, "1", nx=True, ex=lock_ttl)
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
            _run_async(client.close())

            # Save to external_tasks — Poller will track completion and do integrity check
            async def _save_external():
                async with get_db_context() as db:
                    repo = ExternalTaskRepository(db)
                    await repo.create(
                        orchestrator_task_id=int(job_id),
                        step_name="rag_index",
                        external_service="rag_builder",
                        external_task_id=int(document_id),
                        context_data={
                            "job_id": job_id,
                            "document_id": document_id,
                            "sections_count": len(sections),
                        },
                    )
                    await db.commit()

            _run_async(_save_external())

            # Release lock after successful submission — Poller handles completion
            _release_lock(lock_key)

            logger.info(
                f"RAG Build submitted for doc {document_id}, will be polled",
            )
            return {"status": "pending", "step": "rag_index", "job_id": job_id}

        except Exception as svc_err:
            logger.error(f"RAG Builder call failed: {svc_err}")
            _release_lock(lock_key)
            raise

    except Exception as exc:
        logger.error(f"RAG Index submission failed: {exc}")
        _release_lock(lock_key)
        _run_async(
            _notify_step_failed(job_id, "rag_index", "RAG_INDEX_ERROR", str(exc))
        )
        raise self.retry(exc=exc)


def _release_lock(lock_key: str) -> None:
    """Release a Redis advisory lock."""
    try:
        import redis as sync_redis
        r = sync_redis.from_url(settings.REDIS_URL)
        r.delete(lock_key)
        r.close()
    except Exception:
        pass


@celery_app.task(
    bind=True, max_retries=2, default_retry_delay=30,
    name="tasks.pipeline.run_reprocess_step"
)
def run_reprocess_step(self, task_id: int, document_id: str):
    """
    Reprocess a document (P2I-9).

    Deletes existing index, triggers re-indexation via RAG Builder, then exits.
    BackgroundTaskPoller handles waiting for completion and notifying.
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
        _run_async(
            rag.index_document(
                document_id=document_id,
                sections=sections,
            )
        )
        _run_async(rag.close())

        # Save to external_tasks — Poller will track completion
        async def _save_external():
            async with get_db_context() as db:
                repo = ExternalTaskRepository(db)
                await repo.create(
                    orchestrator_task_id=task_id,
                    step_name="reprocess",
                    external_service="rag_builder",
                    external_task_id=int(document_id),
                    context_data={
                        "task_id": task_id,
                        "document_id": document_id,
                    },
                )
                await db.commit()

        _run_async(_save_external())

        logger.info(f"Reprocess submitted for doc {document_id}, will be polled")
        return {"status": "pending", "step": "reprocess", "task_id": task_id}

    except Exception as exc:
        logger.error(f"Reprocess submission failed: {exc}")
        _run_async(_notify_step_failed(task_id, "reprocess", "REPROCESS_ERROR", str(exc)))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30, name="tasks.pipeline.run_activate_document_step")
def run_activate_document_step(self, job_id: str, document_id: int):
    """
    Background task: check RAG Builder status, then defer to Poller if needed.

    BackgroundTaskPoller handles waiting for completion and activating the document.
    """
    logger.info(f"Background activation for document {document_id} (job={job_id})")
    from app.services.rag_client import RAGBuilderClient

    try:
        rag = RAGBuilderClient()
        # Check status once (no longpoll) — if already done, handle immediately
        status_result = _run_async(rag.get_build_status(
            document_id=document_id, longpoll=0,
        ))
        _run_async(rag.close())

        final_status = status_result.get("status", "")

        if final_status == "indexed":
            # Already done — activate directly
            return _activate_document_sync(document_id)

        elif final_status == "failed":
            logger.error(
                f"Background activation: RAG build already failed for doc {document_id}, "
                f"staying in validating",
                extra={"status_result": status_result},
            )
            return {"status": "build_failed", "document_id": document_id}

        else:
            # Still indexing — defer to Poller
            async def _save_external():
                async with get_db_context() as db:
                    repo = ExternalTaskRepository(db)
                    await repo.create(
                        orchestrator_task_id=int(job_id),
                        step_name="activate",
                        external_service="rag_builder",
                        external_task_id=int(document_id),
                        context_data={
                            "document_id": document_id,
                        },
                    )
                    await db.commit()

            _run_async(_save_external())
            logger.info(
                f"Background activation deferred to Poller for doc {document_id}",
            )
            return {"status": "pending", "document_id": document_id}

    except Exception as e:
        logger.error(f"Background activation submission failed for doc {document_id}: {e}")
        raise self.retry(exc=e)


def _activate_document_sync(document_id: int) -> dict:
    """Activate document synchronously (called from Celery task when build is already done)."""
    from app.services.registry_client import RegistryServiceClient
    from app.services.rag_client import RAGBuilderClient

    try:
        rag = RAGBuilderClient()
        check_result = _run_async(rag.check_index(document_id=document_id))
        _run_async(rag.close())

        integrity_ok = check_result.get("integrity_ok", False)
        if not integrity_ok:
            logger.warning(
                f"Background activation: integrity check failed for doc {document_id}, "
                f"staying in validating",
                extra={"check_result": check_result},
            )
            return {"status": "integrity_failed", "document_id": document_id}

        registry = RegistryServiceClient()
        _run_async(registry.update_document_status(
            document_id=document_id,
            status="active",
        ))
        _run_async(registry.close())
        logger.info(f"Document {document_id} activated")
        return {"status": "active", "document_id": document_id}

    except Exception as e:
        logger.error(f"Background activation failed for doc {document_id}: {e}")
        raise


async def _notify_step_completed(job_id: str, step_name: str, result: dict):
    async with get_db_context() as db:
        try:
            task_id = int(job_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid job_id for _notify_step_completed: {job_id}")
            return
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_completed(task_id, step_name, result)


async def _notify_step_failed(
    job_id: str, step_name: str, error_code: str, error_message: str
):
    async with get_db_context() as db:
        try:
            task_id = int(job_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid job_id for _notify_step_failed: {job_id}")
            return
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.on_step_failed(task_id, step_name, error_code, error_message)


# ------------------------------------------------------------------
#  External task handlers (used by BackgroundTaskPoller)
# ------------------------------------------------------------------


async def get_rag_build_status(document_id: str) -> dict:
    """Get current RAG Builder build status for a document."""
    from app.services.rag_client import RAGBuilderClient
    client = RAGBuilderClient()
    try:
        return await client.get_build_status(document_id=document_id)
    finally:
        await client.close()


async def process_rag_index_result(
    job_id: str, document_id: str, status_result: dict,
) -> None:
    """Handle RAG index completion: integrity check + notify orchestrator.

    Called by BackgroundTaskPoller when external task for rag_index completes.
    """
    chunks_count = status_result.get("chunks_count", 0)
    final_status = status_result.get("status", "indexed")

    # Integrity check (P2I-2)
    if final_status == "failed":
        error_msg = status_result.get("errors", "RAG Build failed")
        await _notify_step_failed(job_id, "rag_index", "INTEGRITY_CHECK_FAILED", error_msg)
        return

    integrity_ok = True
    integrity_detail = ""
    check_result = None
    try:
        from app.services.rag_client import RAGBuilderClient
        rag_check = RAGBuilderClient()
        check_result = await rag_check.check_index(document_id=document_id)
        await rag_check.close()
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

    if not integrity_ok:
        await _notify_step_failed(
            job_id, "rag_index", "INTEGRITY_CHECK_FAILED", integrity_detail,
        )
        return

    # Check for partially_indexed (P2I-1)
    # expected_count берётся из /check эндпоинта, chunks_count — из /status
    check_data = check_result or {}
    expected_count = check_data.get("expected_count", chunks_count)
    if expected_count > 0 and chunks_count < expected_count:
        logger.warning(
            f"Partially indexed: {chunks_count}/{expected_count} chunks for doc {document_id}",
        )
        await _notify_step_completed(
            job_id, "rag_index",
            {**status_result, "status": TaskStatus.PARTIALLY_INDEXED.value}
        )
    else:
        await _notify_step_completed(job_id, "rag_index", status_result)


async def process_reprocess_result(
    task_id: int, document_id: str, status_result: dict,
) -> None:
    """Handle reprocess completion: notify orchestrator."""
    final_status = status_result.get("status", "indexed")
    status_result["status"] = final_status
    await _notify_step_completed(task_id, "reprocess", status_result)


async def process_activate_result(document_id: int) -> None:
    """Handle activate completion: integrity check + activate document.

    Called by BackgroundTaskPoller when external task for activate completes.
    """
    from app.services.rag_client import RAGBuilderClient
    from app.services.registry_client import RegistryServiceClient

    rag = RAGBuilderClient()
    try:
        check_result = await rag.check_index(document_id=document_id)
    finally:
        await rag.close()

    integrity_ok = check_result.get("integrity_ok", False)
    if not integrity_ok:
        logger.warning(
            f"Poller activation: integrity check failed for doc {document_id}, "
            f"staying in validating",
            extra={"check_result": check_result},
        )
        return

    registry = RegistryServiceClient()
    try:
        await registry.update_document_status(
            document_id=document_id,
            status="active",
        )
    finally:
        await registry.close()

    logger.info(f"Document {document_id} activated via Poller")
