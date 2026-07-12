from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "convertor_validator_service_lama"
    environment: str = "local"
    cloud_api_key: str | None = None
    parse_base_url: str = "https://api.cloud.llamaindex.ai"
    extract_base_url: str = "https://api.cloud.llamaindex.ai"
    extract_project_id: str | None = None
    rag_builder_base_url: str = "http://rag-builder-service:8000"
    parse_result_format: Literal["markdown", "json"] = "markdown"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LAMA_",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
