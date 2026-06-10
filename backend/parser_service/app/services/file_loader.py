"""
Утилита для единообразного скачивания и валидации файлов из MinIO.
Используется в preview-эндпоинтах (v1 и v2).
"""
import asyncio
import logging
from app.core.minio_client import minio_client
from app.core.validator import Validator
from app.core.exceptions import StorageError, UnsupportedFormatError, FileNotFoundError, FileTooLargeError
from app.config import settings

logger = logging.getLogger(__name__)


async def fetch_and_validate(file_key: str) -> bytes:
    """
    Скачивает файл из MinIO и выполняет полную валидацию (размер, MIME, безопасность).

    Args:
        file_key: Ключ файла в MinIO.

    Returns:
        bytes: Содержимое файла.

    Raises:
        StorageError: При ошибках доступа к MinIO или таймауте.
        FileNotFoundError: Если файл не найден.
        UnsupportedFormatError: Если MIME-тип не поддерживается.
        FileTooLargeError: Если файл превышает лимит размера.
    """
    logger.debug("Fetching file: %s", file_key)

    try:
        file_bytes = await asyncio.wait_for(
            minio_client.download_file(file_key),
            timeout=settings.minio_timeout
        )
        logger.info(
            "File downloaded successfully: %s, size=%d bytes",
            file_key, len(file_bytes)
        )
    except asyncio.TimeoutError:
        logger.error(
            "MinIO download timeout for %s after %d seconds",
            file_key, settings.minio_timeout, exc_info=True
        )
        raise StorageError(f"download timeout {file_key}")
    except FileNotFoundError:
        # Пробрасываем дальше без логирования (исключение будет обработано выше)
        raise
    except Exception as e:
        logger.error(
            "MinIO download error for %s: %s",
            file_key, str(e), exc_info=True
        )
        raise StorageError(f"download {file_key}") from e

    try:
        mime = Validator.validate(file_bytes)
        logger.debug("Validation passed for %s, MIME=%s", file_key, mime)
    except Exception as e:
        logger.error(
            "Validation failed for %s: %s",
            file_key, str(e), exc_info=True
        )
        raise

    if mime != "application/pdf":
        logger.warning("Unsupported MIME type for %s: %s", file_key, mime)
        raise UnsupportedFormatError(mime)

    return file_bytes