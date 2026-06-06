"""
Тесты для фабрики парсеров (parser_factory.py)
Проверяют, что для поддерживаемых MIME-типов возвращаются правильные экземпляры,
а для неподдерживаемых – None.
"""
from app.services.parser_factory import ParserFactory
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.doc_parser import DocParser
from app.services.parsers.docx_parser import DocxParser


def test_get_pdf_parser():
    """PDF MIME должен возвращать экземпляр PdfParser."""
    parser = ParserFactory.get_parser("application/pdf")
    assert isinstance(parser, PdfParser)


def test_get_doc_parser():
    """DOC MIME возвращает заглушку DocParser."""
    parser = ParserFactory.get_parser("application/msword")
    assert isinstance(parser, DocParser)


def test_get_docx_parser():
    """DOCX MIME возвращает заглушку DocxParser."""
    parser = ParserFactory.get_parser(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert isinstance(parser, DocxParser)


def test_unsupported_mime():
    """Неподдерживаемый MIME возвращает None."""
    parser = ParserFactory.get_parser("image/png")
    assert parser is None