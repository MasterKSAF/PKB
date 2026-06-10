"""
Тесты эндпоинта GET /api/v1/parser/process/{task_id}/status.
"""
import pytest
import asyncio
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus


@pytest.mark.asyncio
async def test_status_immediate_for_completed(async_client, clear_task_store):
    """Уже завершённая задача возвращает статус completed без ожидания."""
    task = TaskInfo(201, "v", "f", {})
    task.status = TaskStatus.COMPLETED
    task.progress_percent = 100
    task_store.add(task)

    response = await async_client.get("/api/v1/parser/process/201/status?timeout=1")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["progress_percent"] == 100


@pytest.mark.asyncio
async def test_status_longpoll_waits_for_change(async_client, clear_task_store):
    """Longpoll ожидает изменения статуса с ACCEPTED до PROCESSING."""
    task_id = 202
    task = TaskInfo(task_id, "v", "f", {})
    task.status = TaskStatus.ACCEPTED
    task_store.add(task)

    # Запрос статуса с таймаутом 5 сек
    longpoll_task = asyncio.create_task(
        async_client.get(f"/api/v1/parser/process/{task_id}/status?timeout=5")
    )
    await asyncio.sleep(0.1)
    # Меняем статус
    await task_store.update_task(task_id, status=TaskStatus.PROCESSING, progress_percent=10)

    response = await asyncio.wait_for(longpoll_task, timeout=2.0)
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert response.json()["progress_percent"] == 10


@pytest.mark.asyncio
async def test_status_timeout(async_client, clear_task_store):
    """Если статус не меняется, запрос завершается по таймауту и возвращает текущий статус."""
    task_id = 203
    task = TaskInfo(task_id, "v", "f", {})
    task.status = TaskStatus.ACCEPTED
    task_store.add(task)

    response = await async_client.get(f"/api/v1/parser/process/{task_id}/status?timeout=1")
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_status_task_not_found(client, clear_task_store):
    """Несуществующая задача → 404 TASK_NOT_FOUND."""
    response = client.get("/api/v1/parser/process/999/status")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"