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

    # Порт самого Gateway
    port: int = field(
        default_factory=lambda: int(os.getenv("GATEWAY_PORT", "8080"))
    )

    # Хост
    host: str = field(default_factory=lambda: os.getenv("GATEWAY_HOST", "127.0.0.1"))

    # Адреса внутренних сервисов
    # Формат: "http://host:port"
    service_urls: Dict[str, str] = field(default_factory=lambda: {
        "auth":         os.getenv("AUTH_SERVICE_URL",         "http://127.0.0.1:8082"),
        "orchestrator": os.getenv("ORCHESTRATOR_SERVICE_URL", "http://127.0.0.1:8081"),
        "query":        os.getenv("QUERY_SERVICE_URL",        "http://127.0.0.1:8083"),
        "registry":     os.getenv("REGISTRY_SERVICE_URL",     "http://127.0.0.1:8084"),
    })

    # Таймауты
    request_timeout: float = float(os.getenv("GATEWAY_REQUEST_TIMEOUT", "30.0"))
    health_timeout: float = float(os.getenv("GATEWAY_HEALTH_TIMEOUT", "5.0"))

    # CORS
    cors_allowed_origins: str = field(
        default_factory=lambda: os.getenv("CORS_ALLOWED_ORIGINS", "*")
    )

    # Idempotency
    idempotency_ttl: int = int(os.getenv("IDEMPOTENCY_TTL", "3600"))

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


# Глобальный экземпляр конфигурации
config = GatewayConfig()
