"""
Тесты для кастомных исключений сервиса.
Проверяют HTTP-статусы, коды ошибок и формат сообщений.
"""
import pytest
from fastapi import status
from app.core.exceptions import (
    ParserServiceError,
    FileNotFoundError,
    FileTooLargeError,
    UnsupportedFormatError,
    ParserFailedError,
    StorageError,
    TaskNotFoundError,
    TaskExpiredError,
)


class TestExceptions:
    """Проверка каждого типа исключения."""

    def test_parser_service_error_base(self):
        """Базовое исключение: должно содержать код, статус и детали."""
        exc = ParserServiceError(400, "TEST_CODE", "test message", {"detail": "extra"})
        assert exc.status_code == 400
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"detail": "extra"}
        assert exc.detail["error"]["code"] == "TEST_CODE"
        assert exc.detail["error"]["message"] == "test message"

    def test_file_not_found_error(self):
        """FILE_NOT_FOUND: 404, сообщение содержит имя файла."""
        exc = FileNotFoundError("missing.pdf")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "FILE_NOT_FOUND"
        assert "missing.pdf" in exc.detail["error"]["message"]

    def test_file_too_large_error(self):
        """FILE_TOO_LARGE: 413, сообщение содержит размер и лимит (без пробелов)."""
        exc = FileTooLargeError(600, 500)
        assert exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert exc.error_code == "FILE_TOO_LARGE"
        # Ожидаемый формат: "600MB" (целое число, без десятичной точки и пробела)
        assert "600MB" in exc.detail["error"]["message"]
        assert "500MB" in exc.detail["error"]["message"]

    def test_unsupported_format_error(self):
        """UNSUPPORTED_FORMAT: 415, сообщение содержит неподдерживаемый MIME."""
        exc = UnsupportedFormatError("image/png")
        assert exc.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert exc.error_code == "UNSUPPORTED_FORMAT"
        assert "image/png" in exc.detail["error"]["message"]

    def test_parser_failed_error(self):
        """PARSER_FAILED: 500, сообщение содержит оригинальную ошибку."""
        inner = ValueError("bad parse")
        exc = ParserFailedError(inner)
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "PARSER_FAILED"
        assert "bad parse" in exc.detail["error"]["message"]

    def test_storage_error(self):
        """STORAGE_ERROR: 502, сообщение указывает операцию."""
        exc = StorageError("download file.pdf")
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.error_code == "STORAGE_ERROR"
        assert "download file.pdf" in exc.detail["error"]["message"]

    def test_task_not_found_error(self):
        """TASK_NOT_FOUND: 404, сообщение содержит task_id."""
        exc = TaskNotFoundError(123)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "TASK_NOT_FOUND"
        assert "123" in exc.detail["error"]["message"]

    def test_task_expired_error(self):
        """TASK_EXPIRED: 410, сообщение содержит task_id и TTL."""
        from app.config import settings  # settings имеет значение по умолчанию 7 дней
        exc = TaskExpiredError(456)
        assert exc.status_code == status.HTTP_410_GONE
        assert exc.error_code == "TASK_EXPIRED"
        assert "456" in exc.detail["error"]["message"]
        assert str(settings.task_ttl_days) in exc.detail["error"]["message"]