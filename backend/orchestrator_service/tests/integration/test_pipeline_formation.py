"""
Integration tests for Pipeline 1 (Formation) workflow.

Tests the end-to-end pipeline flow:
1. Create document in DB
2. Start Pipeline 1
3. Advance through all 4 steps (ocr, parser, converter, registry)
4. Verify FSM transitions
5. Verify step logs are created

All tests use async SQLite in-memory and mock service responses.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.fsm import PIPELINE_1_STEPS, PIPELINE_2_STEPS
from app.core.pipeline.orchestrator import PipelineOrchestrator
from app.repositories.document import DocumentRepository
from app.repositories.pipeline import PipelineRepository


@pytest.mark.asyncio
class TestPipeline1Formation:
    """Integration tests for Pipeline 1 (formation)."""

    async def _create_document(self, db_session):
        repo = DocumentRepository(db_session)
        return await repo.create(
            file_hash_sha256="pipeline1_int",
            original_filename="p1_test.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
        )

    async def test_start_pipeline_1_creates_job(self, db_session: AsyncSession):
        """Starting Pipeline 1 creates a PipelineJob and transitions doc to previewing."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)

        job_id = await orchestrator.start_pipeline_1(doc.id)
        assert job_id is not None

        # Check job
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job(job_id)
        assert job is not None
        assert job.document_id == doc.id
        assert job.pipeline_type == "formation"
        assert job.status == "running"
        assert job.total_steps == 4

        # Check document FSM transition
        updated_doc = await orchestrator.doc_repo.get(doc.id)
        assert updated_doc.status == "previewing"

    async def test_pipeline_1_creates_all_step_logs(self, db_session: AsyncSession):
        """Starting Pipeline 1 creates step logs for all 4 steps."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)
        job_id = await orchestrator.start_pipeline_1(doc.id)

        pipeline_repo = PipelineRepository(db_session)
        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        assert len(logs) == 4

        step_names = [log.step_name for log in logs]
        assert step_names == ["ocr", "parser", "converter", "registry"]

        # First step should be running, rest pending
        assert logs[0].status == "running"
        assert all(log.status == "pending" for log in logs[1:])

    async def test_pipeline_1_full_success(self, db_session: AsyncSession):
        """Completing all 4 steps in Pipeline 1 transitions to registry."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)
        job_id = await orchestrator.start_pipeline_1(doc.id)

        # Simulate each step completing in order
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job(job_id)

        for step_name in PIPELINE_1_STEPS:
            if step_name == PIPELINE_1_STEPS[-1]:
                # Simulate the orchestrator being called back
                # We need to call on_step_completed which itself advances
                pass

            await orchestrator.on_step_completed(
                job_id=job_id,
                step_name=step_name,
                result={f"{step_name}_result": "ok"},
            )

        # After all steps: job should be completed
        job = await pipeline_repo.get_job(job_id)
        assert job.status == "completed"

        # Document should be in Pipeline 1 terminal state
        # (Pipeline 2 auto-starts, transitioning registry -> pending_index)
        doc = await orchestrator.doc_repo.get(doc.id)
        assert doc.status in ("registry", "pending_index"), (
            f"Expected registry or pending_index, got {doc.status}"
        )

        # All step logs should be success
        logs = await pipeline_repo.get_step_logs_for_job(job_id)
        for log in logs:
            assert log.status == "success"

    async def test_pipeline_1_step_failure_triggers_retry(self, db_session: AsyncSession):
        """A step failure increments retry count and does not fail the pipeline yet."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)
        job_id = await orchestrator.start_pipeline_1(doc.id)

        # First step (ocr) fails
        await orchestrator.on_step_failed(
            job_id=job_id,
            step_name="ocr",
            error_code="OCR_ERROR",
            error_message="OCR service timed out",
        )

        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job(job_id)

        # Job should still be running (retry pending)
        assert job.status == "running"
        assert job.retry_count == 1

    async def test_pipeline_1_exhaust_retries_fails(self, db_session: AsyncSession):
        """After exhausting retries, pipeline fails and document goes to failed."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)
        job_id = await orchestrator.start_pipeline_1(doc.id)

        # Fail more times than MAX_STEP_RETRIES (default 3)
        for i in range(5):  # Fail many times
            await orchestrator.on_step_failed(
                job_id=job_id,
                step_name="ocr",
                error_code="OCR_ERROR",
                error_message=f"Attempt {i} failed",
            )

        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job(job_id)
        assert job.status == "failed"

        # Document should be in 'failed' state
        doc = await orchestrator.doc_repo.get(doc.id)
        assert doc.status == "failed"
        assert doc.error_code == "OCR_ERROR"

    async def test_pipeline_1_starts_pipeline_2_on_completion(self, db_session: AsyncSession):
        """After Pipeline 1 completes, Pipeline 2 (indexation) auto-starts."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)
        job_id = await orchestrator.start_pipeline_1(doc.id)

        # Complete all Pipeline 1 steps
        for step_name in PIPELINE_1_STEPS:
            await orchestrator.on_step_completed(
                job_id=job_id, step_name=step_name, result={"ok": True}
            )

        # Pipeline 2 should have started
        pipeline_repo = PipelineRepository(db_session)

        # Find the indexation job
        all_jobs = []
        # We need to search for jobs by document type
        p2_jobs = await pipeline_repo.get_queued_jobs(pipeline_type="indexation")
        # If completed, it won't be "queued" — check all by iterating
        # Actually after on_step_completed the P2 job is created and runs immediately
        # Let's check the document's pipeline_2_status or find job directly

        # Pipeline 2 job should exist (just check doc went to pending_index or beyond)
        doc = await orchestrator.doc_repo.get(doc.id)

        # After Pipeline 1 finishes (registry), on_step_completed auto-triggers Pipeline 2
        # which transitions doc from registry -> pending_index
        assert doc.status in ("pending_index", "indexing", "indexed"), (
            f"Doc should be in Pipeline 2 state, got {doc.status}"
        )

    async def test_pipeline_2_full_success(self, db_session: AsyncSession):
        """Pipeline 2 completes successfully and document reaches 'indexed'."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)

        # Precondition: doc must be in 'registry' state to start Pipeline 2
        await orchestrator.doc_repo.fsm_transition(doc.id, "previewing")
        await orchestrator.doc_repo.fsm_transition(doc.id, "awaiting_decision")
        await orchestrator.doc_repo.fsm_transition(doc.id, "parsing")
        await orchestrator.doc_repo.fsm_transition(doc.id, "validation")
        await orchestrator.doc_repo.fsm_transition(doc.id, "ready_for_promotion")
        await orchestrator.doc_repo.fsm_transition(doc.id, "approved")
        await orchestrator.doc_repo.fsm_transition(doc.id, "registry")

        p2_job_id = await orchestrator.start_pipeline_2(doc.id)

        # Complete the single RAG Index step
        await orchestrator.on_step_completed(
            job_id=p2_job_id,
            step_name="rag_index",
            result={"chunks": 42},
        )

        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job(p2_job_id)
        assert job.status == "completed"

        doc = await orchestrator.doc_repo.get(doc.id)
        assert doc.status == "indexed"

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    async def test_start_pipeline_nonexistent_doc(self, db_session: AsyncSession):
        """Starting pipeline on non-existent doc raises ValueError."""
        orchestrator = PipelineOrchestrator(db_session)
        with pytest.raises(ValueError, match="not found"):
            await orchestrator.start_pipeline_1("no-such-doc")

    async def test_on_step_completed_unknown_job(self, db_session: AsyncSession):
        """Calling on_step_completed with unknown job does not crash."""
        orchestrator = PipelineOrchestrator(db_session)
        await orchestrator.on_step_completed("bad-job", "ocr", {"ok": True})

    async def test_cleanup_stale_jobs(self, db_session: AsyncSession):
        """cleanup_stale_jobs marks stale jobs as dead."""
        doc = await self._create_document(db_session)
        orchestrator = PipelineOrchestrator(db_session)
        job_id = await orchestrator.start_pipeline_1(doc.id)

        # Manually set started_at far in the past
        from datetime import datetime, timedelta, timezone
        pipeline_repo = PipelineRepository(db_session)
        job = await pipeline_repo.get_job_for_update(job_id)
        job.started_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db_session.flush()

        cleaned = await orchestrator.cleanup_stale_jobs()
        assert cleaned >= 1

        # Doc should be failed
        doc = await orchestrator.doc_repo.get(doc.id)
        assert doc.status == "failed"
