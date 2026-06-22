import pytest
import asyncio
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus


@pytest.mark.asyncio
async def test_v1_status_immediate_for_completed(async_client, clear_task_store):
    task = TaskInfo(201, 1, "", "f", {})
    task.status = TaskStatus.COMPLETED
    task.progress_percent = 100
    task_store.add(task)

    response = await async_client.get("/api/v1/parser/process/201/status?timeout=1")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_v1_status_longpoll_waits_for_change(async_client, clear_task_store):
    task_id = 202
    task = TaskInfo(task_id, 1, "", "f", {})
    task.status = TaskStatus.ACCEPTED
    task_store.add(task)

    longpoll_task = asyncio.create_task(
        async_client.get(f"/api/v1/parser/process/{task_id}/status?timeout=5")
    )
    await asyncio.sleep(0.1)
    await task_store.update_task(task_id, status=TaskStatus.PROCESSING, progress_percent=10)

    response = await asyncio.wait_for(longpoll_task, timeout=2.0)
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_v1_status_task_not_found(client, clear_task_store):
    response = client.get("/api/v1/parser/process/999/status")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"