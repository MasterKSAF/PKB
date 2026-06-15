"""Тесты пайплайна multi_document_cross_search."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.multi_document_cross_search import MultiDocumentCrossSearchPipeline


class TestMultiDocumentCrossSearchPipeline:
    """Пайплайн multi_document_cross_search — 19 шагов."""

    def test_pipeline_attributes(self):
        p = MultiDocumentCrossSearchPipeline()
        assert p.name == "multi_document_cross_search"
        assert p.description
        assert len(p.services) >= 4

    def test_build_steps_count(self):
        p = MultiDocumentCrossSearchPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 19, f"Ожидалось 19 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = MultiDocumentCrossSearchPipeline()
        steps = p.build_steps(PipelineContext())
        names = [s.name for s in steps]
        assert names[0] == "Аутентификация"
        assert "Загрузка PDF #1" in names[2]
        assert "Загрузка PDF #2" in names[9]
        assert "Поиск по общему запросу" in names[16]
        assert "Поиск после удаления" in names[18]

    def test_two_documents_processed(self):
        p = MultiDocumentCrossSearchPipeline()
        steps = p.build_steps(PipelineContext())
        names = [s.name for s in steps]
        doc1_related = [n for n in names if "#1" in n]
        doc2_related = [n for n in names if "#2" in n]
        assert len(doc1_related) >= 2
        assert len(doc2_related) >= 2

    def test_minio_bucket_step(self):
        p = MultiDocumentCrossSearchPipeline()
        steps = p.build_steps(PipelineContext())
        assert steps[1].service == "minio"
        assert steps[1].path == "/documents"

    def test_no_422_workaround_on_build_steps(self):
        """RAG Builder build шаги (9, 16) не содержат 422 в expected_status."""
        p = MultiDocumentCrossSearchPipeline()
        steps = p.build_steps(PipelineContext())
        # Шаг 9 — построение индекса #1
        build_1 = steps[8]
        assert build_1.service == "rag_builder"
        assert 422 not in build_1.expected_status, (
            "Шаг build #1 не должен содержать 422 (silent workaround)"
        )
        # Шаг 16 — построение индекса #2
        build_2 = steps[15]
        assert build_2.service == "rag_builder"
        assert 422 not in build_2.expected_status, (
            "Шаг build #2 не должен содержать 422 (silent workaround)"
        )

    def test_rag_search_steps_have_on_error(self):
        """Шаги RAG Search (17, 19) имеют on_error для известной ошибки bigint=uuid."""
        p = MultiDocumentCrossSearchPipeline()
        steps = p.build_steps(PipelineContext())
        search_step_17 = steps[16]  # "Поиск по общему запросу"
        assert search_step_17.service == "rag_search"
        assert search_step_17.on_error is not None, (
            "Шаг 17 должен иметь on_error для известной ошибки bigint=uuid"
        )
        search_step_19 = steps[18]  # "Поиск после удаления"
        assert search_step_19.service == "rag_search"
        assert search_step_19.on_error is not None, (
            "Шаг 19 должен иметь on_error для известной ошибки bigint=uuid"
        )

    def test_on_rag_search_error_sets_context(self):
        """_on_rag_search_error распознаёт 'bigint = uuid' и устанавливает флаг."""
        ctx = PipelineContext()
        body = '{"error": {"message": "Search failed: operator does not exist: bigint = uuid"}}'
        MultiDocumentCrossSearchPipeline._on_rag_search_error(body, ctx)
        assert ctx.get("rag_search_bigint_uuid") is True

    def test_on_rag_search_error_ignores_other_errors(self):
        """_on_rag_search_error не срабатывает на другие ошибки."""
        ctx = PipelineContext()
        body = '{"error": {"message": "Connection refused"}}'
        MultiDocumentCrossSearchPipeline._on_rag_search_error(body, ctx)
        assert ctx.get("rag_search_bigint_uuid") is None

    def test_on_rag_search_error_ignores_empty_body(self):
        ctx = PipelineContext()
        MultiDocumentCrossSearchPipeline._on_rag_search_error(None, ctx)
        assert ctx.get("rag_search_bigint_uuid") is None
