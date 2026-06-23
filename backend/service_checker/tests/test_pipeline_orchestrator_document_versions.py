"""Тесты пайплайна orchestrator_document_versions."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_document_versions import OrchestratorDocumentVersionsPipeline


class TestOrchestratorDocumentVersionsPipeline:
    """Пайплайн orchestrator_document_versions — 9 шагов (версионирование)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDocumentVersionsPipeline()
        assert p.name == "orchestrator_document_versions"
        assert p.description
        assert "orchestrator" in p.services
        assert "registry" in p.services

    def test_build_steps_count(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 9, f"Ожидалось 9 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация",
            "Создание черновика",
            "Статус задачи (longpoll)",
            "Детали черновика",
            "Решение по черновику (approve)",
            "Проверка document_id после approve",
            "Создание документа в Registry",
            "Загрузка новой версии документа",
            "Проверка списка версий",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "auth"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_draft_creation_step(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "orchestrator"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.on_error is not None

    def test_decide_step(self):
        """Шаг approve — action=approve."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        decide = steps[4]
        assert decide.expected_status == {200, 409}
        assert decide.body["action"] == "approve"

    def test_registry_create_step(self):
        """Создание документа в Registry."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        reg = steps[6]
        assert reg.service == "registry"
        assert reg.method == "POST"
        assert reg.path == "/api/v1/registry/documents"
        assert reg.expected_status == {201, 409}
        assert reg.extract_keys == ["doc_id"]

    def test_version_upload_step(self):
        """Загрузка новой версии — POST /documents/{id}/versions."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        ver = steps[7]
        assert ver.service == "orchestrator"
        assert ver.method == "POST"
        assert "versions" in ver.path
        assert ver.expected_status == {200, 201}
        assert ver.extract_keys == ["new_version_id"]
        assert ver.form_files is not None
        assert "file" in ver.form_files
        assert ver.form_files["file"][2] == "application/pdf"

    def test_versions_list_step(self):
        """Проверка списка версий — GET /documents/{id}/versions."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        lst = steps[8]
        assert lst.service == "orchestrator"
        assert lst.method == "GET"
        assert "versions" in lst.path
        assert lst.expected_status == 200
        # Проверка check — ответ содержит document_id, versions, meta
        assert lst.check is not None

    def test_skip_if_on_draft_steps(self):
        """Шаги 3-6 (индексы 2-5) имеют skip_if."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(2, 6):
            assert steps[i].skip_if is not None

    def test_skip_if_on_registry_and_versions(self):
        """Шаги 7-9 имеют skip_if по approved_doc_id."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(6, 9):
            assert steps[i].skip_if is not None

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги 3-6 пропускаются."""
        p = OrchestratorDocumentVersionsPipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        for i in range(2, 6):
            assert steps[i].skip_if(ctx) is True
