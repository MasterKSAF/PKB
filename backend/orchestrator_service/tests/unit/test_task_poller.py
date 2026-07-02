"""
Unit tests for BackgroundTaskPoller and handler functions.

Tests verify the actual behavior of:
  - BackgroundTaskPoller._poll_once — dispatch logic
  - BackgroundTaskPoller._process_task — per-task handling
  - BackgroundTaskPoller._check_parser_status — parser polling
  - BackgroundTaskPoller._check_rag_builder_status — RAG Builder polling
  - BackgroundTaskPoller._handle_parser_completed — result fetch + notify
  - BackgroundTaskPoller._handle_rag_builder_completed — per-step dispatch
  - BackgroundTaskPoller._handle_failed — failure notification
  - Timeout safety valve (EXTERNAL_TASK_TIMEOUT)
  - process_parser_full_result — result transformation + notify
  - process_rag_index_result — integrity check + notify
  - process_reprocess_result — notify orchestrator
  - process_activate_result — integrity check + activate
  - _normalize_bbox — edge cases
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo():
    """Mock ExternalTaskRepository."""
    return AsyncMock()


@pytest.fixture
def poller():
    """BackgroundTaskPoller instance with mocked internals."""
    from app.services.task_poller import BackgroundTaskPoller
    p = BackgroundTaskPoller()
    return p


def _make_mock_task(
    task_id: int = 1,
    orchestrator_task_id: str = "42",
    step_name: str = "full_ocr",
    external_service: str = "parser",
    external_task_id: str = "ext-123",
    status: str = "pending",
    created_at: datetime = None,
    context_data: dict = None,
):
    """Helper to create a mock ExternalTask-like object."""
    task = MagicMock()
    task.id = task_id
    task.orchestrator_task_id = orchestrator_task_id
    task.step_name = step_name
    task.external_service = external_service
    task.external_task_id = external_task_id
    task.status = status
    task.created_at = created_at or datetime.now(timezone.utc)
    task.context_data = context_data or {}
    return task


# ============================================================================
#  BackgroundTaskPoller — _process_task dispatch
# ============================================================================

class TestProcessTaskDispatch:
    """_process_task dispatches by external_service correctly."""

    async def test_dispatches_parser_task(self, poller, mock_repo):
        """Parser external_service → _check_parser_status called."""
        poller._check_parser_status = AsyncMock()
        task = _make_mock_task(external_service="parser")
        await poller._process_task(task, mock_repo)
        poller._check_parser_status.assert_awaited_once_with(task, mock_repo)

    async def test_dispatches_rag_builder_task(self, poller, mock_repo):
        """rag_builder external_service → _check_rag_builder_status called."""
        poller._check_rag_builder_status = AsyncMock()
        task = _make_mock_task(external_service="rag_builder")
        await poller._process_task(task, mock_repo)
        poller._check_rag_builder_status.assert_awaited_once_with(task, mock_repo)

    async def test_unknown_service_calls_handle_failed(self, poller, mock_repo):
        """Unknown service → _handle_failed with UNKNOWN_SERVICE."""
        poller._handle_failed = AsyncMock()
        task = _make_mock_task(external_service="unknown_svc")
        await poller._process_task(task, mock_repo)
        poller._handle_failed.assert_awaited_once_with(
            task, mock_repo, "UNKNOWN_SERVICE",
            "Unknown external service: unknown_svc",
        )


# ============================================================================
#  Timeout safety valve
# ============================================================================

class TestTimeoutSafetyValve:
    """EXTERNAL_TASK_TIMEOUT — stale tasks are failed automatically."""

    async def test_expired_task_fails(self, poller, mock_repo):
        """Task older than EXTERNAL_TASK_TIMEOUT → failed with EXTERNAL_TASK_TIMEOUT."""
        poller._handle_failed = AsyncMock()
        old_time = datetime.now(timezone.utc) - timedelta(
            seconds=settings.pipeline.EXTERNAL_TASK_TIMEOUT + 1
        )
        task = _make_mock_task(
            external_service="parser",
            created_at=old_time,
        )
        await poller._process_task(task, mock_repo)
        poller._handle_failed.assert_awaited_once_with(
            task, mock_repo, "EXTERNAL_TASK_TIMEOUT",
            f"External task timed out after {settings.pipeline.EXTERNAL_TASK_TIMEOUT + 1:.0f}s",
        )

    async def test_recent_task_not_failed(self, poller, mock_repo):
        """Task within timeout → NOT failed, dispatches to normal handler."""
        poller._check_parser_status = AsyncMock()
        poller._handle_failed = AsyncMock()
        recent_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        task = _make_mock_task(
            external_service="parser",
            created_at=recent_time,
        )
        await poller._process_task(task, mock_repo)
        poller._check_parser_status.assert_awaited_once()
        poller._handle_failed.assert_not_called()


# ============================================================================
#  Parser status checks
# ============================================================================

class TestCheckParserStatus:
    """_check_parser_status handles completed/failed/processing."""

    def _make_async_client(self, methods: dict = None):
        """Create an AsyncMock-based service client with async methods."""
        client = AsyncMock()
        if methods:
            for name, return_val in methods.items():
                getattr(client, name).return_value = return_val
        client.close = AsyncMock()
        return client

    async def test_completed_triggers_handle_parser_completed(self, poller, mock_repo):
        """Parser status=completed → _handle_parser_completed."""
        client = self._make_async_client({
            "get_status": {"data": {"status": "completed"}},
        })
        with patch("app.services.parser_client.ParserServiceClient", return_value=client):
            poller._handle_parser_completed = AsyncMock()
            task = _make_mock_task()
            await poller._check_parser_status(task, mock_repo)

            poller._handle_parser_completed.assert_awaited_once_with(task, mock_repo)
            client.get_status.assert_awaited_once_with(task.external_task_id)

    async def test_failed_triggers_handle_failed(self, poller, mock_repo):
        """Parser status=failed → _handle_failed with PARSER_FAILED."""
        client = self._make_async_client({
            "get_status": {"data": {"status": "failed", "error": "OOM"}},
        })
        with patch("app.services.parser_client.ParserServiceClient", return_value=client):
            poller._handle_failed = AsyncMock()
            task = _make_mock_task()
            await poller._check_parser_status(task, mock_repo)

            poller._handle_failed.assert_awaited_once_with(
                task, mock_repo, "PARSER_FAILED", "OOM",
            )

    async def test_processing_skips(self, poller, mock_repo):
        """Parser status=processing → no action."""
        client = self._make_async_client({
            "get_status": {"data": {"status": "processing"}},
        })
        with patch("app.services.parser_client.ParserServiceClient", return_value=client):
            poller._handle_parser_completed = AsyncMock()
            poller._handle_failed = AsyncMock()
            task = _make_mock_task()
            await poller._check_parser_status(task, mock_repo)

            poller._handle_parser_completed.assert_not_called()
            poller._handle_failed.assert_not_called()


# ============================================================================
#  RAG Builder status checks
# ============================================================================

class TestCheckRagBuilderStatus:
    """_check_rag_builder_status handles indexed/failed/processing."""

    async def test_indexed_triggers_handle_completed(self, poller, mock_repo):
        """Build status=indexed → _handle_rag_builder_completed."""
        client = AsyncMock()
        client.get_build_status.return_value = {"status": "indexed", "chunks_count": 10}
        client.close = AsyncMock()

        with patch("app.services.rag_client.RAGBuilderClient", return_value=client):
            poller._handle_rag_builder_completed = AsyncMock()
            task = _make_mock_task(external_service="rag_builder")
            await poller._check_rag_builder_status(task, mock_repo)

            poller._handle_rag_builder_completed.assert_awaited_once_with(
                task, mock_repo, {"status": "indexed", "chunks_count": 10},
            )

    async def test_failed_triggers_handle_failed(self, poller, mock_repo):
        """Build status=failed → _handle_failed."""
        client = AsyncMock()
        client.get_build_status.return_value = {"status": "failed", "errors": "timeout"}
        client.close = AsyncMock()

        with patch("app.services.rag_client.RAGBuilderClient", return_value=client):
            poller._handle_failed = AsyncMock()
            task = _make_mock_task(external_service="rag_builder")
            await poller._check_rag_builder_status(task, mock_repo)

            poller._handle_failed.assert_awaited_once_with(
                task, mock_repo, "RAG_BUILD_FAILED", "timeout",
            )

    async def test_processing_skips(self, poller, mock_repo):
        """Build status=indexing → no action."""
        client = AsyncMock()
        client.get_build_status.return_value = {"status": "indexing", "progress": 50}
        client.close = AsyncMock()

        with patch("app.services.rag_client.RAGBuilderClient", return_value=client):
            poller._handle_rag_builder_completed = AsyncMock()
            poller._handle_failed = AsyncMock()
            task = _make_mock_task(external_service="rag_builder")
            await poller._check_rag_builder_status(task, mock_repo)

            poller._handle_rag_builder_completed.assert_not_called()
            poller._handle_failed.assert_not_called()

    async def test_status_completed_also_triggers(self, poller, mock_repo):
        """Build status=completed (legacy) → _handle_rag_builder_completed."""
        client = AsyncMock()
        client.get_build_status.return_value = {"status": "completed"}
        client.close = AsyncMock()

        with patch("app.services.rag_client.RAGBuilderClient", return_value=client):
            poller._handle_rag_builder_completed = AsyncMock()
            task = _make_mock_task(external_service="rag_builder")
            await poller._check_rag_builder_status(task, mock_repo)

            poller._handle_rag_builder_completed.assert_awaited_once()


# ============================================================================
#  _handle_parser_completed — fetch result + transform + notify
# ============================================================================

class TestHandleParserCompleted:
    """_handle_parser_completed fetches result, transforms, notifies, deletes."""

    async def test_fetches_and_processes_result(self, poller, mock_repo):
        """Gets parser result, calls process_parser_full_result, deletes task."""
        client = AsyncMock()
        client.get_result.return_value = {
            "data": {"sections": [{"id": 1, "content": "test"}]},
        }
        client.close = AsyncMock()

        with patch("app.services.parser_client.ParserServiceClient", return_value=client), \
             patch("app.tasks.pipeline_formation.process_parser_full_result") as mock_process:
            task = _make_mock_task(
                step_name="full_ocr",
                context_data={"draft_id": 10, "file_key": "file.pdf"},
            )
            await poller._handle_parser_completed(task, mock_repo)

            # Verify result was fetched
            client.get_result.assert_awaited_once_with(task.external_task_id)

            # Verify transformation + notification was called with correct args
            mock_process.assert_awaited_once_with(
                task_id=int(task.orchestrator_task_id),
                draft_id=10,
                file_key="file.pdf",
                full_parser_result={"sections": [{"id": 1, "content": "test"}]},
            )

            # Verify external task record is deleted
            mock_repo.delete.assert_awaited_once_with(task.id)


# ============================================================================
#  _handle_rag_builder_completed — per-step dispatch
# ============================================================================

class TestHandleRagBuilderCompleted:
    """_handle_rag_builder_completed dispatches by step_name."""

    async def test_rag_index_step(self, poller, mock_repo):
        """step_name=rag_index → process_rag_index_result + delete."""
        with patch(
            "app.tasks.pipeline_indexation.process_rag_index_result"
        ) as mock_process:
            task = _make_mock_task(
                external_service="rag_builder",
                step_name="rag_index",
                orchestrator_task_id="job-1",
                external_task_id="42",
            )
            status_result = {"status": "indexed", "chunks_count": 10}

            await poller._handle_rag_builder_completed(task, mock_repo, status_result)

            mock_process.assert_awaited_once_with(
                job_id="job-1",
                document_id="42",
                status_result=status_result,
            )
            mock_repo.delete.assert_awaited_once_with(task.id)

    async def test_reprocess_step(self, poller, mock_repo):
        """step_name=reprocess → process_reprocess_result + delete."""
        with patch(
            "app.tasks.pipeline_indexation.process_reprocess_result"
        ) as mock_process:
            task = _make_mock_task(
                external_service="rag_builder",
                step_name="reprocess",
                orchestrator_task_id="7",
                external_task_id="doc-99",
            )
            status_result = {"status": "indexed"}

            await poller._handle_rag_builder_completed(task, mock_repo, status_result)

            mock_process.assert_awaited_once_with(
                task_id="7",
                document_id="doc-99",
                status_result=status_result,
            )
            mock_repo.delete.assert_awaited_once_with(task.id)

    async def test_activate_step(self, poller, mock_repo):
        """step_name=activate → process_activate_result + delete."""
        with patch(
            "app.tasks.pipeline_indexation.process_activate_result"
        ) as mock_process:
            task = _make_mock_task(
                external_service="rag_builder",
                step_name="activate",
                external_task_id="42",
            )

            await poller._handle_rag_builder_completed(
                task, mock_repo, {"status": "indexed"},
            )

            mock_process.assert_awaited_once_with(document_id=42)
            mock_repo.delete.assert_awaited_once_with(task.id)

    async def test_unknown_step(self, poller, mock_repo):
        """Unknown step_name → _handle_failed."""
        poller._handle_failed = AsyncMock()
        task = _make_mock_task(
            external_service="rag_builder",
            step_name="unknown_step",
        )

        await poller._handle_rag_builder_completed(
            task, mock_repo, {"status": "indexed"},
        )

        poller._handle_failed.assert_awaited_once_with(
            task, mock_repo, "UNKNOWN_STEP",
            "Unknown step: unknown_step",
        )


# ============================================================================
#  _handle_failed — per-step failure notification
# ============================================================================

class TestHandleFailed:
    """_handle_failed notifies orchestrator and deletes task."""

    async def test_full_ocr_notifies_formation(self, poller, mock_repo):
        """step_name=full_ocr → _notify_step_failed from pipeline_formation."""
        import app.tasks.pipeline_formation as formation_tasks
        with patch.object(formation_tasks, "_notify_step_failed") as mock_notify:
            task = _make_mock_task(
                step_name="full_ocr",
                orchestrator_task_id="42",
            )
            await poller._handle_failed(
                task, mock_repo, "PARSER_FAILED", "Parser OOM",
            )

            mock_notify.assert_awaited_once_with(
                task_id=42,
                step_name="full_ocr",
                error_code="PARSER_FAILED",
                error_message="Parser OOM",
            )
            mock_repo.delete.assert_awaited_once_with(task.id)

    async def test_rag_index_notifies_indexation(self, poller, mock_repo):
        """step_name=rag_index → _notify_step_failed from pipeline_indexation."""
        import app.tasks.pipeline_indexation as indexation_tasks
        with patch.object(indexation_tasks, "_notify_step_failed") as mock_notify:
            task = _make_mock_task(
                step_name="rag_index",
                orchestrator_task_id="job-1",
            )
            await poller._handle_failed(
                task, mock_repo, "RAG_BUILD_FAILED", "Build failed",
            )

            mock_notify.assert_awaited_once_with(
                job_id="job-1",
                step_name="rag_index",
                error_code="RAG_BUILD_FAILED",
                error_message="Build failed",
            )
            mock_repo.delete.assert_awaited_once_with(task.id)

    async def test_reprocess_notifies_indexation(self, poller, mock_repo):
        """step_name=reprocess → _notify_step_failed from pipeline_indexation."""
        import app.tasks.pipeline_indexation as indexation_tasks
        with patch.object(indexation_tasks, "_notify_step_failed") as mock_notify:
            task = _make_mock_task(
                step_name="reprocess",
                orchestrator_task_id="7",
            )
            await poller._handle_failed(
                task, mock_repo, "REPROCESS_ERROR", "Delete failed",
            )

            mock_notify.assert_awaited_once_with(
                job_id="7",
                step_name="reprocess",
                error_code="REPROCESS_ERROR",
                error_message="Delete failed",
            )
            mock_repo.delete.assert_awaited_once_with(task.id)

    async def test_activate_just_logs(self, poller, mock_repo):
        """step_name=activate → no notification, just log + delete."""
        with patch("app.services.task_poller.logger", autospec=True) as mock_logger:
            task = _make_mock_task(
                step_name="activate",
                external_task_id="42",
            )
            await poller._handle_failed(
                task, mock_repo, "RAG_BUILD_FAILED", "timeout",
            )

            # Should log error but NOT call any _notify_step_failed
            mock_logger.error.assert_called_once()
            mock_repo.delete.assert_awaited_once_with(task.id)


# ============================================================================
#  process_parser_full_result — transformation
# ============================================================================

class TestProcessParserFullResult:
    """process_parser_full_result transforms parser blocks and notifies."""

    async def test_transforms_blocks_to_sections(self):
        """Parser blocks → sections format via _normalize_bbox."""
        from app.tasks.pipeline_formation import process_parser_full_result

        with patch(
            "app.tasks.pipeline_formation._notify_step_completed"
        ) as mock_notify:
            parser_result = {
                "document": {
                    "block": [
                        {"number": 1, "type": "heading", "content": "Intro", "page": 1, "bbox": [0, 0, 100, 20]},
                        {"number": 2, "type": "text", "content": "Body text", "page": 1, "bbox": "0,20,100,50"},
                        {"number": 3, "type": "text", "content": "", "page": 2},  # empty → filtered
                    ],
                },
            }

            await process_parser_full_result(
                task_id=42,
                draft_id=10,
                file_key="doc.pdf",
                full_parser_result=parser_result,
            )

            mock_notify.assert_awaited_once()
            args, _ = mock_notify.await_args
            assert args[0] == 42  # task_id
            assert args[1] == "full_ocr"  # step_name
            assert args[2] == {"file_key": "doc.pdf", "mode": "full", "draft_id": 10}  # input_data

            output = args[3]
            assert output["status"] == "completed"
            assert len(output["sections"]) == 2  # empty block filtered
            assert output["sections"][0]["section_id"] == 1
            assert output["sections"][0]["type"] == "text"
            assert output["sections"][0]["content"]["text"] == "Intro"
            # First block is heading → level=1, second is text → level=2
            assert output["sections"][0]["level"] == 1
            assert output["sections"][1]["level"] == 2

    async def test_passes_through_existing_sections(self):
        """If parser already returns sections, use them directly."""
        from app.tasks.pipeline_formation import process_parser_full_result

        with patch(
            "app.tasks.pipeline_formation._notify_step_completed"
        ) as mock_notify:
            parser_result = {
                "sections": [{"section_id": 10, "content": {"text": "pre-built"}}],
            }

            await process_parser_full_result(
                task_id=1, draft_id=5, file_key="f.pdf",
                full_parser_result=parser_result,
            )

            args, _ = mock_notify.await_args
            output = args[3]
            assert len(output["sections"]) == 1
            assert output["sections"][0]["section_id"] == 10

    async def test_empty_results_notifies_with_empty_sections(self):
        """No blocks, no sections → empty sections list."""
        from app.tasks.pipeline_formation import process_parser_full_result

        with patch(
            "app.tasks.pipeline_formation._notify_step_completed"
        ) as mock_notify:
            await process_parser_full_result(
                task_id=1, draft_id=5, file_key="f.pdf",
                full_parser_result={},
            )

            args, _ = mock_notify.await_args
            output = args[3]
            assert output["sections"] == []
            assert output["status"] == "completed"


# ============================================================================
#  _normalize_bbox
# ============================================================================

class TestNormalizeBbox:
    """_normalize_bbox handles various input formats."""

    def test_none_returns_none(self):
        from app.tasks.pipeline_formation import _normalize_bbox
        assert _normalize_bbox(None) is None

    def test_list_passthrough(self):
        from app.tasks.pipeline_formation import _normalize_bbox
        assert _normalize_bbox([1, 2, 3, 4]) == [1.0, 2.0, 3.0, 4.0]

    def test_string_csv(self):
        from app.tasks.pipeline_formation import _normalize_bbox
        assert _normalize_bbox("10,20,30,40") == [10.0, 20.0, 30.0, 40.0]

    def test_string_semicolon(self):
        from app.tasks.pipeline_formation import _normalize_bbox
        assert _normalize_bbox("1;2;3;4") == [1.0, 2.0, 3.0, 4.0]

    def test_invalid_string_returns_none(self):
        from app.tasks.pipeline_formation import _normalize_bbox
        assert _normalize_bbox("not-a-bbox") is None

    def test_any_list_converts_to_floats(self):
        """Any list/tuple is converted to float list (no length validation)."""
        from app.tasks.pipeline_formation import _normalize_bbox
        assert _normalize_bbox([1, 2, 3]) == [1.0, 2.0, 3.0]  # 3 elements ok


# ============================================================================
#  process_rag_index_result — integrity check + notification
# ============================================================================

class TestProcessRagIndexResult:
    """process_rag_index_result does integrity check and notifies correctly."""

    def _make_rag_mock(self, check_index_result: dict):
        """Create an AsyncMock RAG builder client."""
        rag = AsyncMock()
        rag.check_index.return_value = check_index_result
        rag.close = AsyncMock()
        return rag

    async def test_indexed_with_ok_integrity_notifies_completed(self):
        """status=indexed + integrity_ok → _notify_step_completed."""
        from app.tasks.pipeline_indexation import process_rag_index_result

        mock_rag = self._make_rag_mock({
            "integrity_ok": True,
            "indexed_count": 10,
            "expected_count": 10,
        })
        with patch(
            "app.services.rag_client.RAGBuilderClient", return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation._notify_step_completed"
        ) as mock_notify:
            status_result = {"status": "indexed", "chunks_count": 10}
            await process_rag_index_result(
                job_id="job-1", document_id="42", status_result=status_result,
            )

            mock_notify.assert_awaited_once_with(
                "job-1", "rag_index", status_result,
            )

    async def test_integrity_failure_notifies_failed(self):
        """integrity_ok=False → _notify_step_failed."""
        from app.tasks.pipeline_indexation import process_rag_index_result

        mock_rag = self._make_rag_mock({
            "integrity_ok": False,
            "indexed_count": 3,
            "expected_count": 10,
        })
        with patch(
            "app.services.rag_client.RAGBuilderClient", return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation._notify_step_failed"
        ) as mock_notify:
            await process_rag_index_result(
                job_id="job-1", document_id="42",
                status_result={"status": "failed", "errors": "chunking failed"},
            )

            mock_notify.assert_awaited_once_with(
                "job-1", "rag_index", "INTEGRITY_CHECK_FAILED",
                "chunking failed",
            )

    async def test_build_failed_notifies_failed(self):
        """status=failed → _notify_step_failed, no integrity check."""
        from app.tasks.pipeline_indexation import process_rag_index_result

        with patch(
            "app.tasks.pipeline_indexation._notify_step_failed"
        ) as mock_notify:
            await process_rag_index_result(
                job_id="job-1", document_id="42",
                status_result={"status": "failed", "errors": "chunking error"},
            )

            mock_notify.assert_awaited_once_with(
                "job-1", "rag_index", "INTEGRITY_CHECK_FAILED",
                "chunking error",
            )

    async def test_partially_indexed_when_expected_gt_chunks(self):
        """P2I-1: expected_count > chunks_count → partially_indexed status.

        expected_count берётся из /check эндпоинта (check_result),
        chunks_count — из /status (status_result).
        """
        from app.tasks.pipeline_indexation import process_rag_index_result

        mock_rag = self._make_rag_mock({
            "integrity_ok": True,
            "indexed_count": 5,
            "expected_count": 10,
        })
        with patch(
            "app.services.rag_client.RAGBuilderClient", return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation._notify_step_completed"
        ) as mock_notify:
            # expected_count (10 из check_result) > chunks_count (5 из status_result)
            status_result = {"status": "indexed", "chunks_count": 5}
            await process_rag_index_result(
                job_id="job-1", document_id="42", status_result=status_result,
            )

            args, _ = mock_notify.await_args
            assert args[2]["status"] == "partially_indexed", \
                "P2I-1: expected_count > chunks_count should trigger partially_indexed"

    async def test_partially_indexed_skipped_when_check_fails(self):
        """P2I-1: when /check endpoint fails, fallback to chunks_count → skip partial."""
        from app.tasks.pipeline_indexation import process_rag_index_result

        # /check возвращает пустой результат (без expected_count)
        mock_rag = self._make_rag_mock({})
        with patch(
            "app.services.rag_client.RAGBuilderClient", return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation._notify_step_completed"
        ) as mock_notify:
            status_result = {"status": "indexed", "chunks_count": 5}
            await process_rag_index_result(
                job_id="job-1", document_id="42", status_result=status_result,
            )

            args, _ = mock_notify.await_args
            assert args[2]["status"] == "indexed", \
                "Expected not to trigger partially_indexed when check has no expected_count"


# ============================================================================
#  process_reprocess_result
# ============================================================================

class TestProcessReprocessResult:
    """process_reprocess_result notifies orchestrator of completion."""

    async def test_notifies_completed(self):
        from app.tasks.pipeline_indexation import process_reprocess_result

        with patch(
            "app.tasks.pipeline_indexation._notify_step_completed"
        ) as mock_notify:
            status_result = {"status": "indexed", "chunks_count": 5}
            await process_reprocess_result(
                task_id="7", document_id="doc-99",
                status_result=status_result,
            )

            mock_notify.assert_awaited_once_with(
                "7", "reprocess", status_result,
            )
            # Verify status is preserved
            assert status_result["status"] == "indexed"


# ============================================================================
#  process_activate_result
# ============================================================================

class TestProcessActivateResult:
    """process_activate_result does integrity check and activates document."""

    async def test_integrity_ok_activates_document(self):
        """integrity_ok=True → update_document_status active."""
        from app.tasks.pipeline_indexation import process_activate_result

        mock_rag = AsyncMock()
        mock_rag.check_index.return_value = {
            "integrity_ok": True,
            "indexed_count": 10,
            "expected_count": 10,
        }
        mock_rag.close = AsyncMock()

        mock_reg = AsyncMock()
        mock_reg.update_document_status = AsyncMock()
        mock_reg.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient", return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient", return_value=mock_reg,
        ):
            await process_activate_result(document_id=42)

            mock_rag.check_index.assert_awaited_once_with(document_id=42)
            mock_reg.update_document_status.assert_awaited_once_with(
                document_id=42, status="active",
            )

    async def test_integrity_fail_does_not_activate(self):
        """integrity_ok=False → document NOT activated."""
        from app.tasks.pipeline_indexation import process_activate_result

        mock_rag = AsyncMock()
        mock_rag.check_index.return_value = {
            "integrity_ok": False,
            "indexed_count": 5,
            "expected_count": 10,
        }
        mock_rag.close = AsyncMock()

        mock_reg = AsyncMock()
        mock_reg.update_document_status = AsyncMock()
        mock_reg.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient", return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient", return_value=mock_reg,
        ):
            await process_activate_result(document_id=42)

            mock_rag.check_index.assert_awaited_once_with(document_id=42)
            mock_reg.update_document_status.assert_not_called()
