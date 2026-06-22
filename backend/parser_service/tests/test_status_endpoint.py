"""
Интеграционный тест эндпоинта /process/{task_id}/status (longpoll).
Проверяет, что клиент дожидается изменения статуса через longpoll.
"""

import pytest
import asyncio
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus

pytestmark = pytest.mark.asyncio


async def test_longpoll_waits_for_completion(async_client, clear_task_store):
    task_id = 999
    task_info = TaskInfo(task_id, 1, "v1", "file", {})
    task_info.status = TaskStatus.ACCEPTED
    task_store.add(task_info)

    async def do_longpoll():
        response = await async_client.get(f"/api/v1/parser/process/{task_id}/status?timeout=5")
        return response

    longpoll_task = asyncio.create_task(do_longpoll())
    await asyncio.sleep(0.2)
    await task_store.update_task(task_id, status=TaskStatus.COMPLETED, progress_percent=100)

    response = await asyncio.wait_for(longpoll_task, timeout=3.0)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["progress_percent"] == 100