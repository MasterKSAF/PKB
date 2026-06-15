"""Тесты пайплайна full_document_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext, StepStatus
from pipelines.full_document_lifecycle import FullDocumentLifecyclePipeline


class TestFullDocumentLifecyclePipeline:
    """Пайплайн full_document_lifecycle — 12 шагов с ветвлением."""

    def test_pipeline_attributes(self):
        p = FullDocumentLifecyclePipeline()
        assert p.name == "full_document_lifecycle"
        assert p.description
        assert len(p.services) >= 4

    def test_build_steps_count(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 12, f"Ожидалось 12 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание документа в Registry",
            "Первая попытка построения индекса",
            "Обновление метаданных документа",
            "Повторное построение индекса (recovery)",
            "Поиск по индексу RAG Search",
            "Удаление документа из Registry",
            "Удаление индекса RAG",
            "Поиск — проверка пустого результата",
            "Воссоздание документа в Registry",
            "Финальное построение индекса",
            "Финальный поиск по индексу",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_step_ports(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.port > 0, f"Шаг '{step.name}' имеет порт 0"
            assert step.method in ("GET", "POST", "PUT", "PATCH", "DELETE")

    def test_build_has_on_error_not_422(self):
        """Шаги RAG Builder build (3, 5, 11) НЕ включают 422 в expected_status.

        Вместо этого используется on_error для фиксации ошибки в контексте.
        """
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        build_steps = [s for s in steps if s.service == "rag_builder" and s.method == "POST"]
        for s in build_steps:
            assert 422 not in s.expected_status, (
                f"Шаг '{s.name}' не должен содержать 422 — on_error вместо обхода"
            )
            assert s.on_error is not None, (
                f"Шаг '{s.name}' должен иметь on_error для recovery-ветвления"
            )

    def test_build_on_error_sets_context(self):
        """on_error при ошибке build устанавливает build_ok=False в контексте."""
        ctx = PipelineContext()
        FullDocumentLifecyclePipeline._on_build_error(None, ctx)
        assert ctx.get("build_ok") is False

    def test_build_check_sets_context(self):
        """check при успешном build устанавливает build_ok=True в контексте."""
        import json
        ctx = PipelineContext()
        ok, msg = FullDocumentLifecyclePipeline._check_build_ok(
            json.dumps({"status": "ok"}), ctx
        )
        assert ok
        assert ctx.get("build_ok") is True

    def test_skip_if_on_recovery_step(self):
        """Шаг 5 (recovery build) имеет skip_if — пропускается если первый build успешен."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        recovery_step = steps[4]  # "Повторное построение индекса (recovery)"
        assert recovery_step.skip_if is not None, "recovery шаг должен иметь skip_if"

        # Если build_ok=True — шаг пропускается
        ctx = PipelineContext()
        ctx.set("build_ok", True)
        assert recovery_step.skip_if(ctx), "skip_if должен вернуть True когда build_ok=True"

        # Если build_ok нет — шаг выполняется
        ctx2 = PipelineContext()
        assert not recovery_step.skip_if(ctx2), "skip_if должен вернуть False когда build_ok нет"

    def test_initial_status(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.status == StepStatus.PENDING, f"Шаг '{step.name}' должен быть PENDING"
