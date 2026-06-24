from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus
import pytest


@pytest.mark.asyncio
async def test_v1_result_success_v1_format(async_client, clear_task_store, init_test_services):
    task = TaskInfo(300, 1, "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = {
        "api_version": 2,
        "metadata": {"schema": "raw_ocr_v4", "mode": "full"},
        "document": {"text": "hello"},
        "quality": {"confidence": 0.9},
        "errors": [],
        "status": "completed"
    }
    await task_store.add(task)

    response = await async_client.get("/api/v1/parser/process/300/result")
    assert response.status_code == 200
    assert response.json()["document"]["text"] == "hello"


@pytest.mark.asyncio
async def test_v1_result_success_v1_format_converted(async_client, clear_task_store, init_test_services):
    task = TaskInfo(301, 1, "f", {})
    task.status = TaskStatus.COMPLETED
    task.result = {
        "document": {"text": "old"},
        "quality": {},
        "errors": [],
        "status": "completed"
    }
    await task_store.add(task)

    response = await async_client.get("/api/v1/parser/process/301/result")
    assert response.status_code == 200
    assert response.json()["document"]["text"] == "old"


@pytest.mark.asyncio
async def test_v1_result_not_completed(async_client, clear_task_store, init_test_services):
    task = TaskInfo(200, 1, "f", {})
    task.status = TaskStatus.PROCESSING
    await task_store.add(task)
    response = await async_client.get("/api/v1/parser/process/200/result")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_v1_result_failed(async_client, clear_task_store, init_test_services):
    task = TaskInfo(400, 1, "f", {})
    task.status = TaskStatus.FAILED
    task.error = {"code": "PARSER_FAILED", "message": "error"}
    await task_store.add(task)
    response = await async_client.get("/api/v1/parser/process/400/result")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PARSER_FAILED"