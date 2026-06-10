"""
Тесты для фасада task_store (app.core.task_store).
Проверяет, что экспортирует правильные объекты.
"""
from app.core.task_store import task_store, TaskInfo, TaskStatus


def test_task_store_export():
    assert task_store is not None
    assert TaskInfo is not None
    assert TaskStatus is not None


def test_task_store_singleton():
    from app.core.task_store import task_store as ts2
    assert task_store is ts2


def test_task_info_creation():
    info = TaskInfo(1, "v", "key", {})
    assert info.task_id == 1