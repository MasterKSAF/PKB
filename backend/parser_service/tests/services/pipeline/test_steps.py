"""
Тесты для всех шагов пайплайна (steps.py).
Каждый шаг тестируется изолированно с моками зависимостей.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from pypdf import PdfReader, PdfWriter

from app.services.pipeline.steps import (
    DownloadStep, ValidateStep, ParseStep, NormalizeStep, StoreResultStep,
    TruncatePdfStep, StandardizeStep, SaveJsonToFileStep, UploadImagesStep,
    PagesTotalStep
)
from app.services.pipeline.context import ProcessingContext
from app.services.parsers.base import ParseResult
from app.core.exceptions import StorageError, UnsupportedFormatError, FileTooLargeError
from app.core.task_models import TaskStatus, TaskInfo
from app.config import settings


# ===================== DownloadStep =====================
@pytest.mark.asyncio
async def test_download_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="folder/test.pdf")
    mock_minio = AsyncMock()
    mock_minio.download_file.return_value = b"pdfdata"

    with patch("app.services.pipeline.steps.minio_client", mock_minio):
        step = DownloadStep()
        new_ctx = await step.execute(ctx)

    assert new_ctx.file_bytes == b"pdfdata"
    assert new_ctx.original_file_name == "test.pdf"


@pytest.mark.asyncio
async def test_download_step_storage_error():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="missing.pdf")
    mock_minio = AsyncMock()
    mock_minio.download_file.side_effect = StorageError("download missing.pdf")

    with patch("app.services.pipeline.steps.minio_client", mock_minio):
        step = DownloadStep()
        with pytest.raises(StorageError):
            await step.execute(ctx)


# ===================== ValidateStep =====================
@pytest.mark.asyncio
async def test_validate_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf", file_bytes=b"fake")
    with patch("app.services.pipeline.steps.Validator.validate", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = "application/pdf"
        step = ValidateStep()
        new_ctx = await step.execute(ctx)
    assert new_ctx.mime_type == "application/pdf"
    mock_validate.assert_called_once_with(b"fake", "")


# ===================== PagesTotalStep =====================
@pytest.mark.asyncio
async def test_pages_total_step_pdf():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf", file_bytes=b"%PDF-1.4")
    ctx.mime_type = "application/pdf"
    ctx.track_progress = True
    with patch("app.services.pipeline.steps.PdfReader") as mock_reader:
        mock_reader.return_value.pages = [1, 2, 3]
        with patch("app.services.pipeline.steps.task_store") as mock_store:
            mock_store.update_task = AsyncMock()
            step = PagesTotalStep()
            new_ctx = await step.execute(ctx)
    assert new_ctx.total_pages == 3
    mock_store.update_task.assert_called_once_with(1, pages_total=3, pages_processed=0)


# ===================== ParseStep =====================
@pytest.mark.asyncio
async def test_parse_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf",
                            mime_type="application/pdf", file_bytes=b"fake")
    ctx.track_progress = True

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = ParseResult(full_json={"pages": []}, total_pages=5)

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=mock_parser):
        step = ParseStep()
        new_ctx = await step.execute(ctx)

    assert new_ctx.parse_result.total_pages == 5


# ===================== NormalizeStep =====================
@pytest.mark.asyncio
async def test_normalize_step_success():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf",
                            parse_result=ParseResult(full_json={}, total_pages=1))
    mock_normalizer = AsyncMock()
    mock_normalizer.normalize.return_value = {"normalized": "json"}
    step = NormalizeStep(mock_normalizer)
    new_ctx = await step.execute(ctx)
    assert new_ctx.final_json == {"normalized": "json"}


# ===================== StoreResultStep =====================
@pytest.mark.asyncio
async def test_store_result_step():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf",
                            parse_result=ParseResult(full_json={}, total_pages=10),
                            final_json={"result": "ok"})
    ctx.track_progress = True

    mock_task_info = MagicMock(spec=TaskInfo)
    mock_task_info.pages_total = 10
    mock_store = MagicMock()
    mock_store.get.return_value = mock_task_info
    mock_store.update_task = AsyncMock()

    with patch("app.services.pipeline.steps.task_store", mock_store):
        step = StoreResultStep()
        new_ctx = await step.execute(ctx)

    mock_store.update_task.assert_called_once()
    call_kwargs = mock_store.update_task.call_args[1]
    assert call_kwargs["status"] == TaskStatus.COMPLETED
    assert call_kwargs["pages_total"] == 10
    assert call_kwargs["pages_processed"] == 10
    assert call_kwargs["progress_percent"] == 100


@pytest.mark.asyncio
async def test_store_result_step_with_preview_not_supported():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf", track_progress=True,
                            max_pages=2, preview_not_supported=True,
                            parse_result=ParseResult(full_json={}, total_pages=10))
    ctx.final_json = {"content": {}}

    mock_task_info = MagicMock(spec=TaskInfo)
    mock_task_info.pages_total = 10
    mock_store = MagicMock()
    mock_store.get.return_value = mock_task_info
    mock_store.update_task = AsyncMock()

    with patch("app.services.pipeline.steps.task_store", mock_store):
        step = StoreResultStep()
        await step.execute(ctx)

    call_kwargs = mock_store.update_task.call_args[1]
    assert call_kwargs["result"]["metadata"]["preview_not_supported"] is True


# ===================== UploadImagesStep =====================
@pytest.mark.asyncio
async def test_upload_images_step_full_mode():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf", track_progress=True)
    parse_result = ParseResult(
        full_json={"pages": [{"image": {"_temp_path": "/tmp/img.png"}}]},
        images=[(1, "/tmp/img.png", ".png")],
        total_pages=1
    )
    ctx.parse_result = parse_result
    ctx.temp_dir = "/tmp"

    mock_minio = AsyncMock()
    mock_minio.upload_image.return_value = "minio_key_123"
    mock_minio._ensure_bucket = AsyncMock()

    with patch("app.services.pipeline.steps.minio_client", mock_minio):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", MagicMock()) as mock_open:
                mock_file = MagicMock()
                mock_file.read.return_value = b"imgdata"
                mock_open.return_value.__enter__.return_value = mock_file
                with patch("os.unlink") as mock_unlink:
                    with patch("shutil.rmtree") as mock_rmtree:
                        step = UploadImagesStep()
                        new_ctx = await step.execute(ctx)

    mock_minio.upload_image.assert_called_once()
    mock_unlink.assert_called_once_with("/tmp/img.png")
    mock_rmtree.assert_called_once_with("/tmp", ignore_errors=True)
    assert new_ctx.parse_result.full_json["pages"][0]["image"]["image_key"] == "minio_key_123"


@pytest.mark.asyncio
async def test_upload_images_step_preview_mode():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf", track_progress=False)
    ctx.temp_dir = "/tmp"
    step = UploadImagesStep()
    with patch("shutil.rmtree") as mock_rmtree:
        new_ctx = await step.execute(ctx)
    mock_rmtree.assert_not_called()


@pytest.mark.asyncio
async def test_upload_images_step_full_mode_with_images():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf", track_progress=True)
    parse_result = ParseResult(
        full_json={"pages": [{"image": {"_temp_path": "/tmp/img.png"}}]},
        images=[(1, "/tmp/img.png", ".png")],
        total_pages=1
    )
    ctx.parse_result = parse_result
    ctx.temp_dir = "/tmp"

    mock_minio = AsyncMock()
    mock_minio.upload_image.return_value = "minio_key"
    with patch("app.services.pipeline.steps.minio_client", mock_minio):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", MagicMock()) as mock_open:
                mock_file = MagicMock()
                mock_file.read.return_value = b"imgdata"
                mock_open.return_value.__enter__.return_value = mock_file
                with patch("os.unlink") as mock_unlink:
                    with patch("shutil.rmtree") as mock_rmtree:
                        step = UploadImagesStep()
                        await step.execute(ctx)
    mock_minio.upload_image.assert_called_once()
    mock_unlink.assert_called_once()
    mock_rmtree.assert_called_once_with("/tmp", ignore_errors=True)


# ===================== TruncatePdfStep =====================
@pytest.mark.asyncio
async def test_truncate_pdf_step_reduces_pages():
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=72, height=72)
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf",
                            max_pages=3, file_bytes=pdf_bytes.read())
    step = TruncatePdfStep()
    new_ctx = await step.execute(ctx)
    reader = PdfReader(BytesIO(new_ctx.file_bytes))
    assert len(reader.pages) == 3


# ===================== StandardizeStep =====================
@pytest.mark.asyncio
async def test_standardize_step():
    ctx = ProcessingContext(task_id=1, draft_id=1, version_id="v1", file_key="test.pdf",
                            final_json={"content": "raw"}, original_file_name="orig.pdf")
    mock_std = MagicMock()
    mock_std.transform.return_value = {"content": "standardized"}
    step = StandardizeStep(mock_std)
    new_ctx = await step.execute(ctx)
    assert new_ctx.final_json == {"content": "standardized"}


# ===================== SaveJsonToFileStep =====================
@pytest.mark.asyncio
async def test_save_json_to_file_step_enabled():
    with patch.object(settings, 'save_json_to_dir', True):
        with patch.object(settings, 'json_output_dir', './output'):
            ctx = ProcessingContext(task_id=123, draft_id=1, version_id="v1", file_key="test.pdf",
                                    final_json={"result": "data"})
            with patch("builtins.open", MagicMock()) as mock_open:
                with patch("json.dump") as mock_dump:
                    with patch("os.makedirs") as mock_makedirs:
                        step = SaveJsonToFileStep()
                        await step.execute(ctx)
            mock_makedirs.assert_called_once_with("./output", exist_ok=True)
            mock_open.assert_called_once()
            mock_dump.assert_called_once()