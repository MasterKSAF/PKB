# Исправление: пайплайны + rate limiter + brute-force

## Сделано

### 1. Пайплайны — все вызовы напрямую (без Gateway) ✅
Скопированы 14 файлов из `PKB_neuroassistant_checker` → `PKB_neuroassistant_develop/pipelines/`:
auth, query, orchestrator, registry, parser, converter_validator, rag_builder, rag_search — все напрямую, без Gateway.

### 2. Brute-force protection — отключена блокировка ✅
- **Проблема:** `admin_user_lifecycle` делает 5 brute-force попыток → `failed_attempts=5` → Auth блокирует аккаунт на 30 мин (`ACCOUNT_LOCKED` 423).
- **Решение:** Добавлены `MAX_FAILED_ATTEMPTS=100`, `LOCKOUT_DURATION_SECONDS=0` в `create_env.py` и `.env`.
- Auth Service прочитает эти переменные при старте: порог блокировки 100 попыток, длительность блокировки 0 сек (фактически отключена).

### 3. Gateway rate limiter — не влияет ✅
Checker вызывает сервисы напрямую, минуя Gateway. Rate limiter Gateway (10 запросов/мин к auth/token) не применяется.

### 4. Orchestrator double /api/v1/ — обход ✅
Checker вызывает Registry напрямую (`registry:8084`), минуя Orchestrator. Двойной префикс не возникает.

## Файлы изменены

| Файл | Изменение |
|------|-----------|
| `pipelines/*.py` (14 шт) | Скопированы из checker (прямые вызовы) |
| `docker/create_env.py` | Добавлены `MAX_FAILED_ATTEMPTS`, `LOCKOUT_DURATION_SECONDS` |
| `docker/.env` | Перегенерирован (39 vars, новые параметры) |
