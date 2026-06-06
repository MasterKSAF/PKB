"""
Нормализация результата парсинга:
- загрузка изображений в MinIO
- замена поля 'data' (base64) на 'image_key'
- формирование JSON-контейнера
"""
import copy
from typing import Dict, Any
from app.services.parsers.base import ParseResult
from app.services.image_uploader import MinIOImageUploader, ImageUploader


class Normalizer:
    """Преобразует ParseResult в итоговый JSON-контейнер."""

    def __init__(self, image_uploader: ImageUploader = None):
        self.image_uploader = image_uploader or MinIOImageUploader()

    async def normalize(self, parse_result: ParseResult, task_id: int) -> Dict[str, Any]:
        """
        Загружает изображения, заменяет ссылки и упаковывает результат.
        :param parse_result: результат парсинга
        :param task_id: ID задачи (для привязки изображений)
        :return: словарь-контейнер с полями document_info, content, metadata
        """
        # 1. Загрузка изображений в MinIO
        image_mapping = await self.image_uploader.upload_images(parse_result.images, task_id)

        # 2. Глубокое копирование исходного JSON (чтобы не мутировать оригинал)
        enriched_json = copy.deepcopy(parse_result.full_json)

        # 3. Рекурсивная замена base64 на image_key
        def replace_images(node, page_num_hint=1):
            if isinstance(node, dict):
                if "page_num" in node:
                    page_num_hint = node["page_num"]
                if "images" in node and isinstance(node["images"], list):
                    new_images = []
                    for idx, img in enumerate(node["images"]):
                        if "data" in img:
                            key = image_mapping.get((page_num_hint, idx))
                            if key:
                                img["image_key"] = key
                            del img["data"]   # удаляем base64 для уменьшения размера
                        new_images.append(img)
                    node["images"] = new_images
                for v in node.values():
                    replace_images(v, page_num_hint)
            elif isinstance(node, list):
                for item in node:
                    replace_images(item, page_num_hint)

        replace_images(enriched_json)

        # 4. Формирование финального контейнера
        container = {
            "document_info": {
                "task_id": task_id,
                "parser_version": "1.0",
                "extraction_options": parse_result.full_json.get("options", {})
            },
            "content": enriched_json,
            "metadata": {
                "total_pages": parse_result.total_pages,
                "has_tables": "table" in str(enriched_json).lower()
            }
        }
        return container