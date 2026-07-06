"""
MinIO proxy — gateway читает файлы напрямую из MinIO и отдаёт клиенту.

Использует aiobotocore (AWS SDK S3) для доступа к объектам MinIO.
"""

import logging
from typing import Optional

import httpx

from gateway.config import config

logger = logging.getLogger(__name__)


async def fetch_from_minio(file_key: str, bucket: Optional[str] = None) -> httpx.Response:
    """
    Читает файл из MinIO через S3 API и возвращает httpx.Response.

    Args:
        file_key: Ключ объекта в MinIO.
        bucket: Имя бакета. Если None — используется config.minio_bucket.

    Returns:
        httpx.Response с содержимым файла.

    Raises:
        Exception: При ошибке доступа к MinIO.
    """
    bucket = bucket or config.minio_bucket
    url = await _s3_get_url(file_key, bucket)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response


async def _s3_get_url(object_key: str, bucket: str) -> str:
    """Генерирует presigned GET URL через aiobotocore.

    Использует AWS Signature V4 через S3 SDK, что гарантирует
    корректную подпись, совместимую с MinIO.
    """
    import aiobotocore
    from aiobotocore.session import get_session

    session = get_session()

    # Build endpoint URL
    endpoint = config.minio_endpoint
    if not endpoint.startswith("http"):
        endpoint = f"http://{endpoint}"

    async with session.create_client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=config.minio_access_key,
        aws_secret_access_key=config.minio_secret_key,
        use_ssl=config.minio_secure,
        region_name="us-east-1",
    ) as client:
        url = await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_key},
            ExpiresIn=3600,
        )
        return url
