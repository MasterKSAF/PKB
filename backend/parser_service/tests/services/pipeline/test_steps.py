"""
Тесты для всех шагов пайплайна (steps.py).
Каждый шаг тестируется изолированно с моками зависимостей.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from pypdf import PdfReader, PdfWriter

from app.services.pipeline.steps import (
    DownloadStep, ValidateStep, ParseStep, NormalizeStep, StoreResultStep,
    TruncatePdfStep, StandardizeStep, SaveJsonToFileStep
)
from app.services.pipeline.context import ProcessingContext
from app.services.parsers.base import ParseResult
from app.core.exceptions import StorageError, UnsupportedFormatError, FileTooLargeError
from app.core.task_models import TaskStatus
from app.config import settings


# ===================== DownloadStep =====================
@pytest.mark.asyncio
async def test_download_step_success():
    """Успешное скачивание файла и установка original_file_name."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="folder/test.pdf")
    mock_minio = AsyncMock()
    mock_minio.download_file.return_value = b"pdfdata"

    with patch("app.services.pipeline.steps.minio_client", mock_minio):
        step = DownloadStep()
        new_ctx = await step.execute(ctx)

    assert new_ctx.file_bytes == b"pdfdata"
    assert new_ctx.original_file_name == "test.pdf"


@pytest.mark.asyncio
async def test_download_step_storage_error():
    """Ошибка скачивания → StorageError."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="missing.pdf")
    mock_minio = AsyncMock()
    mock_minio.download_file.side_effect = StorageError("download missing.pdf")

    with patch("app.services.pipeline.steps.minio_client", mock_minio):
        step = DownloadStep()
        with pytest.raises(StorageError):
            await step.execute(ctx)


# ===================== ValidateStep =====================
@pytest.mark.asyncio
async def test_validate_step_success():
    """Валидация проходит → устанавливается mime_type."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf", file_bytes=b"fake")
    with patch("app.services.pipeline.steps.Validator") as mock_validator:
        mock_validator.validate.return_value = "application/pdf"
        step = ValidateStep()
        new_ctx = await step.execute(ctx)

    assert new_ctx.mime_type == "application/pdf"


@pytest.mark.asyncio
async def test_validate_step_unsupported():
    """Неподдерживаемый MIME → UnsupportedFormatError."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.jpg", file_bytes=b"fake")
    with patch("app.services.pipeline.steps.Validator") as mock_validator:
        mock_validator.validate.side_effect = UnsupportedFormatError("image/jpeg")
        step = ValidateStep()
        with pytest.raises(UnsupportedFormatError):
            await step.execute(ctx)


@pytest.mark.asyncio
async def test_validate_step_too_large():
    """Файл слишком большой → FileTooLargeError."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="big.pdf", file_bytes=b"fake")
    with patch("app.services.pipeline.steps.Validator") as mock_validator:
        mock_validator.validate.side_effect = FileTooLargeError(600, 500)
        step = ValidateStep()
        with pytest.raises(FileTooLargeError):
            await step.execute(ctx)


# ===================== ParseStep =====================
@pytest.mark.asyncio
async def test_parse_step_success():
    """Парсинг успешен → сохраняется pages_total и parse_result."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            mime_type="application/pdf", file_bytes=b"fake")

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = ParseResult(full_json={"pages": []}, total_pages=5)

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=mock_parser):
        with patch("app.services.pipeline.steps.task_store") as mock_store:
            mock_store.update_task = AsyncMock()
            step = ParseStep()
            new_ctx = await step.execute(ctx)

    assert new_ctx.parse_result.total_pages == 5
    mock_store.update_task.assert_called_once_with(1, pages_total=5, pages_processed=0)


@pytest.mark.asyncio
async def test_parse_step_truncate():
    """При max_pages < total_pages → обрезаются страницы и изображения."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            mime_type="application/pdf", max_pages=2, file_bytes=b"fake")

    mock_parser = AsyncMock()
    mock_parser.parse.return_value = ParseResult(
        full_json={"pages": [1, 2, 3]},
        images=[(1, b"i1", ".png"), (2, b"i2", ".png"), (3, b"i3", ".png")],
        total_pages=3
    )

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=mock_parser):
        with patch("app.services.pipeline.steps.task_store") as mock_store:
            mock_store.update_task = AsyncMock()
            step = ParseStep()
            new_ctx = await step.execute(ctx)

    assert new_ctx.parse_result.total_pages == 2
    assert len(new_ctx.parse_result.images) == 2


@pytest.mark.asyncio
async def test_parse_step_no_parser():
    """Не найден парсер для MIME → ValueError."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.xyz",
                            mime_type="application/xyz", file_bytes=b"fake")

    with patch("app.services.pipeline.steps.ParserFactory.get_parser", return_value=None):
        step = ParseStep()
        with pytest.raises(ValueError, match="No parser for MIME application/xyz"):
            await step.execute(ctx)


# ===================== NormalizeStep =====================
@pytest.mark.asyncio
async def test_normalize_step_success():
    """Нормализация вызывает normalizer.normalize и сохраняет final_json."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            parse_result=ParseResult(full_json={}, total_pages=1))

    mock_normalizer = AsyncMock()
    mock_normalizer.normalize.return_value = {"normalized": "json"}

    step = NormalizeStep(mock_normalizer)
    new_ctx = await step.execute(ctx)

    mock_normalizer.normalize.assert_called_once_with(ctx.parse_result, 1)
    assert new_ctx.final_json == {"normalized": "json"}


# ===================== StoreResultStep =====================
@pytest.mark.asyncio
async def test_store_result_step():
    """Сохранение результата в task_store с правильными полями."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            parse_result=ParseResult(full_json={}, total_pages=10, 
                            # html_content="<html>"
                            ),
                            final_json={"result": "ok"})

    mock_store = AsyncMock()
    with patch("app.services.pipeline.steps.task_store", mock_store):
        step = StoreResultStep()
        new_ctx = await step.execute(ctx)

    mock_store.update_task.assert_called_once()
    call_kwargs = mock_store.update_task.call_args[1]
    assert call_kwargs["status"] == TaskStatus.COMPLETED
    assert call_kwargs["result"] == {"result": "ok"}
    # assert call_kwargs["html_content"] == "<html>"
    assert call_kwargs["pages_total"] == 10
    assert call_kwargs["pages_processed"] == 10
    assert call_kwargs["progress_percent"] == 100


# ===================== TruncatePdfStep =====================
@pytest.mark.asyncio
async def test_truncate_pdf_step_reduces_pages():
    """PDF обрезается до max_pages."""
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=72, height=72)
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            max_pages=3, file_bytes=pdf_bytes.read())

    step = TruncatePdfStep()
    new_ctx = await step.execute(ctx)
    reader = PdfReader(BytesIO(new_ctx.file_bytes))
    assert len(reader.pages) == 3


@pytest.mark.asyncio
async def test_truncate_pdf_step_no_truncate():
    """Если max_pages >= total_pages, обрезания нет."""
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_blank_page(width=72, height=72)
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            max_pages=5, file_bytes=pdf_bytes.read())

    step = TruncatePdfStep()
    new_ctx = await step.execute(ctx)
    reader = PdfReader(BytesIO(new_ctx.file_bytes))
    assert len(reader.pages) == 2


@pytest.mark.asyncio
async def test_truncate_pdf_step_no_file_bytes():
    """Ошибка: file_bytes отсутствует."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf", max_pages=3)
    step = TruncatePdfStep()
    with pytest.raises(ValueError, match="No file bytes to truncate"):
        await step.execute(ctx)


# ===================== StandardizeStep =====================
@pytest.mark.asyncio
async def test_standardize_step():
    """Вызывает standardizer.transform с file_name."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf",
                            final_json={"content": "raw"}, original_file_name="orig.pdf")

    mock_std = MagicMock()
    mock_std.transform.return_value = {"content": "standardized"}

    step = StandardizeStep(mock_std)
    new_ctx = await step.execute(ctx)

    mock_std.transform.assert_called_once_with({"content": "raw"}, file_name="orig.pdf")
    assert new_ctx.final_json == {"content": "standardized"}


@pytest.mark.asyncio
async def test_standardize_step_no_json():
    """Ошибка: final_json отсутствует."""
    ctx = ProcessingContext(task_id=1, version_id="v1", file_key="test.pdf", final_json=None)
    mock_std = MagicMock()
    step = StandardizeStep(mock_std)
    with pytest.raises(ValueError, match="No final JSON to standardize"):
        await step.execute(ctx)


# ===================== SaveJsonToFileStep =====================
@pytest.mark.asyncio
async def test_save_json_to_file_step_enabled():
    """При включённой настройке сохраняет JSON в файл."""
    # Используем patch.object вместо прямой записи в settings
    with patch.object(settings, 'save_json_to_dir', True):
        with patch.object(settings, 'json_output_dir', './output'):
            ctx = ProcessingContext(task_id=123, version_id="v1", file_key="test.pdf",
                                    final_json={"result": "data"})

            with patch("builtins.open", MagicMock()) as mock_open:
                with patch("json.dump") as mock_dump:
                    with patch("os.makedirs") as mock_makedirs:
                        step = SaveJsonToFileStep()
                        await step.execute(ctx)

            mock_makedirs.assert_called_once_with("./output", exist_ok=True)
            mock_open.assert_called_once_with("./output/task_123.json", "w", encoding="utf-8")
            mock_dump.assert_called_once()


@pytest.mark.asyncio
async def test_save_json_to_file_step_disabled():
    """При выключенной настройке ничего не сохраняет."""
    with patch.object(settings, 'save_json_to_dir', False):
        ctx = ProcessingContext(task_id=123, version_id="v1", file_key="test.pdf",
                                final_json={"result": "data"})

        with patch("builtins.open") as mock_open:
            step = SaveJsonToFileStep()
            await step.execute(ctx)

        mock_open.assert_not_called()