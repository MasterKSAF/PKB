#!/usr/bin/env python3
"""Создание bucket'ов MinIO при старте контейнера."""

import os
import time
import sys

try:
    from minio import Minio
except ImportError:
    print("   ⚠ minio Python SDK not installed, trying botocore...")
    try:
        from botocore.session import Session
        HAS_BOTOCORE = True
    except ImportError:
        print("   ✗ Neither minio nor botocore available, install one of them")
        sys.exit(1)
else:
    HAS_BOTOCORE = False

ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKETS = ["documents", "images"]
SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


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


def create_buckets_minio_sdk():
    """Создание bucket через MinIO Python SDK."""
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


def create_buckets_botocore():
    """Создание bucket через botocore (S3 API)."""
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
        except Exception:
            client.create_bucket(Bucket=bucket)
            print(f"   ✓ Bucket '{bucket}' created")


def main():
    if not wait_for_minio():
        print("   ✗ MinIO not available, skipping bucket creation")
        sys.exit(1)
    
    if HAS_BOTOCORE:
        create_buckets_botocore()
    else:
        create_buckets_minio_sdk()


if __name__ == "__main__":
    main()
