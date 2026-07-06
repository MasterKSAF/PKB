"""
Тесты для DoclingParser.
Используются моки для изоляции от Docling-воркера.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from app.services.parsers.docling_parser import DoclingParser
from app.services.parsers.base import ParseResult


SAMPLE_DOCLING_JSON = {
    "content": {
        "document": {
            "source": {
                "file_name": "test.pdf",
                "page_count": 3,
            },
            "pages": [
                {"page": 1, "width": 595, "height": 842},
                {"page": 2, "width": 595, "height": 842},
                {"page": 3, "width": 595, "height": 842},
            ],
            "block": [
                {
                    "type": "paragraph",
                    "page number": 1,
                    "content": "Test paragraph",
                    "bounding box": [0, 0, 100, 50],
                },
                {
                    "type": "image",
                    "page number": 1,
                    "content": "",
                    "image_key": "images/page_1_1.png",
                    "bounding box": [0, 0, 200, 150],
                },
                {
                    "type": "paragraph",
                    "page number": 2,
                    "content": "More text",
                    "bounding box": [0, 0, 80, 40],
                },
            ],
        },
        "quality": {
            "confidence": 0.85,
            "pages_processed": 3,
            "per_page": [
                {"page": 1, "confidence": 0.85, "status": "ok"},
                {"page": 2, "confidence": 0.85, "status": "ok"},
                {"page": 3, "confidence": 0.85, "status": "ok"},
            ],
        },
        "errors": [],
        "status": "completed",
        "metadata": {
            "total_pages": 3,
            "has_tables": False,
        },
    }
}


@pytest.mark.asyncio
async def test_docling_parser_success():
    """Базовый тест успешного парсинга через DoclingParser."""
    pdf_bytes = b"%PDF-1.4 mock content"

    with patch("app.services.parsers.docling_parser.parse_pdf_worker") as mock_worker:
        mock_worker.return_value = SAMPLE_DOCLING_JSON
        with patch("app.services.parsers.docling_parser.process_pool_executor") as mock_executor:
            with patch("tempfile.mkdtemp") as mock_mkdtemp:
                mock_mkdtemp.return_value = "/tmp/docling_test"
                with patch("os.makedirs"), patch("os.path.exists", return_value=True):
                    # Мокаем run_in_executor, чтобы он вызвал функцию синхронно
                    loop_mock = MagicMock()
                    loop_mock.run_in_executor.return_value = SAMPLE_DOCLING_JSON

                    with patch("asyncio.get_running_loop", return_value=loop_mock):
                        with patch("app.services.parsers.docling.quality_metrics.assess_quality_from_json") as mock_quality:
                            mock_quality.return_value = {}
                            parser = DoclingParser()
                            result = await parser.parse(
                                pdf_bytes,
                                {"extract_images": True},
                                task_id=1,
                                total_pages=3,
                            )
                            assert isinstance(result, ParseResult)
                            assert result.total_pages == 3
                            assert result.full_json is SAMPLE_DOCLING_JSON


@pytest.mark.asyncio
async def test_docling_parser_collect_images():
    """Проверка сбора изображений из JSON (image_key)."""
    pdf_bytes = b"%PDF-1.4 mock content"

    with patch("app.services.parsers.docling_parser.parse_pdf_worker") as mock_worker:
        mock_worker.return_value = SAMPLE_DOCLING_JSON
        with patch("app.services.parsers.docling_parser.process_pool_executor") as mock_executor:
            loop_mock = MagicMock()
            loop_mock.run_in_executor.return_value = SAMPLE_DOCLING_JSON
            with patch("asyncio.get_running_loop", return_value=loop_mock):
                with patch("tempfile.mkdtemp") as mock_mkdtemp:
                    mock_mkdtemp.return_value = "/tmp/docling_test"
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True) as mock_exists:
                            with patch("app.services.parsers.docling.quality_metrics.assess_quality_from_json") as mock_quality:
                                mock_quality.return_value = {}
                                parser = DoclingParser()

                                # Мокаем _collect_image_paths
                                with patch.object(
                                    parser,
                                    "_collect_image_paths",
                                    return_value=[(1, "/tmp/docling_test/images/page_1_1.png", ".png")],
                                ):
                                    result = await parser.parse(
                                        pdf_bytes,
                                        {"extract_images": True},
                                        task_id=1,
                                    )
                                    assert len(result.images) == 1
                                    assert result.images[0][0] == 1
                                    assert result.images[0][2] == ".png"


@pytest.mark.asyncio
async def test_docling_parser_no_images_option():
    """Проверка, что при extract_images=False изображения не собираются."""
    pdf_bytes = b"%PDF-1.4 mock content"

    with patch("app.services.parsers.docling_parser.parse_pdf_worker") as mock_worker:
        mock_worker.return_value = SAMPLE_DOCLING_JSON
        with patch("app.services.parsers.docling_parser.process_pool_executor") as mock_executor:
            loop_mock = MagicMock()
            loop_mock.run_in_executor.return_value = SAMPLE_DOCLING_JSON
            with patch("asyncio.get_running_loop", return_value=loop_mock):
                with patch("tempfile.mkdtemp") as mock_mkdtemp:
                    mock_mkdtemp.return_value = "/tmp/docling_test"
                    with patch("os.makedirs"), patch("os.path.exists", return_value=True):
                        with patch("app.services.parsers.docling.quality_metrics.assess_quality_from_json") as mock_quality:
                            mock_quality.return_value = {}
                            parser = DoclingParser()
                            result = await parser.parse(
                                pdf_bytes,
                                {"extract_images": False},
                                task_id=1,
                            )
                            assert len(result.images) == 0
