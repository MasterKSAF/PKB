# Завершено: Gateway Integration Tests

## Что сделано
- Создана директория `backend/gateway_service/tests/` с 15 тестовыми файлами
- Создан `conftest.py` с фикстурами для unit- и Docker-тестов
- Создан `helpers.py` с вспомогательными функциями
- Все unit-тесты проходят (168 шт.)

## Список файлов
| Файл | Описание | Тестов (unit/Docker) |
|------|----------|---------------------|
| `test_routing.py` | resolve_service + ROUTE_TABLE (51 сценарий) | 53 / 0 |
| `test_config.py` | GatewayConfig validation (8 сценариев) | 12 / 0 |
| `test_rate_limiter.py` | rate_limiter + IDOR protection | 17 / 0 |
| `test_middleware_pii.py` | PIIQueryValidatorMiddleware | 12 / 17 |
| `test_middleware_correlation.py` | CorrelationHeadersMiddleware | 4 / 2 |
| `test_middleware_strip_slash.py` | StripTrailingSlashMiddleware | 4 / 2 |
| `test_middleware_process_time.py` | ProcessTimeMiddleware | 3 / 2 |
| `test_rbac.py` | RBACMiddleware | 0 / 14 |
| `test_idempotency.py` | IdempotencyMiddleware | 0 / 5 |
| `test_proxy.py` | proxy_request | 0 / 12 |
| `test_health.py` | check_service_health | 7 / 4 |
| `test_client.py` | get_client / is_deprecated_integration_route | 13 / 0 |
| `test_diagnostics.py` | diagnostics | 10 / 0 |
| `test_main_handlers.py` | собственные эндпоинты Gateway | 5 / 7 |
| `test_logging.py` | JSONLogFormatter, PII-маскировка | 12 / 0 |

## Интеграция с service_checker
- Добавлена функция `_docker_run_gateway_tests()` в `docker.py`
- Добавлены флаги `--skip-gateway-tests` / `--gateway-tests` в `cli.py`
- Gateway-тесты запускаются как часть `full-report`
- `recheck.bat` поддерживает `--skip-gateway-tests`

## Как запускать
1. Unit-тесты (без Docker): `python -m pytest tests/ -v -m "not docker"`
2. Все тесты (с Docker): `python -m pytest tests/ -v`
3. Через recheck.bat: `recheck.bat` (запускается как часть full-report)
