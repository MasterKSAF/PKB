"""
Тесты эндпоинта POST /api/v1/parser/preview.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status
from app.core.exceptions import FileNotFoundError, UnsupportedFormatError, FileTooLargeError


@pytest.fixture
def mock_minio_download():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_validator():
    with patch("app.services.file_loader.Validator.validate") as mock:
        mock.return_value = "application/pdf"
        yield mock


def test_preview_success(client, clear_task_store, mock_minio_download, mock_validator):
    """
    Успешный предпросмотр: возвращает 200, документ содержит page_count и file_name.
    """
    mock_minio_download.return_value = b"%PDF-1.4 mock"
    # Мокаем парсинг и пайплайн
    with patch("app.api.v1.endpoints.preview.Pipeline.create") as mock_pipeline_factory:
        mock_pipeline = AsyncMock()
        mock_ctx = MagicMock()
        mock_ctx.final_json = {
            "content": {
                "document": {
                    "source": {"file_name": "test.pdf", "page_count": 3},
                    "block": []
                }
            }
        }
        mock_pipeline.run = AsyncMock(return_value=mock_ctx)
        mock_pipeline_factory.return_value = mock_pipeline

        response = client.post(
            "/api/v1/parser/preview",
            json={
                "task_id": 1,
                "version_id": "v1",
                "file_key": "test.pdf",
                "max_pages": 2,
                "options": {}
            }
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["task_id"] == 1
    assert data["preview"] is True
    assert data["max_pages"] == 2
    assert data["document"]["source"]["file_name"] == "test.pdf"
    assert data["document"]["source"]["page_count"] == 3


def test_preview_file_not_found(client, clear_task_store, mock_minio_download):
    """Ошибка FILE_NOT_FOUND при отсутствии файла."""
    mock_minio_download.side_effect = FileNotFoundError("test.pdf")
    response = client.post(
        "/api/v1/parser/preview",
        json={"task_id": 1, "version_id": "v1", "file_key": "missing.pdf", "max_pages": 2}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["code"] == "FILE_NOT_FOUND"


def test_preview_unsupported_format(client, clear_task_store, mock_minio_download, mock_validator):
    """Неподдерживаемый MIME → 415 UNSUPPORTED_FORMAT."""
    mock_minio_download.return_value = b"fake"
    mock_validator.side_effect = UnsupportedFormatError("image/jpeg")
    response = client.post(
        "/api/v1/parser/preview",
        json={"task_id": 1, "version_id": "v1", "file_key": "image.jpg", "max_pages": 2}
    )
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert response.json()["error"]["code"] == "UNSUPPORTED_FORMAT"


def test_preview_file_too_large(client, clear_task_store, mock_minio_download, mock_validator):
    """Файл больше лимита → 413 FILE_TOO_LARGE."""
    mock_minio_download.return_value = b"fake"
    mock_validator.side_effect = FileTooLargeError(600, 500)
    response = client.post(
        "/api/v1/parser/preview",
        json={"task_id": 1, "version_id": "v1", "file_key": "big.pdf", "max_pages": 2}
    )
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"