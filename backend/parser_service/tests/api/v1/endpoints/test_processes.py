"""
Тесты эндпоинта GET /parser/processes.
Проверяют:
- список активных задач (статусы accepted или processing).
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.task_store import task_store
from app.core.task_models import TaskInfo

client = TestClient(app)


def test_list_processes(client, clear_task_store):
    """
    Проверка: возвращается массив processes с одной активной задачей.
    """
    task1 = TaskInfo(1, "v1", "f1", {})
    task1.status = "processing"
    task_store.add(task1)
    response = client.get("/api/v1/parser/processes")
    assert response.status_code == 200
    assert len(response.json()["processes"]) == 1