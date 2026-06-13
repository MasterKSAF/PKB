"""
Тесты для валидатора файлов (размер, MIME, безопасность).
"""
import pytest
from unittest.mock import patch, MagicMock
from app.core.validator import Validator
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError


class TestValidator:
    def test_validate_size_ok(self):
        data = b"x" * (1024 * 1024)  # 1 MB
        Validator.validate_size(data)  # не должно выбросить ошибку

    def test_validate_size_too_large(self):
        data = b"x" * (501 * 1024 * 1024)
        with pytest.raises(FileTooLargeError) as exc:
            Validator.validate_size(data)
        assert "501" in str(exc.value)
        assert "500" in str(exc.value)

    @patch("app.core.validator.magic")
    def test_validate_mime_supported(self, mock_magic):
        mock_magic.from_buffer.return_value = "application/pdf"
        mime = Validator.validate_mime(b"fake")
        assert mime == "application/pdf"

    @patch("app.core.validator.magic")
    def test_validate_mime_unsupported(self, mock_magic):
        mock_magic.from_buffer.return_value = "image/jpeg"
        with pytest.raises(UnsupportedFormatError) as exc:
            Validator.validate_mime(b"fake")
        assert "image/jpeg" in str(exc.value)

    def test_validate_safety(self):
        """Заглушка всегда возвращает True."""
        assert Validator.validate_safety(b"any") is True

    @patch("app.core.validator.Validator.validate_size")
    @patch("app.core.validator.Validator.validate_mime")
    @patch("app.core.validator.Validator.validate_safety")
    def test_validate_calls_all(self, mock_safety, mock_mime, mock_size):
        mock_mime.return_value = "application/pdf"
        data = b"test"
        mime = Validator.validate(data)
        mock_size.assert_called_once_with(data)
        mock_mime.assert_called_once_with(data)
        mock_safety.assert_called_once_with(data)
        assert mime == "application/pdf"