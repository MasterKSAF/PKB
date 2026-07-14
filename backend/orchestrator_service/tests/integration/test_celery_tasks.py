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
            task_id=1, file_key="drafts/10/file.pdf", draft_id=DRAFT_ID, mode="preview", max_pages=3
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

    def test_failure_mid_retry_does_not_notify(self):
        """When OCR raises mid-retry, notify_failed is NOT called (only on last retry)."""
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

            mock_retry, retry_patcher = _patch_task_retry(
                run_ocr_preview_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_ocr_preview_step.run(
                        task_id=1,
                        draft_id=DRAFT_ID,
                        file_key="drafts/10/file.pdf",
                    )
            finally:
                retry_patcher.stop()

        # retries=0 < max_retries=3 : notify should NOT be called
        notify_failed.assert_not_awaited()
        mock_retry.assert_called_once()

    def test_failure_notifies_on_last_retry(self):
        """When OCR raises on the LAST attempt, notify_failed IS called."""
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

            # Simulate last retry attempt: retries = max_retries
            task_instance = run_ocr_preview_step.run.__self__
            original_retries = task_instance.request.retries
            task_instance.request.retries = task_instance.max_retries

            mock_retry, retry_patcher = _patch_task_retry(
                run_ocr_preview_step, exc_to_raise=RuntimeError("retry-called"),
            )
            try:
                with pytest.raises(RuntimeError, match="retry-called"):
                    run_ocr_preview_step.run(
                        task_id=1,
                        draft_id=DRAFT_ID,
                        file_key="drafts/10/file.pdf",
                    )
            finally:
                task_instance.request.retries = original_retries
                retry_patcher.stop()

        notify_failed.assert_awaited_once_with(
            1, "preview_ocr", "OCR_ERROR", "OCR service down",
        )
        mock_retry.assert_called_once()


class TestRunConverterPreviewStep:
    """Tests for run_converter_preview_step Celery task."""

    HAPPY_CONVERTER_RESPONSE = {
        "doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56",
        "title": "Test doc",
        "document_type": "normative",
        "era": "USSR",
        "validity_status": "active",
        "source_type": "GOST",
        "language": "ru",
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
            "metadata": {
                "doc_code": "&#1043;&#1054;&#1057;&#1058; 1234-56",
                "title": "Test doc",
                "document_type": "normative",
                "era": "USSR",
                "validity_status": "active",
                "source_type": "GOST",
                "language": "ru",
            },
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
        mock_client.get_document_sections = AsyncMock(return_value={
            "data": {"sections": []}
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

        # Verify service call — now calls update_draft_status with processing (final approved deferred to rag_index)
        mock_client.update_draft_status.assert_awaited_once_with(
            draft_id=DRAFT_ID, status="processing", document_id=42
        )
        mock_client.create_document.assert_not_called()

        # Verify notify
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 3
        assert args[1] == "registry_creation"
        assert args[2] == {"draft_id": DRAFT_ID, "document_id": 42}
        assert args[3] == {
            "registry_id": 42, "version_id": 421, "status": "registered",
            "document_id": 42, "sections": [],
        }

        assert result == {
            "status": "completed",
            "step": "registry_creation",
            "task_id": 3,
        }

    def test_with_document_data(self):
        """Registry step with converter document_data saves to Registry and reads sections with IDs."""
        mock_client = AsyncMock()
        mock_client.create_document = AsyncMock(return_value={
            "data": {
                "document_id": 42,
                "version_id": 421,
                "sections": [
                    {"section_id": 4201, "type": "text", "clause": "1", "path": "1", "page": 1},
                    {"section_id": 4202, "type": "text", "clause": "2", "path": "2", "page": 1},
                ],
                "registry": {"document_id": 42, "version_id": 421, "sections_count": 2},
            }
        })
        mock_client.get_document_sections = AsyncMock(return_value={
            "data": {
                "document": {"id": 42, "title": "Test"},
                "sections": [
                    {"section_id": 4201, "document_id": 42, "type": "text",
                     "clause": "1", "path": "1", "page": 1,
                     "content": {"text": "Section 1"}},
                    {"section_id": 4202, "document_id": 42, "type": "text",
                     "clause": "2", "path": "2", "page": 1,
                     "content": {"text": "Section 2"}},
                ],
            }
        })
        mock_client.update_draft_status = AsyncMock(return_value={
            "data": {"status": "approved", "document_id": 42}
        })
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        # document_data уже содержит metadata (doc_code, title) — как реальный конвертер
        document_data = {
            "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test Document"},
            "content": [
                {"clause": "1", "type": "text", "path": "1", "page": 1,
                 "content": {"text": "Section 1"}},
                {"clause": "2", "type": "text", "path": "2", "page": 1,
                 "content": {"text": "Section 2"}},
            ],
        }

        with patch(
            "app.tasks.pipeline_formation.RegistryServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_registry_step

            result = run_registry_step.run(
                task_id=3, draft_id=DRAFT_ID, document_id=42, version_id=421,
                document_data=document_data,
            )

        # Verify: create_document called with full payload
        mock_client.create_document.assert_awaited_once()
        payload = mock_client.create_document.await_args[0][0]
        assert payload.get("draft_id") == DRAFT_ID
        assert "document" in payload
        # document_data передаётся как есть (response_metadata НЕ мержится)
        assert payload["document"] == document_data

        # Verify: get_document_sections called to read sections with IDs
        mock_client.get_document_sections.assert_awaited_once_with(42)

        # Verify: update_draft_status still called (processing — final approved deferred to rag_index)
        mock_client.update_draft_status.assert_awaited_once_with(
            draft_id=DRAFT_ID, status="processing", document_id=42
        )

        # Verify notify contains sections in output_data
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[1] == "registry_creation"
        output = args[3]
        assert output["registry_id"] == 42
        assert "sections" in output
        assert len(output["sections"]) == 2
        assert output["sections"][0]["section_id"] == 4201
        assert output["sections"][1]["section_id"] == 4202
        assert output["document_id"] == 42

        assert result == {
            "status": "completed",
            "step": "registry_creation",
            "task_id": 3,
        }

    def test_response_metadata_not_merged_into_document(self):
        """Registry step does NOT merge response_metadata into document.metadata.

        Converter response metadata (schema, task_id, created_at, parser)
        must NOT be passed to Registry (Registries validated_v3 schema
        rejects unknown fields in document.metadata with HTTP 400).
        Only document_data["metadata"] (doc_code, title, era, source_type)
        should be in the payload.
        """
        mock_client = AsyncMock()
        mock_client.create_document = AsyncMock(return_value={
            "data": {"document_id": 42, "version_id": 421, "sections": [],
                     "registry": {"sections_count": 0}},
        })
        mock_client.get_document_sections = AsyncMock(return_value={
            "data": {"sections": []},
        })
        mock_client.update_draft_status = AsyncMock(return_value={
            "data": {"status": "approved", "document_id": 42}
        })
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        # document_data already contains metadata (from converter)
        document_data = {
            "source": {"file_name": "f-test.pdf", "page_count": 5},
            "metadata": {
                "doc_code": "22786-77",
                "title": "ГОСТ 22786-77 Трубы",
                "era": "USSR",
                "source_type": "GOST",
            },
            "content": [],
        }
        # metadata = response_metadata (schema, task_id, created_at, parser)
        # Registry rejects these inside document.metadata (HTTP 400)
        response_metadata = {
            "schema": "validated_v3",
            "task_id": 106,
            "created_at": "2026-07-01T08:16:08Z",
            "parser": {"name": "test", "version": "1.0"},
        }

        with patch(
            "app.tasks.pipeline_formation.RegistryServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_registry_step

            run_registry_step.run(
                task_id=3, draft_id=DRAFT_ID, document_id=42, version_id=421,
                document_data=document_data, metadata=response_metadata,
            )

        # Verify: create_document got metadata from document_data only
        mock_client.create_document.assert_awaited_once()
        payload = mock_client.create_document.await_args[0][0]
        doc_meta = payload["document"]["metadata"]

        # doc_code/title сохранились
        assert doc_meta.get("doc_code") == "22786-77"
        assert doc_meta.get("title") == "ГОСТ 22786-77 Трубы"
        assert doc_meta.get("era") == "USSR"
        assert doc_meta.get("source_type") == "GOST"

        # response_metadata НЕ попала в document.metadata
        assert doc_meta.get("schema") is None
        assert doc_meta.get("task_id") is None
        assert doc_meta.get("created_at") is None
        assert doc_meta.get("parser") is None

    def test_with_document_data_no_data_wrapper_breaks_doc_id(self):
        """РЕАЛЬНЫЙ Registry возвращает ответ БЕЗ 'data'-обёртки.

        Воспроизводит баг (Проблема 2a):
        - Registry API возвращает {"document_id": 42, "version_id": "v1-42", "sections": [...]}
          без обёртки 'data'.
        - run_registry_step ожидает doc_result["data"]["document_id"].
        - Из-за этого 'new_doc_id' = None, current_doc_id НЕ обновляется.
        - sections читаются для СТАРОГО document_id (не того, что создал Registry).
        """
        mock_client = AsyncMock()
        # Registry возвращает БЕЗ 'data' (как в реальном API)
        mock_client.create_document = AsyncMock(return_value={
            "document_id": 99,  # Registry создал doc_id=99 (новый!)
            "version_id": "v1-99",
            "sections": [{"section_id": 9901, "type": "text", "clause": "1"}],
            "registry": {"document_id": 99, "version_id": "v1-99"},
        })
        # get_document_sections для старого doc_id (42) возвращает пусто
        mock_client.get_document_sections = AsyncMock(return_value={
            "data": {"sections": []},  # для doc_id=42 секций нет
        })
        mock_client.update_draft_status = AsyncMock(return_value={
            "data": {"status": "approved", "document_id": 42}
        })
        mock_client.close = AsyncMock()

        notify_completed = AsyncMock()

        document_data = {
            "metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test Document"},
            "content": [
                {"clause": "1", "type": "text", "path": "1", "page": 1,
                 "content": {"text": "Section 1"}},
            ],
        }

        with patch(
            "app.tasks.pipeline_formation.RegistryServiceClient",
            return_value=mock_client,
        ), patch(
            "app.tasks.pipeline_formation._notify_step_completed",
            notify_completed,
        ):
            from app.tasks.pipeline_formation import run_registry_step

            result = run_registry_step.run(
                task_id=3, draft_id=DRAFT_ID, document_id=42, version_id=421,
                document_data=document_data,
            )

        # create_document БЫЛ вызван
        mock_client.create_document.assert_awaited_once()

        # get_document_sections вызван с ИСХОДНЫМ document_id=42, а НЕ 99
        mock_client.get_document_sections.assert_awaited_once_with(42)

        # Но Registry создал документ с id=99, а sections читались для 42
        # Поэтому sections пустые
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        output = args[3]
        # document_id остался исходным (42), не обновился на 99
        assert output.get("registry_id") == 42
        # sections пустые, хотя Registry создал их для doc_id=99
        sections = output.get("sections", [])
        assert len(sections) == 0, (
            f"БАГ: sections пустые, потому что читались для doc_id=42, "
            f"а не для 99 (который создал Registry)"
        )

    def test_create_document_upsert_by_draft_id(self):
        """Registry step должен обновлять существующий документ по draft_id,
        а НЕ создавать новый (Проблема 1: дублирование).

        Сейчас run_registry_step вызывает client.create_document() без передачи
        существующего document_id → Registry создаёт второй документ.
        """
        mock_client = AsyncMock()
        # Первый вызов create_document от approve_draft (уже создал doc_id=19, draft_id=110)
        # Второй вызов от run_registry_step с document_data — создаёт doc_id=20
        mock_client.create_document = AsyncMock(return_value={
            "data": {
                "document_id": 99,  # Registry мог создать новый (в mock - upsert, в real - новый)
                "version_id": 991,
                "sections": [{"section_id": 9901}],
                "registry": {"document_id": 99, "version_id": 991},
            }
        })
        mock_client.get_document_sections = AsyncMock(return_value={
            "data": {
                "sections": [{"section_id": 9901, "document_id": 99}],
            }
        })
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
                task_id=3, draft_id=DRAFT_ID, document_id=42, version_id=421,
                document_data={"metadata": {"doc_code": "ГОСТ 1234-56", "title": "Test"}, "content": [{"clause": "1"}]},
            )

        # create_document вызван с payload содержащим draft_id
        mock_client.create_document.assert_awaited_once()
        payload = mock_client.create_document.await_args[0][0]
        assert payload.get("draft_id") == DRAFT_ID

        # Mock: _mock_create_document делает upsert по draft_id
        #       Но реальный Registry НЕ делает — создаёт новый документ
        # В реальности: было два POST /documents → doc_id=19 и doc_id=20
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        output = args[3]
        # Проблема: registry_id в output не изменился на 99
        # (если бы ответ был без 'data', registry_id остался бы 42)
        # Но даже если бы обновился — Registry всё равно создал второй документ
        logger_output = output.get("registry_id", None)
        assert logger_output is not None


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
            task_id=4, file_key="drafts/10/file.pdf", draft_id=DRAFT_ID, mode="full"
        )

        # Verify notify
        notify_completed.assert_awaited_once()
        args, _ = notify_completed.await_args
        assert args[0] == 4
        assert args[1] == "full_ocr"
        assert args[2] == {"file_key": "drafts/10/file.pdf", "mode": "full", "draft_id": DRAFT_ID}
        assert args[3] == {"pages_processed": 15, "full_result": {"pages_processed": 15, "status": "completed"}, "status": "completed"}

        assert result == {
            "status": "completed",
            "step": "full_ocr",
            "task_id": 4,
        }
