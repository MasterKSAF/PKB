"""
Эндпоинт POST /parser/preview – быстрый предпросмотр документа.
Возвращает только метаданные (имя файла, количество страниц) без содержимого.
"""
from datetime import datetime, timezone
import os
import io

from fastapi import APIRouter, status, HTTPException
from pypdf import PdfReader

from app.api.v1.schemas import PreviewRequest, PreviewResponse
from app.core.minio_client import minio_client
from app.core.validator import Validator
from app.core.exceptions import StorageError, UnsupportedFormatError, ParserFailedError
from app.services.pipeline.pipeline import Pipeline
from app.services.pipeline.steps import DownloadStep, ValidateStep, TruncatePdfStep, ParseStep
from app.services.pipeline.context import ProcessingContext

router = APIRouter()


def get_preview_pipeline() -> Pipeline:
    """Создаёт пайплайн для предпросмотра (скачивание → валидация → обрезание → парсинг)."""
    steps = [
        DownloadStep(),
        ValidateStep(),
        TruncatePdfStep(),
        ParseStep()
    ]
    return Pipeline(steps)


@router.post("/preview", status_code=status.HTTP_200_OK, response_model=PreviewResponse)
async def preview_document(request: PreviewRequest):
    """
    Обрабатывает запрос предпросмотра:
    1. Скачивает файл из MinIO.
    2. Валидирует (размер, MIME, безопасность).
    3. Извлекает общее количество страниц через pypdf (быстро).
    4. Запускает пайплайн на обрезанном PDF (первые max_pages страниц) – это необходимо,
       чтобы гарантировать, что парсер opendataloader_pdf не обработает весь документ.
    5. Возвращает ответ с именем файла и общим числом страниц (без блоков).
    """
    # 1. Скачивание
    try:
        file_bytes = await minio_client.download_file(request.file_key)
    except Exception as e:
        raise StorageError(f"download {request.file_key}") from e

    # 2. Валидация
    try:
        mime = Validator.validate(file_bytes)
    except Exception as e:
        raise e

    if mime != "application/pdf":
        raise UnsupportedFormatError(mime)

    # 3. Общее число страниц (без парсинга содержимого)
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        total_pages_original = len(reader.pages)
    except Exception as e:
        raise ParserFailedError(e) from e

    # 4. Запуск пайплайна для обрезанного PDF
    ctx = ProcessingContext(
        task_id=request.task_id,
        version_id=request.version_id,
        file_key=request.file_key,
        options=request.options or {},
        max_pages=request.max_pages,
        file_bytes=file_bytes
    )

    pipeline = get_preview_pipeline()
    try:
        ctx = await pipeline.run(ctx)
    except (StorageError, UnsupportedFormatError) as e:
        raise e
    except Exception as e:
        raise ParserFailedError(e) from e

    # 5. Формирование ответа
    file_name = os.path.basename(request.file_key)
    return PreviewResponse(
        task_id=request.task_id,
        version_id=request.version_id,
        preview=True,
        max_pages=request.max_pages,
        metadata={
            "schema": "raw_ocr_v4",
            "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        },
        document={
            "source": {
                "file_name": file_name,
                "page_count": total_pages_original
            }
        }
    )


@router.get("/preview", include_in_schema=False)
async def preview_info():
    """GET-обработчик для удобства: подсказывает, что нужно использовать POST."""
    return {
        "message": "This endpoint accepts only POST requests. Please use POST with JSON body.",
        "example": {
            "task_id": 420000,
            "version_id": "d5e0f3a2-...",
            "file_key": "document.pdf",
            "max_pages": 3
        }
    }