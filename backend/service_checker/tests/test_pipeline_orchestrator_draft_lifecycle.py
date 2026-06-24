"""Тесты пайплайна orchestrator_draft_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_draft_lifecycle import OrchestratorDraftLifecyclePipeline


class TestOrchestratorDraftLifecyclePipeline:
    """Пайплайн orchestrator_draft_lifecycle — 11 шагов (+OR-13, +Registry check, +OR-14 MIME)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDraftLifecyclePipeline()
        assert p.name == "orchestrator_draft_lifecycle"
        assert p.description
        assert "orchestrator" in p.services

    def test_build_steps_count(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 11, f"Ожидалось 11 шагов, получено {len(steps)}"

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
            "Проверка document_id после approve",  # OR-13
            "Проверка документа в Registry",  # OR-13
            "Создание черновика (image/png для OR-14)",  # OR-14
            "Статус задачи image (OR-14)",  # OR-14
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_extract_keys(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[1].extract_keys == ["draft_id", "task_id"]

    def test_last_step_allows_skip_if(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        last = steps[-1]
        assert last.service == "orchestrator"
        # expected_status может быть int (200) или set ({200, 404})
        expected = last.expected_status
        if isinstance(expected, set):
            assert 200 in expected
        else:
            assert expected == 200

    def test_or14_mime_branching(self):
        """OR-14: черновик с image/png должен создаваться и иметь статус."""
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        img_draft = steps[9]  # Шаг 10 — создание image-черновика
        assert "image/png" in str(img_draft.form_files.get("file", ()))
        assert img_draft.expected_status == 202
        assert img_draft.extract_keys == ["draft_id_2", "task_id_2"]
        img_status = steps[10]  # Шаг 11 — статус
        assert img_status.service == "orchestrator"
        assert img_status.path == "/api/v1/tasks/{task_id_2}/status"

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
