import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status

# ===================== PREVIEW TESTS =====================
def test_v1_preview_success(client, clear_task_store):
    """Успешный preview возвращает 202 (согласно декоратору) и структуру ResultResponse"""
    with patch("app.api.v1.endpoints.process.fetch_and_validate", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = b"%PDF-1.4 mock"
        with patch("app.services.file_loader.Validator.validate", new_callable=AsyncMock) as mock_validator:
            mock_validator.return_value = "application/pdf"
            with patch("app.api.v1.endpoints.process.Pipeline.create") as mock_pipeline_factory:
                mock_pipeline = AsyncMock()
                mock_ctx = MagicMock()
                mock_ctx.final_json = {
                    "content": {
                        "document": {"source": {"file_name": "test.pdf", "page_count": 3}},
                        "quality": {},
                        "errors": [],
                        "status": "completed"
                    }
                }
                mock_pipeline.run = AsyncMock(return_value=mock_ctx)
                mock_pipeline_factory.return_value = mock_pipeline

                response = client.post(
                    "/api/v1/parser/process",
                    json={"task_id": 200, "file_key": "doc.pdf", "mode": "preview", "max_pages": 3}
                )
    # Ожидаем 202, так как декоратор эндпоинта установлен на 202 Accepted
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["task_id"] == 200
    assert data["metadata"]["mode"] == "preview"
    assert data["document"]["source"]["page_count"] == 3


def test_v1_preview_missing_max_pages(client):
    """Отсутствие max_pages в preview → 422"""
    response = client.post(
        "/api/v1/parser/process",
        json={"task_id": 1, "file_key": "doc.pdf", "mode": "preview"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "max_pages is required" in response.text


def test_v1_preview_forbidden_options(client):
    """extract_tables=True в preview → 422"""
    response = client.post(
        "/api/v1/parser/process",
        json={
            "task_id": 1,
            "file_key": "doc.pdf",
            "mode": "preview",
            "max_pages": 3,
            "options": {"extract_tables": True}
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "extract_tables cannot be True" in response.text


def test_v1_preview_extract_images_forbidden(client):
    """extract_images=True в preview → 422"""
    response = client.post(
        "/api/v1/parser/process",
        json={
            "task_id": 1,
            "file_key": "doc.pdf",
            "mode": "preview",
            "max_pages": 3,
            "options": {"extract_images": True}
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "extract_images cannot be True" in response.text


# ===================== FULL MODE TESTS =====================
def test_v1_full_accepted(client, clear_task_store):
    """Full-режим возвращает 202 Accepted"""
    with patch("app.api.v1.endpoints.process._run_full_pipeline", new_callable=AsyncMock):
        response = client.post(
            "/api/v1/parser/process",
            json={"task_id": 100, "file_key": "doc.pdf", "mode": "full"}
        )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["task_id"] == 100
    assert data["status"] == "accepted"


def test_v1_full_idempotent(client, clear_task_store):
    """Повторный запрос с тем же task_id возвращает существующую задачу"""
    with patch("app.api.v1.endpoints.process._run_full_pipeline", new_callable=AsyncMock):
        resp1 = client.post("/api/v1/parser/process", json={"task_id": 300, "file_key": "f.pdf", "mode": "full"})
        resp2 = client.post("/api/v1/parser/process", json={"task_id": 300, "file_key": "f2.pdf", "mode": "full"})
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["task_id"] == 300
    assert resp2.json()["task_id"] == 300
    assert resp2.json()["status"] == "accepted"