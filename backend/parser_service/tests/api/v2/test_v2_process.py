import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status
from datetime import datetime

from app.api.v1.schemas import ResultResponse, ResultMetadata, ParserInfo, ProcessingMode


# ===================== PREVIEW TESTS =====================
@pytest.mark.asyncio
async def test_v1_preview_success(async_client, clear_task_store, init_test_services):
    """Успешный preview возвращает 202 и структуру ResultResponse"""
    with patch("app.services.pipeline_service.PipelineService.run_preview", new_callable=AsyncMock) as mock_preview:
        # Создаём реальный объект ResultResponse
        mock_result = ResultResponse(
            metadata=ResultMetadata(
                schema_version="raw_ocr_v4",
                task_id=200,
                draft_id=200,
                mode="preview",
                preview_not_supported=False,
                created_at=datetime.now(),
                parser=ParserInfo(name="test", version="1.0")
            ),
            document={"source": {"file_name": "test.pdf", "page_count": 3}},
            quality={},
            errors=[],
            status="completed"
        )
        mock_preview.return_value = mock_result

        response = await async_client.post(
            "/api/v1/parser/process",
            json={
                "task_id": 200,
                "draft_id": 200,
                "file_key": "doc.pdf",
                "mode": "preview",
                "max_pages": 3,
                "options": {}
            }
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        # Проверяем, что task_id и mode теперь внутри metadata
        assert data["metadata"]["task_id"] == 200
        assert data["metadata"]["mode"] == "preview"
        assert data["document"]["source"]["page_count"] == 3


def test_v1_preview_missing_max_pages(client):
    """Отсутствие max_pages в preview → 422"""
    response = client.post(
        "/api/v1/parser/process",
        json={"task_id": 1, "draft_id": 1, "file_key": "doc.pdf", "mode": "preview"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "max_pages is required" in response.text


def test_v1_preview_forbidden_options(client):
    """extract_tables=True в preview → 422"""
    response = client.post(
        "/api/v1/parser/process",
        json={
            "task_id": 1,
            "draft_id": 1,
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
            "draft_id": 1,
            "file_key": "doc.pdf",
            "mode": "preview",
            "max_pages": 3,
            "options": {"extract_images": True}
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "extract_images cannot be True" in response.text


# ===================== FULL MODE TESTS =====================
@pytest.mark.asyncio
async def test_v1_full_accepted(async_client, clear_task_store, init_test_services):
    """Full-режим возвращает 202 Accepted"""
    with patch("app.services.pipeline_service.PipelineService.submit_full_task", new_callable=AsyncMock) as mock_submit:
        mock_submit.return_value = True
        with patch("app.services.pipeline_service.PipelineService.can_run_full_pipeline", new_callable=AsyncMock) as mock_can:
            mock_can.return_value = True
            response = await async_client.post(
                "/api/v1/parser/process",
                json={"task_id": 100, "draft_id": 100, "file_key": "doc.pdf", "mode": "full"}
            )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    # Для full-режима ответ — ProcessResponse, у которого есть task_id на верхнем уровне
    assert data["task_id"] == 100
    assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_v1_full_idempotent(async_client, clear_task_store, init_test_services):
    """Повторный запрос с тем же task_id возвращает существующую задачу"""
    with patch("app.services.pipeline_service.PipelineService.submit_full_task", new_callable=AsyncMock) as mock_submit:
        mock_submit.return_value = True
        with patch("app.services.pipeline_service.PipelineService.can_run_full_pipeline", new_callable=AsyncMock) as mock_can:
            mock_can.return_value = True
            resp1 = await async_client.post(
                "/api/v1/parser/process",
                json={"task_id": 300, "draft_id": 300, "file_key": "f.pdf", "mode": "full"}
            )
            resp2 = await async_client.post(
                "/api/v1/parser/process",
                json={"task_id": 300, "draft_id": 300, "file_key": "f2.pdf", "mode": "full"}
            )
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["task_id"] == 300
    assert resp2.json()["task_id"] == 300
    assert resp2.json()["status"] == "accepted"