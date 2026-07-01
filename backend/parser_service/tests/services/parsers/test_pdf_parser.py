"""
Тесты для PdfParser (без реального вызова opendataloader_pdf).
Используются моки для изоляции от файловой системы и Java-процессов.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.base import ParseResult


@pytest.mark.asyncio
async def test_pdf_parser_success():
    pdf_bytes = b"%PDF-1.4 mock"
    # Мокаем стандартизатор, чтобы он возвращал исходный JSON без изменений
    with patch("app.services.parsers.pdf_parser.JsonStandardizer") as MockStandardizer:
        mock_std = MockStandardizer.return_value
        mock_std.transform.return_value = {"pages": [{"page_num": 1}], "page_count": 1}
        with patch("opendataloader_pdf.convert") as mock_convert:
            mock_convert.return_value = None
            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
                with patch("tempfile.mkdtemp") as mock_mkdtemp:
                    mock_mkdtemp.return_value = "/tmp/mock_output"
                    with patch("pathlib.Path.glob") as mock_glob:
                        mock_glob.return_value = [Path("/tmp/mock_output/output.json")]
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
    with patch("app.services.parsers.pdf_parser.JsonStandardizer") as MockStandardizer:
        mock_std = MockStandardizer.return_value
        mock_std.transform.return_value = {"pages": [], "page_count": 2, "image": {"source": "img1.png"}}
        with patch("opendataloader_pdf.convert") as mock_convert:
            mock_convert.return_value = None
            with patch("tempfile.NamedTemporaryFile") as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
                with patch("tempfile.mkdtemp") as mock_mkdtemp:
                    mock_mkdtemp.return_value = "/tmp/mock_output"
                    with patch("pathlib.Path.glob") as mock_glob:
                        mock_glob.return_value = [Path("/tmp/mock_output/output.json")]
                        with patch("builtins.open", MagicMock()):
                            with patch("json.load") as mock_json_load:
                                mock_json_load.return_value = {"pages": [], "page_count": 2, "image": {"source": "img1.png"}}
                                with patch("os.path.exists", return_value=True):
                                    with patch("os.unlink"), patch("shutil.rmtree"):
                                        parser = PdfParser()
                                        # Мокаем сбор изображений, чтобы вернуть одно изображение
                                        with patch.object(parser, '_collect_image_paths', return_value=[(1, "/tmp/mock_output/images/img1.png", ".png")]):
                                            result = await parser.parse(pdf_bytes, {"extract_images": True}, task_id=1)
                                            assert len(result.images) == 1
                                            assert result.images[0][0] == 1
                                            assert result.images[0][2] == ".png"


@pytest.mark.asyncio
async def test_pdf_parser_timeout():
    pdf_bytes = b"%PDF-1.4"
    # Мокаем _run_parser, чтобы он сразу выбрасывал TimeoutError
    with patch("app.services.parsers.pdf_parser.PdfParser._run_parser", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = TimeoutError("Simulated timeout")
        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/mock.pdf"
            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/mock_output"
                parser = PdfParser()
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
                with patch("pathlib.Path.glob") as mock_glob:
                    mock_glob.return_value = []  # JSON не найден
                    with pytest.raises(FileNotFoundError, match="JSON файл не найден"):
                        parser = PdfParser()
                        await parser.parse(pdf_bytes, {}, task_id=1)