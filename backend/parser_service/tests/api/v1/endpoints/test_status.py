"""
Тесты эндпоинта GET /parser/process/{task_id}/status (longpoll).
Проверяют:
- мгновенный возврат для терминальных статусов
- ожидание изменения статуса (longpoll) до таймаута
- корректное заполнение полей ответа.
"""
import pytest
import threading
import asyncio
from app.core.task_models import TaskInfo, TaskStatus
from app.core.task_store import task_store


@pytest.mark.asyncio
async def test_status_longpoll(client, clear_task_store):
    """
    Проверка longpoll: клиент ждёт до 2 секунд, при завершении задачи получает статус completed.
    """
    task = TaskInfo(task_id=200, version_id="v", file_key="f", options={})
    task_store.add(task)

    result = {}

    def do_request():
        resp = client.get("/api/v1/parser/process/200/status?timeout=2")
        result["resp"] = resp

    thread = threading.Thread(target=do_request)
    thread.start()
    # Имитация завершения задачи через 0.5 секунды
    await asyncio.sleep(0.5)
    await task_store.update_task(200, status=TaskStatus.COMPLETED)
    thread.join(timeout=3)

    assert "resp" in result
    assert result["resp"].status_code == 200
    assert result["resp"].json()["status"] == "completed"


def test_status_immediate_for_completed(client, clear_task_store):
    """
    Проверка: для уже завершённой задачи возвращается статус completed без ожидания.
    """
    task = TaskInfo(201, "v", "f", {})
    task.status = TaskStatus.COMPLETED
    task_store.add(task)
    response = client.get("/api/v1/parser/process/201/status?timeout=1")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"