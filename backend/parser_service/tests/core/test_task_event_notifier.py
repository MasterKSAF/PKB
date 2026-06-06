"""
Тесты для TaskEventNotifier (асинхронные уведомления об изменении задач).
"""
import pytest
import asyncio
from app.core.task_event_notifier import TaskEventNotifier


class TestTaskEventNotifier:
    @pytest.fixture
    def notifier(self):
        return TaskEventNotifier()

    @pytest.mark.asyncio
    async def test_wait_timeout(self, notifier):
        """Ожидание без уведомления → возвращает False по таймауту."""
        changed = await notifier.wait_for_task_change(1, current_version=0, timeout=0.1)
        assert changed is False

    @pytest.mark.asyncio
    async def test_notify_triggers_wait(self, notifier):
        """Уведомление о изменении задачи пробуждает ожидающий wait_for_task_change."""
        task_id = 42
        async def waiter():
            return await notifier.wait_for_task_change(task_id, current_version=0, timeout=2)
        task = asyncio.create_task(waiter())
        await asyncio.sleep(0.1)
        await notifier.notify_task_changed(task_id)
        result = await task
        assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_removes_condition(self, notifier):
        """Удаление задачи очищает associated Condition."""
        await notifier.get_condition(1)
        assert 1 in notifier._conditions
        await notifier.cleanup_task(1)
        assert 1 not in notifier._conditions