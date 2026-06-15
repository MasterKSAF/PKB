"""
Тесты для валидатора файлов (размер, MIME, безопасность).
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.core.validator import Validator
from app.core.exceptions import FileTooLargeError, UnsupportedFormatError

class TestValidator:
    def test_validate_size_ok(self):
        data = b"x" * (1024 * 1024)
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

    @pytest.mark.asyncio
    async def test_validate_success(self):
        data = b"%PDF-1.4"
        with patch("app.core.validator.SecurityScanner.scan_pdf", return_value=(True, None)):
            mime = await Validator.validate(data, "test.pdf")
            assert mime == "application/pdf"

    @pytest.mark.asyncio
    async def test_validate_security_failure(self):
        data = b"%PDF-1.4"
        with patch("app.core.validator.SecurityScanner.scan_pdf", return_value=(False, "malicious")):
            with pytest.raises(UnsupportedFormatError, match="Security check failed: malicious"):
                await Validator.validate(data, "bad.pdf")