# todo — синхронизация документации (внутренние расхождения)

> Все пункты, не требующие доступа к коду, выполнены.

---

## 🔴 Приоритет 1 (критичные)

### T1. `pipeline1-formation.md` — нет `title_key` в preview-метаданных
✅ **Сделано** — добавлено поле `title_key` в JSON-пример.

### T2. Health-формат не унифицирован
✅ **Сделано** — решение в `guide.md`. `uptime_seconds` убран из `common_api.md`, `orchestrator_service_api.md`, `_data_dictionary.md` (20.06).

---

## 🟡 Приоритет 2 (важные)

### T3. Поисковые эндпоинты не описаны
✅ **Сделано** — POST/GET /documents/search и POST /ask добавлены в `query_service_api.md` (группа search).

### T4. `GET /tasks` и `GET /tasks/stats` не описаны
✅ **Сделано** — добавлены в `orchestrator_service_api.md`.

### T5. `POST /ask` не описан
✅ **Сделано** — добавлен в `query_service_api.md`.

---

## 🔵 Приоритет 3 (уточнения)

### T6. Нет маппинга статусных моделей
✅ **Сделано** — таблица маппинга в `guide.md`.

### T7. DraftItem в Registry internal API (4.2) — неполный состав полей
✅ **Сделано** — примечание о расширении Orchestrator и маппинге `id → draft_id`.

### T8. DecideResponse — `decided_by`/`decided_at` только в публичном API
✅ **Сделано** — примечание в Registry 4.5.

### T9. `POST /documents/{doc_id}/reprocess` — `user_id` в ответе
⏳ **Требует верификации с кодом** — в спеке ответ корректный (без user_id). Если код возвращает — убрать из кода.

### T10. `POST /drafts/{draft_id}/preview` — `estimated_completion`
⏳ **Требует верификации с кодом** — поле есть в спеке. Если код не возвращает — убрать из спеки или реализовать.

### T13. `GET /tasks/{id}/status` — отсутствовали `version_id`, `has_notifications`, `critical_count`
✅ **Сделано** (20.06) — поля добавлены в спеки по результатам сверки с кодом.

### T14. `GET /tasks/{id}/steps` — отсутствовал `total`
✅ **Сделано** (20.06) — поле добавлено в спеки.

### T15. `GET /tasks` — отсутствовал query-параметр `pipeline_type`
✅ **Сделано** (20.06) — параметр добавлен в спеки.

### T16. Типизация `_at`/`_by` полей — унификация
✅ **Сделано** (20.06) — `_at` → `datetime`, `_by` → описание «субъект (пользователь или сервис)». Конвенция записана в `guide.md`. Затронуты файлы: `_schemas.md`, `orchestrator_service_api.md`, `registry_service_api.md`, `auth_service_api.md`, `converter_validator_service_api.md`, `ocr_service_api.md`, `parser_service_api.md`, `rag_builder_service_api.md`.

---

## ⚪ Приоритет 4 (проверить)

### T11. POST /drafts — 9 form-полей vs 2 поля в коде
⏳ **Требует доступа к коду** — в спеке 9 полей. Синхронизировать со спекой или урезать спеки.

### T12. `has_notifications`/`critical_count` в TaskStatusResponse
✅ **Сделано** (20.06) — поля добавлены в `orchestrator_service_api.md` GET /tasks/{task_id}/status.

---

## Gateway route table

✅ Добавлены маршруты:
- `/api/v1/search/*` → Query Service (8083)
- `/api/v1/ask` → Query Service (8083)
- `/api/v1/tasks` + `/api/v1/tasks/stats` → Orchestrator (8081)

## README.md

✅ Обновлено описание Query Service — добавлены поисковые эндпоинты.

## Скрипт кросс-проверки

✅ `check_cross_references.py` — 62 проверки, все проходят.

## Что остаётся сделать (когда появится доступ к коду)

1. Сверить реализацию этих эндпоинтов со спеками:
   - POST/GET /documents/search — структура запроса/ответа
   - POST /ask — структура запроса/ответа
2. Проверить reprocess response — нет ли `user_id` в теле
3. Проверить POST /drafts — реальное количество form-полей
4. Проверить `estimated_completion` в POST /drafts/{draft_id}/preview

## Принятые архитектурные решения (без правок кода)

По результатам сверки с кодом (20.06):
- `GET /tasks` — формат пагинации `meta: {}` оставлен как целевой дизайн (common_api.md). Код должен быть приведён к стандарту.
- `GET /tasks/stats` — формат `by_status` + `by_stage` оставлен как целевой дизайн. Код использует `active/completed/failed/by_type` — требуется доработка кода.
- `GET /drafts/{draft_id}/tasks` — подтверждён как необходимый эндпоинт. Ожидает реализации.
