"""
Фабрика парсеров: возвращает подходящий парсер по MIME-типу.
Поддерживает мок-режим через настройку USE_MOCK_PARSER.
"""

import logging
from typing import Optional
from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.pdf_parser import PdfParser
from app.config import settings
import json
import os

logger = logging.getLogger(__name__)


class ParserFactory:
    """Фабрика, возвращающая экземпляр парсера для заданного MIME-типа."""

    _parsers = {
        "application/pdf": PdfParser,
    }

    @classmethod
    def get_parser(cls, mime_type: str) -> Optional[BaseParser]:
        """
        Возвращает экземпляр парсера для указанного MIME-типа.

        Args:
            mime_type: MIME-тип документа.

        Returns:
            Экземпляр парсера или None, если тип не поддерживается.
        """
        if settings.use_mock_parser:
            logger.debug("Using MockPdfParser")
            return MockPdfParser()

        parser_class = cls._parsers.get(mime_type)
        if parser_class:
            logger.debug("Returning parser for MIME %s: %s", mime_type, parser_class.__name__)
            return parser_class()
        else:
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