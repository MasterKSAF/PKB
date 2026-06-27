# Выполнено: Gateway Tests — 287 тестов (fix 4 групп ошибок)

## Исправления

### 1. ALLOW_ANONYMOUS=false в Docker
- `conftest.py`: замена `setdefault("ALLOW_ANONYMOUS", "true")` на принудительное
  `os.environ["ALLOW_ANONYMOUS"] = "true"` — тесты теперь работают независимо
  от окружения (Docker/локально).

### 2. Event loop is closed
- `test_client.py`: конвертированы sync-тесты с ручным
  `asyncio.get_event_loop().run_until_complete()` в async-тесты
  с `@pytest.mark.asyncio` — устранён `RuntimeError('Event loop is closed')`.

### 3. PII-параметры — проверка
- Middleware `PIIQueryValidatorMiddleware` корректно блокирует все 12 PII-параметров
  (password, email, access_token, refresh_token, api_key, apikey, secret_key,
  phone, passport, inn, snils, ogrn).
- `file_key` и `q` не блокируются — это разрешённые параметры (тесты проходят).

### 4. Proxy/routing — проверка
- ROUTE_TABLE полностью покрывает 51 тестовый сценарий resolve_service().
- Все тесты маршрутизации и проксирования проходят.

## Результат
- ✅ **287 passed, 0 failed** (26.22s)
- Обновлены: specificity.md, guide.md, readme.md
