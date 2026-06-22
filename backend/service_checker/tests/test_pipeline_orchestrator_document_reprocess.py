"""Тесты пайплайна orchestrator_document_reprocess."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_document_reprocess import OrchestratorDocumentReprocessPipeline


class TestOrchestratorDocumentReprocessPipeline:
    """Пайплайн orchestrator_document_reprocess — 9 шагов (переиндексация)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDocumentReprocessPipeline()
        assert p.name == "orchestrator_document_reprocess"
        assert p.description
        assert "orchestrator" in p.services
        assert "registry" in p.services

    def test_build_steps_count(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 9, f"Ожидалось 9 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание черновика",
            "Статус задачи (longpoll)",
            "Детали черновика",
            "Решение по черновику (approve)",
            "Проверка document_id после approve",
            "Проверка документа в Registry",
            "Переиндексация документа",
            "Статус задачи переиндексации",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "auth"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_draft_creation_step(self):
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "orchestrator"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.on_error is not None

    def test_decide_step(self):
        """Шаг approve — action=approve."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        decide = steps[4]
        assert decide.expected_status == {200, 409}
        assert decide.service == "orchestrator"
        assert decide.body["action"] == "approve"

    def test_doc_id_check(self):
        """Шаг 6 — проверка document_id после approve."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        doc_check = steps[5]
        assert doc_check.service == "orchestrator"
        assert doc_check.path == "/api/v1/drafts/{draft_id}"
        assert doc_check.expected_status == {200, 404}
        assert doc_check.check is not None

    def test_registry_check(self):
        """Шаг 7 — проверка в Registry."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        reg = steps[6]
        assert reg.service == "registry"
        assert reg.path == "/api/v1/registry/documents/{approved_doc_id}"
        assert reg.expected_status == {200, 404}

    def test_reprocess_step(self):
        """Шаг переиндексации — POST /documents/{id}/reprocess."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        repro = steps[7]
        assert repro.service == "orchestrator"
        assert repro.method == "POST"
        assert "reprocess" in repro.path
        assert repro.expected_status == 202
        assert repro.extract_keys == ["reprocess_task_id"]
        assert repro.body is not None
        assert repro.body["mode"] == "full"

    def test_reprocess_status_step(self):
        """Шаг 9 — статус задачи переиндексации."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        status = steps[8]
        assert status.service == "orchestrator"
        assert status.method == "GET"
        assert "{reprocess_task_id}" in status.path
        assert status.expected_status == 200

    def test_skip_if_on_draft_steps(self):
        """Шаги 3-6 (индексы 2-5) имеют skip_if."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(2, 6):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_skip_if_on_registry_and_reprocess(self):
        """Шаги 7-9 имеют skip_if по approved_doc_id / reprocess_task_id."""
        p = OrchestratorDocumentReprocessPipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(6, 9):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги 3-6 пропускаются."""
        p = OrchestratorDocumentReprocessPipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        for i in range(2, 6):
            assert steps[i].skip_if(ctx) is True
