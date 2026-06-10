import pytest
import os
from unittest.mock import patch
from app.config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8087
    assert settings.max_file_size_mb == 500
    assert settings.task_ttl_days == 7
    assert settings.parsing_schema == "raw_ocr_v4"
    assert settings.pdf_dpi == 72
    assert settings.minio_timeout == 30
    assert settings.preview_timeout == 30
    assert settings.pipeline_timeout == 300
    assert settings.parser_timeout == 300
    # Обязательные поля заданы в conftest
    _ = settings.minio_endpoint
    _ = settings.minio_access_key
    _ = settings.minio_secret_key
    _ = settings.minio_bucket
    _ = settings.minio_image_bucket


def test_settings_from_env():
    with patch.dict(os.environ, {
        "MINIO_ENDPOINT": "minio:9000",
        "MINIO_ACCESS_KEY": "admin",
        "MINIO_SECRET_KEY": "password",
        "MINIO_BUCKET": "docs",
        "MINIO_IMAGE_BUCKET": "images",
        "PORT": "9000",
        "LOG_LEVEL": "DEBUG"
    }):
        settings = Settings()
        assert settings.minio_endpoint == "minio:9000"
        assert settings.port == 9000
        assert settings.log_level == "DEBUG"


def test_api_prefix_default():
    settings = Settings()
    assert settings.api_prefix == "/api/v1"