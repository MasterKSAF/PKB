"""
Тесты для TaskInfo и TaskStatus.
"""
import pytest
from datetime import datetime, timezone
from app.core.task_models import TaskInfo, TaskStatus


class TestTaskInfo:
    def test_create_task_info(self):
        """Проверка инициализации TaskInfo со всеми стандартными полями."""
        task = TaskInfo(task_id=42, version_id="v1", file_key="test.pdf", options={"opt": True})
        assert task.task_id == 42
        assert task.version_id == "v1"
        assert task.file_key == "test.pdf"
        assert task.options == {"opt": True}
        assert task.status == TaskStatus.ACCEPTED
        assert task.progress_percent == 0
        assert task.step == "accepted"
        assert task.step_detail == "Задача принята"   # исправлено: сравнение, а не присваивание
        assert task.get_version() == 0
        # Проверяем, что started_at имеет часовой пояс (timezone-aware)
        assert task.started_at.tzinfo is not None

    def test_update_changes_version(self):
        """Каждое обновление увеличивает внутреннюю версию."""
        task = TaskInfo(1, "v", "k", {})
        old_version = task.get_version()
        task.update(progress_percent=50, step="parsing")
        assert task.progress_percent == 50
        assert task.step == "parsing"
        assert task.get_version() == old_version + 1

    def test_multiple_updates(self):
        """Последовательные обновления инкрементируют версию."""
        task = TaskInfo(1, "v", "k", {})
        versions = []
        for i in range(3):
            task.update(pages_total=i+1)
            versions.append(task.get_version())
        assert versions == [1, 2, 3]