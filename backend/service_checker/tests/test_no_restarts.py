"""
Интеграционный тест — проверка что сервисы не крашатся и не перезапускаются.

Требует запущенных Docker-контейнеров с сервисами.
"""

import pytest
import httpx


def _count_starts_in_log() -> int:
    """Считать сколько раз сервис стартовал по логу supervisor.

    Сначала пробует прямой путь (внутри Docker).
    Если нет — через docker exec (с хоста).
    """
    # Прямой доступ (внутри контейнера)
    for path in ["/var/log/supervisor/auth.err", "/var/log/supervisor/auth.log"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().count("Started server process")
        except (FileNotFoundError, IOError):
            pass

    # Через docker exec (с хоста)
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "exec", "pkb-neuro", "cat", "/var/log/supervisor/auth.err"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.count("Started server process")
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    return -1


async def _try_get_refresh_token(client: httpx.AsyncClient) -> str | None:
    """Попробовать получить refresh_token через /auth/token."""
    for creds in [
        {"username": "petrova@example.com", "password": "secret456"},
        {"username": "admin@example.com", "password": "admin123"},
    ]:
        resp = await client.post(
            "http://127.0.0.1:18082/api/v1/auth/token",
            json=creds,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Прямая обёртка или data.refresh_token
            token = data.get("refresh_token")
            if token:
                return token
            inner = data.get("data", {})
            token = inner.get("refresh_token")
            if token:
                return token
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_refresh_does_not_crash_service():
    """
    1. Считаем старты в логе /var/log/supervisor/auth.err
    2. Вызываем /auth/refresh (с реальным или невалидным токеном)
    3. Проверяем что сервис вернул 200/401 (не краш 500)
    4. Считаем старты снова — число не должно вырасти
    5. Проверяем что сервис жив (health check после вызова)
    """
    async with httpx.AsyncClient(timeout=10) as client:

        # Пробуем получить реальный refresh_token
        refresh_token = await _try_get_refresh_token(client)

        if refresh_token:
            token_source = "реальный"
        else:
            token_source = "невалидный (сервис не выдал токен)"
            refresh_token = "test-invalid-token"

        # Считаем старты ДО вызова
        starts_before = _count_starts_in_log()

        # Вызываем /auth/refresh — именно он раньше крашил сервис
        refresh_resp = await client.post(
            "http://127.0.0.1:18082/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Считаем старты ПОСЛЕ вызова
        starts_after = _count_starts_in_log()

        # Проверка статуса — сервис не должен упасть
        assert refresh_resp.status_code in (200, 401), (
            f"/auth/refresh ({token_source}) вернул {refresh_resp.status_code}, "
            f"ожидался 200 или 401. Тело: {refresh_resp.text[:300]}"
        )

        # Если 401 — ответ должен быть JSON с detail или error.code/error.message
        if refresh_resp.status_code == 401:
            try:
                err_data = refresh_resp.json()
            except Exception:
                pytest.fail(
                    f"401 ответ ({token_source}) должен быть JSON: "
                    f"{refresh_resp.text[:200]}"
                )
            has_detail = "detail" in err_data
            has_error = isinstance(err_data.get("error"), dict) and "code" in err_data["error"]
            assert has_detail or has_error, (
                f"401 ответ ({token_source}) должен содержать 'detail' или 'error.code': {err_data}"
            )

        # Проверка что не было рестартов (если доступен лог)
        if starts_before >= 0 and starts_after >= 0:
            assert starts_after == starts_before, (
                f"Auth Service перезапустился после /auth/refresh ({token_source})! "
                f"Было {starts_before} стартов, стало {starts_after}. "
                f"HTTP {refresh_resp.status_code}"
            )
        else:
            # Лог недоступен — проверяем через health check
            health_resp = await client.get(
                "http://127.0.0.1:18082/api/v1/health",
            )
            assert health_resp.status_code < 500, (
                f"Auth Service упал после /auth/refresh ({token_source})! "
                f"Health check: {health_resp.status_code}"
            )
