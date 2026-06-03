from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "pkb_db"
    db_user: str = "pkb_user"
    db_password: str = "pkb_pass"
    database_url: str | None = None

    app_port: int = 8090
    embedding_dim: int = 1536
    vector_dimension: int = 1536
    chunk_max_tokens: int = 512
    chunk_size: int = 512
    max_tokens: int = 512
    chunk_default_strategy: str = "semantic_512"
    embedding_api_url: str = "http://localhost:8000/v1/embeddings"
    embedding_model: str = "text-embedding-3-small"
    embedding_timeout: int = 30
    embedding_provider: str = "openai_compatible"  # mock | openai_compatible
    embedding_api_key: str = ""
    embedding_retries: int = 2
    jwt_secret: str = "change-me"

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
