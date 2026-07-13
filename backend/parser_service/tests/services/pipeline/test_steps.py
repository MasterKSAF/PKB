"""
Тесты для шагов пайплайна (steps.py).
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from pypdf import PdfReader, PdfWriter

# Импортируем только существующие классы
from app.services.pipeline.steps import (
    DownloadStep,
    ValidateStep,
    PagesTotalStep,
    ParseStep,
    UploadImagesStep,
    TransformStep,
    AssessQualityStep,
    SaveJsonToFileStep,
    StoreResultStep,
)
from app.services.pipeline.context import ProcessingContext
from app.services.parsers.base import ParseResult
from app.core.exceptions import StorageError
from app.core.task_models import TaskStatus, TaskInfo
from app.config import settings


# ===================== DownloadStep =====================
@pytest.mark.asyncio
async def test_download_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="folder/test.pdf")
    mock_minio = AsyncMock()
    mock_minio.download_file.return_value = b"pdfdata"

    step = DownloadStep(mock_minio)
    new_ctx = await step.execute(ctx)

    assert new_ctx.file_bytes == b"pdfdata"
    assert new_ctx.original_file_name == "test.pdf"


@pytest.mark.asyncio
async def test_download_step_storage_error():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="missing.pdf")
    mock_minio = AsyncMock()
    mock_minio.download_file.side_effect = StorageError("download missing.pdf")

    step = DownloadStep(mock_minio)
    with pytest.raises(StorageError):
        await step.execute(ctx)


# ===================== ValidateStep =====================
@pytest.mark.asyncio
async def test_validate_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf", file_bytes=b"fake")
    with patch("app.services.pipeline.steps.validate", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = "application/pdf"
        step = ValidateStep()
        new_ctx = await step.execute(ctx)
    assert new_ctx.mime_type == "application/pdf"
    mock_validate.assert_called_once_with(b"fake", "")


# ===================== PagesTotalStep =====================
@pytest.mark.asyncio
async def test_pages_total_step_pdf():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf", file_bytes=b"%PDF-1.4")
    ctx.mime_type = "application/pdf"
    ctx.track_progress = True
    with patch("app.services.pipeline.steps.PdfReader") as mock_reader:
        mock_reader.return_value.pages = [1, 2, 3]
        mock_store = AsyncMock()
        mock_store.update_task = AsyncMock()
        step = PagesTotalStep(mock_store)
        new_ctx = await step.execute(ctx)
    assert new_ctx.total_pages == 3
    mock_store.update_task.assert_called_once_with(1, pages_total=3, pages_processed=0)


# ===================== ParseStep =====================
@pytest.mark.asyncio
async def test_parse_step_success_without_truncation():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            mime_type="application/pdf", file_bytes=b"fake")
    ctx.track_progress = True

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = ParseResult(full_json={"pages": []}, total_pages=5)

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=mock_parser):
        step = ParseStep()
        new_ctx = await step.execute(ctx)

    assert new_ctx.parse_result.total_pages == 5


@pytest.mark.asyncio
async def test_parse_step_truncation_does_not_affect_full_mode():
    """В full mode (track_progress=True) PDF не обрезается."""
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            mime_type="application/pdf", file_bytes=b"some data",
                            max_pages=3, track_progress=True)

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = ParseResult(full_json={"pages": []}, total_pages=2)

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=mock_parser):
        step = ParseStep()
        new_ctx = await step.execute(ctx)

    # В full mode preview_not_supported не выставляется
    assert new_ctx.preview_not_supported is not True


# ===================== TransformStep (объединяет Normalize + Standardize) =====================
@pytest.mark.asyncio
async def test_transform_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            parse_result=ParseResult(full_json={}, total_pages=1))
    ctx.original_file_name = "orig.pdf"

    mock_normalizer = AsyncMock()
    mock_normalizer.normalize.return_value = {"content": "normalized"}

    mock_std = MagicMock()
    mock_std.transform.return_value = {"content": "standardized"}

    with patch("app.services.pipeline.steps.StandardizerFactory.get_standardizer", return_value=mock_std):
        step = TransformStep(mock_normalizer)
        new_ctx = await step.execute(ctx)

    assert new_ctx.final_json == {"content": "standardized"}


# ===================== StoreResultStep =====================
@pytest.mark.asyncio
async def test_store_result_step():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            parse_result=ParseResult(full_json={}, total_pages=10),
                            final_json={"result": "ok"})
    ctx.track_progress = True

    mock_task_info = MagicMock(spec=TaskInfo)
    mock_task_info.pages_total = 10
    mock_store = AsyncMock()  # <-- используем AsyncMock
    mock_store.get.return_value = mock_task_info
    mock_store.update_task = AsyncMock()

    step = StoreResultStep(mock_store, max_result_size_bytes=1024*1024)
    new_ctx = await step.execute(ctx)

    mock_store.update_task.assert_called_once()
    call_kwargs = mock_store.update_task.call_args[1]
    assert call_kwargs["status"] == TaskStatus.COMPLETED
    assert call_kwargs["pages_total"] == 10
    assert call_kwargs["pages_processed"] == 10
    assert call_kwargs["progress_percent"] == 100


# ===================== UploadImagesStep =====================
@pytest.mark.asyncio
async def test_upload_images_step_full_mode():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf", track_progress=True)
    parse_result = ParseResult(
        full_json={"pages": [{"image": {"_temp_path": "/tmp/img.png"}}]},
        images=[(1, "/tmp/img.png", ".png")],
        total_pages=1
    )
    ctx.parse_result = parse_result
    ctx.temp_dir = "/tmp"

    mock_minio = AsyncMock()
    mock_minio.upload_image.return_value = "minio_key_123"

    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"imgdata"
            mock_open.return_value.__enter__.return_value = mock_file
            with patch("os.unlink") as mock_unlink:
                with patch("shutil.rmtree") as mock_rmtree:
                    step = UploadImagesStep(mock_minio)
                    new_ctx = await step.execute(ctx)

    mock_minio.upload_image.assert_called_once()
    mock_unlink.assert_called_once_with("/tmp/img.png")
    mock_rmtree.assert_called_once_with("/tmp", ignore_errors=True)
    assert new_ctx.parse_result.full_json["pages"][0]["image"]["image_key"] == "minio_key_123"


@pytest.mark.asyncio
async def test_upload_images_step_preview_mode():
    ctx = ProcessingContext(
        task_id=1,
        draft_id=1,
        file_key="test.pdf",
        track_progress=False,
        temp_dir="/tmp/some_dir"
    )
    step = UploadImagesStep(AsyncMock())
    with patch("os.path.exists", return_value=True):
        with patch("shutil.rmtree") as mock_rmtree:
            await step.execute(ctx)
            mock_rmtree.assert_called_once_with("/tmp/some_dir", ignore_errors=True)
            assert ctx.temp_dir is None


# ===================== ParseStep: PDF truncation for preview =====================
@pytest.mark.asyncio
async def test_parse_step_truncates_pdf_for_preview():
    """PDF обрезается до max_pages перед парсингом в preview mode."""
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=72, height=72)
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    raw = pdf_bytes.read()

    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            mime_type="application/pdf", file_bytes=raw,
                            max_pages=3, track_progress=False)

    mock_parser = AsyncMock()
    # Парсер получает обрезанный PDF (3 страницы)
    mock_parser.parse.return_value = ParseResult(full_json={"pages": []}, total_pages=3)

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=mock_parser):
        step = ParseStep()
        new_ctx = await step.execute(ctx)

    # Проверяем, что парсер получил обрезанный PDF
    call_bytes = mock_parser.parse.call_args[0][0]
    reader = PdfReader(BytesIO(call_bytes))
    assert len(reader.pages) == 3
    # total_pages должен быть max_pages, а preview_not_supported=True
    assert new_ctx.parse_result.total_pages == 3
    assert new_ctx.preview_not_supported is True


# ===================== SaveJsonToFileStep =====================
@pytest.mark.asyncio
async def test_save_json_to_file_step_enabled():
    with patch.object(settings, 'save_json_to_dir', True):
        with patch.object(settings, 'json_output_dir', './output'):
            ctx = ProcessingContext(task_id=123, draft_id=1, file_key="test.pdf",
                                    final_json={"result": "data"})
            with patch("builtins.open", MagicMock()) as mock_open:
                with patch("json.dump") as mock_dump:
                    with patch("os.makedirs") as mock_makedirs:
                        step = SaveJsonToFileStep()
                        await step.execute(ctx)
            mock_makedirs.assert_called_once_with("./output", exist_ok=True)
            mock_open.assert_called_once()
            mock_dump.assert_called_once()


# ===================== AssessQualityStep =====================
@pytest.mark.asyncio
async def test_assess_quality_step_good():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            final_json={
                                "document": {
                                    "pages": [{"page": 1}, {"page": 2}],
                                    "block": [
                                        {"type": "paragraph", "page": 1, "content": "Hello"},
                                        {"type": "heading", "page": 2, "content": "Title"},
                                    ],
                                },
                            },
                            quality_code="GOOD",
                            total_pages=2)
    step = AssessQualityStep()
    new_ctx = await step.execute(ctx)
    assert new_ctx.quality_assessment is not None
    assert new_ctx.quality_assessment["verdict"] == "good"
    assert new_ctx.quality_assessment["needs_ocr"] is False
    assert new_ctx.final_json["quality"]["verdict"] == "good"


@pytest.mark.asyncio
async def test_assess_quality_step_needs_ocr():
    ctx = ProcessingContext(task_id=1, draft_id=1, file_key="test.pdf",
                            final_json={"document": {"pages": [{"page": 1}], "block": []}},
                            quality_code="BAD",
                            total_pages=1)
    step = AssessQualityStep()
    new_ctx = await step.execute(ctx)
    assert new_ctx.quality_assessment is not None
    assert new_ctx.quality_assessment["verdict"] == "needs_ocr"
    assert new_ctx.quality_assessment["needs_ocr"] is True