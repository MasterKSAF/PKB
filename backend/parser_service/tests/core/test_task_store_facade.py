"""
Тесты для фасада TaskStore (объединяет хранилище, нотификатор и кеш).
"""
import pytest
from unittest.mock import AsyncMock
from app.core.task_store_facade import TaskStore
from app.core.task_models import TaskInfo


class TestTaskStoreFacade:
    @pytest.fixture
    def store(self):
        return TaskStore(ttl_seconds=3600)

    def test_add_and_get(self, store):
        task = TaskInfo(1, "v", "k", {})
        store.add(task)
        assert store.get(1) == task

    def test_get_active_tasks(self, store):
        t1 = TaskInfo(1, "v", "k", {})
        t1.status = "accepted"
        t2 = TaskInfo(2, "v", "k", {})
        t2.status = "completed"
        store.add(t1)
        store.add(t2)
        active = store.get_active_tasks()
        assert len(active) == 1
        assert active[0].task_id == 1

    @pytest.mark.asyncio
    async def test_update_task_notifies(self, store):
        task = TaskInfo(1, "v", "k", {})
        store.add(task)
        store._notifier.notify_task_changed = AsyncMock()
        await store.update_task(1, progress_percent=50)
        assert task.progress_percent == 50
        store._notifier.notify_task_changed.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_wait_for_change_delegates_to_notifier(self, store):
        store._notifier.wait_for_task_change = AsyncMock(return_value=True)
        result = await store.wait_for_change(1, 0, 1.0)
        assert result is True
        store._notifier.wait_for_task_change.assert_called_once_with(1, 0, 1.0)

    @pytest.mark.asyncio
    async def test_remove_task(self, store):
        task = TaskInfo(1, "v", "k", {})
        store.add(task)
        store._notifier.cleanup_task = AsyncMock()
        await store.remove_task(1)
        assert store.get(1) is None
        store._notifier.cleanup_task.assert_called_once_with(1)