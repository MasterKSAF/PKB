"""
Конфигурация приложения на основе Pydantic Settings.

Все параметры читаются из переменных окружения, с поддержкой файла .env.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Настройки сервиса парсинга."""

    # FastAPI
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8087, alias="PORT")
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")
    log_level: str = Field("info", alias="LOG_LEVEL")

    # MinIO
    minio_endpoint: str = Field(..., alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(..., alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(..., alias="MINIO_BUCKET")
    minio_secure: bool = Field(False, alias="MINIO_SECURE")
    minio_image_bucket: str = Field(..., alias="MINIO_IMAGE_BUCKET")
    minio_timeout: int = Field(30, alias="MINIO_TIMEOUT")

    # Лимиты
    max_file_size_mb: int = Field(500, alias="MAX_FILE_SIZE_MB")
    max_pages: int = Field(2000, alias="MAX_PAGES")
    task_ttl_days: int = Field(7, alias="TASK_TTL_DAYS")

    # Таймауты пайплайна (ЭТАЛОННЫЕ ЗНАЧЕНИЯ)
    preview_timeout: int = Field(300, alias="PREVIEW_TIMEOUT")
    pipeline_timeout: int = Field(300, alias="PIPELINE_TIMEOUT")
    parser_timeout: int = Field(300, alias="PARSER_TIMEOUT")

    # Безопасность и валидация
    validation_global_timeout: int = Field(15, alias="VALIDATION_GLOBAL_TIMEOUT")
    enable_yara: bool = Field(False, alias="ENABLE_YARA")
    reject_jbig2: bool = Field(False, alias="REJECT_JBIG2")
    yara_rules_path: str = Field("./app/core/yara_rules", alias="YARA_RULES_PATH")
    max_suspect_font_stream_size: int = Field(10485760, alias="MAX_SUSPECT_FONT_STREAM_SIZE")

    # Моки
    use_mock_minio: bool = Field(False, alias="USE_MOCK_MINIO")
    use_mock_parser: bool = Field(False, alias="USE_MOCK_PARSER")
    use_mock_validator: bool = Field(False, alias="USE_MOCK_VALIDATOR")
    mock_parser_fixture_path: str = Field("", alias="MOCK_PARSER_FIXTURE_PATH")
    mock_minio_delay: float = Field(0.0, alias="MOCK_MINIO_DELAY")
    mock_minio_file_data_path: str = Field("", alias="MOCK_MINIO_FILE_DATA_PATH")

    # Парсинг и вывод
    parsing_schema: str = Field("raw_ocr_v4", alias="PARSING_SCHEMA")
    pdf_dpi: int = Field(72, alias="PDF_DPI")
    save_json_to_dir: bool = Field(False, alias="SAVE_JSON_TO_DIR")
    json_output_dir: str = Field("./output", alias="JSON_OUTPUT_DIR")
    default_extract_tables: bool = Field(True, alias="DEFAULT_EXTRACT_TABLES")
    default_extract_images: bool = Field(True, alias="DEFAULT_EXTRACT_IMAGES")

    # OpenTelemetry
    otel_endpoint: str = Field("localhost:4317", alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()