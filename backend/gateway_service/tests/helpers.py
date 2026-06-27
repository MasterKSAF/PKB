"""
Helpers for Gateway integration tests.

Содержит вспомогательные функции, которые используются в тестах.
"""

from __future__ import annotations

from typing import Dict


def auth_header(token: str) -> Dict[str, str]:
    """Заголовок Authorization: Bearer <token>."""
    return {"Authorization": f"Bearer {token}"}


# PII-параметры, которые должны блокироваться (GW-7)
PII_PARAMS = [
    "password", "email", "access_token", "refresh_token",
    "api_key", "apikey", "secret_key", "phone", "passport",
    "inn", "snils", "ogrn",
]

# Безопасные параметры (должны пропускаться)
SAFE_PARAMS = ["document_key", "file_key", "search", "q", "page"]

# Тестовые credentials (seed-данные из mocks/common.py)
ADMIN_CREDENTIALS = {"username": "admin@example.com", "password": "admin123"}
ENGINEER_CREDENTIALS = {"username": "ivanov@example.com", "password": "secret123"}
KNOWLEDGE_ADMIN_CREDENTIALS = {"username": "petrova@example.com", "password": "secret456"}
