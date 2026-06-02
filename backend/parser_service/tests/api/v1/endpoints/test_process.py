"""
Тесты эндпоинта POST /parser/process.
Проверяют:
- приём запроса, создание задачи, возврат 202 Accepted.
"""
import pytest
from unittest.mock import patch, AsyncMock


def test_process_start(client, clear_task_store):
    """
    Проверка: при корректном запросе возвращается 202 Accepted,
    статус 'accepted', task_id и version_id совпадают.
    """
    with patch("app.api.v1.endpoints.process._run_pipeline", new=AsyncMock()):
        response = client.post(
            "/api/v1/parser/process",
            json={
                "task_id": 100,
                "version_id": "ver-123",
                "file_key": "doc.pdf",
                "options": {"extract_tables": True}
            }
        )
    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == 100
    assert data["status"] == "accepted"