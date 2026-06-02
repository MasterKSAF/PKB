"""
Новая реализация TaskStore (фасад).

Сохраняет публичный API: task_store, TaskInfo, TaskStatus.
Все функции делегируются фасаду TaskStore из task_store_facade.py.
"""
from app.core.task_store_facade import task_store
from app.core.task_models import TaskInfo, TaskStatus

__all__ = ["task_store", "TaskInfo", "TaskStatus"]