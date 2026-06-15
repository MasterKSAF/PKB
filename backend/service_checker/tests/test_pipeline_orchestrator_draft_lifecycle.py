"""Тесты пайплайна orchestrator_draft_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_draft_lifecycle import OrchestratorDraftLifecyclePipeline


class TestOrchestratorDraftLifecyclePipeline:
    """Пайплайн orchestrator_draft_lifecycle — 8 шагов."""

    def test_pipeline_attributes(self):
        p = OrchestratorDraftLifecyclePipeline()
        assert p.name == "orchestrator_draft_lifecycle"
        assert p.description
        assert "orchestrator" in p.services

    def test_build_steps_count(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 8, f"Ожидалось 8 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание черновика",
            "Статус задачи (longpoll)",
            "Детали черновика",
            "Запуск превью черновика",
            "Статус превью",
            "Решение по черновику (approve)",
            "Проверка 404 после решения",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_extract_keys(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[1].extract_keys == ["draft_id", "task_id"]

    def test_last_step_allows_404(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        last = steps[-1]
        assert 404 in last.expected_status

    def test_decide_step(self):
        """Шаг approve (decide) — ожидает action, не decision."""
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        decide = steps[6]
        assert decide.expected_status == {200, 409}
        assert decide.service == "orchestrator"
        assert "approve" in decide.name.lower()
        # Тело должно содержать action, не decision
        assert decide.body["action"] == "approve"
        assert "decision" not in decide.body
