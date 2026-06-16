from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus


def test_v1_result_success_v1_format(client, clear_task_store):
    task = TaskInfo(300, "", "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = {
        "api_version": 2,
        "metadata": {"schema_version": "raw_ocr_v4", "mode": "full"},
        "document": {"text": "hello"},
        "quality": {"confidence": 0.9},
        "errors": [],
        "status": "completed"
    }
    task_store.add(task)

    response = client.get("/api/v1/parser/process/300/result")
    assert response.status_code == 200
    assert response.json()["document"]["text"] == "hello"


def test_v1_result_success_v1_format_converted(client, clear_task_store):
    task = TaskInfo(301, "", "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = {
        "document": {"text": "old"},
        "quality": {},
        "errors": [],
        "status": "completed"
    }
    task_store.add(task)

    response = client.get("/api/v1/parser/process/301/result")
    assert response.status_code == 200
    assert response.json()["document"]["text"] == "old"


def test_v1_result_not_completed(client, clear_task_store):
    task = TaskInfo(200, "", "f", {})
    task.status = TaskStatus.PROCESSING
    task_store.add(task)
    response = client.get("/api/v1/parser/process/200/result")
    assert response.status_code == 409


def test_v1_result_failed(client, clear_task_store):
    task = TaskInfo(400, "", "f", {})
    task.status = TaskStatus.FAILED
    task.error = {"code": "PARSER_FAILED", "message": "error"}
    task_store.add(task)
    response = client.get("/api/v1/parser/process/400/result")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PARSER_FAILED"