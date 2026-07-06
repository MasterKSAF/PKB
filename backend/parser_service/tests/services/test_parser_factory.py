"""
Тесты для фабрики парсеров.
"""
from app.services.parser_factory import ParserFactory
from app.services.parsers.docling_parser import DoclingParser
from app.services.parser_factory import MockPdfParser


def test_get_pdf_parser():
    parser = ParserFactory.get_parser("application/pdf")
    assert isinstance(parser, DoclingParser)


def test_get_unsupported_mime():
    parser = ParserFactory.get_parser("image/png")
    assert parser is None

    parser = ParserFactory.get_parser("application/msword")
    assert parser is None

    parser = ParserFactory.get_parser("")
    assert parser is None