"""
Тесты эндпоинта POST /api/v1/parser/process.
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


def test_process_start(client, clear_task_store):
    """При корректном запросе возвращается 202 Accepted."""
    with patch("app.api.v1.endpoints.process._run_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/v1/parser/process",
            json={
                "task_id": 100,
                "version_id": "ver-123",
                "file_key": "doc.pdf",
                "options": {"extract_tables": True}
            }
        )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["task_id"] == 100
    assert data["status"] == "accepted"
    assert "estimated_completion" in data


def test_process_idempotent(client, clear_task_store):
    """Повторный запрос с тем же task_id возвращает существующую задачу (если не завершена)."""
    with patch("app.api.v1.endpoints.process._run_pipeline", new_callable=AsyncMock):
        # Первый запрос
        resp1 = client.post(
            "/api/v1/parser/process",
            json={"task_id": 200, "version_id": "v1", "file_key": "f1.pdf"}
        )
        # Второй запрос
        resp2 = client.post(
            "/api/v1/parser/process",
            json={"task_id": 200, "version_id": "v2", "file_key": "f2.pdf"}
        )
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    # Должен вернуть тот же status (accepted), а не новый task_id
    assert resp2.json()["task_id"] == 200
    assert resp2.json()["status"] == "accepted"


def test_process_invalid_task_id(client):
    """task_id меньше 1 → 422 Validation Error."""
    response = client.post(
        "/api/v1/parser/process",
        json={"task_id": 0, "version_id": "v1", "file_key": "doc.pdf"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_process_empty_version_id(client):
    """version_id пустая строка → 422."""
    response = client.post(
        "/api/v1/parser/process",
        json={"task_id": 1, "version_id": "", "file_key": "doc.pdf"}
    )
    assert response.status_code == 422