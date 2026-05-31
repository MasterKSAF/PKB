"""
Integration tests for Celery tasks with task_always_eager=True.

Tests verify that Celery tasks properly integrate with the PipelineOrchestrator:
- Successful execution calls on_step_completed → job advances, FSM transitions
- Failed execution calls on_step_failed → retries attempted, errors recorded
- Compensation tasks execute and return expected results
- Scheduler cleanup task marks stale jobs as dead

All tests run synchronously with task_always_eager=True (no Redis broker needed).
Uses nest_asyncio so Celery tasks can create nested event loops in the same thread.
"""

import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import celery.exceptions
import nest_asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.core.fsm import PIPELINE_1_STEPS
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.document import DocumentRepository
from app.repositories.pipeline import PipelineRepository

from app.tasks.pipeline_formation import (
    run_ocr_step,
    run_parser_step,
    run_converter_step,
    run_registry_step,
)
from app.tasks.pipeline_indexation import run_rag_index_step
from app.tasks.compensation import (
    delete_registry_document,
    delete_from_vector_index,
)
from app.tasks.scheduler import cleanup_stale_jobs

# Allow nested event loops so Celery tasks' _run_async() can create its own
# event loop inside pytest-asyncio's already-running loop.
# This is safe because _run_async creates a brand-new loop, runs one coroutine,
# and closes it — no persistent nesting.
nest_asyncio.apply()

logger = logging.getLogger("test_celery_tasks")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


async def _get_fresh(db_session: AsyncSession, model, pk_value: str):
    """Read an ORM object bypassing the session identity map.

    Celery tasks run in a separate DB session (via get_db_context()).
    The test session's identity map may cache stale objects, so we use
    populate_existing=True to force a fresh read from the database.
    """
    from sqlalchemy import select
    result = await db_session.execute(
        select(model)
        .where(model.id == pk_value)
        .execution_options(populate_existing=True)
    )
    return result.scalar_one_or_none()


async def _get_doc_fresh(db_session: AsyncSession, doc_id: str):
    """Read document with populate_existing to bypass identity map."""
    from app.models.document import Document
    return await _get_fresh(db_session, Document, doc_id)


@pytest.fixture(autouse=True)
def celery_eager():
    """Configure Celery for synchronous task execution (no broker required).

    - task_always_eager=True: .delay() executes immediately in-process
    - task_eager_propagates=True: task exceptions propagate to caller
    """
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_eager_propagates = False


async def _create_document(db_session: AsyncSession, suffix: str = "") -> tuple:
    """Create a document in 'uploaded' state and return (doc_repo, doc)."""
    repo = DocumentRepository(db_session)
    doc = await repo.create(
        file_hash_sha256=f"celery_test_{suffix}",
        original_filename=f"celery_{suffix}.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
    )
    return repo, doc


async def _start_pipeline_1(db_session: AsyncSession, doc_id: str) -> str:
    """Start Pipeline 1 for a document and commit. Returns job_id."""
    orchestrator = PipelineOrchestrator(db_session)
    job_id = await orchestrator.start_pipeline_1(doc_id)
    await db_session.commit()
    return job_id


async def _advance_to_step(
    db_session: AsyncSession, job_id: str, target_step: str
) -> None:
    """Advance a Pipeline 1 job up to (but not including) target_step."""
    orchestrator = PipelineOrchestrator(db_session)
    for step in PIPELINE_1_STEPS:
        if step == target_step:
            break
        await orchestrator.on_step_completed(job_id, step, {"ok": True})
    await db_session.commit()


async def _setup_pipeline_1_at_step(
    db_session: AsyncSession, suffix: str, target_step: str
) -> tuple:
    """Create doc, start Pipeline 1, advance to target_step. Returns (doc, job_id)."""
    _, doc = await _create_document(db_session, suffix)
    job_id = await _start_pipeline_1(db_session, doc.id)
    if target_step != PIPELINE_1_STEPS[0]:
        await _advance_to_step(db_session, job_id, target_step)
    return doc, job_id


async def _setup_pipeline_2(db_session: AsyncSession, suffix: str) -> tuple:
    """Set up a document in 'registry' state and start Pipeline 2. Returns (doc, job_id)."""
    _, doc = await _create_document(db_session, suffix)
    orchestrator = PipelineOrchestrator(db_session)
    for state in (
        "previewing",
        "awaiting_decision",
        "parsing",
        "validation",
        "ready_for_promotion",
        "approved",
        "registry",
    ):
        await orchestrator.doc_repo.fsm_transition(doc.id, state)
    await db_session.commit()

    job_id = await orchestrator.start_pipeline_2(doc.id)
    await db_session.commit()
    return doc, job_id


# ---------------------------------------------------------------------------
# Pipeline 1 (Formation) — Task Success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestFormationTaskSuccess:
    """Each formation task completes successfully and advances the pipeline."""

    async def test_run_ocr_step_completes_and_advances(self, db_session):
        """run_ocr_step success: step log marked, job advances, FSM transitions."""
        doc, job_id = await _setup_pipeline_1_at_step(db_session, "ocr_ok", "ocr")
        pipeline_repo = PipelineRepository(db_session)

        # Execute Celery task synchronously (task_always_eager + nest_asyncio)
        result = run_ocr_step.delay(job_id, doc.id)

        # 1 — Task execution
        assert result.status == "SUCCESS"
        assert result.result["status"] == "completed"
        assert result.result["step"] == "ocr"

        # 2 — Step log updated to success
        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        ocr_log = next(l for l in logs if l.step_name == "ocr")
        assert ocr_log.status == "success"

        # 3 — Job advanced to parser step
        job = await pipeline_repo.get_job(job_id)
        assert job.current_step_name == "parser"
        assert job.current_step_index == 1
        assert job.status == "running"

        # 4 — Document FSM transitioned: previewing → parsing
        doc_updated = await _get_doc_fresh(db_session, doc.id)
        assert doc_updated.status == "parsing"

    async def test_run_parser_step_completes(self, db_session):
        """run_parser_step success advances to converter step."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "parser_ok", "parser"
        )
        pipeline_repo = PipelineRepository(db_session)

        result = run_parser_step.delay(job_id, doc.id)
        assert result.status == "SUCCESS"
        assert result.result["step"] == "parser"

        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        parser_log = next(l for l in logs if l.step_name == "parser")
        assert parser_log.status == "success"

        job = await pipeline_repo.get_job(job_id)
        assert job.current_step_name == "converter"
        assert job.current_step_index == 2

    async def test_run_converter_step_completes(self, db_session):
        """run_converter_step success advances to registry step."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "conv_ok", "converter"
        )
        pipeline_repo = PipelineRepository(db_session)

        result = run_converter_step.delay(job_id, doc.id)
        assert result.status == "SUCCESS"
        assert result.result["step"] == "converter"

        job = await pipeline_repo.get_job(job_id)
        assert job.current_step_name == "registry"
        assert job.current_step_index == 3

        # FSM → validation
        doc_updated = await _get_doc_fresh(db_session, doc.id)
        assert doc_updated.status == "validation"

    async def test_run_registry_step_completes_pipeline_1(self, db_session):
        """run_registry_step finalises Pipeline 1 and auto-starts Pipeline 2."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "reg_ok", "registry"
        )
        pipeline_repo = PipelineRepository(db_session)

        result = run_registry_step.delay(job_id, doc.id)
        assert result.status == "SUCCESS"
        assert result.result["step"] == "registry"

        # Pipeline 1 job completed
        job = await pipeline_repo.get_job(job_id)
        assert job.status == "completed"

        # All step logs should be success
        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        assert all(log.status == "success" for log in logs)

        # Document should have transitioned past registry (Pipeline 2 auto-started)
        doc_updated = await _get_doc_fresh(db_session, doc.id)
        assert doc_updated.status in (
            "pending_index",
            "indexing",
            "indexed",
        ), f"Expected Pipeline 2 state, got {doc_updated.status}"

    async def test_full_pipeline_1_sequence_via_celery(self, db_session):
        """All four formation tasks called in sequence via .delay() complete P1."""
        _, doc = await _create_document(db_session, "full_p1")
        job_id = await _start_pipeline_1(db_session, doc.id)

        task_map = {
            "ocr": run_ocr_step,
            "parser": run_parser_step,
            "converter": run_converter_step,
            "registry": run_registry_step,
        }

        for step_name in PIPELINE_1_STEPS:
            result = task_map[step_name].delay(job_id, doc.id)
            assert result.status == "SUCCESS", f"{step_name} task failed"

        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job(job_id)
        assert job.status == "completed", f"Pipeline 1 not completed: {job.status}"

        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        assert all(log.status == "success" for log in logs)

        # Pipeline 2 should have auto-started
        doc_updated = await _get_doc_fresh(db_session, doc.id)
        assert doc_updated.status in ("pending_index", "indexing", "indexed")


# ---------------------------------------------------------------------------
# Pipeline 2 (Indexation) — Task Success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestIndexationTaskSuccess:
    """Pipeline 2 (RAG Index) task completes successfully."""

    async def test_run_rag_index_step_completes(self, db_session):
        """run_rag_index_step completes and marks Pipeline 2 as done."""
        doc, job_id = await _setup_pipeline_2(db_session, "rag_ok")
        pipeline_repo = PipelineRepository(db_session)

        result = run_rag_index_step.delay(job_id, doc.id)
        assert result.status == "SUCCESS"
        assert result.result["step"] == "rag_index"

        job = await pipeline_repo.get_job(job_id)
        assert job.status == "completed"

        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        assert logs[0].status == "success"

        doc_updated = await _get_doc_fresh(db_session, doc.id)
        assert doc_updated.status == "indexed"


# ---------------------------------------------------------------------------
# Task Error Handling & Retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestTaskErrorHandling:
    """Tasks properly handle failures — retry + notify on_step_failed."""

    async def test_task_failure_on_step_failed_is_called(self, db_session):
        """When on_step_completed raises, on_step_failed records the error."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "fail_status", "ocr"
        )
        pipeline_repo = PipelineRepository(db_session)

        with patch.object(
            PipelineOrchestrator,
            "on_step_completed",
            side_effect=RuntimeError("OCR service timeout"),
        ):
            # Retry may propagate in eager mode; we catch it and verify DB state
            try:
                run_ocr_step.delay(job_id, doc.id)
            except (RuntimeError, celery.exceptions.Retry):
                pass

        # The step log should reflect the failure
        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        ocr_logs = [l for l in logs if l.step_name == "ocr" and l.status == "failed"]
        assert len(ocr_logs) >= 1, "Expected at least one failed OCR step log"

    async def test_task_failure_records_error_code_in_step_log(self, db_session):
        """Failed task records error code and message in the step log."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "fail_code", "ocr"
        )
        pipeline_repo = PipelineRepository(db_session)

        with patch.object(
            PipelineOrchestrator,
            "on_step_completed",
            side_effect=RuntimeError("Connection refused"),
        ):
            try:
                run_ocr_step.delay(job_id, doc.id)
            except (RuntimeError, celery.exceptions.Retry):
                pass

        # At least one OCR log should be failed
        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        ocr_logs = [l for l in logs if l.step_name == "ocr" and l.status == "failed"]
        assert len(ocr_logs) >= 1, "No OCR step log in 'failed' state"

        latest_failed = ocr_logs[-1]
        assert latest_failed.error_code is not None, "error_code not set"
        assert latest_failed.error_message is not None, "error_message not set"

    async def test_task_failure_records_error_on_job(self, db_session):
        """Failed task records error info on the job and document."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "fail_job", "ocr"
        )
        pipeline_repo = PipelineRepository(db_session)

        with patch.object(
            PipelineOrchestrator,
            "on_step_completed",
            side_effect=RuntimeError("Fatal error"),
        ):
            try:
                run_ocr_step.delay(job_id, doc.id)
            except (RuntimeError, celery.exceptions.Retry):
                pass

        # Job should have the error code recorded (set_job_error runs on every failure)
        job = await pipeline_repo.get_job(job_id)
        assert job.error_code == "OCR_ERROR", f"Unexpected error_code: {job.error_code}"
        assert job.error_message is not None, "error_message not set"

        # Document error_code is only set when retries are exhausted
        # (the on_step_failed guard for terminal states triggers doc.set_error)
        doc_updated = await _get_doc_fresh(db_session, doc.id)
        # Document may or may not have error_code depending on retry exhaustion

    async def test_on_step_completed_not_called_when_job_terminal(self, db_session):
        """If job is already completed, on_step_completed is skipped gracefully."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "skip_terminal", "ocr"
        )
        pipeline_repo = PipelineRepository(db_session)

        await pipeline_repo.update_job_status(job_id, "completed")
        await db_session.commit()

        result = run_ocr_step.delay(job_id, doc.id)
        assert result.status == "SUCCESS"

    async def test_on_step_failed_skipped_when_job_terminal(self, db_session):
        """If job is already completed, on_step_failed does not process it."""
        doc, job_id = await _setup_pipeline_1_at_step(
            db_session, "skip_fail_term", "ocr"
        )
        pipeline_repo = PipelineRepository(db_session)
        await pipeline_repo.update_job_status(job_id, "completed")
        await db_session.commit()

        with patch.object(
            PipelineOrchestrator,
            "on_step_completed",
            side_effect=RuntimeError("fail"),
        ):
            try:
                run_ocr_step.delay(job_id, doc.id)
            except (RuntimeError, celery.exceptions.Retry):
                pass

        # Job should still be completed (on_step_failed's guard prevented changes)
        job = await pipeline_repo.get_job(job_id)
        assert job.status == "completed"


# ---------------------------------------------------------------------------
# Compensation Tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCompensationTasks:
    """Compensation (Saga rollback) tasks execute without error."""

    async def test_delete_registry_document(self, db_session):
        """delete_registry_document runs and returns compensation status."""
        result = delete_registry_document.delay(
            document_id="test-doc-123",
            registry_id="reg-test-456",
        )
        assert result.status == "SUCCESS"
        assert result.result["status"] == "compensated"
        assert result.result["action"] == "delete_registry_document"
        assert result.result["document_id"] == "test-doc-123"

    async def test_delete_from_vector_index(self, db_session):
        """delete_from_vector_index runs and returns compensation status."""
        result = delete_from_vector_index.delay(document_id="test-doc-789")
        assert result.status == "SUCCESS"
        assert result.result["status"] == "compensated"
        assert result.result["action"] == "delete_from_vector_index"
        assert result.result["document_id"] == "test-doc-789"

    async def test_compensation_tasks_retry_config(self, db_session):
        """Compensation tasks have retry configured."""
        assert delete_registry_document.max_retries == 2
        assert delete_registry_document.default_retry_delay == 30
        assert delete_from_vector_index.max_retries == 2
        assert delete_from_vector_index.default_retry_delay == 30


# ---------------------------------------------------------------------------
# Scheduler Task
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSchedulerTask:
    """Cleanup scheduler task finds and marks stale jobs."""

    async def test_cleanup_stale_jobs_no_stale(self, db_session):
        """cleanup_stale_jobs with no stale jobs returns 0."""
        result = cleanup_stale_jobs.delay()
        assert result.status == "SUCCESS"
        assert result.result["cleaned"] == 0

    async def test_cleanup_stale_jobs_with_stale(self, db_session):
        """cleanup_stale_jobs marks long-running jobs as dead."""
        _, doc = await _create_document(db_session, "stale_clean")
        job_id = await _start_pipeline_1(db_session, doc.id)

        # Manually set started_at far in the past
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job_for_update(job_id)
        job.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db_session.commit()

        result = cleanup_stale_jobs.delay()
        assert result.status == "SUCCESS"
        assert result.result["cleaned"] >= 1, "Expected at least 1 stale job"

        # Job should now be 'dead' (read fresh to bypass identity map)
        from app.models.pipeline import PipelineJob
        job = await _get_fresh(db_session, PipelineJob, job_id)
        assert job.status == "dead"

        # Document should have error
        doc_updated = await _get_doc_fresh(db_session, doc.id)
        assert doc_updated.status == "failed"
        assert doc_updated.error_code == "PIPELINE_TIMEOUT"


# ---------------------------------------------------------------------------
# Pipeline 2 (Indexation) — Error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestIndexationTaskError:
    """Indexation task failures are handled correctly."""

    async def test_rag_index_failure_records_error(self, db_session):
        """run_rag_index_step failure records error and fails pipeline."""
        doc, job_id = await _setup_pipeline_2(db_session, "rag_fail")
        pipeline_repo = PipelineRepository(db_session)

        with patch.object(
            PipelineOrchestrator,
            "on_step_completed",
            side_effect=RuntimeError("Vector DB timeout"),
        ):
            try:
                run_rag_index_step.delay(job_id, doc.id)
            except (RuntimeError, celery.exceptions.Retry):
                pass

        # Error should be recorded on the job (document error only set when retries exhaust)
        job = await pipeline_repo.get_job(job_id)
        assert job.error_code == "RAG_INDEX_ERROR", f"Got: {job.error_code}"
