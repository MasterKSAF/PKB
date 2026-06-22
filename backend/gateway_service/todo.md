# Правки по проблемам API

## Основные проблемы (из таблицы)
- [x] **POST /chat/sessions/{session_id}/messages/search** → 405 — эндпоинт отсутствовал, добавлен
- [x] **POST /registry/documents/import** → 400/500 — добавлен парсинг CSV/XLSX, mode create/update/upsert
- [x] **POST /drafts/** → 400 — добавлен путь со слешем `/drafts/`
- [x] **POST .../messages** → 422 — добавлен fallback на form-data

## Дополнительно (обнаружено по ходу)
- [x] **POST /auth/login** — отсутствовал (только `/auth/token`), добавлен алиас
- [x] **pending_id** — файловый импорт `/classifiers/import` теперь создаёт pending в карантине вместо прямой вставки (checker-совместимость)
- [x] **Порт mock-gateway** — 8081 конфликтовал с Orchestrator, переведён на 8099
- [x] **MOCK_PORT константа** — вынесена в `mocks/common.py` (единая точка)
- [x] **test_91_update_registry_doc** — падал с 422 (`jurisdiction='RF'` невалиден), добавлен `RF` в `VALID_JURISDICTIONS`
- [x] **jurisdiction enums** — код и документация синхронизированы (RU, RF, BY, KZ, AM, KG, OTHER, INTERNATIONAL)
- [x] **rule в guide.md** — добавлено: Checker исправляет проблему на своей стороне сразу

## Документация
- [x] README.md — порт mock 8081→8099 (5 вхождений)
- [x] auth_service_api.md — путь `/auth/token` → `/auth/login`
- [x] registry_service_api.md — jurisdiction enums синхронизированы
- [x] specificy.md — запись об аномалии test_91 + изменения

## Новые эндпоинты (22.06)
- [x] **POST /pending/{id}/accept** — bare-алиас (без /classifiers/) в mock Registry
- [x] **POST /pending/{id}/reject** — bare-алиас (без /classifiers/) в mock Registry
- [x] **POST /api/v1/rag/search** — Gateway proxy-маршрут (`/api/v1/rag/` → rag_search)
- [x] **POST /rag/search** — mock-обработчик RAG Search (mocks/handlers/rag_search_routes.py)
- [x] Gateway routing table docs — обновлена gateway_service_api.md
- [x] Тесты — 11 новых (bare pending + rag search + resolve_service)
