# Recheck — текущее состояние (2026-06-26)

## Результат: все сервисы проходят

## Исправлено за сегодня

### 1. Rate limit (auth + gateway) — ИСПРАВЛЕНО
### 2. Service URLs не резолвятся — ИСПРАВЛЕНО
### 3. Gateway RBAC блокировал registry — ИСПРАВЛЕНО
### 4. GET /api/v1/drafts/{id} шёл в Registry вместо Orchestrator — ИСПРАВЛЕНО
### 5. Checker не находил draft_id в ответе — ИСПРАВЛЕНО
### 6. Parser/Converter/RAG через Gateway (404) — ИСПРАВЛЕНО
### 7. OTEL timeout (grpc UNAVAILABLE) — ИСПРАВЛЕНО
### 8. Port shift +10000 — ВЫПОЛНЕНО
### 9. Orchestrator 10 skipped — ИСПРАВЛЕНО
- Причина: prepare POST /drafts/ (с трейлинг-слешем) → 307 redirect, draft_id не извлекался
- Фикс: `/api/v1/drafts/` → `/api/v1/drafts` в `services/orchestrator.py`
### 10. Query RuntimeError — ИСПРАВЛЕНО
- Причина: context.clear() стирал access_token, Query pre-prepare не мог аутентифицироваться
- Фикс: автополучение токена в pre-prepare Query в `core/api_coverage_test.py`
### 11. Gateway→query контракт — ИСПРАВЛЕНО
- Причина: check_gateway_to_query() не слал JWT, RBACMiddleware блокировал
- Фикс: получение токена + extra_headers в `core/contracts_check.py`
### 12. Service URLs в Docker env — ИСПРАВЛЕНО
- Причина: port shift задел service URLs внутри контейнера (18084 вместо 8084)
- Фикс: возвращены внутренние порты в `docker-compose.yml`, `create_env.py`, `docker-compose-web.yml`

## Осталось (pre-existing):
- Registry: 3 known issues (trailing slash, internal API)
- Gateway: mock/реальный несоответствия
- OCR: dev-статус
- parser_service: OTEL без try/except (требует доработки разработчиком)
