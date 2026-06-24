"""
Хранилище задач в памяти с поддержкой TTL, фоновой очисткой и ограничением на число задач.
А также re-экспорт моделей TaskInfo, TaskStatus.
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.core.task_models import TaskInfo, TaskStatus
from app.core.task_event_notifier import TaskEventNotifier
import logging

logger = logging.getLogger(__name__)


class TaskStateStorage:
    """In-memory хранилище задач с автоматической очисткой устаревших и лимитом на количество."""

    def __init__(self, ttl_seconds: int, max_tasks: int):
        """
        Args:
            ttl_seconds: Время жизни завершённой задачи в секундах.
            max_tasks: Максимальное количество задач в хранилище.
        """
        self._store: Dict[int, TaskInfo] = {}
        self._ttl = ttl_seconds
        self._max_tasks = max_tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._locks: Dict[int, asyncio.Lock] = {}
        self._notifier = TaskEventNotifier()
        logger.debug("TaskStateStorage initialized, TTL=%d, max_tasks=%d", ttl_seconds, max_tasks)

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
                        logger.info("Removed expired task %d", tid)
        except asyncio.CancelledError:
            logger.debug("Cleanup task cancelled")
            return

    def _get_lock(self, task_id: int) -> asyncio.Lock:
        """Возвращает блокировку для задачи, создаёт при необходимости."""
        if task_id not in self._locks:
            self._locks[task_id] = asyncio.Lock()
        return self._locks[task_id]

    async def _evict_old_tasks(self) -> None:
        """
        Принудительно удаляет самые старые завершённые задачи,
        пока размер хранилища не станет < max_tasks.
        """
        while len(self._store) >= self._max_tasks:
            oldest_completed = None
            oldest_time = None
            for tid, info in self._store.items():
                if info.status in ("completed", "failed"):
                    if oldest_time is None or info.started_at < oldest_time:
                        oldest_time = info.started_at
                        oldest_completed = tid
            if oldest_completed is not None:
                async with self._get_lock(oldest_completed):
                    self._store.pop(oldest_completed, None)
                    self._locks.pop(oldest_completed, None)
                    logger.info(
                        "Evicted old completed task %d due to store limit",
                        oldest_completed,
                    )
            else:
                raise RuntimeError(
                    f"Store limit reached ({self._max_tasks}) with only active tasks, cannot add new task"
                )

    async def add(self, task_info: TaskInfo) -> None:
        """Добавляет новую задачу в хранилище, предварительно эвакуируя старые при необходимости."""
        if len(self._store) >= self._max_tasks:
            await self._evict_old_tasks()
        self._store[task_info.task_id] = task_info
        logger.debug(
            "Task %d added to storage (total %d)",
            task_info.task_id,
            len(self._store),
        )

    async def get(self, task_id: int) -> Optional[TaskInfo]:
        """Возвращает задачу или None, если её нет."""
        return self._store.get(task_id)

    async def get_active_tasks(self) -> List[TaskInfo]:
        """Возвращает список активных (не завершённых) задач."""
        return [
            info
            for info in self._store.values()
            if info.status in ("accepted", "processing")
        ]

    async def update_task(self, task_id: int, **kwargs) -> bool:
        """
        Обновляет задачу и уведомляет подписчиков (long polling).
        Возвращает True, если обновление выполнено, False если задача не найдена.
        """
        lock = self._get_lock(task_id)
        async with lock:
            task = self._store.get(task_id)
            if not task:
                logger.warning("Attempt to update non-existent task %d", task_id)
                return False
            task.update(**kwargs)
            await self._notifier.notify_task_changed(task_id)
            logger.debug("Task %d updated: %s", task_id, kwargs)
            return True

    async def wait_for_change(
        self,
        task_id: int,
        current_version: int,
        timeout: float,
    ) -> bool:
        """Ожидает изменения задачи (long polling)."""
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
            logger.info("Task %d removed from storage", task_id)


# Глобальный экземпляр для всего приложения
task_store = TaskStateStorage(
    ttl_seconds=settings.task_ttl_days * 86400,
    max_tasks=settings.max_tasks_in_store,
)

# Re-экспорт моделей для удобства
__all__ = ["task_store", "TaskInfo", "TaskStatus"]