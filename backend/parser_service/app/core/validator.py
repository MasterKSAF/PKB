"""
Валидация файлов: размер, MIME-тип, безопасность.

Поддерживаемые форматы:
- application/pdf
- application/msword (DOC)
- application/vnd.openxmlformats-officedocument.wordprocessingml.document (DOCX)
"""
import magic
from app.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


class Validator:
    """Статический класс с методами валидации."""

    @staticmethod
    def validate_size(data: bytes) -> None:
        """Проверяет, что размер файла не превышает лимит."""
        size_mb = len(data) / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            raise FileTooLargeError(int(round(size_mb, 0)), settings.max_file_size_mb)

    @staticmethod
    def validate_mime(data: bytes) -> str:
        """Определяет MIME-тип по сигнатуре и проверяет поддержку."""
        mime = magic.from_buffer(data[:1024], mime=True)
        if mime not in SUPPORTED_MIME_TYPES:
            raise UnsupportedFormatError(mime)
        return mime

    @staticmethod
    def validate_safety(data: bytes) -> bool:
        """
        Проверка на макросы, инъекции и т.д.
        В текущей версии – заглушка (всегда True).
        TODO: интеграция с ClamAV или анализ структуры PDF.
        """
        return True

    @classmethod
    def validate(cls, data: bytes) -> str:
        """Выполняет полную валидацию: размер → MIME → безопасность. Возвращает MIME-тип."""
        cls.validate_size(data)
        mime = cls.validate_mime(data)
        cls.validate_safety(data)
        return mime