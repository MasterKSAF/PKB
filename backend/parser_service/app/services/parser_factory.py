"""
Фабрика парсеров: возвращает подходящий парсер по MIME-типу.
По умолчанию для PDF используется DoclingParser.
"""

import logging
from typing import Optional
from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.docling_parser import DoclingParser
from app.config import settings
import json
import os

logger = logging.getLogger(__name__)


class ParserFactory:
    """Фабрика, возвращающая экземпляр парсера для заданного MIME-типа."""

    @classmethod
    def get_parser(cls, mime_type: str) -> Optional[BaseParser]:
        """
        Возвращает экземпляр парсера для указанного MIME-типа.
        Для PDF всегда использует DoclingParser (или мок в тестовом режиме).
        """
        if mime_type == "application/pdf":
            if settings.use_mock_parser:
                logger.debug("Using MockPdfParser")
                return MockPdfParser()
            logger.debug("Using DoclingParser")
            return DoclingParser()

        logger.warning("No parser registered for MIME %s", mime_type)
        return None


class MockPdfParser(BaseParser):
    """Мок-парсер, возвращающий фиктивный JSON для тестирования."""

    async def parse(self, file_bytes, options, task_id, total_pages=None):
        logger.info("[MOCK] Parsing PDF for task %d", task_id)
        # Загрузка фикстуры, если указана
        if settings.mock_parser_fixture_path and os.path.exists(settings.mock_parser_fixture_path):
            with open(settings.mock_parser_fixture_path, "r", encoding="utf-8") as f:
                full_json = json.load(f)
        else:
            # Генерация простого тестового JSON
            full_json = {
                "number of pages": 5,
                "kids": [
                    {
                        "type": "paragraph",
                        "page number": 1,
                        "bounding box": [10, 10, 100, 50],
                        "content": "Mock paragraph content",
                    },
                    {
                        "type": "image",
                        "page number": 2,
                        "source": "mock_image.png",
                        "width": 200,
                        "height": 150,
                    },
                ],
            }
        images = []
        return ParseResult(
            full_json=full_json,
            images=images,
            total_pages=total_pages or 5,
            temp_dir=None,
        )