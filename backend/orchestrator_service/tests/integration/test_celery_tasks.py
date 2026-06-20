"""
Integration tests for Celery task functions.

Tests the pipeline_formation task functions directly (without a Celery worker).
All external service clients are mocked.

NOTE: We call task_function.run(...) which bypasses the Celery Task.__call__
wrapper. The .run() is already bound to the Task instance (bind=True), so
the first 'self' parameter is automatically provided by Celery.
We patch self.retry via the task object's __self__ attribute.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# Helper: get the bound task object so we can patch self.retry
def _patch_task_retry(task_func, exc_to_raise=None):
    """Patch self.retry on the bound Celery task.

    Makes self.retry() raise the given exception (or a RuntimeError by default)
    so that tests can verify retry was called via pytest.raises.

    Returns the mock so assertions can be made.
    """
    task_instance = task_func.run.__self__
    patcher = patch.object(task_instance, "retry")
    mock_retry = patcher.start()
    mock_retry.side_effect = exc_to_raise or RuntimeError("retry-called")
    return mock_retry, patcher


DRAFT_ID = 10


class TestRunOcrPreviewStep:
    """Tests for run_ocr_preview_step Celery task."""

    HAPPY_OCR_RESPONSE = {
        "data": {
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56", "title": "Test doc"},
            "quality": {
                "score": 0.94,
                "notifications": [],
            },
        }
    }

    def test_happy_path(self):
        """OCR preview step completes successfully."""
        mock_client = AsyncMock()
        mock_client.process.return_value = self.HAPPY_OCR_RESPONSE
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.OCRServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_ocr_preview_step

            # .run() is already bound to the task instance
            result = run_ocr_preview_step.run(
                task_id=1, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf"
            )

        # Verify service client was called correctly with new unified method
        mock_client.process.assert_awaited_once_with(
            file_key="drafts/10/file.pdf", draft_id=DRAFT_ID, mode="preview", max_pages=3
        )

        # Verify notify was called with correct args
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 1  # task_id
        assert args[1] == "preview_ocr"  # step_name
        assert args[2] == {  # input_data
            "file_key": "drafts/10/file.pdf",
            "mode": "preview",
            "max_pages": 3,
            "draft_id": DRAFT_ID,
        }
        assert args[3] == {  # output_data
            "preview_not_supported": False,
            "pages_processed": 3,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56", "title": "Test doc"},
            "quality": {
                "score": 0.94,
                "notifications": [],
            },
        }

        # Verify return value
        assert result == {
            "status": "completed",
            "step": "preview_ocr",
            "task_id": 1,
        }

    def test_failure_path_triggers_retry(self):
        """When OCR service raises, the task calls notify_failed and retries."""
        mock_client = AsyncMock()
        mock_client.process.side_effect = Exception("OCR service down")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.OCRServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_ocr_preview_step

            # Patch self.retry on the bound task instance
            mock_retry, retry_patcher = _patch_task_retry(
                run_ocr_preview_step, exc_to_raise=Exception("self.retry called")
            )
            try:
                with pytest.raises(Exception, match="self.retry called"):
                    run_ocr_preview_step.run(
                        task_id=1,
                        draft_id=DRAFT_ID,
                        file_key="drafts/10/file.pdf",
                    )
            finally:
                retry_patcher.stop()

        # Verify failure was notified
        notify_failed.assert_awaited_once_with(
            1, "preview_ocr", "OCR_ERROR", "OCR service down"
        )

        # Verify retry was called on the task instance
        mock_retry.assert_called_once()


class TestRunConverterPreviewStep:
    """Tests for run_converter_preview_step Celery task."""

    HAPPY_CONVERTER_RESPONSE = {
        "data": {
            "validated": True,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56", "title": "Test doc"},
        }
    }

    def test_happy_path(self):
        """Converter preview step completes successfully."""
        mock_client = AsyncMock()
        mock_client.convert_preview.return_value = self.HAPPY_CONVERTER_RESPONSE
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ConverterValidatorClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_converter_preview_step

            result = run_converter_preview_step.run(
                task_id=2, draft_id=DRAFT_ID, file_key="drafts/10/file.pdf"
            )

        # Verify service call includes draft_id
        mock_client.convert_preview.assert_awaited_once_with(
            {"file_key": "drafts/10/file.pdf", "draft_id": DRAFT_ID}
        )

        # Verify notify includes draft_id
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 2
        assert args[1] == "preview_converter"
        assert args[2] == {"file_key": "drafts/10/file.pdf", "mode": "preview", "draft_id": DRAFT_ID}
        assert args[3] == {
            "validated": True,
            "metadata": {"doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56", "title": "Test doc"},
        }

        assert result == {
            "status": "completed",
            "step": "preview_converter",
            "task_id": 2,
        }


class TestRunRegistryStep:
    """Tests for run_registry_step Celery task."""

    def test_happy_path(self):
        """Registry step confirms document status."""
        mock_client = AsyncMock()
        mock_client.update_draft_status = AsyncMock(return_value={
            "data": {"status": "approved", "document_id": 42}
        })
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.RegistryServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_registry_step

            result = run_registry_step.run(
                task_id=3, draft_id=DRAFT_ID, document_id=42, version_id=421
            )

        # Verify service call — now calls update_draft_status, not create_document
        mock_client.update_draft_status.assert_awaited_once_with(
            draft_id=DRAFT_ID, status="approved", document_id=42
        )
        mock_client.create_document.assert_not_called()

        # Verify notify
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 3
        assert args[1] == "registry_creation"
        assert args[2] == {"draft_id": DRAFT_ID, "document_id": 42}
        assert args[3] == {"registry_id": 42, "version_id": 421, "status": "registered"}

        assert result == {
            "status": "completed",
            "step": "registry_creation",
            "task_id": 3,
        }


class TestRunOcrFullStep:
    """Tests for run_ocr_full_step Celery task."""

    HAPPY_OCR_FULL_RESPONSE = {
        "data": {"pages_processed": 15, "status": "completed"}
    }

    def test_happy_path(self):
        """Full OCR step completes successfully."""
        mock_client = AsyncMock()
        mock_client.process.return_value = self.HAPPY_OCR_FULL_RESPONSE
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.OCRServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_ocr_full_step

            result = run_ocr_full_step.run(
                task_id=4,
                draft_id=DRAFT_ID,
                file_key="drafts/10/file.pdf",
            )

        # Verify service call with new unified method
        mock_client.process.assert_awaited_once_with(
            file_key="drafts/10/file.pdf", draft_id=DRAFT_ID, mode="full"
        )

        # Verify notify
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 4
        assert args[1] == "full_ocr"
        assert args[2] == {"file_key": "drafts/10/file.pdf", "mode": "full", "draft_id": DRAFT_ID}
        assert args[3] == {"pages_processed": 15, "status": "completed"}

        assert result == {
            "status": "completed",
            "step": "full_ocr",
            "task_id": 4,
        }
