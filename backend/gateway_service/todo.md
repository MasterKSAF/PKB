# Выполнено: Gateway Tests — 281 тест

## Итого

- Создана новая тестовая директория `tests/`
- 16 файлов тестов
- **281 тест, все проходят**

## Структура новых тестов

| Файл | Описание | Тип |
|------|----------|-----|
| `tests/conftest.py` | Фикстуры: TestClient, mock_auth, mock_httpx, seed-данные | Инфраструктура |
| `tests/test_routing.py` | resolve_service() — 51+ сценарий (полное покрытие ROUTE_TABLE) | ✅ LOCAL |
| `tests/test_config.py` | GatewayConfig — валидация mode, env, CORS, service_urls | ✅ LOCAL |
| `tests/test_rate_limiter.py` | InMemoryRateLimiter, _match_rule, IDOR, THROTTLED | ✅ LOCAL |
| `tests/test_middleware_pii.py` | PIIQueryValidatorMiddleware — 12 PII-параметров → 400 | ✅ LOCAL |
| `tests/test_middleware_correlation.py` | X-Request-ID, X-Trace-ID генерация/проброс | ✅ LOCAL |
| `tests/test_middleware_strip_slash.py` | StripTrailingSlashMiddleware — path normalization | ✅ LOCAL |
| `tests/test_middleware_process_time.py` | X-Process-Time header | ✅ LOCAL |
| `tests/test_rbac.py` | RBACMiddleware — 20+ сценариев (мок `_validate_token_remotely`) | ⚠️ LOCAL (мок) |
| `tests/test_idempotency.py` | IdempotencyMiddleware — кеш, TTL, cleanup | ✅ LOCAL |
| `tests/test_proxy.py` | proxy_request — 200/502/504, headers, статус коды | ⚠️ LOCAL (мок) |
| `tests/test_health.py` | check_service_health, check_all_services_health | ⚠️ LOCAL (мок) |
| `tests/test_client.py` | get_client/close_client/is_deprecated_integration_route | ✅ LOCAL |
| `tests/test_logging.py` | JSONLogFormatter, PII masking, _parse_pii_fields | ✅ LOCAL |
| `tests/test_main_handlers.py` | /health, /mode, /metrics, error handlers | ✅ LOCAL |
| `tests/test_diagnostics.py` | KNOWN_SERVICES, START_TIME, build_summary (базовое) | ❌ INTEGRATION |

## Ключевые изменения кода

- Добавлен `pytest-asyncio` в `requirements.txt`
- Создан `pytest.ini` с `asyncio_mode = auto`
- `conftest.py` настроен: ALLOW_ANONYMOUS=True, RATE_LIMIT_ENABLED=0, лог на CRITICAL
