# План рефакторинга registry_client.py — статус выполнения

> **Дата:** 2026-06-08
> **Статус:** ✅ Выполнено

## 1. Переписать `registry_client.py` ✅
- [x] Добавить class-level `_SEED_DRAFTS` / `_SEED_DOCUMENTS` (иммутабельные seed-данные)
- [x] Добавить class-level `_storage` с runtime `drafts`, `documents`, `draft_seq`, `doc_seq`
- [x] Переписать `_generate_mock` — парсить method+endpoint без regex, использовать storage
- [x] Удалить `import re`
- [x] Каждая операция: успех → `{"data": ...}`, не найдено → `{"error": {"code": "NOT_FOUND"}}`
- [x] Seed draft_id=1 и document_id=1 для обратной совместимости
- [x] Runtime reads fall back to seed; deletes only remove runtime override (seed re-exposed)

## 2. Обновить эндпоинты (endpoints/drafts.py) ✅
- [x] `get_draft` — явная проверка `"error"` в ответе
- [x] `get_draft_preview` — явная проверка `"error"` в ответе
- [x] `delete_draft` — явная проверка `"error"` в ответе вместо исключения

## 3. Проверка тестами ✅
- [x] `tests/test_drafts.py` — 24/24 passed
- [x] `TestRegistryDrafts` — 10/10 passed
- [x] Интеграционные тесты — passed (46/48, 2 pre-existing failures в test_tasks.py)
- [x] Pre-existing failures не связаны с изменениями:
  - `test_service_clients_registry.py` — методы `list_classifiers`, `list_terminology`, `list_registry_documents`, `get_statistics`, `get_enums` не реализованы (тесты опережают код)
  - `test_tasks.py` — тест проверяет `"error" in data`, но FastAPI оборачивает в `"detail"`; второй тест не учитывает auth-fixture
