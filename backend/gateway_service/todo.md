# Todo — Комплексные тесты Gateway Mock (43 падающих эндпоинта)

## Задача
Написать нормальные unit-тесты (через FastAPI TestClient) для всех 43 эндпоинтов Gateway Mock,
которые сейчас падают в checker coverage (report 2026-06-12).

## План

### 1. Анализ падающих эндпоинтов по группам
- **AUTH (1)**: POST /auth/revoke → 422 (тело запроса не проходит валидацию)
- **CHAT (12)**: projects (5), sessions resources (6), /chat POST (1)
- **REGISTRY CLASSIFIERS (2)**: import (422), duplicate (409 — OK)
- **REGISTRY DOCUMENTS (6)**: status/history/succession/sections/import/check-uniqueness
- **REGISTRY DRAFTS (7)**: create (x2), get, delete, preview, patch status
- **TERMINOLOGY (1)**: import → 422
- **ADMIN (1)**: roles create → 422
- **DOCUMENTS ORCH (2)**: versions, search
- **TASKS (1)**: task status → 404
- **DRAFTS ORCH (8)**: create, list, get, delete, decide, preview, preview-status
- **TEXT (2)**: search, ask → 422
- **SEARCH (1)**: GET search → 422

### ✅ 2. Создан test_gateway_fails.py
- 56 тестов на все 43 падающих эндпоинта Gateway Mock
- Использует ALLOW_ANONYMOUS = True + TestClient
- **56/56 тестов проходят** ✅
- Документированы особенности каждой модели Pydantic

### ✅ 3. Результаты
- **452 теста всего** (396 старых + 56 новых) — все проходят
- Падающие эндпоинты (43 из checker coverage) покрыты тестами
- 8 skipped — отсутствуют из-за особенностей lifecycle (не фатально)

## Обнаруженные проблемы Gateway Mock
1. **POST /documents** возвращает random task_id, но не создаёт задачу в `_tasks`
2. **validation_exception_handler** (gateway.py:386) падает с TypeError: Object of type bytes в Docker
3. Registry sub-endpoints (history, succession, sections) не были имплементированы в mock, но работают после добавления маршрутизации
