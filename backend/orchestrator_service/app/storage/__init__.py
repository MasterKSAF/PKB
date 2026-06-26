"""
MinIO storage client for uploading draft files.
Uses aiobotocore (async S3-compatible) to match the Parser service.
"""

import logging
from typing import Optional

import aiobotocore.session
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


async def upload_file(
    file_key: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    bucket: Optional[str] = None,
) -> None:
    """Upload a file to MinIO storage.

    Args:
        file_key: Object key in the bucket (e.g. "f-abc123def456").
        content: File bytes.
        content_type: MIME type of the file.
        bucket: MinIO bucket name. Defaults to settings.minio.MINIO_BUCKET.

    Raises:
        RuntimeError: If the upload fails.
    """
    cfg = settings.minio
    bucket_name = bucket or cfg.MINIO_BUCKET

    endpoint = cfg.MINIO_ENDPOINT
    if not endpoint.startswith("http"):
        endpoint = f"http://{endpoint}"

    session = aiobotocore.session.AioSession()
    client_kwargs = dict(
        aws_access_key_id=cfg.MINIO_ACCESS_KEY,
        aws_secret_access_key=cfg.MINIO_SECRET_KEY,
        endpoint_url=endpoint,
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )

    async with session.create_client("s3", **client_kwargs) as client:
        # Ensure bucket exists
        try:
            await client.head_bucket(Bucket=bucket_name)
        except Exception:
            try:
                await client.create_bucket(Bucket=bucket_name)
                logger.info("Created MinIO bucket: %s", bucket_name)
            except Exception:
                pass  # race condition with other services

        try:
            await client.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=content,
                ContentType=content_type,
            )
            logger.info(
                "Uploaded to MinIO: bucket=%s key=%s size=%d",
                bucket_name, file_key, len(content),
            )
        except Exception as exc:
            logger.error(
                "MinIO upload failed: bucket=%s key=%s error=%s",
                bucket_name, file_key, exc,
            )
            raise RuntimeError(
                f"MinIO upload failed for {file_key}: {exc}"
            ) from exc
