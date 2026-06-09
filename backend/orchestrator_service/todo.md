# План исправления ошибки ValidationError в Settings — ВЫПОЛНЕНО

## Проблема
В Docker окружении передаются env-переменные:
- `AUTH_SERVICE_URL=http://127.0.0.1:8082`
- `AUTH_SERVICE_MOCK=True`
- `REGISTRY_SERVICE_URL=http://127.0.0.1:8084`
- `REGISTRY_SERVICE_MOCK=True`

Pydantic `Settings` класс содержит вложенную модель `services: ServiceConfig`, и использует `env_nested_delimiter="__"`. 
Плоские env-переменные (без префикса `SERVICES__`) не маппятся на поля `Settings` и отбрасываются как "extra inputs".

`AUTH_SERVICE_*` не добавлены в модель — оркестратор не использует Auth Service напрямую
(всегда mock в `app/api/deps/__init__.py`), с `extra='ignore'` они просто игнорируются.

## Что сделано

| Шаг | Файл | Статус |
|-----|------|--------|
| 1. Добавлен `extra='ignore'` в `Settings.model_config` | `app/core/config.py` | ✅ |
| 2. `services` и `pipeline` переведены на `default_factory=` | `app/core/config.py` | ✅ |
| 3. Обновлены тесты (flat env vars) | `tests/test_config.py` | ✅ |
| 4. Аномалия зафиксирована в `specificity.md` | `specificity.md` | ✅ |
| 5. Тесты пройдены (349 passed, 0 failed) | - | ✅ |
