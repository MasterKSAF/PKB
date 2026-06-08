from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Auth Service"
    env: str = "dev"

    database_url: str = "sqlite:///./auth.db"

    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 3600
    refresh_token_expire_seconds: int = 60 * 60 * 24 * 30

    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "Admin1234!"

    class Config:
        env_file = ".env"


settings = Settings()
