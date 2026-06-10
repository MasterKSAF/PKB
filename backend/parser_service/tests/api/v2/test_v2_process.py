import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status


def test_v2_process_full_async(client, clear_task_store):
    with patch("app.api.v2.endpoints.process._run_full_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/v2/parser/process",
            json={"task_id": 100, "file_key": "doc.pdf", "mode": "full"}
        )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["task_id"] == 100
    assert data["status"] == "accepted"


def test_v2_process_preview_sync(client, clear_task_store, mock_minio_download, mock_validator, mock_pipeline_preview):
    mock_minio_download.return_value = b"%PDF-1.4"
    response = client.post(
        "/api/v2/parser/process",
        json={"task_id": 200, "file_key": "doc.pdf", "mode": "preview", "max_pages": 3}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["task_id"] == 200
    assert data["preview"] is True


def test_v2_process_preview_missing_max_pages(client):
    response = client.post(
        "/api/v2/parser/process",
        json={"task_id": 1, "file_key": "doc.pdf", "mode": "preview"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_v2_process_preview_forbidden_options(client):
    response = client.post(
        "/api/v2/parser/process",
        json={
            "task_id": 1,
            "file_key": "doc.pdf",
            "mode": "preview",
            "max_pages": 3,
            "options": {"extract_tables": True}
        }
    )
    assert response.status_code == 422


def test_v2_process_idempotent_full(client, clear_task_store):
    with patch("app.api.v2.endpoints.process._run_full_pipeline", new_callable=AsyncMock):
        resp1 = client.post("/api/v2/parser/process", json={"task_id": 300, "file_key": "f.pdf", "mode": "full"})
        resp2 = client.post("/api/v2/parser/process", json={"task_id": 300, "file_key": "f2.pdf", "mode": "full"})
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["status"] == "accepted"