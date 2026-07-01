"""
Gateway configuration via environment variables.

Единственный режим — GATEWAY_MODE=real (reverse-proxy к реальным микросервисам, порт 8080).

Мок-сервер для тестирования — отдельное приложение mocks/gateway.py
"""

import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class GatewayConfig:
    # Режим работы
    mode: str = field(default_factory=lambda: os.getenv("GATEWAY_MODE", "real"))

    # Окружение: development | production (GW-3)
    env: str = field(
        default_factory=lambda: os.getenv("ENV", "development").lower()
    )

    # Порт самого Gateway
    port: int = field(
        default_factory=lambda: int(os.getenv("GATEWAY_PORT", "8080"))
    )

    # Хост
    host: str = field(default_factory=lambda: os.getenv("GATEWAY_HOST", "127.0.0.1"))

    # MinIO
    minio_endpoint: str = field(
        default_factory=lambda: os.getenv("MINIO_ENDPOINT", "minio:9000")
    )
    minio_access_key: str = field(
        default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    )
    minio_secret_key: str = field(
        default_factory=lambda: os.getenv("MINIO_SECRET_KEY", "minioadmin")
    )
    minio_bucket: str = field(
        default_factory=lambda: os.getenv("MINIO_BUCKET", "documents")
    )
    minio_image_bucket: str = field(
        default_factory=lambda: os.getenv("MINIO_IMAGE_BUCKET", "images")
    )
    minio_secure: bool = field(
        default_factory=lambda: os.getenv("MINIO_SECURE", "false").lower() in ("1", "true", "yes")
    )

    # Адреса внутренних сервисов
    # Формат: "http://host:port"
    service_urls: Dict[str, str] = field(default_factory=lambda: {
        "auth":                os.getenv("AUTH_SERVICE_URL",                "http://127.0.0.1:8082"),
        "orchestrator":        os.getenv("ORCHESTRATOR_SERVICE_URL",        "http://127.0.0.1:8081"),
        "query":               os.getenv("QUERY_SERVICE_URL",               "http://127.0.0.1:8083"),
        "registry":            os.getenv("REGISTRY_SERVICE_URL",            "http://127.0.0.1:8084"),
        "converter_validator": os.getenv("CONVERTER_VALIDATOR_SERVICE_URL","http://127.0.0.1:8086"),
        "parser":              os.getenv("PARSER_SERVICE_URL",              "http://127.0.0.1:8087"),
        "ocr":                 os.getenv("OCR_SERVICE_URL",                 "http://127.0.0.1:8088"),
        "analyse":             os.getenv("ANALYSE_SERVICE_URL",             "http://127.0.0.1:8089"),
        "rag_builder":         os.getenv("RAG_BUILDER_SERVICE_URL",         "http://127.0.0.1:8090"),
        "rag_search":          os.getenv("RAG_SEARCH_SERVICE_URL",          "http://127.0.0.1:8091"),
    })

    # Таймауты
    request_timeout: float = float(os.getenv("GATEWAY_REQUEST_TIMEOUT", "30.0"))
    health_timeout: float = float(os.getenv("GATEWAY_HEALTH_TIMEOUT", "5.0"))

    # CORS (GW-3)
    cors_allowed_origins: str = field(
        default_factory=lambda: os.getenv("CORS_ALLOWED_ORIGINS", "*")
    )

    # Idempotency
    idempotency_ttl: int = int(os.getenv("IDEMPOTENCY_TTL", "3600"))

    # Rate limiting + IDOR protection (CM-2, CM-3, GW-4, GW-6)
    rate_limit_enabled: bool = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "1").lower() in ("1", "true", "yes")
    )

    # Разрешён ли анонимный доступ (для тестов)
    allow_anonymous: bool = field(
        default_factory=lambda: os.getenv("ALLOW_ANONYMOUS", "").lower() in ("1", "true", "yes")
    )

    def __post_init__(self):
        valid_modes = ("real",)
        if self.mode not in valid_modes:
            raise ValueError(
                f"GATEWAY_MODE={self.mode!r} не поддерживается. "
                f"Допустимые значения: {', '.join(valid_modes)}"
            )

        # Валидация ENV (GW-3)
        valid_envs = ("development", "production")
        if self.env not in valid_envs:
            raise ValueError(
                f"ENV={self.env!r} не поддерживается. "
                f"Допустимые значения: {', '.join(valid_envs)}"
            )

        # CI-check: * запрещён для production (GW-3)
        if self.env == "production" and self.cors_allowed_origins == "*":
            raise ValueError(
                "CORS_ALLOWED_ORIGINS=* запрещён для production. "
                "Укажите конкретные домены через запятую."
            )


# Глобальный экземпляр конфигурации
config = GatewayConfig()
