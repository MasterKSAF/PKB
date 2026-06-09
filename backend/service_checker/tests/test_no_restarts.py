"""
Интеграционный тест — проверка что сервисы не крашатся и не перезапускаются.

Требует запущенных Docker-контейнеров с сервисами.
"""

import pytest
import httpx


def _count_starts_in_log(log_path: str) -> int:
    """Считать сколько раз сервис стартовал по логу supervisor."""
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return f.read().count("Started server process")
    except (FileNotFoundError, IOError):
        return -1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_refresh_does_not_crash_service():
    """
    1. Считаем старты в логе /var/log/supervisor/auth.err
    2. Получаем токен
    3. Вызываем /auth/refresh
    4. Проверяем что сервис вернул 200/401 (не краш)
    5. Считаем старты снова — число не должно вырасти
    6. Проверяем что сервис жив (health check)
    """
    log_path = "/var/log/supervisor/auth.err"

    async with httpx.AsyncClient(timeout=10) as client:

        # 1. Получаем токен
        token_resp = await client.post(
            "http://127.0.0.1:8082/api/v1/auth/token",
            json={"username": "petrova@example.com", "password": "secret456"},
        )

        if token_resp.status_code != 200:
            pytest.skip(
                f"Auth service не отвечает: HTTP {token_resp.status_code}. "
                f"Тест требуется запускать внутри Docker."
            )

        token_data = token_resp.json()
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            data = token_data.get("data", {})
            refresh_token = data.get("refresh_token")

        assert refresh_token, f"Не удалось извлечь refresh_token: {token_data}"

        # Считаем старты ДО вызова
        starts_before = _count_starts_in_log(log_path)

        # 2. Вызываем /auth/refresh — именно он раньше крашил сервис
        refresh_resp = await client.post(
            "http://127.0.0.1:8082/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Считаем старты ПОСЛЕ вызова
        starts_after = _count_starts_in_log(log_path)

        # 3. Проверка статуса — сервис не должен упасть
        assert refresh_resp.status_code in (200, 401), (
            f"/auth/refresh вернул {refresh_resp.status_code}, "
            f"ожидался 200 или 401. Тело: {refresh_resp.text[:300]}"
        )

        # 4. Если 401 — ответ должен быть JSON с detail
        if refresh_resp.status_code == 401:
            try:
                err_data = refresh_resp.json()
            except Exception:
                pytest.fail(f"401 ответ должен быть JSON: {refresh_resp.text[:200]}")
            assert "detail" in err_data, f"401 ответ должен содержать 'detail': {err_data}"

        # 5. Проверка что не было рестартов (если доступен лог)
        if starts_before >= 0 and starts_after >= 0:
            assert starts_after == starts_before, (
                f"Auth Service перезапустился после /auth/refresh! "
                f"Было {starts_before} стартов, стало {starts_after}. "
                f"HTTP {refresh_resp.status_code}"
            )
        else:
            # Лог недоступен — проверяем через health check
            health_resp = await client.get(
                "http://127.0.0.1:8082/api/v1/health",
            )
            assert health_resp.status_code < 500, (
                f"Auth Service упал после /auth/refresh! "
                f"Health check: {health_resp.status_code}"
            )
