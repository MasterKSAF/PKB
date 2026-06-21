"""
Модели задач, используемые хранилищем и нотификатором.

Определяет статус задачи (TaskStatus) и структуру TaskInfo,
содержащую всю информацию о задаче: прогресс, результат, ошибки.
"""
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from enum import Enum


class TaskStatus(str, Enum):
    """Возможные состояния задачи."""
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo:
    """
    Информация о задаче парсинга.

    Хранит метаданные, статус, прогресс, результат и версию для long polling.
    Все изменения должны производиться через метод update(), который увеличивает версию.
    """

    def __init__(self, task_id: int, draft_id: int, version_id: str, file_key: str, options: dict):  # <-- ИЗМЕНЕНИЕ
        self.task_id = task_id
        self.draft_id = draft_id  # <-- ИЗМЕНЕНИЕ
        self.version_id = version_id
        self.file_key = file_key
        self.options = options

        self.status = TaskStatus.ACCEPTED
        self.progress_percent = 0
        self.pages_processed = 0
        self.pages_total = 0
        self.avg_confidence = 0.0
        self.step = "accepted"
        self.step_detail = "Задача принята"

        self.started_at = datetime.now(timezone.utc)
        self.completed_at = None

        self.error = None
        self.result = None
        self._version = 0

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты задачи и увеличивает версию.

        Args:
            **kwargs: Пары (имя_атрибута, значение) для обновления.
        """
        updated = False
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                updated = True
        if updated:
            self._version += 1

    def get_version(self) -> int:
        """Возвращает текущую версию задачи (монотонно возрастает при каждом обновлении)."""
        return self._version