"""
Кастомные исключения для Parser Service.

Каждому исключению соответствует HTTP-код и код ошибки по спецификации API.
Все исключения наследуются от ParserServiceError, который форматирует ответ
в виде {"error": {"code": ..., "message": ..., "details": ...}}.
"""
from fastapi import HTTPException, status
from app.config import settings


class ParserServiceError(HTTPException):
    """
    Базовое исключение для всех ошибок сервиса парсинга.

    :param status_code: HTTP-статус ответа
    :param error_code: строковый код ошибки (например, "FILE_NOT_FOUND")
    :param message: человекочитаемое описание
    :param details: дополнительные детали (опционально)
    """
    def __init__(self, status_code: int, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": self.details
                }
            }
        )


# ----- Конкретные ошибки -----

class FileNotFoundError(ParserServiceError):
    """Файл не найден в MinIO (HTTP 404)."""
    def __init__(self, file_key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="FILE_NOT_FOUND",
            message=f"Файл '{file_key}' не найден в MinIO"
        )


class FileTooLargeError(ParserServiceError):
    """Превышен допустимый размер файла (HTTP 413)."""
    def __init__(self, size_mb: int, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_TOO_LARGE",
            message=f"Файл размером {size_mb}MB превышает лимит {max_mb}MB"
        )


class UnsupportedFormatError(ParserServiceError):
    """Неподдерживаемый MIME-тип (HTTP 415)."""
    def __init__(self, mime_type: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error_code="UNSUPPORTED_FORMAT",
            message=f"Неподдерживаемый тип файла: {mime_type}"
        )


class ParserFailedError(ParserServiceError):
    """Критическая ошибка в процессе парсинга (HTTP 500)."""
    def __init__(self, original_exception: Exception):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PARSER_FAILED",
            message=f"Критическая ошибка парсинга: {str(original_exception)}"
        )


class StorageError(ParserServiceError):
    """Ошибка взаимодействия с MinIO (HTTP 502)."""
    def __init__(self, operation: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="STORAGE_ERROR",
            message=f"Ошибка доступа к MinIO при {operation}"
        )


class TaskNotFoundError(ParserServiceError):
    """Задача с указанным task_id не найдена (HTTP 404)."""
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="TASK_NOT_FOUND",
            message=f"Задача с task_id={task_id} не найдена"
        )


class TaskExpiredError(ParserServiceError):
    """Результат задачи удалён из-за истечения TTL (HTTP 410)."""
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            error_code="TASK_EXPIRED",
            message=f"Результат задачи {task_id} удалён (старше {settings.task_ttl_days} дней)"
        )