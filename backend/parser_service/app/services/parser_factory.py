"""
Фабрика парсеров: возвращает экземпляр парсера в зависимости от MIME-типа.
"""
from typing import Optional
from app.services.parsers.base import BaseParser
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.doc_parser import DocParser
from app.services.parsers.docx_parser import DocxParser


class ParserFactory:
    """Регистрирует поддерживаемые MIME-типы и создаёт соответствующие парсеры."""

    _parsers = {
        "application/pdf": PdfParser,
        "application/msword": DocParser,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
    }

    @classmethod
    def get_parser(cls, mime_type: str) -> Optional[BaseParser]:
        """
        Возвращает экземпляр парсера для указанного MIME-типа.
        Если тип не поддерживается, возвращает None.
        """
        parser_class = cls._parsers.get(mime_type)
        return parser_class() if parser_class else None