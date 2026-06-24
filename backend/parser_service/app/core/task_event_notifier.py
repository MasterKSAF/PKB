"""
Уведомления об изменениях задач (через asyncio.Condition).

Используется для long polling в эндпоинтах статуса.
Каждая задача имеет отдельную Condition и счётчик версий.
"""
import asyncio
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class TaskEventNotifier:
    """
    Менеджер уведомлений для задач.

    Хранит Condition для каждой задачи и версию для отслеживания изменений.
    """

    def __init__(self):
        self._conditions: Dict[int, asyncio.Condition] = {}
        self._versions: Dict[int, int] = {}
        self._lock = asyncio.Lock()

    async def get_condition(self, task_id: int) -> asyncio.Condition:
        """
        Возвращает Condition для задачи, создаёт при необходимости.

        Args:
            task_id: Идентификатор задачи.

        Returns:
            asyncio.Condition для ожидания изменений.
        """
        async with self._lock:
            if task_id not in self._conditions:
                self._conditions[task_id] = asyncio.Condition()
                self._versions[task_id] = 0
                logger.debug("Created condition for task %d", task_id)
            return self._conditions[task_id]

    async def notify_task_changed(self, task_id: int) -> None:
        """
        Уведомляет всех ожидающих об изменении задачи.
        Увеличивает внутреннюю версию.

        Args:
            task_id: Идентификатор задачи.
        """
        async with self._lock:
            cond = self._conditions.get(task_id)
            if cond:
                self._versions[task_id] = self._versions.get(task_id, 0) + 1
                logger.debug("Task %d version incremented to %d", task_id, self._versions[task_id])
        if cond:
            async with cond:
                cond.notify_all()
                logger.debug("Notified all waiters for task %d", task_id)

    async def wait_for_task_change(
        self,
        task_id: int,
        current_version: int,
        timeout: float,
    ) -> bool:
        """
        Ожидает изменения версии задачи.

        Args:
            task_id: Идентификатор задачи.
            current_version: Текущая известная версия.
            timeout: Максимальное время ожидания в секундах.

        Returns:
            True, если изменение произошло, False по таймауту.
        """
        cond = await self.get_condition(task_id)
        async with cond:
            while self._versions.get(task_id, 0) == current_version:
                try:
                    await asyncio.wait_for(cond.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    logger.debug("Timeout waiting for task %d change", task_id)
                    return False
            logger.debug("Task %d changed from version %d", task_id, current_version)
            return True

    async def cleanup_task(self, task_id: int) -> None:
        """
        Удаляет все данные задачи при её завершении.

        Args:
            task_id: Идентификатор задачи.
        """
        async with self._lock:
            self._conditions.pop(task_id, None)
            self._versions.pop(task_id, None)
            logger.debug("Cleaned up notifier data for task %d", task_id)