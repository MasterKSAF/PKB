"""
Утилита: загрузить PDF в MinIO → вызвать parser API → получить JSON.
"""
import json
import sys
import time
import uuid
from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig
import httpx

MINIO_ENDPOINT = "localhost:19000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "documents"  # из конфига запущенного parser_service
PARSER_API_URL = "http://localhost:8087/api/v1/parser"


def upload_to_minio(pdf_path: str) -> str:
    """Загружает PDF в MinIO, возвращает file_key."""
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )

    # Создаём bucket если нет
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=MINIO_BUCKET)

    file_key = f"test_{uuid.uuid4().hex[:8]}_{Path(pdf_path).name}"
    s3.upload_file(pdf_path, MINIO_BUCKET, file_key)
    print(f"  Uploaded: {file_key}", file=sys.stderr)
    return file_key


def call_parser_preview(file_key: str, max_pages: int = 5) -> dict:
    """Вызывает preview API парсера и возвращает JSON."""
    payload = {
        "task_id": 9999,
        "draft_id": 9999,
        "file_key": file_key,
        "mode": "preview",
        "max_pages": max_pages,
        "options": {},
    }

    with httpx.Client(timeout=300) as client:
        print(f"  Calling parser preview (pages={max_pages})...", file=sys.stderr)
        resp = client.post(f"{PARSER_API_URL}/process", json=payload)
        resp.raise_for_status()
        result = resp.json()
        print(f"  Status: {result.get('status')}", file=sys.stderr)
        return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_via_api.py <pdf_path> [--max-pages N] [-o output.json]", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    max_pages = 5
    output_path = None

    for i, arg in enumerate(sys.argv[2:]):
        if arg == "--max-pages" and i + 3 < len(sys.argv):
            max_pages = int(sys.argv[i + 3])
        elif arg == "-o" and i + 3 < len(sys.argv):
            output_path = sys.argv[i + 3]

    if not Path(pdf_path).exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Uploading {pdf_path} to MinIO...", file=sys.stderr)
    file_key = upload_to_minio(pdf_path)

    result = call_parser_preview(file_key, max_pages=max_pages)

    json_str = json.dumps(result, indent=2, ensure_ascii=False)

    if output_path:
        Path(output_path).write_text(json_str, encoding="utf-8")
        print(f"Saved to {output_path}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
