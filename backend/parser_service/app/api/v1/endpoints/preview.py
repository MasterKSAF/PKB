"""
Эндпоинт POST /parser/preview – быстрый предпросмотр документа (v1).

Этот модуль обрабатывает синхронный запрос на предпросмотр документа:
- Скачивает файл из MinIO.
- Валидирует его (размер, MIME-тип, безопасность).
- Запускает пайплайн в режиме preview (ограничение по страницам).
- Возвращает результат предпросмотра без сохранения в постоянное хранилище.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.api.v1.schemas import PreviewRequest, PreviewResponse
from app.services.file_loader import fetch_and_validate
from app.core.exceptions import (
    StorageError, UnsupportedFormatError, ParserFailedError,
    FileTooLargeError, FileNotFoundError
)
from app.services.pipeline.context import ProcessingContext
from app.services.pipeline.pipeline import Pipeline
from app.config import settings
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/preview", status_code=status.HTTP_200_OK, response_model=PreviewResponse)
async def preview_document(request: PreviewRequest):
    """
    Выполняет предпросмотр документа.

    Процесс:
    1. Скачивает файл из MinIO по file_key.
    2. Валидирует файл (размер, MIME, безопасность).
    3. Создаёт контекст обработки с ограничением max_pages.
    4. Запускает пайплайн в режиме preview.
    5. Удаляет временные пути из результирующего JSON.
    6. Возвращает PreviewResponse.

    Args:
        request: PreviewRequest с полями task_id, version_id, file_key, max_pages, options.

    Returns:
        PreviewResponse: Результат предпросмотра с метаданными и документом.

    Raises:
        FileNotFoundError: Если файл не найден в MinIO.
        StorageError: При ошибке доступа к MinIO.
        UnsupportedFormatError: Если MIME-тип не поддерживается.
        FileTooLargeError: Если файл превышает лимит размера.
        ParserFailedError: При критической ошибке парсинга.
    """
    logger.info(f"Preview request: task_id={request.task_id}, file_key={request.file_key}, max_pages={request.max_pages}")
    try:
        file_bytes = await fetch_and_validate(request.file_key)
        logger.debug(f"File downloaded and validated, size={len(file_bytes)} bytes")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except (StorageError, UnsupportedFormatError, FileTooLargeError) as e:
        logger.error(f"Download/validation error: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error during fetch_and_validate")
        raise ParserFailedError(e) from e

    ctx = ProcessingContext(
        task_id=request.task_id,
        version_id=request.version_id,
        file_key=request.file_key,
        options=request.options or {},
        max_pages=request.max_pages,
        file_bytes=file_bytes,
        track_progress=False
    )
    pipeline = Pipeline.create(mode="preview", track_progress=False)
    try:
        ctx = await pipeline.run(ctx)
        logger.info(f"Preview pipeline completed for task {request.task_id}")
    except (StorageError, UnsupportedFormatError, FileTooLargeError, FileNotFoundError) as e:
        logger.error(f"Pipeline error: {e}")
        raise
    except Exception as e:
        logger.exception("Preview pipeline failed")
        raise ParserFailedError(e) from e

    document = ctx.final_json.get("content", {}).get("document", {}) if ctx.final_json else {}

    def remove_temp_paths(obj):
        """
        Рекурсивно удаляет временные пути из объекта JSON.

        Удаляет поля '_temp_path', а также любые поля, содержащие путь к временной
        директории ('image_key', 'source', 'file_path', 'path'), если в строке есть
        'tmp' или '_temp'.

        Args:
            obj: Словарь или список для очистки.
        """
        if isinstance(obj, dict):
            if "_temp_path" in obj:
                del obj["_temp_path"]
            for key in ("image_key", "source", "file_path", "path"):
                if key in obj and isinstance(obj[key], str) and ("tmp" in obj[key] or "_temp" in obj[key]):
                    del obj[key]
            for v in obj.values():
                remove_temp_paths(v)
        elif isinstance(obj, list):
            for item in obj:
                remove_temp_paths(item)

    remove_temp_paths(document)
    logger.debug(f"Preview response prepared, document has {len(document)} blocks")

    return PreviewResponse(
        task_id=request.task_id,
        version_id=request.version_id,
        preview=True,
        max_pages=request.max_pages,
        metadata={
            "schema": settings.parsing_schema,
            "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        },
        document=document
    )


@router.get("/preview", include_in_schema=False)
async def preview_info():
    """
    Информационный эндпоинт для GET-запросов к /preview.

    Так как эндпоинт поддерживает только POST, этот обработчик возвращает
    сообщение с инструкцией.

    Returns:
        dict: Сообщение о необходимости использовать POST.
    """
    logger.debug("GET /preview called, returning info message")
    return {"message": "This endpoint accepts only POST requests. Please use POST with JSON body."}