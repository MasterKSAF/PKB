"""
Comprehensive unit tests for all Celery pipeline tasks.

Covers all tasks from:
  - pipeline_formation (Parser, Converter full, missing failure paths)
  - pipeline_indexation (rag_index, reprocess)
  - scheduler (cleanup_stale_tasks)
  - compensation (delete_registry_document, delete_from_vector_index)

Pattern: mock all external clients, patch _notify_*, call .run() directly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

DRAFT_ID = 10
DOCUMENT_ID = 42


def _patch_task_retry(task_func, exc_to_raise=None):
    """Patch self.retry on the bound Celery task (copied from test_celery_tasks.py)."""
    task_instance = task_func.run.__self__
    patcher = patch.object(task_instance, "retry")
    mock_retry = patcher.start()
    mock_retry.side_effect = exc_to_raise or RuntimeError("retry-called")
    return mock_retry, patcher


# ============================================================================
#  Pipeline Formation — Parser Preview
# ============================================================================


class TestRunParserPreviewStep:
    """Tests for run_parser_preview_step Celery task."""

    HAPPY_PARSER_RESPONSE = {
        "data": {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Parser doc"},
            "quality": {"score": 0.95, "notifications": []},
        }
    }

    def test_happy_path(self):
        """Parser preview step completes successfully."""
        mock_client = AsyncMock()
        mock_client.process.return_value = self.HAPPY_PARSER_RESPONSE
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ParserServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_parser_preview_step

            result = run_parser_preview_step.run(
                task_id=1, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
            )

        mock_client.process.assert_awaited_once_with(
            task_id=1, file_key="drafts/10/file.pdf", draft_id=DRAFT_ID,
            mode="preview", max_pages=3,
        )

        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 1  # task_id
        assert args[1] == "preview_ocr"  # normalized step name
        assert args[2]["draft_id"] == DRAFT_ID
        assert args[3]["preview_not_supported"] is False
        assert args[3]["pages_processed"] == 3

        assert result == {"status": "completed", "step": "preview_ocr", "task_id": 1}

    def test_failure_mid_retry_does_not_notify(self):
        """When Parser raises mid-retry, notify_failed is NOT called (only on last retry)."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("Parser service down")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ParserServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_parser_preview_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_parser_preview_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_parser_preview_step.run(
                        task_id=1, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                retry_patcher.stop()

        # retries=0 < max_retries=3 : notify should NOT be called
        notify_failed.assert_not_awaited()
        mock_retry.assert_called_once()

    def test_failure_notifies_on_last_retry(self):
        """When Parser raises on the LAST attempt, notify_failed IS called."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("Parser service down")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ParserServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_parser_preview_step

            # Simulate last retry attempt: retries = max_retries
            task_instance = run_parser_preview_step.run.__self__
            original_retries = task_instance.request.retries
            task_instance.request.retries = task_instance.max_retries

            mock_retry, retry_patcher = _patch_task_retry(
                run_parser_preview_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_parser_preview_step.run(
                        task_id=1, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                task_instance.request.retries = original_retries
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            1, "preview_ocr", "PARSER_ERROR", "Parser service down",
        )
        mock_retry.assert_called_once()


# ============================================================================
#  Pipeline Formation — Converter Full
# ============================================================================


class TestRunConverterFullStep:
    """Tests for run_converter_full_step Celery task."""

    HAPPY_CONVERTER_FULL = {
        "task_id": 3,
        "version_id": 420001,
        "metadata": {"schema": "validated_v3"},
        "document": {"content": [{"section_id": 1, "type": "text", "content": {"text": "doc"}}]},
        "validation": {"structure_valid": True, "status": "completed"},
        "document_id": 1,
    }

    def test_happy_path(self):
        """Converter full step completes successfully."""
        mock_client = AsyncMock()
        mock_client.convert_full.return_value = self.HAPPY_CONVERTER_FULL
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ConverterValidatorClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_converter_full_step

            result = run_converter_full_step.run(
                task_id=3, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
            )

        mock_client.convert_full.assert_awaited_once_with(
            {"file_key": "drafts/10/file.pdf", "draft_id": DRAFT_ID,
             "task_id": 3},
        )

        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 3
        assert args[1] == "full_converter"
        assert args[3]["validated"] is True
        assert args[3]["metadata"]["schema"] == "validated_v3"
        assert args[3]["validation"]["structure_valid"] is True
        assert args[3]["status"] == "completed"

        assert result == {"status": "completed", "step": "full_converter", "task_id": 3}

    def test_failure_path_triggers_retry(self):
        """When Converter full raises, task retries but does NOT notify mid-retry.

        _notify_step_failed is called only on the last retry attempt
        (retries >= max_retries).
        """
        mock_client = AsyncMock()
        mock_client.convert_full.side_effect = Exception("Converter full error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ConverterValidatorClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_converter_full_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_converter_full_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_converter_full_step.run(
                        task_id=3, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                retry_patcher.stop()

        # retries=0 < max_retries=3 : notify should NOT be called
        notify_failed.assert_not_awaited()
        mock_retry.assert_called_once()

    def test_failure_path_notifies_on_last_retry(self):
        """When Converter full raises on the LAST attempt, notify_failed IS called."""
        mock_client = AsyncMock()
        mock_client.convert_full.side_effect = Exception("Converter full error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ConverterValidatorClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_converter_full_step

            # Simulate last retry attempt: retries = max_retries
            task_instance = run_converter_full_step.run.__self__
            original_retries = task_instance.request.retries
            task_instance.request.retries = task_instance.max_retries

            mock_retry, retry_patcher = _patch_task_retry(
                run_converter_full_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_converter_full_step.run(
                        task_id=3, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                task_instance.request.retries = original_retries
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            3, "full_converter", "CONVERTER_ERROR", "Converter full error",
        )
        mock_retry.assert_called_once()


# ============================================================================
#  Pipeline Formation — Parser Full
# ============================================================================


class TestRunParserFullStep:
    """Tests for run_parser_full_step Celery task (fire-and-forget mode)."""

    HAPPY_PARSER_RESP = {
        "data": {
            "task_id": "parser-task-123",
            "status": "processing",
        }
    }

    def test_happy_path(self):
        """Parser full submits task and exits (no polling)."""
        mock_client = AsyncMock()
        mock_client.process.return_value = self.HAPPY_PARSER_RESP
        mock_client.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ParserServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_formation.get_db_context",
        ):
            from app.tasks.pipeline_formation import run_parser_full_step

            result = run_parser_full_step.run(
                task_id=4, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
            )

        mock_client.process.assert_awaited_once_with(
            task_id=4, file_key="drafts/10/file.pdf", draft_id=DRAFT_ID,
            mode="full",
        )

        # Verify external task was saved
        mock_ext_repo.create.assert_awaited_once_with(
            orchestrator_task_id=4,
            step_name="full_ocr",
            external_service="parser",
            external_task_id='parser-task-123',
            context_data={"draft_id": DRAFT_ID, "file_key": "drafts/10/file.pdf"},
        )

        assert result == {"status": "pending", "step": "full_ocr", "task_id": 4, "parser_task_id": "parser-task-123"}

    def test_failure_mid_retry_does_not_notify(self):
        """When Parser full raises mid-retry, notify_failed is NOT called."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("Parser full error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ParserServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_parser_full_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_parser_full_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_parser_full_step.run(
                        task_id=4, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                retry_patcher.stop()

        # retries=0 < max_retries=3 : notify should NOT be called
        notify_failed.assert_not_awaited()
        mock_retry.assert_called_once()

    def test_failure_notifies_on_last_retry(self):
        """When Parser full raises on the LAST attempt, notify_failed IS called."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("Parser full error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ParserServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_parser_full_step

            # Simulate last retry attempt: retries = max_retries
            task_instance = run_parser_full_step.run.__self__
            original_retries = task_instance.request.retries
            task_instance.request.retries = task_instance.max_retries

            mock_retry, retry_patcher = _patch_task_retry(
                run_parser_full_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_parser_full_step.run(
                        task_id=4, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                task_instance.request.retries = original_retries
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            4, "full_ocr", "PARSER_ERROR", "Parser full error",
        )
        mock_retry.assert_called_once()


# ============================================================================
#  Pipeline Formation — OCR Full (failure path only, happy exists)
# ============================================================================


class TestRunOcrFullStepFailure:
    """Failure path for run_ocr_full_step (happy path already tested)."""

    def test_failure_mid_retry_does_not_notify(self):
        """When OCR full raises mid-retry, notify_failed is NOT called."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("OCR full error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.OCRServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_ocr_full_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_ocr_full_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_ocr_full_step.run(
                        task_id=5, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                retry_patcher.stop()

        # retries=0 < max_retries=3 : notify should NOT be called
        notify_failed.assert_not_awaited()
        mock_retry.assert_called_once()

    def test_failure_notifies_on_last_retry(self):
        """When OCR full raises on the LAST attempt, notify_failed IS called."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("OCR full error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.OCRServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_ocr_full_step

            # Simulate last retry attempt: retries = max_retries
            task_instance = run_ocr_full_step.run.__self__
            original_retries = task_instance.request.retries
            task_instance.request.retries = task_instance.max_retries

            mock_retry, retry_patcher = _patch_task_retry(
                run_ocr_full_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_ocr_full_step.run(
                        task_id=5, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf",
                    )
            finally:
                task_instance.request.retries = original_retries
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            5, "full_ocr", "OCR_ERROR", "OCR full error",
        )
        mock_retry.assert_called_once()


# ============================================================================
#  Pipeline Formation — Registry Step (failure path only, happy exists)
# ============================================================================


class TestRunRegistryStepFailure:
    """Failure path for run_registry_step."""

    def test_failure_triggers_retry(self):
        """Registry step failure calls notify_failed and retries."""
        mock_client = AsyncMock()
        mock_client.get_document_sections.return_value = {"data": {"sections": [{"id": 1}]}}
        mock_client.update_draft_status.side_effect = Exception("Registry error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.RegistryServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_registry_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_registry_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_registry_step.run(
                        task_id=6, draft_id=DRAFT_ID, document_id=DOCUMENT_ID,
                    )
            finally:
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            6, "registry_creation", "REGISTRY_ERROR", "Registry error",
        )
        mock_retry.assert_called_once()


# ============================================================================
#  Pipeline Indexation — run_rag_index_step
# ============================================================================


class TestRunRagIndexStep:
    """Tests for run_rag_index_step Celery task (pipeline_indexation, fire-and-forget)."""

    def test_happy_path(self, monkeypatch):
        """RAG index submits and exits (no polling)."""
        # Mock redis to avoid real connection
        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # lock acquired
        mock_redis.delete.return_value = True

        import redis as sync_redis
        monkeypatch.setattr(sync_redis, "from_url", lambda url: mock_redis)

        # Mock RegistryServiceClient.get_document_sections
        mock_registry = AsyncMock()
        mock_registry.get_document_sections.return_value = {
            "data": {"sections": [{"id": 1, "title": "S1"}, {"id": 2, "title": "S2"}]},
        }
        mock_registry.close = AsyncMock()

        # Mock RAGBuilderClient
        mock_rag = AsyncMock()
        mock_rag.index_document.return_value = {
            "status": "indexing",
            "indexing_txn_id": "txn-123",
        }
        mock_rag.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_indexation.get_db_context",
        ):
            from app.tasks.pipeline_indexation import run_rag_index_step

            result = run_rag_index_step.run(
                job_id=1, document_id=str(DOCUMENT_ID),
            )

        # Verify Registry was called
        mock_registry.get_document_sections.assert_awaited_once_with(
            document_id=DOCUMENT_ID,
        )

        # Verify RAG Builder was called
        mock_rag.index_document.assert_awaited_once_with(
            document_id=str(DOCUMENT_ID),
            sections=[{"id": 1, "title": "S1"}, {"id": 2, "title": "S2"}],
        )

        # Verify NO polling — get_build_status should NOT be called from the task
        mock_rag.get_build_status.assert_not_called()

        # Verify external task was saved
        mock_ext_repo.create.assert_awaited_once()

        assert result == {"status": "pending", "step": "rag_index", "job_id": 1}
        # No integrity check from the task anymore — Poller handles it
        mock_rag.check_index.assert_not_called()

        assert result["status"] == "pending"

    def test_lock_held_skips(self, monkeypatch):
        """When Redis advisory lock is held, task skips."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = None  # lock NOT acquired (redis-py SET NX returns None when key exists)
        mock_redis.delete.return_value = True

        import redis as sync_redis
        monkeypatch.setattr(sync_redis, "from_url", lambda url: mock_redis)

        from app.tasks.pipeline_indexation import run_rag_index_step

        result = run_rag_index_step.run(
            job_id=99, document_id="99",
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "lock_held"
        assert result["document_id"] == "99"

    def test_invalid_document_id_format(self, monkeypatch):
        """Non-integer document_id raises ValueError."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        import redis as sync_redis
        monkeypatch.setattr(sync_redis, "from_url", lambda url: mock_redis)

        from app.tasks.pipeline_indexation import run_rag_index_step

        with pytest.raises(ValueError, match="document_id must be an integer"):
            run_rag_index_step.run(
                job_id="job-bad", document_id="not-an-int",
            )

    def test_submit_and_save_external_task(self, monkeypatch):
        """Task submits to RAG Builder and saves external_task (no integrity check in task)."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        import redis as sync_redis
        monkeypatch.setattr(sync_redis, "from_url", lambda url: mock_redis)

        mock_registry = AsyncMock()
        mock_registry.get_document_sections.return_value = {
            "data": {"sections": [{"id": 1}]},
        }
        mock_registry.close = AsyncMock()

        mock_rag = AsyncMock()
        mock_rag.index_document.return_value = {"status": "indexing"}
        mock_rag.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_indexation.get_db_context",
        ):
            from app.tasks.pipeline_indexation import run_rag_index_step

            result = run_rag_index_step.run(
                job_id=1, document_id="50",
            )

        # Integrity check is NOT called from the task anymore
        mock_rag.check_index.assert_not_called()

        # External task was saved
        mock_ext_repo.create.assert_awaited_once()

        assert result["status"] == "pending"

    def test_build_submission_fails_triggers_retry(self, monkeypatch):
        """When RAG Builder fails, task calls notify_failed and retries."""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        import redis as sync_redis
        monkeypatch.setattr(sync_redis, "from_url", lambda url: mock_redis)

        mock_registry = AsyncMock()
        mock_registry.get_document_sections.return_value = {
            "data": {"sections": [{"id": 1}]},
        }
        mock_registry.close = AsyncMock()

        mock_rag = AsyncMock()
        mock_rag.index_document.side_effect = Exception("RAG Builder unavailable")
        mock_rag.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_indexation import run_rag_index_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_rag_index_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_rag_index_step.run(
                        job_id=1, document_id="51",
                    )
            finally:
                retry_patcher.stop()

        notify_failed.assert_awaited_once()
        mock_retry.assert_called_once()


# ============================================================================
#  Pipeline Indexation — run_reprocess_step
# ============================================================================


class TestRunReprocessStep:
    """Tests for run_reprocess_step Celery task (fire-and-forget)."""

    def test_happy_path(self):
        """Reprocess submits and exits (no polling)."""
        mock_rag = AsyncMock()
        mock_rag.delete_index = AsyncMock()
        mock_rag.index_document.return_value = {"status": "indexing", "indexing_txn_id": "txn-456"}
        mock_rag.close = AsyncMock()

        mock_registry = AsyncMock()
        mock_registry.get_document_sections.return_value = {
            "data": {"sections": [{"id": 1}]},
        }
        mock_registry.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ), patch(
            "app.tasks.pipeline_indexation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_indexation.get_db_context",
        ):
            from app.tasks.pipeline_indexation import run_reprocess_step

            result = run_reprocess_step.run(
                task_id=7, document_id=str(DOCUMENT_ID),
            )

        # Verify delete_index was called first
        mock_rag.delete_index.assert_awaited_once_with(str(DOCUMENT_ID))

        # Verify index_document was called
        mock_rag.index_document.assert_awaited_once()

        # Verify NO polling
        mock_rag.get_build_status.assert_not_called()

        # Verify external task was saved
        mock_ext_repo.create.assert_awaited_once()

        assert result["status"] == "pending"

    def test_failure_triggers_retry(self):
        """Reprocess failure calls notify_failed and retries."""
        mock_rag = AsyncMock()
        mock_rag.delete_index.side_effect = Exception("RAG delete error")
        mock_rag.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient",
            new=MagicMock(),
        ), patch(
            "app.tasks.pipeline_indexation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_indexation import run_reprocess_step

            mock_retry, retry_patcher = _patch_task_retry(
                run_reprocess_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_reprocess_step.run(
                        task_id=7, document_id=str(DOCUMENT_ID),
                    )
            finally:
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            7, "reprocess", "REPROCESS_ERROR", "RAG delete error",
        )
        mock_retry.assert_called_once()


# ============================================================================
#  Activate Document — run_activate_document_step
# ============================================================================


class TestRunActivateDocumentStep:
    """Tests for run_activate_document_step Celery task."""

    def test_already_indexed_activates(self):
        """Build already indexed → activate immediately."""
        mock_rag = AsyncMock()
        mock_rag.get_build_status.return_value = {
            "status": "indexed", "chunks_count": 42,
        }
        mock_rag.check_index.return_value = {
            "integrity_ok": True,
            "indexed_count": 42, "expected_count": 42,
        }
        mock_rag.close = AsyncMock()

        mock_registry = AsyncMock()
        mock_registry.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ):
            from app.tasks.pipeline_indexation import run_activate_document_step

            result = run_activate_document_step.run(job_id="test", document_id=42)

        assert result == {"status": "active", "document_id": 42}
        mock_rag.get_build_status.assert_awaited_once_with(
            document_id=42, longpoll=0,
        )
        mock_rag.check_index.assert_awaited_once_with(document_id=42)
        mock_registry.update_document_status.assert_awaited_once_with(
            document_id=42, status="active",
        )

    def test_build_failed_stays_validating(self):
        """Build already failed → stays in validating."""
        mock_rag = AsyncMock()
        mock_rag.get_build_status.return_value = {
            "status": "failed", "errors": ["chunking error"],
        }
        mock_rag.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ):
            from app.tasks.pipeline_indexation import run_activate_document_step

            result = run_activate_document_step.run(job_id="test", document_id=42)

        assert result == {"status": "build_failed", "document_id": 42}
        mock_rag.check_index.assert_not_called()

    def test_still_indexing_defers_to_poller(self):
        """Build still processing → defer to Poller via external_tasks."""
        mock_rag = AsyncMock()
        mock_rag.get_build_status.return_value = {
            "status": "processing", "chunks_count": 0,
        }
        mock_rag.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_indexation.get_db_context",
        ):
            from app.tasks.pipeline_indexation import run_activate_document_step

            result = run_activate_document_step.run(job_id="12345", document_id=42)

        assert result == {"status": "pending", "document_id": 42}
        mock_ext_repo.create.assert_awaited_once()
        # No check_index for still-processing status
        mock_rag.check_index.assert_not_called()

    def test_processing_status_defers_to_poller(self):
        """Poll returns indexing/processing → defer to Poller."""
        mock_rag = AsyncMock()
        mock_rag.get_build_status.return_value = {
            "status": "indexing", "progress": 50,
        }
        mock_rag.close = AsyncMock()

        mock_ext_repo = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ), patch(
            "app.tasks.pipeline_indexation.ExternalTaskRepository",
            return_value=mock_ext_repo,
        ), patch(
            "app.tasks.pipeline_indexation.get_db_context",
        ):
            from app.tasks.pipeline_indexation import run_activate_document_step

            result = run_activate_document_step.run(job_id="12345", document_id=42)

        # No self.retry() — defer to Poller
        assert result == {"status": "pending", "document_id": 42}
        mock_ext_repo.create.assert_awaited_once()
        mock_rag.get_build_status.assert_awaited_once_with(
            document_id=42, longpoll=0,
        )


# ============================================================================
#  Scheduler — cleanup_stale_tasks
# ============================================================================


class TestCleanupStaleTasks:
    """Tests for cleanup_stale_tasks Celery task (scheduler)."""

    def test_happy_path(self):
        """Cleanup calls orchestrator and returns count."""
        mock_orch = MagicMock()
        mock_orch.cleanup_stale_tasks = AsyncMock(return_value=3)

        with patch(
            "app.tasks.scheduler.PipelineOrchestrator",
            return_value=mock_orch,
        ):
            from app.tasks.scheduler import cleanup_stale_tasks

            result = cleanup_stale_tasks.run()

        mock_orch.cleanup_stale_tasks.assert_awaited_once()
        assert result == {"cleaned": 3}


# ============================================================================
#  Compensation — delete_registry_document
# ============================================================================


class TestDeleteRegistryDocument:
    """Tests for delete_registry_document compensation task."""

    def test_happy_path(self):
        """Compensation deletes registry document successfully."""
        mock_registry = AsyncMock()
        mock_registry.delete_document = AsyncMock()
        mock_registry.close = AsyncMock()

        with patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ):
            from app.tasks.compensation import delete_registry_document

            result = delete_registry_document.run(
                draft_id=DRAFT_ID, registry_id=str(DOCUMENT_ID),
            )

        mock_registry.delete_document.assert_awaited_once_with(int(DOCUMENT_ID))
        assert result["status"] == "compensated"
        assert result["action"] == "delete_registry_document"
        assert result["draft_id"] == DRAFT_ID

    def test_failure_propagates(self):
        """When Registry delete fails, exception propagates."""
        mock_registry = AsyncMock()
        mock_registry.delete_document.side_effect = Exception("Registry delete failed")
        mock_registry.close = AsyncMock()

        with patch(
            "app.services.registry_client.RegistryServiceClient",
            return_value=mock_registry,
        ):
            from app.tasks.compensation import delete_registry_document

            with pytest.raises(Exception, match="Registry delete failed"):
                delete_registry_document.run(
                    draft_id=DRAFT_ID, registry_id=str(DOCUMENT_ID),
                )


# ============================================================================
#  Compensation — delete_from_vector_index
# ============================================================================


class TestDeleteFromVectorIndex:
    """Tests for delete_from_vector_index compensation task."""

    def test_happy_path(self):
        """Compensation deletes from vector index successfully."""
        mock_rag = AsyncMock()
        mock_rag.delete_index = AsyncMock()
        mock_rag.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ):
            from app.tasks.compensation import delete_from_vector_index

            result = delete_from_vector_index.run(
                document_id=str(DOCUMENT_ID),
            )

        mock_rag.delete_index.assert_awaited_once_with(str(DOCUMENT_ID))
        assert result["status"] == "compensated"
        assert result["action"] == "delete_from_vector_index"
        assert result["document_id"] == str(DOCUMENT_ID)

    def test_failure_propagates(self):
        """When RAG delete fails, exception propagates."""
        mock_rag = AsyncMock()
        mock_rag.delete_index.side_effect = Exception("RAG delete failed")
        mock_rag.close = AsyncMock()

        with patch(
            "app.services.rag_client.RAGBuilderClient",
            return_value=mock_rag,
        ):
            from app.tasks.compensation import delete_from_vector_index

            with pytest.raises(Exception, match="RAG delete failed"):
                delete_from_vector_index.run(
                    document_id=str(DOCUMENT_ID),
                )
