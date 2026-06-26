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
        assert "gateway" in p.services
        assert len(p.services) == 4

    def test_build_steps_count(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 12, f"Ожидалось 12 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание документа в Registry (через Gateway)",
            "Первая попытка построения индекса (RAG Builder)",
            "Обновление метаданных документа (через Gateway)",
            "Повторное построение индекса (RAG Builder)",
            "Поиск по индексу RAG Search (RAG Search)",
            "Удаление документа из Registry (через Gateway)",
            "Удаление индекса RAG (RAG Builder)",
            "Поиск — проверка пустого результата (RAG Search)",
            "Воссоздание документа в Registry (через Gateway)",
            "Финальное построение индекса (RAG Builder)",
            "Финальный поиск по индексу (RAG Search)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_step_ports(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.port > 0, f"Шаг '{step.name}' имеет порт 0"
            assert step.method in ("GET", "POST", "PUT", "PATCH", "DELETE")

    def test_build_steps_no_422(self):
        """Шаги build не содержат 422 в expected_status."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        build_steps = [s for s in steps if s.path == "/api/v1/rag/build" and s.method == "POST"]
        for s in build_steps:
            assert 422 not in s.expected_status, (
                f"Шаг '{s.name}' не должен содержать 422"
            )

    def test_both_build_steps_use_doc_id(self):
        """Шаги 3 и 5 используют {doc_id} из контекста."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step3 = steps[2]
        step5 = steps[4]
        for s in [step3, step5]:
            assert "{doc_id}" in str(s.body), f"'{s.name}' должен использовать doc_id из контекста"


    def test_step6_rag_search_no_on_error(self):
        """Шаг 6 (RAG Search) больше не имеет on_error."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step6 = steps[5]  # "Поиск по индексу RAG Search"
        assert step6.service == "rag_search"
        assert step6.on_error is None

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

    def test_recovery_runs_regardless(self):
        """Шаг 5 (recovery) выполняется всегда, без skip_if и on_error."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step5 = steps[4]
        assert step5.skip_if is None
        assert step5.on_error is None
        assert step5.service == "rag_builder"
        assert step5.method == "POST"

    def test_step2_extracts_doc_id(self):
        """Шаг 2 извлекает doc_id из Registry (через Gateway)."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step2 = steps[1]  # "Создание документа в Registry (через Gateway)"
        assert step2.name == "Создание документа в Registry (через Gateway)"
        assert step2.extract_keys == ["doc_id"]

    def test_step10_extracts_doc_id_2(self):
        """Шаг 10 извлекает doc_id_2 из Registry (для второго документа)."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step10 = steps[9]  # "Воссоздание документа в Registry (через Gateway)"
        assert step10.name == "Воссоздание документа в Registry (через Gateway)"
        assert step10.extract_keys == ["doc_id_2"]

    def test_initial_status(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.status == StepStatus.PENDING, f"Шаг '{step.name}' должен быть PENDING"
