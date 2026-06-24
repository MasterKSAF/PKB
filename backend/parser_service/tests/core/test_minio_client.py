"""
Тесты для MinIO клиента.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from botocore.exceptions import ClientError
from app.core.minio_client import MinIOClient
from app.core.exceptions import StorageError, FileNotFoundError


class TestMinIOClient:
    @pytest.fixture
    def client(self):
        with patch("app.core.minio_client.aiobotocore.session.get_session") as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.create_client.return_value.__aenter__.return_value = mock_client
            client = MinIOClient()
            client._session = mock_session.return_value
            yield client

    @pytest.mark.asyncio
    async def test_download_file_success(self, client):
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
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.get_object.side_effect = Exception("network error")
        with pytest.raises(StorageError) as exc:
            await client.download_file("missing.pdf")
        assert "download missing.pdf" in str(exc.value)

    @pytest.mark.asyncio
    async def test_ensure_bucket_exists(self, client):
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.head_bucket = AsyncMock()
        await client._ensure_bucket("existing_bucket")
        mock_s3.head_bucket.assert_called_once_with(Bucket="existing_bucket")
        mock_s3.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_bucket_creates_missing(self, client):
        """Проверка: если бакет не найден, он создаётся."""
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        # Создаём ClientError с кодом NoSuchBucket
        error_response = {"Error": {"Code": "NoSuchBucket"}}
        mock_s3.head_bucket.side_effect = ClientError(error_response, "HeadBucket")
        mock_s3.create_bucket = AsyncMock()
        
        await client._ensure_bucket("new_bucket")
        mock_s3.create_bucket.assert_called_once_with(Bucket="new_bucket")

    @pytest.mark.asyncio
    async def test_ensure_bucket_other_error_raises_storage_error(self, client):
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3.head_bucket.side_effect = ClientError(error_response, "HeadBucket")
        with pytest.raises(StorageError):
            await client._ensure_bucket("problem_bucket")

    @pytest.mark.asyncio
    async def test_upload_image(self, client):
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.put_object = AsyncMock()
        key = await client.upload_image(b"img", task_id=42, page_num=1, ext=".png")
        assert key.startswith("task_42/page_1_")
        assert key.endswith(".png")
        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == client.image_bucket
        assert call_kwargs["Key"] == key
        assert call_kwargs["ContentType"] == "image/png"

    @pytest.mark.asyncio
    async def test_upload_image_custom_key(self, client):
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.put_object = AsyncMock()
        custom_key = "custom/path.png"
        key = await client.upload_image(b"img", task_id=1, page_num=1, ext=".png", custom_key=custom_key)
        assert key == custom_key

    @pytest.mark.asyncio
    async def test_upload_image_failure_raises_storage_error(self, client):
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.put_object.side_effect = Exception("upload failed")
        with pytest.raises(StorageError):
            await client.upload_image(b"img", task_id=1, page_num=1)

    @pytest.mark.asyncio
    async def test_get_presigned_url(self, client):
        mock_s3 = client._session.create_client.return_value.__aenter__.return_value
        mock_s3.generate_presigned_url = AsyncMock(return_value="http://presigned.url")
        url = await client.get_presigned_url("file.pdf", expires_in=60)
        assert url == "http://presigned.url"