#!/usr/bin/env python3
"""Создание bucket'ов MinIO при старте контейнера."""

import os
import time
import sys

ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKETS = ["documents", "images"]
SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


def _detect_backend():
    """Определяем, какой S3-клиент доступен: MinIO SDK или botocore.
    
    Returns:
        (has_botocore: bool, error_msg: str | None)
    """
    try:
        from minio import Minio  # noqa: F401
        return False, None
    except ImportError:
        pass
    try:
        from botocore.session import Session  # noqa: F401
        return True, None
    except ImportError:
        return False, "Neither minio nor botocore available, install one of them"


def wait_for_minio(max_retries=10, delay=2):
    """Ждём, пока MinIO станет доступен."""
    import urllib.request
    
    host = ENDPOINT.split(":")[0]
    port = ENDPOINT.split(":")[1] if ":" in ENDPOINT else 9000
    url = f"http://{host}:{port}/minio/health/live"
    
    for i in range(max_retries):
        try:
            resp = urllib.request.urlopen(url, timeout=3)
            if resp.status == 200:
                return True
        except Exception:
            pass
        print(f"   ⏳ Waiting for MinIO at {ENDPOINT} (attempt {i+1}/{max_retries})...")
        time.sleep(delay)
    return False


def create_buckets_minio_sdk(client=None):
    """Создание bucket через MinIO Python SDK."""
    if client is None:
        from minio import Minio
        client = Minio(
            ENDPOINT,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            secure=SECURE,
        )
    for bucket in BUCKETS:
        if client.bucket_exists(bucket):
            print(f"   ✓ Bucket '{bucket}' already exists")
        else:
            client.make_bucket(bucket)
            print(f"   ✓ Bucket '{bucket}' created")


def create_buckets_botocore(client=None):
    """Создание bucket через botocore (S3 API)."""
    if client is None:
        from botocore.session import Session
        session = Session()
        client = session.create_client(
            "s3",
            endpoint_url=f"http://{ENDPOINT}",
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            use_ssl=SECURE,
            region_name="us-east-1",
        )
    for bucket in BUCKETS:
        try:
            client.head_bucket(Bucket=bucket)
            print(f"   ✓ Bucket '{bucket}' already exists")
        except Exception as e:
            # Duck-typing: botocore ClientError или любая S3-подобная ошибка имеет response["Error"]["Code"]
            if hasattr(e, "response"):
                code = e.response.get("Error", {}).get("Code", "")
                if code in ("404", "NoSuchBucket"):
                    client.create_bucket(Bucket=bucket)
                    print(f"   ✓ Bucket '{bucket}' created")
                    continue
                print(f"   ⚠ Bucket '{bucket}' head_bucket error: {code} — {e}")
            else:
                print(f"   ⚠ Unexpected error checking bucket '{bucket}': {e}")
            raise


def main():
    if not wait_for_minio():
        print("   ✗ MinIO not available, skipping bucket creation")
        sys.exit(1)
    
    has_botocore, err = _detect_backend()
    if err:
        print(f"   ✗ {err}")
        sys.exit(1)
    if has_botocore:
        create_buckets_botocore()
    else:
        create_buckets_minio_sdk()


if __name__ == "__main__":
    main()
