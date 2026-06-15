# Todo: Синхронизация API с пайплайнами (финальная проверка)

## Задачи

Все пункты выполнены ✅

## Правки

### C1 — 🔴 `db_diagrams.md`: типы секций
- [x] Исправить описание `section` → `text` и дополнить список актуальными типами из JSON-схемы

### C2 — 🔴 `converter_validator_service_api.md`: удалить `document_id`
- [x] Удалить `document_id` из JSON-примера ответа `POST /converter/convert`
- [x] Удалить `document_id` из таблицы полей

### C3 — 🟡 `orchestrator_service_api.md`: убрать `version_id` из `POST /drafts`
- [x] Удалить `version_id` из JSON-примера ответа
- [x] `version_id` в таблице полей ответа отсутствовала — только в JSON

### C4 — 🟡 `orchestrator_service_api.md` + `common_api.md`: удалить `POST /documents/{doc_id}/approve`
- [x] Удалить секцию `POST /documents/{doc_id}/approve` из orchestrator_service_api.md
- [x] Удалить строку `approve` из RBAC-матрицы в common_api.md

### C5 — 🟡 `query_service_api.md` + `rag_search_service_api.md`: добавить `confidence` в цепочку
- [x] `confidence` в RAG Search — остаётся
- [x] Добавить `confidence` в `sources[]` Query API (ответы чата + `/text/search`)
- [x] Добавить `confidence` в таблицу именования полей источников

### C6 — 🟡 `db_diagrams.md`: CHECK для `chat.messages.status`
- [x] Добавить CHECK-constraint для `chat.messages.status`
- [x] Убрать `idle` из описания (виртуальный статус)

### C7 — 🟡 `overview.md`: маппинг статусных моделей
- [x] Добавить таблицу маппинга трёхуровневой статусной модели (DB/Task/UI)

### C8 — 🟡 `common_api.md`: RBAC
- [x] Удалить строку `POST /documents/{doc_id}/approve` из RBAC-матрицы (в C4)

### Дополнительно
- [x] `specificity.md`: обновлён статус LP-C2 (document_id в Converter) на 🔄 исправлено
