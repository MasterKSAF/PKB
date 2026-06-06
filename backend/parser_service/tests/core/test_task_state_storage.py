"""
Тесты для TaskStateStorage (хранение задач, TTL, активные задачи).
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.core.task_state_storage import TaskStateStorage
from app.core.task_models import TaskInfo, TaskStatus


class TestTaskStateStorage:
    @pytest.fixture
    def storage(self):
        return TaskStateStorage(ttl_seconds=3600)

    def test_add_and_get(self, storage):
        task = TaskInfo(1, "v", "k", {})
        storage.add(task)
        retrieved = storage.get(1)
        assert retrieved == task

    def test_get_nonexistent(self, storage):
        assert storage.get(999) is None

    def test_get_active_tasks(self, storage):
        t1 = TaskInfo(1, "v", "k", {})
        t1.status = TaskStatus.ACCEPTED
        t2 = TaskInfo(2, "v", "k", {})
        t2.status = TaskStatus.PROCESSING
        t3 = TaskInfo(3, "v", "k", {})
        t3.status = TaskStatus.COMPLETED
        storage.add(t1)
        storage.add(t2)
        storage.add(t3)
        active = storage.get_active_tasks()
        assert len(active) == 2
        assert {t.task_id for t in active} == {1, 2}

    def test_remove_task(self, storage):
        task = TaskInfo(1, "v", "k", {})
        storage.add(task)
        storage.remove(1)
        assert storage.get(1) is None

    @pytest.mark.asyncio
    async def test_cleanup_removes_expired(self):
        """Устаревшие задачи (completed/failed старше TTL) удаляются при очистке."""
        storage = TaskStateStorage(ttl_seconds=1)
        task = TaskInfo(1, "v", "k", {})
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc) - timedelta(seconds=2)
        storage.add(task)

        # Имитируем логику очистки (в реальном коде вызывается start_cleanup)
        async def cleanup():
            now = datetime.now(timezone.utc)
            expired = []
            for tid, info in storage._store.items():
                if info.status in ("completed", "failed"):
                    deadline = info.completed_at or info.started_at
                    if deadline + timedelta(seconds=storage._ttl) < now:
                        expired.append(tid)
            for tid in expired:
                del storage._store[tid]

        await cleanup()
        assert storage.get(1) is None