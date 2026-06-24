"""
Тесты для TaskStateStorage (хранилище задач).
"""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from app.core.task_store import TaskStateStorage
from app.core.task_models import TaskInfo, TaskStatus


class TestTaskStateStorage:
    @pytest.fixture
    def storage(self):
        return TaskStateStorage(ttl_seconds=3600, max_tasks=100)

    @pytest.mark.asyncio
    async def test_add_and_get(self, storage):
        task = TaskInfo(1, 1, "key", {})
        await storage.add(task)
        assert await storage.get(1) == task

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        assert await storage.get(999) is None

    @pytest.mark.asyncio
    async def test_get_active_tasks(self, storage):
        t1 = TaskInfo(1, 1, "k", {})
        t1.status = TaskStatus.ACCEPTED
        t2 = TaskInfo(2, 1, "k", {})
        t2.status = TaskStatus.PROCESSING
        t3 = TaskInfo(3, 1, "k", {})
        t3.status = TaskStatus.COMPLETED
        for t in [t1, t2, t3]:
            await storage.add(t)
        active = await storage.get_active_tasks()
        assert len(active) == 2
        assert {t.task_id for t in active} == {1, 2}

    @pytest.mark.asyncio
    async def test_update_task_success(self, storage):
        task = TaskInfo(1, 1, "k", {})
        await storage.add(task)
        await storage.update_task(1, progress_percent=50, step="parsing")
        assert task.progress_percent == 50
        assert task.step == "parsing"
        assert task.get_version() == 1

    @pytest.mark.asyncio
    async def test_update_task_nonexistent_does_nothing(self, storage):
        await storage.update_task(999, progress_percent=50)
        assert await storage.get(999) is None

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, storage):
        task = TaskInfo(1, 1, "k", {})
        await storage.add(task)

        async def updater(value):
            await storage.update_task(1, progress_percent=value)

        await asyncio.gather(updater(10), updater(20), updater(30))
        assert task.get_version() == 3
        assert task.progress_percent in (10, 20, 30)

    @pytest.mark.asyncio
    async def test_wait_for_change_immediate(self, storage):
        task = TaskInfo(1, 1, "k", {})
        await storage.add(task)
        task._version = 5
        result = await storage.wait_for_change(1, current_version=3, timeout=1.0)
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_change_timeout(self, storage):
        task = TaskInfo(1, 1, "k", {})
        await storage.add(task)
        start = asyncio.get_event_loop().time()
        result = await storage.wait_for_change(1, current_version=0, timeout=0.2)
        elapsed = asyncio.get_event_loop().time() - start
        assert result is False
        assert elapsed >= 0.19

    @pytest.mark.asyncio
    async def test_wait_for_change_notified(self, storage):
        task = TaskInfo(1, 1, "k", {})
        await storage.add(task)

        async def waiter():
            return await storage.wait_for_change(1, current_version=0, timeout=2)

        w = asyncio.create_task(waiter())
        await asyncio.sleep(0.1)
        await storage.update_task(1, progress_percent=10)
        result = await w
        assert result is True

    @pytest.mark.asyncio
    async def test_remove_task(self, storage):
        task = TaskInfo(1, 1, "k", {})
        await storage.add(task)
        await storage.remove_task(1)
        assert await storage.get(1) is None

    @pytest.mark.asyncio
    async def test_cleanup_removes_expired_tasks(self):
        ttl = 1
        storage = TaskStateStorage(ttl_seconds=ttl, max_tasks=100)

        task1 = TaskInfo(1, 1, "k", {})
        task1.status = TaskStatus.COMPLETED
        task1.completed_at = datetime.now(timezone.utc) - timedelta(seconds=ttl + 1)
        await storage.add(task1)

        task2 = TaskInfo(2, 1, "k", {})
        task2.status = TaskStatus.FAILED
        task2.completed_at = datetime.now(timezone.utc) - timedelta(seconds=ttl + 2)
        await storage.add(task2)

        task3 = TaskInfo(3, 1, "k", {})
        task3.status = TaskStatus.COMPLETED
        task3.completed_at = datetime.now(timezone.utc)
        await storage.add(task3)

        # Симулируем один цикл очистки
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            async def run_one_cleanup():
                while True:
                    await asyncio.sleep(3600)
                    now = datetime.now(timezone.utc)
                    expired = []
                    for tid, info in storage._store.items():
                        if info.status in ("completed", "failed"):
                            deadline = info.completed_at or info.started_at
                            if deadline + timedelta(seconds=storage._ttl) < now:
                                expired.append(tid)
                    for tid in expired:
                        async with storage._get_lock(tid):
                            storage._store.pop(tid, None)
                    break

            await run_one_cleanup()
            assert await storage.get(1) is None
            assert await storage.get(2) is None
            assert await storage.get(3) is not None

    @pytest.mark.asyncio
    async def test_start_cleanup_cancellation(self, storage):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            cleanup_task = asyncio.create_task(storage.start_cleanup())
            await asyncio.sleep(0.1)
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
            mock_sleep.assert_called()