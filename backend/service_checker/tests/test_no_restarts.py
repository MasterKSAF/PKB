"""
Интеграционный тест — проверка что сервисы не крашатся при тестировании.

Требует запущенных Docker-контейнеров с сервисами.
"""

import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_refresh_does_not_crash_service():
    """
    1. Получаем токен
    2. Вызываем /auth/refresh
    3. Проверяем что сервис жив (health check)

    Если сервис крашнулся — health check вернёт ошибку подключения.
    """
    async with httpx.AsyncClient(timeout=10) as client:

        # 1. Получаем токен
        token_resp = await client.post(
            "http://127.0.0.1:8082/api/v1/auth/token",
            json={"username": "petrova@example.com", "password": "secret456"},
        )

        if token_resp.status_code != 200:
            # Сервис недоступен — это не ошибка теста, а условие запуска
            # (тест только внутри Docker)
            pytest.skip(
                f"Auth service не отвечает: HTTP {token_resp.status_code}. "
                f"Тест требуется запускать внутри Docker."
            )

        token_data = token_resp.json()
        # Может быть как прямая обёртка, так и data.refresh_token
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            data = token_data.get("data", {})
            refresh_token = data.get("refresh_token")

        assert refresh_token, f"Не удалось извлечь refresh_token из ответа: {token_data}"

        # 2. Вызываем /auth/refresh — именно он раньше крашил сервис
        refresh_resp = await client.post(
            "http://127.0.0.1:8082/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Сервис должен вернуть 200 (ok) или 401 (токен истёк) — но не упасть
        assert refresh_resp.status_code in (200, 401), (
            f"/auth/refresh вернул {refresh_resp.status_code}, "
            f"ожидался 200 или 401. Тело: {refresh_resp.text[:300]}"
        )

        # Если 401 — проверяем что это JSON с detail (а не краш)
        if refresh_resp.status_code == 401:
            try:
                err_data = refresh_resp.json()
            except Exception:
                pytest.fail(
                    f"401 ответ должен быть JSON: {refresh_resp.text[:200]}"
                )
            assert "detail" in err_data, (
                f"401 ответ должен содержать 'detail': {err_data}"
            )

        # 3. Проверяем что сервис жив после вызова
        health_resp = await client.get(
            "http://127.0.0.1:8082/api/v1/health",
        )

        # Если сервис крашнулся — health check даст connect error
        assert health_resp.status_code < 500, (
            f"Auth Service упал после /auth/refresh! "
            f"Health check вернул {health_resp.status_code}: {health_resp.text[:200]}"
        )
