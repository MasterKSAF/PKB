"""
Тесты для PdfParser (без реального вызова opendataloader_pdf).
Используются моки для изоляции от файловой системы и Java-процессов.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.base import ParseResult
from app.config import settings


@pytest.mark.asyncio
async def test_pdf_parser_success():
    pdf_bytes = b"%PDF-1.4 mock"
    with patch("opendataloader_pdf.convert") as mock_convert:
        mock_convert.return_value = None
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/mock_output"
                with patch("os.listdir") as mock_listdir:
                    mock_listdir.return_value = ["output.json"]
                    with patch("builtins.open", MagicMock()):
                        with patch("json.load") as mock_json_load:
                            mock_json_load.return_value = {"pages": [{"page_num": 1}], "page_count": 1}
                            with patch("os.unlink"), patch("shutil.rmtree"):
                                parser = PdfParser()
                                result = await parser.parse(pdf_bytes, {"extract_images": True}, task_id=1)
                                assert isinstance(result, ParseResult)
                                assert result.total_pages == 1
                                assert result.full_json == {"pages": [{"page_num": 1}], "page_count": 1}
                                assert result.temp_dir == "/tmp/mock_output"
                                assert result.images == []  # нет изображений


@pytest.mark.asyncio
async def test_pdf_parser_with_images():
    pdf_bytes = b"%PDF-1.4"
    with patch("opendataloader_pdf.convert") as mock_convert:
        mock_convert.return_value = None
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/mock_output"
                with patch("os.listdir") as mock_listdir:
                    mock_listdir.return_value = ["output.json"]
                    with patch("builtins.open", MagicMock()):
                        with patch("json.load") as mock_json_load:
                            # JSON содержит ссылку на изображение
                            mock_json_load.return_value = {
                                "pages": [],
                                "page_count": 2,
                                "image": {"source": "img1.png"}
                            }
                            # Мокаем существование файла изображения во временной директории
                            with patch("os.path.exists", return_value=True):
                                with patch("os.unlink"), patch("shutil.rmtree"):
                                    parser = PdfParser()
                                    result = await parser.parse(pdf_bytes, {"extract_images": True}, task_id=1)
                                    assert len(result.images) == 1
                                    assert result.images[0][0] == 1  # page_num по умолчанию
                                    assert result.images[0][2] == ".png"


@pytest.mark.asyncio
async def test_pdf_parser_timeout():
    pdf_bytes = b"%PDF-1.4"
    with patch("opendataloader_pdf.convert", side_effect=lambda *args, **kwargs: __import__("time").sleep(10)):
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/mock_output"
                parser = PdfParser()
                # Устанавливаем маленький таймаут для теста (в реальном коде settings.parser_timeout)
                with patch("app.config.settings.parser_timeout", 0.1):
                    with pytest.raises(TimeoutError):
                        await parser.parse(pdf_bytes, {}, task_id=1)


@pytest.mark.asyncio
async def test_pdf_parser_no_json_file():
    pdf_bytes = b"%PDF-1.4"
    with patch("opendataloader_pdf.convert") as mock_convert:
        mock_convert.return_value = None
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/mock_output"
                with patch("os.listdir") as mock_listdir:
                    mock_listdir.return_value = ["output.html"]  # нет JSON
                    with pytest.raises(Exception, match="JSON file not generated"):
                        parser = PdfParser()
                        await parser.parse(pdf_bytes, {}, task_id=1)