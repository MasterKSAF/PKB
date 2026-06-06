from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
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

    # Лимиты
    max_file_size_mb: int = Field(500, alias="MAX_FILE_SIZE_MB")
    max_pages: int = Field(2000, alias="MAX_PAGES")
    task_ttl_days: int = Field(7, alias="TASK_TTL_DAYS")

    # Парсинг
    default_extract_tables: bool = Field(True, alias="DEFAULT_EXTRACT_TABLES")
    default_extract_images: bool = Field(True, alias="DEFAULT_EXTRACT_IMAGES")

    # Сохранение JSON в файл
    save_json_to_dir: bool = Field(False, alias="SAVE_JSON_TO_DIR")
    json_output_dir: str = Field("./output", alias="JSON_OUTPUT_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()