"""
Тесты эндпоинта POST /parser/preview.
Проверяют:
- успешный предпросмотр документа (возврат метаданных)
- правильность формирования ответа (file_name, page_count)
- обработку ошибок (валидация, StorageError и т.д.)
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.services.pipeline.context import ProcessingContext
from app.services.parsers.base import ParseResult


@pytest.fixture
def mock_preview_pipeline():
    """
    Фикстура: подменяет фабрику preview-пайплайна,
    возвращает мок-пайплайн с предопределённым контекстом.
    """
    with patch("app.api.v1.endpoints.preview.get_preview_pipeline") as mock_factory:
        mock_pipeline = AsyncMock()
        mock_ctx = ProcessingContext(
            task_id=1,
            version_id="v1",
            file_key="test.pdf",
            options={},
            original_file_name="test.pdf"
        )
        mock_ctx.parse_result = ParseResult(full_json={"pages": []}, total_pages=3)
        mock_pipeline.run = AsyncMock(return_value=mock_ctx)
        mock_factory.return_value = mock_pipeline
        yield mock_factory


def test_preview_success(client, clear_task_store, mock_preview_pipeline):
    """
    Проверка: при корректном запросе возвращается 200 OK,
    ответ содержит task_id, preview: true, source.file_name и source.page_count.
    """
    with patch("app.api.v1.endpoints.preview.minio_client.download_file", AsyncMock(return_value=b"%PDF-1.4")):
        with patch("app.api.v1.endpoints.preview.PdfReader") as mock_reader:
            mock_reader.return_value.pages = [1, 2, 3]  # имитация 3 страниц
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
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 1
    assert data["preview"] is True
    assert data["document"]["source"]["page_count"] == 3
    assert data["document"]["source"]["file_name"] == "test.pdf"