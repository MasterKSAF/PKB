from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "rag-builder"
    app_version: str = "1.0.0"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "pkb_neuro"
    db_user: str = "pkb"
    db_password: str = "pkb"
    database_url: str | None = None

    app_port: int = 8090
    embedding_dim: int = 2048
    vector_dimension: int = 2048
    chunk_max_tokens: int = 1024
    chunk_size: int = 1024
    max_tokens: int = 1024
    chunk_default_strategy: str = "semantic_1024"
    embedding_api_url: str = "http://localhost:8000/v1/embeddings"
    embedding_model: str = "text-embedding-3-small"
    embedding_timeout: int = 30
    embedding_batch_size: int = 32
    embedding_provider: str = "mock"  # mock | openai_compatible | infinity
    embedding_api_key: str = ""
    embedding_retries: int = 2

    api_prefix: str = "/api/v1"
    default_longpoll_seconds: int = 15

    log_dir: str = "logs"
    log_file: str = "rag_builder.log"
    log_level: str = "DEBUG"
    log_rotation: str = "10 MB"
    log_retention: str = "14 days"
    log_compression: str = "zip"


settings = Settings()


def build_database_url(s: Settings) -> str:
    if s.database_url:
        return s.database_url
    return f"postgresql+asyncpg://{s.db_user}:{s.db_password}@{s.db_host}:{s.db_port}/{s.db_name}"
