"""
Тесты для MinIO клиента.
Проверяют скачивание файлов, загрузку изображений и обработку ошибок.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.minio_client import MinIOClient
from app.core.exceptions import StorageError


class TestMinIOClient:
    """Все тесты используют мок S3-клиента, реальное подключение не требуется."""

    @pytest.fixture
    def client(self):
        """Фикстура: создаёт MinIOClient с подменённой сессией aiobotocore."""
        with patch("app.core.minio_client.aiobotocore.session.get_session") as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.create_client.return_value.__aenter__.return_value = mock_client
            client = MinIOClient()
            client._session = mock_session.return_value
            yield client

    @pytest.mark.asyncio
    async def test_download_file_success(self, client):
        """Успешное скачивание: возвращаются байты файла."""
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=b"data")
        mock_body = MagicMock()
        mock_body.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_body.__aexit__ = AsyncMock(return_value=None)
        mock_s3.get_object.return_value = {"Body": mock_body}

        data = await client.download_file("file.pdf")
        assert data == b"data"
        mock_s3.get_object.assert_called_once_with(Bucket=client.bucket, Key="file.pdf")

    @pytest.mark.asyncio
    async def test_download_file_failure_raises_storage_error(self, client):
        """Ошибка при скачивании → StorageError."""
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.get_object.side_effect = Exception("network error")
        with pytest.raises(StorageError) as exc:
            await client.download_file("missing.pdf")
        assert "download missing.pdf" in str(exc.value)

    @pytest.mark.asyncio
    async def test_upload_image(self, client):
        """Загрузка изображения: формируется правильный ключ и вызывается put_object."""
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.put_object = AsyncMock()
        key = await client.upload_image(b"img", task_id=42, page_num=1, ext=".png")
        assert key.startswith("task_42/page_1_")
        assert key.endswith(".png")
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args[1]
        assert call_args["Bucket"] == client.image_bucket
        assert call_args["Key"] == key
        assert call_args["ContentType"] == "image/png"