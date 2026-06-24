"""Тесты для docker/init_minio.py — создание bucket'ов MinIO."""

from unittest.mock import MagicMock

import pytest

from service_checker.docker.init_minio import (
    BUCKETS,
    create_buckets_minio_sdk,
    create_buckets_botocore,
)


class _FakeClientError(Exception):
    """Заглушка botocore.exceptions.ClientError — без импорта botocore."""

    def __init__(self, error_code, message="Fake"):
        self.response = {"Error": {"Code": error_code, "Message": message}}
        super().__init__(f"{error_code}: {message}")


# ── create_buckets_minio_sdk ────────────────────────────────────────────────


class TestCreateBucketsMinioSdk:
    """MinIO SDK (make_bucket) — проверка bucket_exists перед созданием."""

    def test_bucket_already_exists(self):
        """Если bucket_exists=True → make_bucket не вызывается."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True

        create_buckets_minio_sdk(mock_client)

        assert mock_client.bucket_exists.call_count == len(BUCKETS)
        mock_client.make_bucket.assert_not_called()

    def test_bucket_does_not_exist(self):
        """Если bucket_exists=False → make_bucket вызывается для каждого."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False

        create_buckets_minio_sdk(mock_client)

        assert mock_client.make_bucket.call_count == len(BUCKETS)
        for b in BUCKETS:
            mock_client.make_bucket.assert_any_call(b)


# ── create_buckets_botocore ─────────────────────────────────────────────────


class TestCreateBucketsBotocore:
    """botocore (S3 API) — проверка head_bucket и create_bucket."""

    def test_bucket_already_exists(self):
        """head_bucket успешен → create_bucket не вызывается."""
        mock_client = MagicMock()
        mock_client.head_bucket.return_value = {}

        create_buckets_botocore(mock_client)

        assert mock_client.head_bucket.call_count == len(BUCKETS)
        mock_client.create_bucket.assert_not_called()

    def test_bucket_does_not_exist_404(self):
        """head_bucket → ClientError 404 → create_bucket вызывается."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _FakeClientError("404")

        create_buckets_botocore(mock_client)

        assert mock_client.create_bucket.call_count == len(BUCKETS)

    def test_bucket_does_not_exist_nosuchbucket(self):
        """head_bucket → ClientError NoSuchBucket → create_bucket вызывается."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _FakeClientError("NoSuchBucket")

        create_buckets_botocore(mock_client)

        assert mock_client.create_bucket.call_count == len(BUCKETS)

    def test_head_bucket_raises_unexpected_error(self):
        """head_bucket → ClientError 403 → create_bucket НЕ вызывается, исключение пробрасывается."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = _FakeClientError("403")

        with pytest.raises(_FakeClientError):
            create_buckets_botocore(mock_client)

        mock_client.create_bucket.assert_not_called()

    def test_head_bucket_raises_non_client_error(self):
        """head_bucket → ConnectionError → create_bucket НЕ вызывается."""
        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError):
            create_buckets_botocore(mock_client)

        mock_client.create_bucket.assert_not_called()
