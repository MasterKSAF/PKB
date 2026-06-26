"""Тесты пайплайна orchestrator_document_reprocess."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_document_reprocess import OrchestratorDocumentReprocessPipeline


class TestOrchestratorDocumentReprocessPipeline:
    """Пайплайн orchestrator_document_reprocess — 6 шагов (переиндексация)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDocumentReprocessPipeline()
        assert p.name == "orchestrator_document_reprocess"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 1

    def test_build_steps_count(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 6, f"Ожидалось 6 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание документа в Registry (через Gateway)",
            "Создание черновика (через Gateway)",
            "Статус задачи (через Gateway)",
            "Переиндексация документа (через Gateway)",
            "Статус задачи переиндексации (через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "gateway"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_doc_creation_step(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        doc = steps[1]
        assert doc.service == "gateway"
        assert doc.method == "POST"
        assert doc.path == "/api/v1/registry/documents"
        assert doc.expected_status == {201, 409}
        assert doc.check is not None

    def test_draft_creation_step(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[2]
        assert draft.service == "gateway"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.on_error is not None

    def test_reprocess_step(self):
        """Шаг переиндексации — POST /documents/{id}/reprocess."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        repro = steps[4]
        assert repro.service == "gateway"
        assert repro.method == "POST"
        assert "reprocess" in repro.path
        assert repro.expected_status == {202, 409}
        assert repro.extract_keys == ["reprocess_task_id"]
        assert repro.body is not None
        assert repro.body["mode"] == "full"

    def test_reprocess_status_step(self):
        """Статус задачи переиндексации."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        status = steps[5]
        assert status.service == "gateway"
        assert status.method == "GET"
        assert "{reprocess_task_id}" in status.path
        assert status.expected_status == 200
        assert status.skip_if is not None

    def test_skip_if_on_draft_steps(self):
        """Шаг 4 (индекс 3) имеет skip_if от draft."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[3].skip_if is not None, (
            f"Шаг '{steps[3].name}' должен иметь skip_if"
        )

    def test_skip_if_on_reprocess_steps(self):
        """Шаг 6 (индекс 5) имеет skip_if по reprocess_task_id."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[5].skip_if is not None

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаг 4 (индекс 3) пропускается."""
        p = OrchestratorDocumentReprocessPipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        assert steps[3].skip_if(ctx) is True
