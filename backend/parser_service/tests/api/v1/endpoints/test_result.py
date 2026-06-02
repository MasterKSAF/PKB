"""
Тесты эндпоинта GET /parser/process/{task_id}/result.
Проверяют:
- получение результата для завершённой задачи
- ошибки TASK_NOT_FOUND, CONFLICT, FAILED.
"""
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus


def test_get_result_not_found(client):
    """
    Проверка: для несуществующего task_id возвращается 404 TASK_NOT_FOUND.
    """
    response = client.get("/api/v1/parser/process/999/result")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"


def test_get_result_not_completed(client, clear_task_store):
    """
    Проверка: для задачи со статусом PROCESSING возвращается 409 Conflict.
    """
    task = TaskInfo(200, "v", "f", {})
    task.status = TaskStatus.PROCESSING
    task_store.add(task)
    response = client.get("/api/v1/parser/process/200/result")
    assert response.status_code == 409
    assert "Task not completed yet" in response.text


def test_get_result_success(client, clear_task_store):
    """
    Проверка: для завершённой задачи возвращается сохранённый JSON-результат.
    """
    task = TaskInfo(300, "v", "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = {"data": "test"}
    task_store.add(task)
    response = client.get("/api/v1/parser/process/300/result")
    assert response.status_code == 200
    assert response.json() == {"data": "test"}