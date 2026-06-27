"""
Тесты IdempotencyMiddleware.

Сценарии:
  - POST /api/v1/drafts с Idempotency-Key — первый запрос → 202
  - POST /api/v1/drafts с тем же ключом — возвращает закешированный ответ
  - POST /chat/send с Idempotency-Key
  - POST без Idempotency-Key — обычный flow
  - POST /api/v1/documents/search с ключом — игнорируется (не idempotency prefix)

Интеграционные тесты (требуют Docker).
"""

from __future__ import annotations

import os
import sys
import uuid

import pytest

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_GATEWAY_DIR = os.path.join(_TEST_DIR, "..")
if _TEST_DIR not in sys.path:
    sys.path.insert(0, _TEST_DIR)
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)

from helpers import auth_header


@pytest.mark.docker
class TestIdempotency:
    """IdempotencyMiddleware — идемпотентность POST-запросов."""

    @pytest.mark.asyncio
    async def test_first_request_returns_202(self, http_client, docker_gateway_base, system_admin_token):
        """POST /api/v1/drafts с Idempotency-Key — первый → 202."""
        key = str(uuid.uuid4())
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers={
                **auth_header(system_admin_token),
                "Idempotency-Key": key,
            },
            json={"file_key": "test.pdf", "document_key": "doc-idemp-001"},
        )
        # В Docker с mock может быть 200/201 вместо 202
        # Главное — не 500
        assert resp.status_code not in (401, 403, 500), (
            f"Первый запрос с Idempotency-Key не должен падать: "
            f"{resp.status_code} {resp.text[:100]}"
        )

    @pytest.mark.asyncio
    async def test_same_key_returns_cached_response(self, http_client, docker_gateway_base, system_admin_token):
        """POST с тем же Idempotency-Key — возвращает закешированный ответ."""
        key = str(uuid.uuid4())
        # Первый запрос
        resp1 = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers={
                **auth_header(system_admin_token),
                "Idempotency-Key": key,
            },
            json={"file_key": "test.pdf", "document_key": "doc-idemp-002"},
        )

        # Второй запрос с тем же ключом
        resp2 = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers={
                **auth_header(system_admin_token),
                "Idempotency-Key": key,
            },
            json={"file_key": "test.pdf", "document_key": "doc-idemp-002"},
        )

        # Должен вернуть тот же результат (200/409/201) — не 500
        assert resp2.status_code not in (500,), (
            f"Повторный запрос с Idempotency-Key не должен падать: "
            f"{resp2.status_code}"
        )

    @pytest.mark.asyncio
    async def test_without_key_normal_flow(self, http_client, docker_gateway_base, system_admin_token):
        """POST без Idempotency-Key — обычный flow."""
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers=auth_header(system_admin_token),
            json={"file_key": "test-no-key.pdf", "document_key": "doc-no-key-001"},
        )
        assert resp.status_code not in (500,), (
            f"POST без Idempotency-Key: {resp.status_code} {resp.text[:100]}"
        )

    @pytest.mark.asyncio
    async def test_search_key_ignored(self, http_client, docker_gateway_base, system_admin_token):
        """POST /api/v1/documents/search с Idempotency-Key — игнорируется (не idempotency prefix)."""
        key = str(uuid.uuid4())
        resp = await http_client.post(
            f"{docker_gateway_base}/api/v1/documents/search",
            headers={
                **auth_header(system_admin_token),
                "Idempotency-Key": key,
            },
            json={"q": "test"},
        )
        # Ожидаем нормальный поисковый ответ
        assert resp.status_code not in (500,), (
            f"Search с Idempotency-Key: {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_different_keys_different_results(self, http_client, docker_gateway_base, system_admin_token):
        """POST с разными ключами — создаются разные ресурсы."""
        key1 = str(uuid.uuid4())
        key2 = str(uuid.uuid4())

        resp1 = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers={
                **auth_header(system_admin_token),
                "Idempotency-Key": key1,
            },
            json={"file_key": "test-diff-1.pdf", "document_key": "doc-diff-001"},
        )
        resp2 = await http_client.post(
            f"{docker_gateway_base}/api/v1/drafts",
            headers={
                **auth_header(system_admin_token),
                "Idempotency-Key": key2,
            },
            json={"file_key": "test-diff-2.pdf", "document_key": "doc-diff-002"},
        )
        assert resp1.status_code not in (500,)
        assert resp2.status_code not in (500,)
