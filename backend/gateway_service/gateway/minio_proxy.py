"""
MinIO proxy — gateway читает файлы напрямую из MinIO и отдаёт клиенту.

Использует S3 API (AWS Signature V4) для доступа к объектам MinIO.
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from gateway.config import config

logger = logging.getLogger(__name__)


def _sign(key: bytes, msg: str) -> bytes:
    """Вычисляет HMAC-SHA256."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    """Вычисляет ключ подписи AWS Signature V4."""
    k_date = _sign(f"AWS4{key}".encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region_name)
    k_service = _sign(k_region, service_name)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _s3_presigned_get_url(
    endpoint: str,
    bucket: str,
    object_key: str,
    access_key: str,
    secret_key: str,
    region: str = "us-east-1",
    expires: int = 3600,
) -> str:
    """
    Генерирует presigned URL для GET объекта из S3-совместимого хранилища (MinIO).

    AWS Signature V4, Query-параметры.
    """
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    host = endpoint.replace("http://", "").replace("https://", "")
    canonical_uri = f"/{bucket}/{object_key}"

    query_params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{access_key}/{date_stamp}/{region}/s3/aws4_request",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_querystring = "&".join(
        f"{k}={_uri_encode(v)}" for k, v in sorted(query_params.items())
    )

    payload_hash = hashlib.sha256(b"").hexdigest()
    canonical_request = (
        f"GET\n{canonical_uri}\n{canonical_querystring}\n"
        f"host:{host}\n\nhost\n{payload_hash}"
    )

    credential_scope = f"{date_stamp}/{region}/s3/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = _get_signature_key(secret_key, date_stamp, region, "s3")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    scheme = "https" if config.minio_secure else "http"
    return (
        f"{scheme}://{host}{canonical_uri}?{canonical_querystring}&X-Amz-Signature={signature}"
    )


def _uri_encode(s: str) -> str:
    """URI-кодирование для query-параметров."""
    import urllib.parse
    return urllib.parse.quote(s, safe="~")


async def fetch_from_minio(file_key: str, bucket: Optional[str] = None) -> httpx.Response:
    """
    Читает файл из MinIO и возвращает httpx.Response.

    Args:
        file_key: Ключ объекта в MinIO (например, 'documents/f-abc123.pdf')
        bucket: Имя бакета. Если None — используется config.minio_bucket.

    Returns:
        httpx.Response с содержимым файла.
    """
    bucket = bucket or config.minio_bucket
    url = _s3_presigned_get_url(
        endpoint=config.minio_endpoint,
        bucket=bucket,
        object_key=file_key,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response
