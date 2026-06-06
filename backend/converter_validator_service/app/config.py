from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8086, alias="PORT")
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")
    log_level: str = Field("info", alias="LOG_LEVEL")

    registry_service_url: str | None = Field(
        None, alias="REGISTRY_SERVICE_URL"
    )
    registry_timeout_sec: float = Field(10.0, alias="REGISTRY_TIMEOUT_SEC")

    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    default_llm_model: str = Field("gpt-4o-mini", alias="DEFAULT_LLM_MODEL")
    default_llm_max_tokens: int = Field(4096, alias="DEFAULT_LLM_MAX_TOKENS")
    default_llm_timeout: int = Field(60, alias="DEFAULT_LLM_TIMEOUT")

    confidence_threshold: float = Field(
        0.55, alias="CONFIDENCE_THRESHOLD"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
