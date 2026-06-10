"""
Хранилище задач в памяти с поддержкой TTL и фоновой очистки.

Использует TaskEventNotifier для long polling.
Все операции с задачей потокобезопасны благодаря asyncio.Lock на каждую задачу.
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.core.task_models import TaskInfo
from app.core.task_event_notifier import TaskEventNotifier
import logging

logger = logging.getLogger(__name__)


class TaskStateStorage:
    """In-memory хранилище задач с автоматической очисткой устаревших."""

    def __init__(self, ttl_seconds: int):
        """
        Args:
            ttl_seconds: Время жизни завершённой задачи в секундах.
        """
        self._store: Dict[int, TaskInfo] = {}
        self._ttl = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._locks: Dict[int, asyncio.Lock] = {}
        self._notifier = TaskEventNotifier()

    async def start_cleanup(self):
        """
        Фоновая задача: каждый час удаляет завершённые задачи старше TTL.
        Должна быть запущена при старте приложения.
        """
        try:
            while True:
                await asyncio.sleep(3600)
                now = datetime.now(timezone.utc)
                expired = []
                for tid, info in self._store.items():
                    if info.status in ("completed", "failed"):
                        deadline = info.completed_at or info.started_at
                        if deadline + timedelta(seconds=self._ttl) < now:
                            expired.append(tid)
                for tid in expired:
                    async with self._get_lock(tid):
                        self._store.pop(tid, None)
                        self._locks.pop(tid, None)
                        logger.info(f"Removed expired task {tid}")
        except asyncio.CancelledError:
            logger.debug("Cleanup task cancelled")
            return

    def _get_lock(self, task_id: int) -> asyncio.Lock:
        """Возвращает блокировку для задачи, создаёт при необходимости."""
        if task_id not in self._locks:
            self._locks[task_id] = asyncio.Lock()
        return self._locks[task_id]

    def add(self, task_info: TaskInfo) -> None:
        """Добавляет новую задачу в хранилище."""
        self._store[task_info.task_id] = task_info
        logger.debug(f"Task {task_info.task_id} added to storage")

    def get(self, task_id: int) -> Optional[TaskInfo]:
        """Возвращает задачу или None, если её нет."""
        return self._store.get(task_id)

    def get_active_tasks(self) -> List[TaskInfo]:
        """Возвращает список активных (не завершённых) задач."""
        return [info for info in self._store.values()
                if info.status in ("accepted", "processing")]

    async def update_task(self, task_id: int, **kwargs) -> None:
        """
        Обновляет задачу и уведомляет подписчиков (long polling).

        Args:
            task_id: Идентификатор задачи.
            **kwargs: Атрибуты для обновления (статус, прогресс, результат и т.д.).
        """
        lock = self._get_lock(task_id)
        async with lock:
            task = self._store.get(task_id)
            if task:
                task.update(**kwargs)
                await self._notifier.notify_task_changed(task_id)
                logger.debug(f"Task {task_id} updated: {kwargs}")
            else:
                logger.warning(f"Attempt to update non-existent task {task_id}")

    async def wait_for_change(self, task_id: int, current_version: int, timeout: float) -> bool:
        """
        Ожидает изменения задачи (long polling).

        Args:
            task_id: Идентификатор задачи.
            current_version: Версия, которая известна вызывающей стороне.
            timeout: Максимальное время ожидания в секундах.

        Returns:
            True, если изменение произошло, False по таймауту или если задача исчезла.
        """
        task = self._store.get(task_id)
        if task is None:
            return False
        if task.get_version() != current_version:
            return True
        return await self._notifier.wait_for_task_change(task_id, current_version, timeout)

    async def remove_task(self, task_id: int):
        """Полностью удаляет задачу из хранилища (принудительно)."""
        lock = self._get_lock(task_id)
        async with lock:
            self._store.pop(task_id, None)
            self._locks.pop(task_id, None)
            await self._notifier.cleanup_task(task_id)
            logger.info(f"Task {task_id} removed from storage")


# Глобальный экземпляр для всего приложения
task_store = TaskStateStorage(ttl_seconds=settings.task_ttl_days * 86400)