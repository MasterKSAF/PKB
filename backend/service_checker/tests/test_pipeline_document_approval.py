"""Тесты пайплайна document_approval."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.document_approval import DocumentApprovalPipeline


class TestDocumentApprovalPipeline:
    """Пайплайн document_approval — 10 шагов (черновик → решение → Registry → индексация)."""

    def test_pipeline_attributes(self):
        p = DocumentApprovalPipeline()
        assert p.name == "document_approval"
        assert p.description
        assert "orchestrator" in p.services
        assert "registry" in p.services
        assert "rag_builder" in p.services
        assert "rag_search" in p.services

    def test_build_steps_count(self):
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 10, f"Ожидалось 10 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание черновика",
            "Статус задачи (longpoll)",
            "Детали черновика",
            "Запуск превью черновика",
            "Статус превью",
            "Решение по черновику (approve)",
            "Проверка document_id после approve",
            "Создание документа в Registry",
            "Индексация документа",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        """Первый шаг — аутентификация."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "auth"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]
        assert not auth.needs_auth

    def test_draft_creation_step(self):
        """Создание черновика через Orchestrator."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "orchestrator"
        assert draft.method == "POST"
        assert draft.path == "/api/v1/drafts/"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.needs_auth
        assert draft.on_error is not None
        # Проверка form_body полей
        assert draft.form_body is not None
        assert draft.form_body["source_type"] == "GOST"
        # Проверка form_files
        assert draft.form_files is not None
        assert "file" in draft.form_files
        file_tuple = draft.form_files["file"]
        assert len(file_tuple) == 3
        assert file_tuple[2] == "application/pdf"

    def test_decide_step(self):
        """Шаг approve (decide) — ожидает action, не decision."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        decide = steps[6]
        assert decide.expected_status == {200, 409}
        assert decide.service == "orchestrator"
        assert "approve" in decide.name.lower()
        # Тело должно содержать action, не decision
        assert decide.body["action"] == "approve"
        assert "decision" not in decide.body

    def test_registry_creation_step(self):
        """Создание документа в Registry."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        reg = steps[8]
        assert reg.service == "registry"
        assert reg.method == "POST"
        assert reg.path == "/api/v1/registry/documents"
        assert reg.expected_status == {201, 409}
        assert reg.extract_keys == ["doc_id"]
        assert reg.needs_auth
        # Проверка body — document_key не передаётся, title и doc_code есть
        assert reg.body is not None
        assert "title" in reg.body
        assert "doc_code" in reg.body

    def test_rag_build_step(self):
        """Индексация в RAG Builder."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        rag = steps[9]
        assert rag.service == "rag_builder"
        assert rag.method == "POST"
        assert rag.path == "/api/v1/rag/build"
        assert rag.expected_status == {200, 201, 202}
        assert rag.needs_auth
        # Проверка body
        assert rag.body is not None
        assert rag.body["document_id"] == "{doc_id}"
        assert len(rag.body["sections"]) == 1
        assert rag.body["sections"][0]["section_id"] == 1

    def test_skip_if_on_draft_steps(self):
        """Шаги после черновика имеют skip_if."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        # Шаги 3..9 (индексы 2..8) должны иметь skip_if
        # Шаг 1 (создание черновика) — не имеет skip_if, т.к. это точка входа
        for i in range(2, 9):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги пропускаются."""
        p = DocumentApprovalPipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        # Проверка, что skip_if вернёт True для зависимых шагов
        for i in range(2, 9):
            skip_fn = steps[i].skip_if
            assert skip_fn is not None
            assert skip_fn(ctx) is True, (
                f"Шаг '{steps[i].name}' должен пропускаться при draft_failed=True"
            )

    def test_draft_created_context_skip(self):
        """При успешном черновике skip_if возвращает False."""
        p = DocumentApprovalPipeline()
        ctx = PipelineContext()
        steps = p.build_steps(ctx)
        # По умолчанию draft_failed нет
        for i in range(2, 9):
            skip_fn = steps[i].skip_if
            assert skip_fn is not None
            assert skip_fn(ctx) is False, (
                f"Шаг '{steps[i].name}' не должен пропускаться при успешном черновике"
            )

    def test_draft_detail_check_fields(self):
        """Детали черновика проверяют OR-7 поля."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        detail = steps[3]
        assert detail.service == "orchestrator"
        assert detail.path == "/api/v1/drafts/{draft_id}"
        # Проверка, что check определён
        assert detail.check is not None

    def test_preview_steps(self):
        """Шаги превью корректно настроены."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        # Запуск превью
        preview_start = steps[4]
        assert preview_start.service == "orchestrator"
        assert preview_start.method == "POST"
        assert preview_start.path == "/api/v1/drafts/{draft_id}/preview"
        assert preview_start.expected_status == {200, 202, 404}
        assert preview_start.body == {}
        # Статус превью
        preview_status = steps[5]
        assert preview_status.service == "orchestrator"
        assert preview_status.method == "GET"
        assert preview_status.path == "/api/v1/drafts/{draft_id}/preview/status"
        assert preview_status.expected_status == {200, 404}
        assert preview_status.params == {"longpoll": 1}

    def test_auth_uses_test_credentials(self):
        """Аутентификация использует тестовые credentials."""
        p = DocumentApprovalPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.body["username"] == "admin@example.com"
        assert auth.body["password"] == "Admin1234!"
