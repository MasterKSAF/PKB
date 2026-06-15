"""Тесты пайплайна full_document_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext, StepStatus
from pipelines.full_document_lifecycle import FullDocumentLifecyclePipeline


class TestSaveUuidForBuild:
    """Тесты _save_uuid_for_build — конвертация BIGINT→UUID с warning."""

    def test_converts_int_to_uuid(self):
        ctx = PipelineContext()
        ctx.set("doc_id", 42)
        check_fn = FullDocumentLifecyclePipeline._save_uuid_for_build("doc_id", "doc_id_uuid")
        ok, msg = check_fn('{}', ctx)
        assert ok
        assert ctx.get("doc_id_uuid") == "00000000-0000-0000-0000-00000000002a"
        assert "42" in msg
        assert "00000000-0000-0000-0000-00000000002a" in msg

    def test_skips_when_missing_from_context(self):
        ctx = PipelineContext()
        check_fn = FullDocumentLifecyclePipeline._save_uuid_for_build("missing_key", "dst_key")
        ok, msg = check_fn('{}', ctx)
        assert ok
        assert "skipping UUID conversion" in msg
        assert ctx.get("dst_key") is None

    def test_works_with_step_2_registry_create(self):
        """Интеграционный тест: шаг 2 (Registry) → extract doc_id → _save_uuid_for_build.
        Проверяет что PipelineStep с check=_save_uuid_for_build корректно настраивается."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step2 = steps[1]  # "Создание документа в Registry"
        assert step2.name == "Создание документа в Registry"
        assert step2.check is not None
        assert step2.extract_keys == ["doc_id"]


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

    def test_build_steps_no_422(self):
        """Шаги RAG Builder build (3, 5, 11) не содержат 422 в expected_status.

        Шаг 3 и 5 используют UUID — 422 не ожидается.
        Шаг 11 использует doc_id2_uuid — 422 не ожидается.
        """
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        build_steps = [s for s in steps if s.service == "rag_builder" and s.method == "POST"]
        for s in build_steps:
            assert 422 not in s.expected_status, (
                f"Шаг '{s.name}' не должен содержать 422"
            )

    def test_both_build_steps_use_uuid(self):
        """Шаги 3 и 5 используют UUID ({doc_id_uuid})."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step3 = steps[2]
        step5 = steps[4]
        for s in [step3, step5]:
            assert "{doc_id_uuid}" in str(s.body), f"'{s.name}' должен использовать UUID"
            assert "{doc_id}" not in str(s.body), f"'{s.name}' НЕ должен использовать raw BIGINT"

    def test_recovery_runs_always(self):
        """Шаг 5 (recovery) выполняется всегда — нет skip_if."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step5 = steps[4]
        assert step5.skip_if is None, "recovery должен выполняться всегда (без skip_if)"

    def test_step6_rag_search_has_on_error(self):
        """Шаг 6 (RAG Search) имеет on_error для известной ошибки bigint=uuid."""
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        step6 = steps[5]  # "Поиск по индексу RAG Search"
        assert step6.service == "rag_search"
        assert step6.on_error is not None, (
            "Шаг 6 должен иметь on_error для известной ошибки bigint=uuid"
        )

    def test_on_rag_search_error_sets_context(self):
        """_on_rag_search_error распознаёт 'bigint = uuid'."""
        ctx = PipelineContext()
        body = '{"error": {"message": "Search failed: operator does not exist: bigint = uuid"}}'
        FullDocumentLifecyclePipeline._on_rag_search_error(body, ctx)
        assert ctx.get("rag_search_bigint_uuid") is True

    def test_on_rag_search_error_ignores_other(self):
        ctx = PipelineContext()
        FullDocumentLifecyclePipeline._on_rag_search_error('{"error": "x"}', ctx)
        assert ctx.get("rag_search_bigint_uuid") is None

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

    def test_initial_status(self):
        p = FullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for step in steps:
            assert step.status == StepStatus.PENDING, f"Шаг '{step.name}' должен быть PENDING"
