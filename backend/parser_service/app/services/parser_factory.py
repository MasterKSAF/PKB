"""
Фабрика парсеров: возвращает подходящий парсер по MIME-типу.
"""
import logging
from typing import Optional
from app.services.parsers.base import BaseParser
from app.services.parsers.pdf_parser import PdfParser

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
        parser_class = cls._parsers.get(mime_type)
        if parser_class:
            logger.debug(
                "Returning parser for MIME %s: %s",
                mime_type, parser_class.__name__
            )
            return parser_class()
        else:
            logger.warning("No parser registered for MIME %s", mime_type)
            return None