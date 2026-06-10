"""
Тесты для file_loader.py
"""
import pytest
from unittest.mock import patch, AsyncMock
from app.services.file_loader import fetch_and_validate
from app.core.exceptions import StorageError, UnsupportedFormatError, FileTooLargeError
import asyncio

@pytest.mark.asyncio
async def test_fetch_and_validate_success():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = b"%PDF-1.4"
        with patch("app.services.file_loader.Validator.validate") as mock_validate:
            mock_validate.return_value = "application/pdf"
            data = await fetch_and_validate("test.pdf")
            assert data == b"%PDF-1.4"
            mock_download.assert_called_once_with("test.pdf")
            mock_validate.assert_called_once_with(b"%PDF-1.4")


@pytest.mark.asyncio
async def test_fetch_and_validate_minio_timeout():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.side_effect = asyncio.TimeoutError()
        with pytest.raises(StorageError) as exc:
            await fetch_and_validate("test.pdf")
        assert "download timeout test.pdf" in str(exc.value)


@pytest.mark.asyncio
async def test_fetch_and_validate_minio_error():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.side_effect = Exception("connection refused")
        with pytest.raises(StorageError) as exc:
            await fetch_and_validate("test.pdf")
        assert "download test.pdf" in str(exc.value)


@pytest.mark.asyncio
async def test_fetch_and_validate_unsupported_mime():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = b"fake"
        with patch("app.services.file_loader.Validator.validate") as mock_validate:
            mock_validate.side_effect = UnsupportedFormatError("image/jpeg")
            with pytest.raises(UnsupportedFormatError):
                await fetch_and_validate("test.jpg")


@pytest.mark.asyncio
async def test_fetch_and_validate_file_too_large():
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = b"fake"
        with patch("app.services.file_loader.Validator.validate") as mock_validate:
            mock_validate.side_effect = FileTooLargeError(600, 500)
            with pytest.raises(FileTooLargeError):
                await fetch_and_validate("big.pdf")


@pytest.mark.asyncio
async def test_fetch_and_validate_non_pdf_mime():
    """После успешной валидации MIME != PDF → UnsupportedFormatError."""
    with patch("app.services.file_loader.minio_client.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = b"fake"
        with patch("app.services.file_loader.Validator.validate") as mock_validate:
            mock_validate.return_value = "text/plain"
            with pytest.raises(UnsupportedFormatError) as exc:
                await fetch_and_validate("test.txt")
            assert "text/plain" in str(exc.value)