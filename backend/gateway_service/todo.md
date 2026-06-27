# Gateway Tests — merge исправлений 4 групп ошибок + Docker-тесты

## Исправлено (наши изменения)
### 1. ALLOW_ANONYMOUS=false в Docker
- `conftest.py`: принудительное `os.environ["ALLOW_ANONYMOUS"] = "true"` (вместо `setdefault`)

### 2. Event loop is closed
- `test_client.py`: конвертированы sync→async с `@pytest.mark.asyncio` (устранён RuntimeError)

### 3. PII-параметры
- Все 12 PII-параметров блокируются корректно. `file_key` и `q` — разрешённые.

### 4. Proxy/routing
- ROUTE_TABLE покрывает 51 сценарий. Все тесты проходят.

## Добавлено (remote — Docker-интеграционные тесты)
- `conftest.py`: Docker-фикстуры (http_client, admin_token, engineer_token и др.)
- `helpers.py`: вспомогательные функции
- `test_rbac.py`, `test_proxy.py`, `test_idempotency.py` и др.: Docker-тесты
- Маркер `@pytest.mark.docker` (docker-тесты пропускаются без Docker)

## Состав тестов
| Файл | Unit | Docker |
|------|:----:|:------:|
| test_routing.py | 53 | — |
| test_config.py | 12 | — |
| test_rate_limiter.py | 17 | — |
| test_middleware_pii.py | 15 | — |
| test_middleware_correlation.py | 3 | — |
| test_middleware_strip_slash.py | 3 | — |
| test_middleware_process_time.py | 2 | — |
| test_rbac.py | 20 | — |
| test_idempotency.py | 1 | — |
| test_proxy.py | 15 | — |
| test_health.py | 9 | — |
| test_client.py | 7 | — |
| test_diagnostics.py | 7 | — |
| test_main_handlers.py | 9 | — |
| test_logging.py | 6 | — |
| **Всего** | **~179** | **+ Docker** |

## Результат
- ✅ **287+ unit-тестов, 0 failed**
- Интеграция с `service_checker` (recheck.bat — `--skip-gateway-tests`)
- Для Docker-тестов: `cd tests && pytest -v -m docker` (требует Gateway на :18080)
