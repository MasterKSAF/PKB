"""Тесты пайплайна orchestrator_metadata_update."""
from __future__ import annotations

from pipelines.base import PipelineContext
from pipelines.orchestrator_metadata_update import OrchestratorMetadataUpdatePipeline


class TestOrchestratorMetadataUpdatePipeline:
    """Пайплайн orchestrator_metadata_update — 6 шагов (обновление метаданных)."""

    def test_pipeline_attributes(self):
        p = OrchestratorMetadataUpdatePipeline()
        assert p.name == "orchestrator_metadata_update"
        assert p.description
        assert "gateway" in p.services
        assert len(p.services) == 1

    def test_build_steps_count(self):
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        assert len(steps) == 6, f"Ожидалось 6 шагов, получено {len(steps)}"

    def test_build_steps_order(self):
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        expected_names = [
            "Аутентификация (через Gateway)",
            "Создание черновика (через Gateway)",
            "Статус задачи (через Gateway)",
            "Детали черновика (через Gateway)",
            "Обновление метаданных (через Gateway)",
            "Проверка обновлённых метаданных (через Gateway)",
        ]
        actual = [s.name for s in steps]
        assert actual == expected_names, f"Порядок шагов:\n{actual}"

    def test_auth_step(self):
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        auth = steps[0]
        assert auth.service == "gateway"
        assert auth.method == "POST"
        assert auth.path == "/api/v1/auth/token"
        assert auth.expected_status == 200
        assert auth.extract_keys == ["access_token", "refresh_token"]

    def test_draft_creation_step(self):
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        draft = steps[1]
        assert draft.service == "gateway"
        assert draft.expected_status == 202
        assert draft.extract_keys == ["draft_id", "task_id"]
        assert draft.on_error is not None

    def test_metadata_patch_step(self):
        """PATCH /drafts/{draft_id}/metadata — обновление метаданных."""
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        meta = steps[4]
        assert meta.service == "gateway"
        assert meta.method == "PATCH"
        assert meta.path == "/api/v1/drafts/{draft_id}/metadata"
        assert meta.expected_status == 200
        assert meta.body is not None
        assert "title" in meta.body
        assert "doc_code" in meta.body
        assert meta.needs_auth
        # Проверка check — ответ должен содержать draft_id, title, status
        assert meta.check is not None

    def test_metadata_verify_step(self):
        """GET /drafts/{draft_id} после обновления."""
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        verify = steps[5]
        assert verify.service == "gateway"
        assert verify.method == "GET"
        assert verify.path == "/api/v1/drafts/{draft_id}"
        assert verify.expected_status == 200

    def test_skip_if_on_post_draft_steps(self):
        """Шаги 3-6 (индексы 2-5) имеют skip_if."""
        p = OrchestratorMetadataUpdatePipeline()
        steps = p.build_steps(PipelineContext())
        for i in range(2, 6):
            assert steps[i].skip_if is not None, (
                f"Шаг '{steps[i].name}' (индекс {i}) должен иметь skip_if"
            )

    def test_draft_failed_context_skip(self):
        """При draft_failed=True шаги пропускаются."""
        p = OrchestratorMetadataUpdatePipeline()
        ctx = PipelineContext()
        ctx.set("draft_failed", True)
        steps = p.build_steps(ctx)
        for i in range(2, 6):
            assert steps[i].skip_if(ctx) is True
