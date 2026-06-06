"""
Компонент TaskStateStorage: отвечает только за хранение TaskInfo, TTL и фоновую очистку.

Не содержит логики уведомлений (events/conditions) – это задача TaskEventNotifier.
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.core.task_models import TaskInfo


class TaskStateStorage:
    """
    In-memory хранилище задач с автоматическим удалением устаревших.

    Задачи со статусом completed или failed удаляются через TTL секунд после завершения.
    """

    def __init__(self, ttl_seconds: int):
        self._store: Dict[int, TaskInfo] = {}
        self._ttl = ttl_seconds
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup(self):
        """
        Фоновый сборщик мусора.

        Запускается один раз при старте приложения и работает бесконечно,
        удаляя задачи, у которых (completed_at или started_at) + TTL < текущее время.
        """
        while True:
            await asyncio.sleep(3600)  # раз в час
            now = datetime.now(timezone.utc)
            expired = []
            for tid, info in self._store.items():
                if info.status in ("completed", "failed"):
                    deadline = info.completed_at or info.started_at
                    if deadline + timedelta(seconds=self._ttl) < now:
                        expired.append(tid)
            for tid in expired:
                del self._store[tid]

    def add(self, task_info: TaskInfo) -> None:
        """Добавляет или перезаписывает задачу в хранилище."""
        self._store[task_info.task_id] = task_info

    def get(self, task_id: int) -> Optional[TaskInfo]:
        """Возвращает задачу или None, если её нет."""
        return self._store.get(task_id)

    def get_active_tasks(self) -> List[TaskInfo]:
        """Возвращает список задач со статусами 'accepted' или 'processing'."""
        return [info for info in self._store.values()
                if info.status in ("accepted", "processing")]

    def remove(self, task_id: int) -> None:
        """Принудительно удаляет задачу (используется редко)."""
        self._store.pop(task_id, None)