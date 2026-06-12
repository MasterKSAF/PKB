"""
Конфигурация приложения на основе Pydantic Settings.

Все параметры читаются из переменных окружения, с поддержкой файла .env.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Настройки сервиса парсинга.
    """

    # FastAPI
    host: str = Field("0.0.0.0", alias="HOST", description="Хост для запуска сервера")
    port: int = Field(8087, alias="PORT", description="Порт для запуска сервера")
    api_prefix: str = Field("/api/v1", alias="API_PREFIX", description="Префикс для API версии 1")
    log_level: str = Field("info", alias="LOG_LEVEL", description="Уровень логирования (DEBUG, INFO, WARNING, ERROR)")

    # MinIO
    minio_endpoint: str = Field(..., alias="MINIO_ENDPOINT", description="MinIO endpoint (например, minio:9000)")
    minio_access_key: str = Field(..., alias="MINIO_ACCESS_KEY", description="Access key для MinIO")
    minio_secret_key: str = Field(..., alias="MINIO_SECRET_KEY", description="Secret key для MinIO")
    minio_bucket: str = Field(..., alias="MINIO_BUCKET", description="Бакет для исходных документов")
    minio_secure: bool = Field(False, alias="MINIO_SECURE", description="Использовать HTTPS для MinIO")
    minio_image_bucket: str = Field(..., alias="MINIO_IMAGE_BUCKET", description="Бакет для извлечённых изображений")

    # Лимиты
    max_file_size_mb: int = Field(500, alias="MAX_FILE_SIZE_MB", description="Максимальный размер файла в МБ")
    max_pages: int = Field(2000, alias="MAX_PAGES", description="Максимальное количество страниц для обработки")
    task_ttl_days: int = Field(7, alias="TASK_TTL_DAYS", description="Время жизни результата задачи в днях")

    # Схема вывода
    parsing_schema: str = Field("raw_ocr_v4", alias="PARSING_SCHEMA", description="Версия схемы JSON")

    # Единицы измерения
    pdf_dpi: int = Field(72, alias="PDF_DPI", description="DPI для преобразования мм в пиксели")

    # Парсинг
    default_extract_tables: bool = Field(True, alias="DEFAULT_EXTRACT_TABLES")
    default_extract_images: bool = Field(True, alias="DEFAULT_EXTRACT_IMAGES")

    # Сохранение JSON в файл (отладка)
    save_json_to_dir: bool = Field(False, alias="SAVE_JSON_TO_DIR")
    json_output_dir: str = Field("./output", alias="JSON_OUTPUT_DIR")

    # Таймауты
    minio_timeout: int = Field(30, alias="MINIO_TIMEOUT", description="Таймаут операций с MinIO (сек)")
    preview_timeout: int = Field(30, alias="PREVIEW_TIMEOUT", description="Таймаут preview (сек)")
    pipeline_timeout: int = Field(300, alias="PIPELINE_TIMEOUT", description="Таймаут всего пайплайна (сек)")
    parser_timeout: int = Field(300, alias="PARSER_TIMEOUT", description="Таймаут работы конкретного парсера (сек)")

    # OpenTelemetry
    otel_endpoint: str = Field(
        "localhost:4317",
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
        description="gRPC эндпоинт для OTLP экспортера (например, signoz-otel-collector:4317)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()