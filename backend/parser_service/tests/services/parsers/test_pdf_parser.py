"""
Тесты для PdfParser (без реального вызова opendataloader_pdf).
Используются моки для изоляции от файловой системы и Java-процессов.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.base import ParseResult


@pytest.mark.asyncio
async def test_pdf_parser_returns_parse_result():
    """
    Проверка, что PdfParser.parse возвращает корректный ParseResult
    при мокировании всех внешних зависимостей.
    """
    pdf_bytes = b"%PDF-1.4 mock content"

    # Мокаем opendataloader_pdf.convert (синхронная функция)
    with patch("opendataloader_pdf.convert") as mock_convert:
        mock_convert.return_value = None

        # Мокаем создание временных файлов и директорий
        with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            mock_tempfile.return_value.__enter__.return_value.name = "/tmp/mock.pdf"

            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/mock_output"

                # Мокаем чтение файлов из выходной директории
                with patch("os.listdir") as mock_listdir:
                    mock_listdir.return_value = ["output.json", "output.html"]

                    # Мокаем открытие и чтение JSON
                    with patch("builtins.open", MagicMock()):
                        with patch("json.load") as mock_json_load:
                            mock_json_load.return_value = {
                                "pages": [{"page_num": 1}, {"page_num": 2}],
                                "page_count": 2
                            }
                            # Мокаем удаление временных файлов
                            with patch("os.unlink"), patch("shutil.rmtree"):
                                parser = PdfParser()
                                result = await parser.parse(pdf_bytes, {"extract_images": True})

    assert isinstance(result, ParseResult)
    assert result.total_pages == 2
    assert len(result.full_json["pages"]) == 2