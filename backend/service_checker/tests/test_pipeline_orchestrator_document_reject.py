"""Тесты пайплайна orchestrator_document_reject."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_document_reject import OrchestratorDocumentRejectPipeline


class TestOrchestratorDocumentRejectPipeline:
    """Пайплайн orchestrator_document_reject — 6 шагов (reject-ветка)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDocumentRejectPipeline()
        assert p.name == "orchestrator_document_reject"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 1

    def test_build_steps_count(self):
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 6, f"Ожидалось 6 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание черновика (через Gateway)",
            "Статус задачи (через Gateway)",
            "Детали черновика (через Gateway)",
            "Решение по черновику (reject, через Gateway)",
            "Проверка статуса после reject (через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "gateway"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]
        assert not auth.needs_auth

    def test_draft_creation_step(self):
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "gateway"
        assert draft.method == "POST"
        assert draft.path == "/api/v1/drafts"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.needs_auth
        assert draft.on_error is not None
        assert draft.form_body["source_type"] == "GOST"
        assert draft.form_files is not None
        assert draft.form_files["file"][2] == "application/pdf"

    def test_reject_step(self):
        """Шаг reject — action=reject, не approve."""
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        reject = steps[4]
        assert reject.expected_status == {200, 409}
        assert reject.service == "gateway"
        assert "reject" in reject.name.lower()
        assert reject.body["action"] == "reject"
        assert "approve" not in reject.body["action"]

    def test_final_check_step(self):
        """Последний шаг — проверка статуса после reject."""
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        final = steps[5]
        assert final.service == "gateway"
        assert final.method == "GET"
        assert "/drafts/{draft_id}" in final.path
        assert final.expected_status == {200, 404}

    def test_skip_if_on_post_draft_steps(self):
        """Шаги 3-6 (индексы 2-5) имеют skip_if."""
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(2, 6):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги пропускаются."""
        p = OrchestratorDocumentRejectPipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        for i in range(2, 6):
            assert steps[i].skip_if(ctx) is True

    def test_draft_detail_check_fields(self):
        """Детали черновика проверяют OR-7 поля."""
        p = OrchestratorDocumentRejectPipeline()
        steps = p.build_steps(PipelineContext())
        detail = steps[3]
        assert detail.service == "gateway"
        assert detail.path == "/api/v1/drafts/{draft_id}"
        assert detail.check is not None
