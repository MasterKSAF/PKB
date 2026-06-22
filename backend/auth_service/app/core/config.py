from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "Auth Service"
    env: str = "dev"

    database_url: str

    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 3600
    refresh_token_expire_seconds: int = 60 * 60 * 24 * 30

    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "Admin1234!"

    otel_endpoint: str = "signoz-otel-collector:4317"

    max_failed_attempts: int = 5
    lockout_duration_seconds: int = 30 * 60

    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60


settings = Settings()
