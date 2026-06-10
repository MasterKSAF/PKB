"""
Валидация файлов: размер, MIME-тип, безопасность.

Поддерживаемые форматы: application/pdf (через python-magic).
"""
import magic
from app.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError
import logging

logger = logging.getLogger(__name__)


SUPPORTED_MIME_TYPES = {
    "application/pdf",
}


class Validator:
    """Статический класс с методами валидации файлов."""

    @staticmethod
    def validate_size(data: bytes) -> None:
        """Проверяет, что размер файла не превышает лимит (settings.max_file_size_mb)."""
        size_mb = len(data) / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            logger.warning(f"File too large: {size_mb:.2f}MB > {settings.max_file_size_mb}MB")
            raise FileTooLargeError(int(round(size_mb, 0)), settings.max_file_size_mb)
        logger.debug(f"File size OK: {size_mb:.2f}MB")

    @staticmethod
    def validate_mime(data: bytes) -> str:
        """Определяет MIME-тип по сигнатуре (первые 1024 байта) и проверяет поддержку."""
        mime = magic.from_buffer(data[:1024], mime=True)
        if mime not in SUPPORTED_MIME_TYPES:
            logger.warning(f"Unsupported MIME type: {mime}")
            raise UnsupportedFormatError(mime)
        logger.debug(f"MIME type OK: {mime}")
        return mime

    @staticmethod
    def validate_safety(data: bytes) -> bool:
        """
        Проверка на макросы, инъекции и т.д.
        В текущей версии – заглушка (всегда True).
        """
        # Заглушка – всегда успешно
        return True

    @classmethod
    def validate(cls, data: bytes) -> str:
        """Выполняет полную валидацию: размер → MIME → безопасность. Возвращает MIME-тип."""
        logger.debug("Starting full validation")
        cls.validate_size(data)
        mime = cls.validate_mime(data)
        cls.validate_safety(data)
        logger.info(f"Validation passed, MIME={mime}")
        return mime