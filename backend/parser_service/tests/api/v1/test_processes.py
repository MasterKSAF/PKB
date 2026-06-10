from app.core.task_store import task_store
from app.core.task_models import TaskInfo


def test_list_processes(client, clear_task_store):
    """Возвращает только активные задачи (accepted / processing)."""
    t1 = TaskInfo(1, "v1", "f1", {})
    t1.status = "accepted"
    t2 = TaskInfo(2, "v1", "f2", {})
    t2.status = "processing"
    t3 = TaskInfo(3, "v1", "f3", {})
    t3.status = "completed"
    for t in [t1, t2, t3]:
        task_store.add(t)

    response = client.get("/api/v1/parser/processes")
    assert response.status_code == 200
    data = response.json()
    assert len(data["processes"]) == 2
    statuses = {p["status"] for p in data["processes"]}
    assert statuses == {"accepted", "processing"}


def test_list_processes_empty(client, clear_task_store):
    """Если активных задач нет, возвращается пустой массив."""
    response = client.get("/api/v1/parser/processes")
    assert response.status_code == 200
    assert response.json()["processes"] == []