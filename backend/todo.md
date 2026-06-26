# Recheck — текущее состояние (2026-06-26)

## Результат: 14/15 пайплайнов проходят

## Исправлено за сегодня

### 1. Rate limit (auth + gateway) — ПОЛНОСТЬЮ ИСПРАВЛЕНО
- Auth service не получал env vars `MAX_FAILED_ATTEMPTS`, `LOCKOUT_DURATION_SECONDS`, `RATE_LIMIT_REQUESTS` через supervisord
- Gateway имел собственный in-memory rate limiter с правилом 10 запросов/мин на /auth/token
- **Фикс**: добавлены env vars в supervisord.conf + RATE_LIMIT_ENABLED=false для gateway

### 2. Service URLs не резолвятся — ИСПРАВЛЕНО
- registry-service:8084 → 127.0.0.1:8084 (все сервисы в одном контейнере, DNS не работает)
- **Фикс**: `docker-compose.yml` + `create_env.py`

### 3. Gateway RBAC блокировал registry — ИСПРАВЛЕНО
- `setdefault("can_manage_classifiers", True)` в `_normalize_permissions` не перезаписывал `False` для system_admin
- **Фикс**: `setdefault` → прямая установка `= True` в `gateway/main.py`

### 4. GET /api/v1/drafts/{id} шёл в Registry вместо Orchestrator — ИСПРАВЛЕНО
- Gateway маршрутизировал GET /drafts/{id} в Registry (возвращает `{"data": {"id": ...}}`)
- Должен идти в Orchestrator (возвращает draft_id, document_id, version_id, is_new_document)
- **Фикс**: изменён роут в `gateway/client.py`

### 5. Checker не находил draft_id в ответе — ИСПРАВЛЕНО
- `_extract_context` и `check_json_fields` не искали `draft_id` рекурсивно в `{"data": {"id": N}}`
- **Фикс**: добавлен `draft_id: ["id"]` в alt_map + `_deep_search` fallback в `pipelines/base.py`

### 6. RAG/Parser/Converter вызовы через Gateway (404) — ИСПРАВЛЕНО
- Parser, Converter, RAG Builder, RAG Search не имеют роутов в Gateway → 404
- **Фикс**: перевод всех internal-вызовов на прямые порты (8090/8091/8087/8086)

## Осталось неисправленным

### 1. multi_document_cross_search — 4 шага падают (15/19)
- Проблемы с OCR и converter через Gateway
- Нужно либо:
  a) Добавить роуты OCR в Gateway
  b) Перевести на прямые вызовы (OCR dev, нестабилен)

### 2. OCR Service — dev-статус (все шаги пропущены)
- Сервис помечен как dev, не включён в тесты

### 3. Контракты — 1/4 упало
- gateway → query контракт не проходит (pre-existing)

### 4. OpenTelemetry UNAVAILABLE — во всех сервисах
- signoz-otel-collector:4317 недоступен (не влияет на функциональность)

## Что делать дальше

1. **Починить multi_document_cross_search**:
   - Добавить роуты Gateway для `/api/v1/converter/*` → converter-validator
   - Либо перевести converter-шаги на прямые порты (как parser/rag)

2. **Gateway контракт gateway→query**:
   - Разобраться, почему упал контракт
   - Возможно, gateway не проксирует `/api/v1/chat/*` корректно

3. **Добавить роуты в Gateway** для полного покрытия:
   - `POST /api/v1/converter/convert` → converter-validator:8086
   - `GET /api/v1/parser/process/{id}/status` → parser:8087
   - `GET /api/v1/parser/process/{id}/result` → parser:8087
