"""
Компонент TaskEventNotifier: управляет подписками и уведомлениями об изменении задач.

Использует asyncio.Condition для каждого task_id, что позволяет ожидать изменения
конкретной задачи без активного ожидания (longpoll).
"""
import asyncio
from typing import Dict


class TaskEventNotifier:
    """
    Реализует механизм notify/wait для изменений задач.

    Для каждого task_id хранится своё asyncio.Condition.
    При вызове notify_task_changed пробуждаются все ожидающие корутины.
    """

    def __init__(self):
        self._conditions: Dict[int, asyncio.Condition] = {}
        self._lock = asyncio.Lock()

    async def get_condition(self, task_id: int) -> asyncio.Condition:
        """
        Возвращает Condition для заданного task_id (создаёт при необходимости).
        """
        async with self._lock:
            if task_id not in self._conditions:
                self._conditions[task_id] = asyncio.Condition()
            return self._conditions[task_id]

    async def notify_task_changed(self, task_id: int) -> None:
        """
        Уведомляет всех ожидающих изменения задачи с данным ID.
        """
        async with self._lock:
            cond = self._conditions.get(task_id)
        if cond:
            async with cond:
                cond.notify_all()

    async def wait_for_task_change(self, task_id: int, current_version: int, timeout: float) -> bool:
        """
        Ожидает изменения задачи (сигнала notify).

        :param task_id: ID задачи
        :param current_version: текущая версия (не используется в проверке,
                                 оставлен для совместимости с интерфейсом)
        :param timeout: максимальное время ожидания в секундах
        :return: True, если получен сигнал; False при таймауте
        """
        cond = await self.get_condition(task_id)
        async with cond:
            try:
                await asyncio.wait_for(cond.wait(), timeout=timeout)
                return True
            except asyncio.TimeoutError:
                return False

    async def cleanup_task(self, task_id: int) -> None:
        """
        Удаляет Condition для задачи (вызывается после удаления задачи из хранилища).
        """
        async with self._lock:
            self._conditions.pop(task_id, None)