from app.core.task_store import task_store
from app.core.task_models import TaskInfo


def test_v1_list_processes(client, clear_task_store):
    t1 = TaskInfo(1, 1, "", "f1", {})
    t1.status = "accepted"
    t2 = TaskInfo(2, 1, "", "f2", {})
    t2.status = "processing"
    t3 = TaskInfo(3, 1, "", "f3", {})
    t3.status = "completed"
    for t in [t1, t2, t3]:
        task_store.add(t)

    response = client.get("/api/v1/parser/processes")
    assert response.status_code == 200
    assert len(response.json()["processes"]) == 2


def test_v1_list_processes_empty(client, clear_task_store):
    response = client.get("/api/v1/parser/processes")
    assert response.status_code == 200
    assert response.json()["processes"] == []