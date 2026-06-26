"""Тесты пайплайна orchestrator_document_versions."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_document_versions import OrchestratorDocumentVersionsPipeline


class TestOrchestratorDocumentVersionsPipeline:
    """Пайплайн orchestrator_document_versions — 4 шага (версионирование)."""

    def test_pipeline_attributes(self):
        p = OrchestratorDocumentVersionsPipeline()
        assert p.name == "orchestrator_document_versions"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 3

    def test_build_steps_count(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 4, f"Ожидалось 4 шага, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание документа в Registry (через Gateway)",
            "Загрузка новой версии документа (через Gateway)",
            "Проверка списка версий (через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "gateway"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_doc_creation_step(self):
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        reg = steps[1]
        assert reg.service == "gateway"
        assert reg.method == "POST"
        assert reg.path == "/api/v1/registry/documents"
        assert reg.expected_status == {201, 409}
        assert reg.check is not None

    def test_version_upload_step(self):
        """Загрузка новой версии — POST /documents/{id}/versions."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        ver = steps[2]
        assert ver.service == "gateway"
        assert ver.method == "POST"
        assert "versions" in ver.path
        assert ver.expected_status == {200, 201, 404}
        assert ver.form_files is not None
        assert "file" in ver.form_files
        assert ver.form_files["file"][2] == "application/pdf"

    def test_versions_list_step(self):
        """Проверка списка версий — GET /documents/{id}/versions."""
        p = OrchestratorDocumentVersionsPipeline()
        steps = p.build_steps(PipelineContext())
        lst = steps[3]
        assert lst.service == "gateway"
        assert lst.method == "GET"
        assert "versions" in lst.path
        assert lst.expected_status == {200, 404}
