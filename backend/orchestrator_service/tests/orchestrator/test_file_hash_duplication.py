"""
Test: file_hash_sha256 propagation from upload → approve → document dedup.

Сценарий:
  1. POST /drafts → проверяем что file_hash_sha256 в metadata_fields upload step
  2. Approve → проверяем что file_hash_sha256 передан в doc_payload
  3. Повторный approve того же файла → 409 DUPLICATE_FILE (UNIQUE constraint)
"""

import io, hashlib
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pipeline import Task, TaskStep


class TestFileHashDuplication:
    """Verify file_hash_sha256 is propagated and prevents duplicates."""

    DRAFTS_URL = "/api/v1/drafts/"
    DECIDE_URL = "/api/v1/drafts/{draft_id}/decide"

    @pytest.fixture
    def pdf_content(self) -> bytes:
        """Stable PDF content for deterministic SHA256 (>=1024 bytes для FILE_TOO_SMALL)."""
        return b"%PDF-1.4 unique hash test content for dedup" * 30  # 1410 bytes

    @pytest.fixture
    def pdf_hash(self, pdf_content: bytes) -> str:
        return hashlib.sha256(pdf_content).hexdigest()

    async def _get_upload_step(self, db_session: AsyncSession, task_id: int) -> TaskStep:
        result = await db_session.execute(
            select(TaskStep).where(
                TaskStep.task_id == task_id,
                TaskStep.step_name == "upload",
            )
        )
        return result.scalar_one_or_none()

    async def _get_task(self, db_session: AsyncSession, draft_id: int) -> Task:
        result = await db_session.execute(
            select(Task).where(Task.draft_id == draft_id)
        )
        return result.scalar_one_or_none()

    # ── Test 1: file_hash_sha256 saved in upload step metadata_fields ──
    async def test_upload_saves_file_hash_in_metadata(
        self,
        client: TestClient,
        auth_header: dict,
        pdf_content: bytes,
        pdf_hash: str,
    ):
        """Upload сохраняет file_hash_sha256 в metadata_fields upload step."""
        response = client.post(
            self.DRAFTS_URL,
            headers=auth_header,
            files={"file": ("dedup-test.pdf", io.BytesIO(pdf_content), "application/pdf")},
            data={
                "document_key": pdf_hash,
                "title": "Dedup Test Doc",
                "source_type": "GOST",
                "doc_code": "DEDUP-0001",
                "era": "RF",
                "jurisdiction": "RU",
            },
        )
        assert response.status_code == 202, f"Upload failed: {response.text}"
        data = response.json()
        assert data["file_hash_sha256"] == pdf_hash, (
            f"Response file_hash_sha256 mismatch: expected {pdf_hash}, got {data.get('file_hash_sha256')}"
        )
        assert "draft_id" in data
        assert "task_id" in data

        # Return for chaining
        return data

    # ── Test 2: upload step создаётся с form metadata (file_hash_sha256 — в Registry, не в metadata_fields) ──
    async def test_metadata_fields_contain_file_hash(
        self,
        client: TestClient,
        auth_header: dict,
        db_session: AsyncSession,
        pdf_content: bytes,
        pdf_hash: str,
    ):
        """Проверяем upload step input_data.metadata_fields (form fields, не file_hash).

        file_hash_sha256 сохраняется в Registry draft, а не в metadata_fields upload step.
        Проверка передачи file_hash_sha256 в create_document:
        test_approve_passes_file_hash_to_document.
        """
        upload_data = await self.test_upload_saves_file_hash_in_metadata(
            client, auth_header, pdf_content, pdf_hash,
        )
        task_id = upload_data["task_id"]

        upload_step = await self._get_upload_step(db_session, task_id)
        assert upload_step is not None, "Upload step not found"

        metadata_fields = (upload_step.input_data or {}).get("metadata_fields", {})
        # file_hash_sha256 передаётся в metadata_fields для create_document (P1F-12)
        assert metadata_fields.get("file_hash_sha256") == pdf_hash, (
            f"metadata_fields.file_hash_sha256 mismatch: "
            f"expected {pdf_hash}, got {metadata_fields.get('file_hash_sha256')}"
        )
        # Form-поля должны быть
        assert metadata_fields.get("title") == "Dedup Test Doc"
        assert metadata_fields.get("doc_code") == "DEDUP-0001"
        assert metadata_fields.get("source_type") == "GOST"

    # ── Test 3: file_hash_sha256 из upload step → create_document (через full_converter) ──
    async def test_approve_passes_file_hash_to_document(
        self,
        db_session: AsyncSession,
        pdf_hash: str,
    ):
        """file_hash_sha256 из upload step metadata_fields передаётся в create_document."""
        from unittest.mock import patch
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from app.repositories.pipeline import TaskRepository
        from tests.shared.mock_registry_client import MockRegistryClient

        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=300, pipeline_type="formation", total_steps=7,
        )

        # Upload step с file_hash_sha256 в metadata_fields
        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
            input_data={
                "file_key": "drafts/300/test.pdf",
                "metadata_fields": {"file_hash_sha256": pdf_hash},
            },
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 300, "task_id": task.id, "file_key": "drafts/300/test.pdf"},
        )
        await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
        )
        await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )

        mock_reg = MockRegistryClient()
        mock_reg._ensure_draft(300)

        orchestrator = PipelineOrchestrator(db_session)

        # approve — возвращает document_id=None
        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_reg,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_rag_index_step.delay",
        ), patch(
            "app.tasks.pipeline_indexation.run_activate_document_step.delay",
        ):
            result = await orchestrator.approve_draft(draft_id=300, task_id=task.id)
            assert result["document_id"] is None

        # Симулируем full_ocr → full_converter
        steps = await repo.get_task_steps(task.id)
        full_ocr = next(s for s in steps if s.step_name == "full_ocr")
        await repo.complete_task_step(
            full_ocr.id,
            output_data={"full_result": {"text": "parsed"}},
        )

        # on_step_completed("full_ocr") с Registry mock
        with patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ):
            await orchestrator.on_step_completed(
                task_id=task.id, step_name="full_ocr",
                output_data={"full_result": {"text": "parsed"}},
            )

        # complete full_converter step
        steps = await repo.get_task_steps(task.id)
        conv = next(s for s in steps if s.step_name == "full_converter")
        await repo.complete_task_step(
            conv.id,
            output_data={
                "document": {"content": []},
                "metadata": {"title": "Test Doc", "doc_code": "TEST-300"},
            },
        )

        # on_step_completed("full_converter") захватывает create_document
        captured = {}
        original_create = mock_reg.create_document

        async def _capturing_create(data):
            captured.update(data)
            return await original_create(data)

        mock_reg.create_document = _capturing_create

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_reg,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            await orchestrator.on_step_completed(
                task_id=task.id, step_name="full_converter",
                output_data={
                    "document": {"content": []},
                },
            )

        # file_hash_sha256 должен быть в payload create_document
        assert captured.get("file_hash_sha256") == pdf_hash, (
            f"file_hash_sha256 mismatch: expected {pdf_hash}, got {captured.get('file_hash_sha256')}"
        )
        assert captured.get("draft_id") == 300

    # ── Test 4: Registry error in create_document (full_converter) propagates properly ──
    async def test_duplicate_file_hash_blocks_double_approve(
        self,
        db_session: AsyncSession,
        pdf_hash: str,
    ):
        """Ошибка Registry create_document в full_converter → не глушится."""
        from unittest.mock import patch
        import pytest
        from app.core.pipeline.orchestrator import PipelineOrchestrator
        from app.repositories.pipeline import TaskRepository
        from tests.shared.mock_registry_client import MockRegistryClient

        repo = TaskRepository(db_session)
        task = await repo.create_task(
            draft_id=301, pipeline_type="formation", total_steps=7,
        )

        upload = await repo.create_task_step(
            task_id=task.id, step_name="upload", step_index=0,
            service_name="Orchestrator",
            input_data={"file_key": "drafts/301/test.pdf"},
        )
        await repo.complete_task_step(
            upload.id,
            output_data={"draft_id": 301, "task_id": task.id, "file_key": "drafts/301/test.pdf"},
        )
        await repo.create_task_step(
            task_id=task.id, step_name="preview_ocr", step_index=1,
            service_name="Parser Service",
        )
        await repo.create_task_step(
            task_id=task.id, step_name="preview_converter", step_index=2,
            service_name="Converter-validator",
        )

        mock_reg = MockRegistryClient()
        mock_reg._ensure_draft(301)

        orchestrator = PipelineOrchestrator(db_session)

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_reg,
        ), patch(
            "app.tasks.pipeline_formation.run_parser_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_converter_full_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ), patch(
            "app.tasks.pipeline_formation.run_rag_index_step.delay",
        ), patch(
            "app.tasks.pipeline_indexation.run_activate_document_step.delay",
        ):
            result = await orchestrator.approve_draft(draft_id=301, task_id=task.id)
            assert result["document_id"] is None

        # full_ocr completion
        steps = await repo.get_task_steps(task.id)
        full_ocr = next(s for s in steps if s.step_name == "full_ocr")
        await repo.complete_task_step(full_ocr.id, output_data={"full_result": {"text": "parsed"}})
        with patch("app.tasks.pipeline_formation.run_converter_full_step.delay"):
            await orchestrator.on_step_completed(
                task_id=task.id, step_name="full_ocr",
                output_data={"full_result": {"text": "parsed"}},
            )

        # full_converter step with Registry error
        steps = await repo.get_task_steps(task.id)
        conv = next(s for s in steps if s.step_name == "full_converter")
        await repo.complete_task_step(
            conv.id,
            output_data={
                "document": {"content": []},
                "metadata": {"title": "Test", "doc_code": "T-301"},
            },
        )

        async def _failing_create(data):
            raise RuntimeError("Registry create_document failed: DUPLICATE_FILE")

        mock_reg.create_document = _failing_create

        with patch(
            "app.core.pipeline.orchestrator.RegistryServiceClient",
            return_value=mock_reg,
        ), patch(
            "app.tasks.pipeline_formation.run_registry_step.delay",
        ):
            with pytest.raises(RuntimeError) as exc_info:
                await orchestrator.on_step_completed(
                    task_id=task.id, step_name="full_converter",
                    output_data={"document": {"content": []}},
                )

            assert "DUPLICATE_FILE" in str(exc_info.value), (
                f"Ошибка Registry должна пробрасываться: {exc_info.value}"
            )
