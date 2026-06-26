"""Тесты пайплайна orchestrator_full_document_lifecycle."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_full_document_lifecycle import OrchestratorFullDocumentLifecyclePipeline


class TestOrchestratorFullDocumentLifecyclePipeline:
    """Пайплайн orchestrator_full_document_lifecycle — 11 шагов (полный цикл)."""

    def test_pipeline_attributes(self):
        p = OrchestratorFullDocumentLifecyclePipeline()
        assert p.name == "orchestrator_full_document_lifecycle"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 5

    def test_build_steps_count(self):
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 11, f"Ожидалось 11 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание черновика (через Gateway)",
            "Статус задачи (через Gateway)",
            "Детали черновика (через Gateway)",
            "Запуск превью черновика (через Gateway)",
            "Статус превью (через Gateway)",
            "Решение по черновику (approve, через Gateway)",
            "Проверка документа в Registry (через Gateway)",
            "Индексация документа (RAG Builder)",
            "Поиск RAG Search (RAG Search)",
            "Удаление черновика (через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "gateway"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_draft_creation_step(self):
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "gateway"
        assert draft.expected_status == {202, 409}
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.on_error is not None

    def test_preview_steps(self):
        """Шаги превью корректно настроены."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        # Запуск превью
        preview_start = steps[4]
        assert preview_start.service == "gateway"
        assert preview_start.method == "POST"
        assert preview_start.path == "/api/v1/drafts/{draft_id}/preview"
        assert preview_start.expected_status == {200, 202, 404}
        # Статус превью
        preview_status = steps[5]
        assert preview_status.service == "gateway"
        assert preview_status.method == "GET"
        assert preview_status.path == "/api/v1/drafts/{draft_id}/preview/status"
        assert preview_status.expected_status == {200, 404}
        assert preview_status.params == {"longpoll": 1}

    def test_decide_step(self):
        """Шаг approve — action=approve."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        decide = steps[6]
        assert decide.expected_status == {200, 409}
        assert decide.body["action"] == "approve"
        assert "decision" not in decide.body

    def test_registry_check(self):
        """Проверка документа в Registry."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        reg = steps[7]
        assert reg.service == "gateway"
        assert reg.path == "/api/v1/registry/documents/{approved_doc_id}"
        assert reg.expected_status == {200, 404}

    def test_rag_build_step(self):
        """Индексация в RAG Builder (напрямую)."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        rag = steps[8]
        assert rag.service == "rag_builder"
        assert rag.method == "POST"
        assert rag.path == "/api/v1/rag/build"
        assert rag.expected_status == {200, 201, 202}
        assert rag.body is not None
        assert rag.body["document_id"] == "{approved_doc_id}"

    def test_rag_search_step(self):
        """Поиск RAG Search (напрямую)."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        search = steps[9]
        assert search.service == "rag_search"
        assert search.method == "POST"
        assert search.path == "/api/v1/rag/search"
        assert search.expected_status == 200
        assert search.body is not None
        assert "query" in search.body

    def test_delete_step(self):
        """Удаление черновика."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        delete = steps[10]
        assert delete.service == "gateway"
        assert delete.method == "DELETE"
        assert delete.path == "/api/v1/drafts/{draft_id}"
        assert delete.expected_status == {200, 204}

    def test_skip_if_on_draft_steps(self):
        """Шаги 3-7 (индексы 2-6) имеют skip_if от draft."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(2, 7):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_skip_if_on_post_approve_steps(self):
        """Шаги 8-10 имеют skip_if по approved_doc_id."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(7, 11):
            assert steps[i].skip_if is not None

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги 3-7 пропускаются."""
        p = OrchestratorFullDocumentLifecyclePipeline()
        steps = p.build_steps(PipelineContext())
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        for i in range(2, 7):
            assert steps[i].skip_if(ctx) is True
