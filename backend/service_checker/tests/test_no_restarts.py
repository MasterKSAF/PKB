"""
Интеграционный тест — проверка что сервисы не перезапускаются при тестировании.

Требует запущенных Docker-контейнеров с сервисами.
"""

import pytest
import httpx


def _count_starts_in_log(service_log_path: str) -> int:
    """Считать сколько раз сервис стартовал по логу supervisor."""
    try:
        with open(service_log_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content.count("Started server process")
    except (FileNotFoundError, IOError):
        return -1  # лог недоступен


@pytest.mark.integration
@pytest.mark.asyncio
async def test_auth_no_restart_after_refresh():
    """
    POST /auth/refresh не должен вызывать перезапуск Auth Service.
    Считаем старты в логе до и после запроса — число не должно вырасти.
    """
    # Путь к логу auth сервиса (внутри Docker volume или на хосте)
    log_path = "/var/log/supervisor/auth.err"

    starts_before = _count_starts_in_log(log_path)
    if starts_before == -1:
        pytest.skip(f"Лог не найден: {log_path}. Тест только в Docker.")

    # Выполняем запрос на обновление токена
    async with httpx.AsyncClient(timeout=10) as client:
        # Получаем токен
        token_resp = await client.post(
            "http://127.0.0.1:8082/api/v1/auth/token",
            json={"username": "petrova@example.com", "password": "secret456"},
        )
        if token_resp.status_code != 200:
            pytest.skip(f"Auth service недоступен: {token_resp.status_code}")

        data = token_resp.json()
        refresh_token = data.get("refresh_token") or data.get("data", {}).get("refresh_token")

        if not refresh_token:
            pytest.skip("Не удалось получить refresh_token")

        # Вызываем refresh
        refresh_resp = await client.post(
            "http://127.0.0.1:8082/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    starts_after = _count_starts_in_log(log_path)

    # Проверяем что сервис НЕ перезапустился
    assert starts_after == starts_before, (
        f"Auth Service перезапустился после /auth/refresh! "
        f"Было {starts_before} стартов, стало {starts_after}. "
        f"Ответ: HTTP {refresh_resp.status_code}"
    )



