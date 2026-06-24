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
    """Проверка, что каждое исключение содержит правильный HTTP-код и error.code."""

    def test_parser_service_error_base(self):
        exc = ParserServiceError(400, "TEST_CODE", "test message", {"detail": "extra"})
        assert exc.status_code == 400
        assert exc.error_code == "TEST_CODE"
        assert exc.details == {"detail": "extra"}
        assert exc.detail["error"]["code"] == "TEST_CODE"
        assert exc.detail["error"]["message"] == "test message"

    def test_file_not_found_error(self):
        exc = FileNotFoundError("missing.pdf")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "FILE_NOT_FOUND"
        assert "missing.pdf" in exc.detail["error"]["message"]

    def test_file_too_large_error(self):
        exc = FileTooLargeError(600, 500)
        assert exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert exc.error_code == "FILE_TOO_LARGE"
        assert "600MB" in exc.detail["error"]["message"]
        assert "500MB" in exc.detail["error"]["message"]

    def test_unsupported_format_error(self):
        exc = UnsupportedFormatError("image/png")
        assert exc.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert exc.error_code == "UNSUPPORTED_FORMAT"
        assert "image/png" in exc.detail["error"]["message"]

    def test_parser_failed_error(self):
        inner = ValueError("bad parse")
        exc = ParserFailedError(inner)
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "PARSER_FAILED"
        assert "bad parse" in exc.detail["error"]["message"]

    def test_storage_error(self):
        exc = StorageError("download file.pdf")
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.error_code == "STORAGE_ERROR"
        assert "download file.pdf" in exc.detail["error"]["message"]

    def test_task_not_found_error(self):
        exc = TaskNotFoundError(123)
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "TASK_NOT_FOUND"
        assert "123" in exc.detail["error"]["message"]

    def test_task_expired_error(self):
        # Для TaskExpiredError нужен settings, в тестах можно замокать
        # Но пока проверим структуру (settings.task_ttl_days будет 7 по умолчанию)
        from app.config import settings
        exc = TaskExpiredError(456)
        assert exc.status_code == status.HTTP_410_GONE
        assert exc.error_code == "TASK_EXPIRED"
        assert "456" in exc.detail["error"]["message"]
        assert str(settings.task_ttl_days) in exc.detail["error"]["message"]