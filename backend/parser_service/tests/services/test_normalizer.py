"""
Тесты для модуля normalizer.py (Normalizer)
Проверяют:
- загрузку изображений через ImageUploader
- замену поля 'data' на 'image_key' в JSON
- формирование итогового контейнера
"""
import pytest
from unittest.mock import AsyncMock
from app.services.normalizer import Normalizer
from app.services.parsers.base import ParseResult


@pytest.mark.asyncio
async def test_normalizer_upload_images():
    """
    Проверка, что нормализатор вызывает upload_images, заменяет base64
    на image_key и возвращает контейнер с правильными полями.
    """
    # Создаём мок загрузчика изображений
    mock_uploader = AsyncMock()
    mock_uploader.upload_images.return_value = {(1, 0): "minio_key_1"}

    normalizer = Normalizer(image_uploader=mock_uploader)

    parse_result = ParseResult(
        full_json={
            "pages": [
                {
                    "page_num": 1,
                    "images": [{"data": "base64_encoded_image"}]
                }
            ]
        },
        images=[(1, b"raw_image_data", ".png")],
        total_pages=1
    )

    container = await normalizer.normalize(parse_result, task_id=42)

    # Проверяем, что upload_images был вызван один раз с правильными аргументами
    mock_uploader.upload_images.assert_called_once_with(parse_result.images, 42)

    # Проверяем структуру контейнера
    assert container["document_info"]["task_id"] == 42
    assert container["metadata"]["total_pages"] == 1

    # Проверяем, что изображение было заменено на image_key
    images_in_result = container["content"]["pages"][0]["images"]
    assert len(images_in_result) == 1
    assert images_in_result[0]["image_key"] == "minio_key_1"
    assert "data" not in images_in_result[0]   # base64 удалён