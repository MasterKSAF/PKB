"""
Валидация файлов: размер, MIME-тип, безопасность (расширенная).


Поддерживаемые форматы: application/pdf (через python-magic).
"""


import magic
import asyncio
import logging
from app.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError
from app.core.security_scanner import SecurityScanner


logger = logging.getLogger(__name__)


SUPPORTED_MIME_TYPES = {"application/pdf"}




class Validator:
    """Статический класс с методами валидации файлов."""


    @staticmethod
    def validate_size(data: bytes) -> None:
        """Проверяет размер файла. Выбрасывает FileTooLargeError при превышении лимита."""
        size_mb = len(data) / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            logger.warning(
                f"File too large: {size_mb:.2f}MB > {settings.max_file_size_mb}MB"
            )
            raise FileTooLargeError(int(round(size_mb, 0)), settings.max_file_size_mb)
        logger.debug(f"File size OK: {size_mb:.2f}MB")


    @staticmethod
    def validate_mime(data: bytes) -> str:
        """
        Определяет MIME-тип по сигнатуре (первые 1024 байта) и проверяет поддержку.
        Возвращает MIME-тип.
        """
        mime = magic.from_buffer(data[:1024], mime=True)
        if mime not in SUPPORTED_MIME_TYPES:
            logger.warning(f"Unsupported MIME type: {mime}")
            raise UnsupportedFormatError(mime)
        logger.debug(f"MIME type OK: {mime}")
        return mime


    @classmethod
    async def validate(cls, data: bytes, filename: str = "") -> str:
        """
        Выполняет полную валидацию: размер → MIME → безопасность.
        Возвращает MIME-тип.
        """
        logger.debug("Starting full validation")
        cls.validate_size(data)
        mime = cls.validate_mime(data)


        # Расширенная проверка безопасности в отдельном потоке с таймаутом
        try:
            logger.debug("Running security scan (PDF)")
            is_safe, error_msg = await asyncio.wait_for(
                asyncio.to_thread(
                    SecurityScanner.scan_pdf,
                    data,
                    filename,
                    settings.yara_rules_path,
                    settings.max_suspect_font_stream_size,
                    settings.reject_jbig2,
                    settings.enable_yara
                ),
                timeout=settings.validation_global_timeout
            )
            if not is_safe:
                logger.warning(f"Security check failed: {error_msg}")
                raise UnsupportedFormatError(f"Security check failed: {error_msg}")
            logger.info("Security check passed")
        except asyncio.TimeoutError:
            logger.error(f"Security validation timeout after {settings.validation_global_timeout}s")
            raise UnsupportedFormatError("Security validation timeout")
        except Exception as e:
            logger.exception("Unexpected error during security scan")
            raise UnsupportedFormatError(f"Security scan error: {str(e)}")


        logger.info(f"Validation passed, MIME={mime}")
        return mime