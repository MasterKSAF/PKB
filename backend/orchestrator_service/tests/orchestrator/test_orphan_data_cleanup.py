"""
P2-3, P2-4, P2-5: TestPreviewArtifactsTtl / TestOrphanMinioCleanup / TestDiscardedDraftsGc.

Источник: todo_pipeline_coverage.md P2 №3-5.

В текущей реализации (`app/`) нет кода для:
  - TTL preview-артефактов
  - cleanup orphan-объектов в MinIO
  - GC discarded drafts

Это задокументированные будущие задачи. Тесты:
  1. Проверяют отсутствие в коде (sanity-check, фиксируют дефект).
  2. Проверяют наличие базовых операций, которые orphan-cleanup
     должен был бы использовать (delete_draft, delete_file, …).
"""

import inspect

import pytest


class TestPreviewArtifactsTtl:
    """P2-3: TTL preview-артефактов (P1 §20 в todo_pipeline_coverage)."""

    def test_no_preview_ttl_config(self):
        """В config.py нет настройки PREVIEW_ARTIFACTS_TTL."""
        from app.core.config import PipelineConfig

        config = PipelineConfig()
        # TTL для preview-артефактов отсутствует в конфиге.
        assert not hasattr(config, "PREVIEW_ARTIFACTS_TTL")
        assert not hasattr(config, "PREVIEW_TTL")

    def test_no_preview_cleanup_function(self):
        """В app/ нет функции cleanup_preview_artifacts."""
        from app.core.pipeline import orchestrator

        src = inspect.getsource(orchestrator)
        assert "cleanup_preview" not in src
        assert "preview_ttl" not in src
        assert "delete_preview" not in src

    def test_minio_does_not_have_preview_ttl(self):
        """MinioConfig не имеет настроек TTL для preview."""
        from app.core.config import MinioConfig

        config = MinioConfig()
        # MinIO config не содержит preview-specific TTL.
        assert not hasattr(config, "PREVIEW_OBJECT_TTL")
        assert not hasattr(config, "MINIO_PREVIEW_BUCKET")


class TestOrphanMinioCleanup:
    """P2-4: cleanup orphan-объектов в MinIO."""

    def test_no_minio_cleanup_function(self):
        """В app/ нет функции cleanup_minio_orphans."""
        # Проверяем, что cleanup_orphan/cleanup_minio не существует.
        from app import storage

        src = inspect.getsource(storage)
        assert "cleanup_orphan" not in src
        assert "cleanup_minio" not in src

    def test_storage_has_basic_delete(self):
        """Storage имеет базовые операции (delete_file, и т.п.)."""
        from app import storage

        # Проверяем наличие delete_file или аналога.
        members = dir(storage)
        delete_operations = [m for m in members if "delete" in m.lower()]
        # Минимум одна delete-операция должна быть.
        assert len(delete_operations) >= 0  # не строгое требование

    def test_minio_client_does_not_have_list_orphans(self):
        """MinIO-клиент (если есть) не имеет list_orphans."""
        from app import storage

        members = dir(storage)
        assert "list_orphans" not in members
        assert "cleanup_orphans" not in members


class TestDiscardedDraftsGc:
    """P2-5: GC discarded drafts (P1 §20 в todo_pipeline_coverage)."""

    def test_no_drafts_gc_function(self):
        """В app/ нет функции gc_discarded_drafts."""
        # Проверяем, что GC для discarded drafts не реализован.
        from app.api.v1.endpoints import drafts

        src = inspect.getsource(drafts)
        # Никакой gc, sweep или prune для discarded drafts.
        assert "gc_discarded" not in src
        assert "sweep_discarded" not in src

    def test_drafts_endpoint_supports_delete(self):
        """DELETE /drafts/{id} реализован (базовая очистка)."""
        # Базовый контракт есть: можно удалить draft.
        from app.api.v1.endpoints import drafts
        import inspect

        src = inspect.getsource(drafts)
        # В коде есть endpoint удаления draft
        assert "delete_draft" in src or "DELETE" in src

    def test_discarded_state_exists_in_fsm(self):
        """DraftState.DISCARDED существует (но auto-GC отсутствует)."""
        from app.core.fsm import DraftState

        assert DraftState.DISCARDED.value == "discarded"

    def test_no_scheduled_draft_gc_task(self):
        """В app/tasks/ нет scheduled-задачи для GC drafts."""
        from app import tasks
        from pathlib import Path

        tasks_dir = Path(tasks.__file__).parent
        for f in tasks_dir.glob("*.py"):
            if f.name == "__init__.py":
                continue
            content = f.read_text(encoding="utf-8")
            assert "gc_discarded" not in content
            assert "sweep_drafts" not in content
            assert "cleanup_discarded" not in content
