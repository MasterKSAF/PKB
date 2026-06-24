"""Тесты пайплайна orchestrator_draft_delete."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_draft_delete import OrchestratorDraftDeletePipeline


class TestOrchestratorDraftDeletePipeline:
    """Пайплайн orchestrator_draft_delete — 6 шагов (удаление черновика)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDraftDeletePipeline()
        assert p.name == "orchestrator_draft_delete"
        assert p.description
        assert "orchestrator" in p.services
        assert "auth" in p.services

    def test_build_steps_count(self):
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 6, f"Ожидалось 6 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание черновика",
            "Статус задачи (longpoll)",
            "Детали черновика",
            "Удаление черновика",
            "Проверка 404 после удаления",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "auth"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_draft_creation_step(self):
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "orchestrator"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.on_error is not None

    def test_delete_step(self):
        """Шаг удаления — DELETE /drafts/{draft_id}."""
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        delete = steps[4]
        assert delete.service == "orchestrator"
        assert delete.method == "DELETE"
        assert delete.path == "/api/v1/drafts/{draft_id}"
        assert delete.expected_status == {200, 204}
        assert delete.needs_auth

    def test_404_check_step(self):
        """Последний шаг — GET ожидает 404 (документ удалён)."""
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        check = steps[5]
        assert check.service == "orchestrator"
        assert check.method == "GET"
        assert check.path == "/api/v1/drafts/{draft_id}"
        assert check.expected_status == 404

    def test_skip_if_on_post_draft_steps(self):
        """Шаги 3-6 (индексы 2-5) имеют skip_if."""
        p = OrchestratorDraftDeletePipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(2, 6):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги пропускаются."""
        p = OrchestratorDraftDeletePipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        for i in range(2, 6):
            assert steps[i].skip_if(ctx) is True
