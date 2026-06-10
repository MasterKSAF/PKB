from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus


def test_get_result_success(client, clear_task_store):
    task = TaskInfo(300, "v", "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = {"data": "test"}
    task_store.add(task)
    response = client.get("/api/v1/parser/process/300/result")
    assert response.status_code == 200
    assert response.json() == {"data": "test"}


def test_get_result_empty(client, clear_task_store):
    """Завершённая задача, но result = None → 500."""
    task = TaskInfo(301, "v", "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = None
    task_store.add(task)
    response = client.get("/api/v1/parser/process/301/result")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PARSER_FAILED"  # или INTERNAL_SERVER_ERROR


def test_get_result_not_completed(client, clear_task_store):
    task = TaskInfo(200, "v", "f", {})
    task.status = TaskStatus.PROCESSING
    task_store.add(task)
    response = client.get("/api/v1/parser/process/200/result")
    assert response.status_code == 409
    assert "Task not completed yet" in response.text