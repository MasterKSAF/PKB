"""
Тесты для модуля image_uploader.py
Проверяют:
- загрузку изображений через MinIOImageUploader
- формирование маппинга (page_num, idx) -> image_key
- обработку пустого списка
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.image_uploader import MinIOImageUploader


@pytest.mark.asyncio
async def test_upload_images_success():
    """Проверка: загрузка одного изображения приводит к вызову minio_client.upload_image
    и возвращает правильный маппинг с одним ключом."""
    mock_client = AsyncMock()
    with patch("app.services.image_uploader.minio_client", mock_client):
        uploader = MinIOImageUploader()
        images = [(1, b"imgdata", ".png")]
        mapping = await uploader.upload_images(images, task_id=100)

        # Проверяем, что upload_image был вызван ровно один раз
        assert mock_client.upload_image.call_count == 1
        # Проверяем структуру возвращённого словаря
        assert mapping == {(1, 0): "task_100/img_1_0.png"}


@pytest.mark.asyncio
async def test_upload_images_multiple():
    """Проверка: загрузка нескольких изображений с разных страниц.
    Ключи должны формироваться с учётом page_num и индекса внутри страницы."""
    mock_client = AsyncMock()
    with patch("app.services.image_uploader.minio_client", mock_client):
        uploader = MinIOImageUploader()
        images = [
            (1, b"img1", ".png"),
            (2, b"img2", ".jpg"),
            (1, b"img3", ".png")
        ]
        mapping = await uploader.upload_images(images, task_id=42)

        assert mock_client.upload_image.call_count == 3
        # Проверяем, что для разных страниц и индексов генерируются разные ключи
        assert mapping[(1, 0)] == "task_42/img_1_0.png"
        assert mapping[(2, 1)] == "task_42/img_2_1.jpg"
        assert mapping[(1, 2)] == "task_42/img_1_2.png"


@pytest.mark.asyncio
async def test_upload_empty_images():
    """Проверка: при пустом списке изображений ничего не загружается
    и возвращается пустой словарь."""
    mock_client = AsyncMock()
    with patch("app.services.image_uploader.minio_client", mock_client):
        uploader = MinIOImageUploader()
        mapping = await uploader.upload_images([], task_id=10)

        mock_client.upload_image.assert_not_called()
        assert mapping == {}