"""
Интеграционный тест эндпоинта /process/{task_id}/status (longpoll).
Проверяет, что клиент дожидается изменения статуса через longpoll.
"""

import pytest
import asyncio
from app.core.task_store import task_store
from app.core.task_models import TaskInfo, TaskStatus

pytestmark = pytest.mark.asyncio  # все тесты в этом модуле асинхронные


async def test_longpoll_waits_for_completion(async_client, clear_task_store):
    """
    Сценарий:
    1. Создаётся задача со статусом ACCEPTED.
    2. Запускается longpoll‑запрос (ожидает до 5 секунд).
    3. Через 0.2 секунды задача помечается как COMPLETED.
    4. Longpoll должен завершиться и вернуть статус completed.
    """
    task_id = 999
    task_info = TaskInfo(task_id, "v1", "file", {})
    task_info.status = TaskStatus.ACCEPTED
    task_store.add(task_info)

    async def do_longpoll():
        response = await async_client.get(f"/api/v1/parser/process/{task_id}/status?timeout=5")
        return response

    # Запускаем longpoll в фоновой задаче
    longpoll_task = asyncio.create_task(do_longpoll())
    # Небольшая задержка, чтобы запрос успел установиться
    await asyncio.sleep(0.2)
    # Обновляем задачу – завершаем
    await task_store.update_task(task_id, status=TaskStatus.COMPLETED, progress_percent=100)

    # Ожидаем ответ не более 3 секунд
    response = await asyncio.wait_for(longpoll_task, timeout=3.0)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["progress_percent"] == 100