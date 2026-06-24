"""
Валидация файлов: размер, MIME-тип, безопасность (расширенная).
"""
import magic
import asyncio
import logging
from app.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError
from app.core.security_scanner import SecurityScanner

logger = logging.getLogger(__name__)
SUPPORTED_MIME_TYPES = {"application/pdf"}


def validate_size(data: bytes) -> None:
    """
    Проверяет размер файла на превышение лимита.
    """
    size_mb = len(data) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        logger.warning(
            "File too large: %.2fMB > %dMB",
            size_mb,
            settings.max_file_size_mb,
        )
        raise FileTooLargeError(int(round(size_mb, 0)), settings.max_file_size_mb)
    logger.debug("File size OK: %.2fMB", size_mb)


def validate_mime(data: bytes) -> str:
    """
    Проверяет MIME-тип файла на соответствие поддерживаемым.
    """
    mime = magic.from_buffer(data[:1024], mime=True)
    if mime not in SUPPORTED_MIME_TYPES:
        logger.warning("Unsupported MIME type: %s", mime)
        raise UnsupportedFormatError(mime)
    logger.debug("MIME type OK: %s", mime)
    return mime


async def validate(data: bytes, filename: str = "") -> str:
    """
    Выполняет полную валидацию файла: размер, MIME и безопасность.
    Возвращает MIME-тип при успехе.
    """
    logger.debug("Starting full validation for %s", filename)
    validate_size(data)
    mime = validate_mime(data)

    # Расширенная проверка безопасности
    try:
        logger.debug("Running security scan (PDF) for %s", filename)
        is_safe, error_msg = await asyncio.wait_for(
            asyncio.to_thread(
                SecurityScanner.scan_pdf,
                data,
                filename,
                settings.yara_rules_path,
                settings.max_suspect_font_stream_size,
                settings.reject_jbig2,
                settings.enable_yara,
                settings.block_on_unicode,
                settings.block_on_jbig2,
                settings.block_on_dangerous_keys,
                settings.block_on_yara,
            ),
            timeout=settings.validation_global_timeout,
        )
        if not is_safe:
            logger.warning("Security check failed: %s", error_msg)
            raise UnsupportedFormatError(f"Security check failed: {error_msg}")
        logger.info("Security check passed for %s", filename)
    except asyncio.TimeoutError:
        logger.error(
            "Security validation timeout after %ds for %s",
            settings.validation_global_timeout,
            filename,
            exc_info=True,
        )
        raise UnsupportedFormatError("Security validation timeout")
    except Exception as e:
        logger.exception("Unexpected error during security scan for %s", filename)
        raise UnsupportedFormatError(f"Security scan error: {str(e)}")

    logger.info("Validation passed for %s, MIME=%s", filename, mime)
    return mime