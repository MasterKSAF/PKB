"""
Тесты для DoclingParser.
Используются моки для изоляции от Docling-воркера.
"""
import os
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


def _create_test_pdf_with_image(pdf_path: str) -> None:
    """Создаёт простой PDF с одним встроенным изображением."""
    import fitz
    import io as _io
    from PIL import Image as _PILImage
    import os
    os.makedirs(os.path.dirname(pdf_path) or '.', exist_ok=True)

    # Создаём PNG через PIL и внедряем в PDF
    img = _PILImage.new('RGB', (10, 10), color='red')
    buf = _io.BytesIO()
    img.save(buf, format='PNG')

    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(pdf_path)
    doc.close()


def test_save_images_from_pdf(tmp_path):
    """_save_images_from_pdf извлекает изображения из PDF."""
    from app.services.parsers.docling.docling_mapper import _save_images_from_pdf

    pdf_path = str(tmp_path / "test.pdf")
    _create_test_pdf_with_image(pdf_path)

    images_dir = str(tmp_path / "images")
    result = _save_images_from_pdf(pdf_path, images_dir)

    assert len(result) >= 1
    pno, fpath, ext = result[0]
    assert pno == 1  # 1-based page number
    assert fpath.endswith(".png")
    assert ext == ".png"
    assert os.path.exists(fpath)


def test_save_images_from_pdf_no_images(tmp_path):
    """_save_images_from_pdf возвращает пустой список если в PDF нет изображений."""
    from app.services.parsers.docling.docling_mapper import _save_images_from_pdf
    import fitz

    pdf_path = str(tmp_path / "empty.pdf")
    pdf_doc = fitz.open()
    pdf_doc.new_page()
    pdf_doc.save(pdf_path)
    pdf_doc.close()

    images_dir = str(tmp_path / "images")
    result = _save_images_from_pdf(pdf_path, images_dir)
    assert result == []


def test_save_images_from_pdf_with_uploader(tmp_path):
    """_save_images_from_pdf с uploader'ом возвращает его ключи вместо локальных путей."""
    from app.services.parsers.docling.docling_mapper import _save_images_from_pdf

    pdf_path = str(tmp_path / "test.pdf")
    _create_test_pdf_with_image(pdf_path)

    calls = []

    def fake_uploader(page_no, img_bytes, ext):
        calls.append((page_no, ext))
        return f"minio://images/{page_no}_{len(calls)}.png"

    result = _save_images_from_pdf(pdf_path, "", image_uploader=fake_uploader)

    assert len(result) >= 1
    assert len(calls) >= 1
    pno, key, ext = result[0]
    assert pno == 1
    assert key.startswith("minio://images/")
    assert ext == ".png"
    # Файлы на диске созданы не должны быть
    assert not os.path.exists(str(tmp_path / "images" / "page_1_1.png"))


def test_inject_missing_image_blocks(tmp_path):
    """_inject_missing_image_blocks для локальных путей проставляет _temp_path."""
    from app.services.parsers.docling.docling_mapper import _inject_missing_image_blocks

    images_dir = str(tmp_path / "images")
    os.makedirs(images_dir, exist_ok=True)

    p1 = str(Path(images_dir, "page_1_1.png"))
    p2 = str(Path(images_dir, "page_1_2.png"))
    p3 = str(Path(images_dir, "page_2_1.png"))
    Path(p1).write_text("fake_png_1")
    Path(p2).write_text("fake_png_2")
    Path(p3).write_text("fake_png_3")

    pdf_images = [
        (1, p1, ".png"),
        (1, p2, ".png"),
        (2, p3, ".png"),
    ]

    json_result = {
        "content": {
            "document": {
                "block": [
                    {
                        "type": "image",
                        "page number": 1,
                        "content": "",
                        "image_key": "images/page_1_1.png",
                        "_temp_path": p1,
                    }
                ]
            }
        }
    }

    _inject_missing_image_blocks(json_result, images_dir, pdf_images)

    blocks = json_result["content"]["document"]["block"]
    assert len(blocks) == 3

    assert blocks[0]["image_key"] == "images/page_1_1.png"
    assert blocks[1]["page number"] == 1
    assert blocks[1]["image_key"] == "images/page_1_2.png"
    assert blocks[1]["_temp_path"] == p2
    assert blocks[2]["page number"] == 2
    assert blocks[2]["image_key"] == "images/page_2_1.png"
    assert blocks[2]["_temp_path"] == p3


def test_inject_missing_image_blocks_no_duplicates(tmp_path):
    """_inject_missing_image_blocks не добавляет дубликаты (по _temp_path или image_key)."""
    from app.services.parsers.docling.docling_mapper import _inject_missing_image_blocks

    images_dir = str(tmp_path / "images")
    os.makedirs(images_dir, exist_ok=True)
    p = str(Path(images_dir, "page_1_1.png"))
    Path(p).write_text("fake")

    pdf_images = [(1, p, ".png")]

    # Блок уже с _temp_path → дубликат не добавляется
    json_result = {
        "content": {
            "document": {
                "block": [{"type": "image", "_temp_path": p}]
            }
        }
    }
    _inject_missing_image_blocks(json_result, images_dir, pdf_images)
    assert len(json_result["content"]["document"]["block"]) == 1

    # Блок уже с image_key → дубликат не добавляется
    json_result2 = {
        "content": {
            "document": {
                "block": [{"type": "image", "image_key": "minio://key.png"}]
            }
        }
    }
    _inject_missing_image_blocks(json_result2, "", [(1, "minio://key.png", ".png")])
    assert len(json_result2["content"]["document"]["block"]) == 1


def test_inject_missing_image_blocks_with_uploader():
    """_inject_missing_image_blocks для ключей uploader'а не ставит _temp_path."""
    from app.services.parsers.docling.docling_mapper import _inject_missing_image_blocks

    pdf_images = [
        (1, "minio://abc123.png", ".png"),
        (2, "minio://def456.png", ".png"),
    ]

    json_result = {
        "content": {
            "document": {
                "block": [
                    {"type": "text", "content": "some text"}
                ]
            }
        }
    }

    _inject_missing_image_blocks(json_result, "", pdf_images)

    blocks = json_result["content"]["document"]["block"]
    assert len(blocks) == 3

    # Оба новых блока — с image_key, без _temp_path
    img_blocks = [b for b in blocks if b.get("type") == "image"]
    assert len(img_blocks) == 2
    for b in img_blocks:
        assert "_temp_path" not in b
    assert img_blocks[0]["image_key"] == "minio://abc123.png"
    assert img_blocks[1]["image_key"] == "minio://def456.png"
