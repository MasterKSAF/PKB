"""
Celery tasks: тест вызова _notify_step_completed/failed через _run_async.

Проверяет, что celery task корректно вызывает notify-функции
после успешной обработки и при ошибке. БД замокана.

Следует паттерну test_celery_tasks.py: .run() + patch self.retry.
"""

import os
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_celery.db")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

import pytest
from unittest.mock import AsyncMock, patch


def _patch_task_retry(task_func, exc_to_raise=None):
    """Патч self.retry на bound celery task (как в test_celery_tasks.py)."""
    task_instance = task_func.run.__self__
    patcher = patch.object(task_instance, "retry")
    mock_retry = patcher.start()
    mock_retry.side_effect = exc_to_raise or RuntimeError("retry-called")
    return mock_retry, patcher


class TestRunConverterPreviewStep:
    """run_converter_preview_step — вызов notify через _run_async."""

    def test_happy_path_calls_notify_completed(self):
        """После успешной конвертации вызывается _notify_step_completed."""
        mock_client = AsyncMock()
        mock_client.convert_preview.return_value = {
            "doc_code": "test-code",
            "title": "test",
            "document_type": "normative",
            "era": "USSR",
        }
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

            mock_retry, patcher = _patch_task_retry(run_converter_preview_step)

            result = run_converter_preview_step.run(
                task_id=1, draft_id=10, file_key="test.pdf"
            )

            patcher.stop()

        assert result == {"status": "completed", "step": "preview_converter", "task_id": 1}
        mock_client.convert_preview.assert_awaited_once()
        notify_completed.assert_awaited_once()

    def test_error_calls_notify_failed(self):
        """При ошибке конвертации вызывается _notify_step_failed."""
        mock_client = AsyncMock()
        mock_client.convert_preview.side_effect = Exception("Converter error")
        mock_client.close = AsyncMock()

        notify_failed = AsyncMock()

        with patch(
            "app.tasks.pipeline_formation.ConverterValidatorClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_failed",
            notify_failed,
        ):
            from app.tasks.pipeline_formation import run_converter_preview_step

            mock_retry, patcher = _patch_task_retry(
                run_converter_preview_step,
                exc_to_raise=RuntimeError("retry-called"),
            )

            with pytest.raises(RuntimeError, match="retry-called"):
                run_converter_preview_step.run(
                    task_id=1, draft_id=10, file_key="test.pdf"
                )

            patcher.stop()

        notify_failed.assert_awaited_once()
        args, _ = notify_failed.await_args
        assert args[0] == 1  # task_id
        assert args[1] == "preview_converter"  # step_name
        assert args[2] == "CONVERTER_ERROR"  # error_code
        assert "Converter error" in args[3]  # error_message
