"""Тесты пайплайна orchestrator_draft_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_draft_lifecycle import OrchestratorDraftLifecyclePipeline


class TestOrchestratorDraftLifecyclePipeline:
    """Пайплайн orchestrator_draft_lifecycle — 11 шагов через Gateway."""

    def test_pipeline_attributes(self):
        p = OrchestratorDraftLifecyclePipeline()
        assert p.name == "orchestrator_draft_lifecycle"
        assert p.description
        assert "gateway" in p.services

    def test_build_steps_count(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 11, f"Ожидалось 11 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание черновика (через Gateway)",
            "Статус задачи (через Gateway)",
            "Детали черновика (через Gateway)",
            "Запуск превью (через Gateway)",
            "Статус превью (через Gateway)",
            "Решение approve (через Gateway)",
            "Проверка document_id (через Gateway)",  # OR-13
            "Проверка документа в Registry (через Gateway)",  # OR-13
            "Создание черновика image/png (через Gateway)",  # OR-14
            "Статус задачи image (через Gateway)",  # OR-14
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_all_steps_use_gateway(self):
        """Все шаги должны идти через service='gateway'."""
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for i, step in enumerate(steps):
            assert step.service == "gateway", (
                f"Шаг {i} «{step.name}» использует service={step.service!r}, ожидался 'gateway'"
            )

    def test_draft_creation_path_no_trailing_slash(self):
        """POST /drafts без слеша — чтобы FastAPI не редиректил (307)."""
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        create = steps[1]
        assert create.path == "/api/v1/drafts"
        assert create.method == "POST"
        assert create.expected_status == {202, 409}

    def test_extract_keys(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[1].extract_keys == ["draft_id", "task_id"]

    def test_last_step_allows_skip_if(self):
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        last = steps[-1]
        assert last.service == "gateway"
        expected = last.expected_status
        if isinstance(expected, set):
            assert 200 in expected
        else:
            assert expected == 200

    def test_or14_mime_branching(self):
        """OR-14: черновик с image/png через Gateway."""
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        img_draft = steps[9]
        assert "image/png" in str(img_draft.form_files.get("file", ()))
        assert img_draft.expected_status == {202, 409}
        assert img_draft.extract_keys == ["draft_id_2", "task_id_2"]
        assert img_draft.path == "/api/v1/drafts"  # без слеша
        img_status = steps[10]
        assert img_status.service == "gateway"
        assert img_status.path == "/api/v1/tasks/{task_id_2}/status"

    def test_decide_step(self):
        """Шаг approve (decide) — ожидает action, не decision."""
        p = OrchestratorDraftLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        decide = steps[6]
        assert decide.expected_status == {200, 409}
        assert decide.service == "gateway"
        assert "approve" in decide.name.lower()
        assert decide.body["action"] == "approve"
        assert "decision" not in decide.body
