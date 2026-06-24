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


# ---------- Транзиентные (временные) ошибки ----------
class TransientError(ParserServiceError):
    """Ошибка, которая может быть исправлена повторной попыткой."""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="TRANSIENT_ERROR",
            message=message,
            details={"original": str(original_exception)} if original_exception else {}
        )


class FatalError(ParserServiceError):
    """Неисправимая ошибка, повторные попытки бессмысленны."""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="FATAL_ERROR",
            message=message,
            details={"original": str(original_exception)} if original_exception else {}
        )


# ---------- Конкретные ошибки (наследуем от ParserServiceError) ----------
class FileNotFoundError(ParserServiceError):
    def __init__(self, file_key: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="FILE_NOT_FOUND",
            message=f"Файл '{file_key}' не найден в MinIO"
        )


class FileTooLargeError(ParserServiceError):
    def __init__(self, size_mb: int, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_TOO_LARGE",
            message=f"Файл размером {size_mb}MB превышает лимит {max_mb}MB"
        )


class UnsupportedFormatError(ParserServiceError):
    def __init__(self, mime_type: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error_code="UNSUPPORTED_FORMAT",
            message=f"Неподдерживаемый тип файла: {mime_type}"
        )


class ParserFailedError(ParserServiceError):
    def __init__(self, original_exception: Exception):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PARSER_FAILED",
            message=f"Критическая ошибка парсинга: {str(original_exception)}"
        )


class StorageError(ParserServiceError):
    def __init__(self, operation: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="STORAGE_ERROR",
            message=f"Ошибка доступа к MinIO при {operation}"
        )


class TaskNotFoundError(ParserServiceError):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="TASK_NOT_FOUND",
            message=f"Задача с task_id={task_id} не найдена"
        )


class TaskExpiredError(ParserServiceError):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            error_code="TASK_EXPIRED",
            message=f"Результат задачи {task_id} удалён (старше {settings.task_ttl_days} дней)"
        )