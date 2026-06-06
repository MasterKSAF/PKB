"""
Фасад TaskStore: объединяет TaskStateStorage, TaskEventNotifier и TaskResultCache.

Сохраняет тот же публичный интерфейс, что и старый task_store,
но внутренне использует разделённые компоненты.
"""
from typing import Optional, List
from app.core.task_models import TaskInfo
from app.core.task_state_storage import TaskStateStorage
from app.core.task_event_notifier import TaskEventNotifier
from app.core.task_result_cache import TaskResultCache
from app.config import settings


class TaskStore:
    """
    Единая точка доступа к хранилищу задач.

    - add(): добавляет задачу
    - get(): читает задачу
    - update_task(): обновляет задачу и рассылает уведомление longpoll-подписчикам
    - wait_for_change(): ожидает изменения версии задачи
    - get_active_tasks(): список активных задач
    - start_cleanup(): запускает фоновую очистку
    """

    def __init__(self, ttl_seconds: int):
        self._storage = TaskStateStorage(ttl_seconds)
        self._notifier = TaskEventNotifier()
        self._cache = TaskResultCache()  # пока заглушка

    async def start_cleanup(self):
        """Запускает фоновую очистку старых задач."""
        await self._storage.start_cleanup()

    def add(self, task_info: TaskInfo) -> None:
        """Добавляет задачу в хранилище."""
        self._storage.add(task_info)

    def get(self, task_id: int) -> Optional[TaskInfo]:
        """Возвращает задачу или None."""
        return self._storage.get(task_id)

    def get_active_tasks(self) -> List[TaskInfo]:
        """Возвращает список активных (accepted/processing) задач."""
        return self._storage.get_active_tasks()

    async def update_task(self, task_id: int, **kwargs) -> None:
        """
        Обновляет задачу и уведомляет всех ожидающих её изменения.

        :param task_id: ID задачи
        :param kwargs: атрибуты для обновления (передаются в task_info.update)
        """
        task = self._storage.get(task_id)
        if task:
            task.update(**kwargs)
            await self._notifier.notify_task_changed(task_id)

    async def wait_for_change(self, task_id: int, current_version: int, timeout: float) -> bool:
        """
        Ожидает изменения версии задачи (сигнал от update_task).

        :param task_id: ID задачи
        :param current_version: версия, полученная перед вызовом (для сравнения)
        :param timeout: таймаут в секундах
        :return: True, если изменение произошло; False при таймауте
        """
        return await self._notifier.wait_for_task_change(task_id, current_version, timeout)

    async def remove_task(self, task_id: int):
        """Удаляет задачу из хранилища и очищает связанные ресурсы."""
        self._storage.remove(task_id)
        await self._notifier.cleanup_task(task_id)


# Глобальный экземпляр (синглтон)
task_store = TaskStore(ttl_seconds=settings.task_ttl_days * 86400)