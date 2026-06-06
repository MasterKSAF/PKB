"""
Интерфейс и реализация загрузчика изображений в MinIO.
Отделяет логику загрузки от нормализатора.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from app.core.minio_client import minio_client


class ImageUploader(ABC):
    """Абстрактный загрузчик изображений."""

    @abstractmethod
    async def upload_images(self, images: List[Tuple[int, bytes, str]], task_id: int) -> dict:
        """
        Загружает список изображений в хранилище.
        :param images: список кортежей (page_num, image_bytes, extension)
        :param task_id: идентификатор задачи (используется для формирования ключа)
        :return: словарь {(page_num, idx): image_key}
        """
        pass


class MinIOImageUploader(ImageUploader):
    """Реальная реализация загрузки изображений в MinIO."""

    async def upload_images(self, images: List[Tuple[int, bytes, str]], task_id: int) -> dict:
        mapping = {}
        for idx, (page_num, img_bytes, ext) in enumerate(images):
            # Ключ в MinIO: task_{task_id}/img_{page_num}_{idx}{ext}
            image_key = f"task_{task_id}/img_{page_num}_{idx}{ext}"
            await minio_client.upload_image(img_bytes, task_id, page_num, ext)
            mapping[(page_num, idx)] = image_key
        return mapping