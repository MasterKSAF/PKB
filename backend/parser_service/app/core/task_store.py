"""
TaskStore – точка доступа к хранилищу задач.

Экспортирует глобальный экземпляр task_store и модели TaskInfo, TaskStatus.
"""
from app.core.task_state_storage import task_store
from app.core.task_models import TaskInfo, TaskStatus

__all__ = ["task_store", "TaskInfo", "TaskStatus"]