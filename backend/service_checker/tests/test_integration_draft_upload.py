"""
Интеграционный тест — сквозной сценарий загрузки черновика через Gateway.

Проверяет цепочку Gateway → Orchestrator → Registry:
  - POST /api/v1/auth/token — получение токена (202 или 307)
  - POST /api/v1/drafts — создание черновика (должен быть 202, не 307)
  - GET  /api/v1/drafts/{id} — черновик создан и виден

Требует запущенных Docker-контейнеров с Gateway на :18080.
Пометка: @pytest.mark.integration — запуск только с --test-mode=real или -m integration.
"""

from __future__ import annotations

import io
import time
import pytest
import httpx

GATEWAY_URL = "http://127.0.0.1:18080/api/v1"
ADMIN_LOGIN = "admin@example.com"
ADMIN_PASSWORD = "Admin1234!"
TEST_FILE_CONTENT = b"%PDF-1.4 fake pdf for integration test"


@pytest.fixture
def ts():
    return str(int(time.time() * 1000000))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_draft_upload_full_chain(ts):
    """
    Сквозной тест загрузки черновика.

    1. Авторизация через Gateway
    2. Создание черновика с PDF-файлом → ждём 202
    3. Проверка, что получен draft_id
    4. GET черновика → проверить, что он существует
    """
    async with httpx.AsyncClient(timeout=15) as client:

        # ── 1. Авторизация ────────────────────────────────────────────────
        auth_resp = await client.post(
            f"{GATEWAY_URL}/auth/token",
            json={"username": ADMIN_LOGIN, "password": ADMIN_PASSWORD},
        )
        assert auth_resp.status_code == 200, (
            f"Auth failed: {auth_resp.status_code} {auth_resp.text[:200]}"
        )
        token_data = auth_resp.json()
        access_token = token_data.get("access_token")
        assert access_token, f"No access_token in response: {token_data}"
        headers = {"Authorization": f"Bearer {access_token}"}

        # ── 2. Создание черновика ─────────────────────────────────────────
        doc_key = f"int-test-draft-{ts}"
        file_obj = io.BytesIO(TEST_FILE_CONTENT)
        files = {"file": ("test.pdf", file_obj, "application/pdf")}
        data = {"source_type": "OTHER", "document_key": doc_key}

        draft_resp = await client.post(
            f"{GATEWAY_URL}/drafts",
            headers=headers,
            data=data,
            files=files,
        )

        # Должен быть 202, НЕ 307 (редирект из-за трейлинг-слеша)
        assert draft_resp.status_code == 202, (
            f"Draft creation failed: HTTP {draft_resp.status_code} "
            f"{draft_resp.text[:500]}"
        )

        draft_body = draft_resp.json()
        draft_id = draft_body.get("draft_id")
        task_id = draft_body.get("task_id")
        assert draft_id is not None, f"No draft_id in response: {draft_body}"
        assert task_id is not None, f"No task_id in response: {draft_body}"
        assert draft_body.get("status") == "uploaded"

        # ── 3. Проверка черновика через Registry ──────────────────────────
        get_resp = await client.get(
            f"{GATEWAY_URL}/drafts/{draft_id}",
            headers=headers,
        )
        assert get_resp.status_code == 200, (
            f"GET draft failed: HTTP {get_resp.status_code} "
            f"{get_resp.text[:300]}"
        )
        get_body = get_resp.json()
        # Registry может вернуть data-обёртку или прямой объект
        draft_data = get_body.get("data", get_body)
        assert str(draft_data.get("draft_id") or draft_data.get("id")) == str(draft_id), (
            f"Draft ID mismatch: {get_body}"
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_draft_upload_rejects_unsupported_format(ts):
    """
    Проверяет, что Gateway/Orchestrator отклоняет неподдерживаемый формат (400),
    а не редиректит (307) и не падает (500).
    """
    async with httpx.AsyncClient(timeout=15) as client:

        # Авторизация
        auth_resp = await client.post(
            f"{GATEWAY_URL}/auth/token",
            json={"username": ADMIN_LOGIN, "password": ADMIN_PASSWORD},
        )
        assert auth_resp.status_code == 200
        token = auth_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Отправляем .md файл — неподдерживаемый формат
        file_obj = io.BytesIO(b"# Test markdown")
        files = {"file": ("test.md", file_obj, "text/markdown")}
        data = {"source_type": "OTHER", "document_key": f"int-test-unsupported-{ts}"}

        resp = await client.post(
            f"{GATEWAY_URL}/drafts",
            headers=headers,
            data=data,
            files=files,
        )

        # Должен быть 400, не 307 и не 500
        assert resp.status_code == 400, (
            f"Expected 400 for unsupported format, got {resp.status_code}: "
            f"{resp.text[:300]}"
        )
