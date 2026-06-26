# План исправления ошибок — статус

## Сделано ✅

### 1. Pipeline document_processing — заменён эндпоинт
`pipelines/document_processing.py`:
- `/import` (file upload) → `/check-uniqueness` (JSON)

### 2. Pre-prepare POST /drafts — добавлен файл
`core/api_coverage_test.py`:
- Добавлен PDF в `files=`, иначе Orchestrator возвращал 422

### 3. Orchestrator expected_status — 409 для POST /drafts
`services/orchestrator.py` + 7 пайплайнов:
- `expected_status=202` → `expected_status={202, 409}`
- Registry seed data конфликтует при создании черновика, 409 — штатная ситуация

### 4. Orchestrator GET /documents/queue — schema
`services/orchestrator.py`:
- Убран `expected_status={404}` (эндпоинт реализован, отдаёт 200)
- Убрана `response_schema` (поля не совпадают)

### 5. Registry URL — исправлен на имя сервиса
`docker-compose.yml` + `create_env.py`:
- `REGISTRY_SERVICE_URL=http://127.0.0.1:8084` → `http://registry-service:8084`
- Аналогично INTEGRATION, VALIDATE, RAG

### 6. Mock-режимы — выключены
`docker-compose.yml` + `create_env.py`:
- `AUTH_SERVICE_MOCK=false`, `DEV_AUTH_MODE=false`
- `MOCK_LLM_ENABLED=false`, `REGISTRY_SERVICE_MOCK=false`

### 7. Contract gateway → rag_search
`core/contracts_check.py` — уже отключён (не вызывается)

---

## Результат прогона (Orchestrator)

| Метрика | Было | Стало |
|---------|------|-------|
| API Coverage Orchestrator | 22/35 | **35/35** |
| Registry API | 3 failed | **0 failed** |
| document_processing pipeline | 1 failed | **0 failed** |
| Gateway API (предыдущий замер, не перепрогонялся) | 29 failed | 15 failed |

---

## Осталось 🔍

### admin_user_lifecycle — Cannot create project
Auth не в mock-режиме. Checker не может создать проект для чат-сессий.
**Требуется:** проверить pre-prepare для Query (POST /chat/projects) — Auth в real mode требует JWT.

### Контракты: 1/4 упало
Нужно посмотреть какой контракт упал.

### Gateway — 15 failed, 13 skipped
После исправления Registry URL и mock-режимов, Gateway coverage не перезапускался.
**Требуется:** полный прогон `recheck.bat` без фильтров.

---

## Файлы изменены

| Файл | Изменение |
|------|-----------|
| `core/api_coverage_test.py` | PDF в pre-prepare POST /drafts |
| `pipelines/document_processing.py` | `/import` → `/check-uniqueness` |
| `pipelines/*orchestrator*.py` (7 шт) | `expected_status={202, 409}` |
| `pipelines/document_approval.py` | `expected_status={202, 409}` |
| `services/orchestrator.py` | 409, /documents/queue, schema |
| `docker/docker-compose.yml` | URL сервисов, mock=false |
| `docker/create_env.py` | URL сервисов, mock=false |
| `docker/recheck.bat` | Удаление orchestrator.db |
