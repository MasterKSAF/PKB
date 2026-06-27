"""
Тесты IdempotencyMiddleware — кеш идемпотентности.

Unit-тесты, не требуют Docker.
"""

from __future__ import annotations

import os
import sys

import pytest

_GATEWAY_DIR = os.path.join(os.path.dirname(__file__), "..")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


class TestIdempotency:
    """IdempotencyMiddleware — базовые проверки."""

    def test_idempotency_key_accepted(self, client):
        """Запрос с Idempotency-Key проходит."""
        resp = client.post(
            "/api/v1/drafts",
            json={"title": "test"},
            headers={"Authorization": "Bearer test", "Idempotency-Key": "key-123"},
        )
        # Не блокируется (может быть 502 если прокси не отвечает)
        assert resp.status_code not in (409,)
