from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "rag_search_service_spd"

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "pkb_neuro"
    POSTGRES_USER: str = "pkb"
    POSTGRES_PASSWORD: str = "pkb"
    POSTGRES_SCHEMA: str = "nsi"

    EMBEDDING_PROVIDER: str = "stub"
    EMBEDDING_MODEL: str = "stub"
    EMBEDDING_DIM: int = 312
    EMBEDDING_API_BASE_URL: str | None = None
    EMBEDDING_BASE_URL: str | None = None
    EMBEDDING_API_URL: str | None = None
    EMBEDDING_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


    @property
    def effective_embedding_api_base_url(self) -> str | None:
        if self.EMBEDDING_API_BASE_URL:
            return self.EMBEDDING_API_BASE_URL.rstrip("/")

        if self.EMBEDDING_BASE_URL:
            return self.EMBEDDING_BASE_URL.rstrip("/")

        if self.EMBEDDING_API_URL:
            value = self.EMBEDDING_API_URL.rstrip("/")
            if value.endswith("/embeddings"):
                return value[: -len("/embeddings")]
            return value

        return None


settings = Settings()
