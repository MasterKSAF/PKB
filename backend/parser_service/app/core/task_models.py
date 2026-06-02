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
    Информация о задаче.

    В отличие от предыдущих версий, не содержит asyncio.Event.
    Вместо этого используется версионирование (_version) для longpoll.
    """

    def __init__(self, task_id: int, version_id: str, file_key: str, options: dict):
        self.task_id = task_id
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

        self.error = None          # словарь с code, message, details
        self.result = None         # итоговый JSON-контейнер

        # Поле html_content удалено, так как больше не используется в API
        # Версия увеличивается при каждом обновлении (для longpoll)
        self._version = 0

    def update(self, **kwargs) -> None:
        """
        Обновляет атрибуты задачи и увеличивает версию.

        :param kwargs: любые атрибуты, существующие в экземпляре
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._version += 1

    def get_version(self) -> int:
        """Возвращает текущую версию задачи (монотонно возрастает)."""
        return self._version