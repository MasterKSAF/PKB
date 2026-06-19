# todo — синхронизация документации (внутренние расхождения)

> Все пункты, не требующие доступа к коду, выполнены.

---

## 🔴 Приоритет 1 (критичные)

### T1. `pipeline1-formation.md` — нет `title_key` в preview-метаданных
✅ **Сделано** — добавлено поле `title_key` в JSON-пример.

### T2. Health-формат не унифицирован
✅ **Сделано** — решение в `guide.md`, Orchestrator приведён к common-формату.

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

---

## ⚪ Приоритет 4 (проверить)

### T11. POST /drafts — 9 form-полей vs 2 поля в коде
⏳ **Требует доступа к коду** — в спеке 9 полей. Синхронизировать со спекой или урезать спеки.

### T12. `has_notifications`/`critical_count` в TaskStatusResponse
⏳ **Требует доступа к коду** — в спеке GET /tasks/{task_id}/status этих полей нет. Если код возвращает — добавить.

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
   - GET /tasks — поля ответа
   - GET /tasks/stats — метрики
2. Проверить reprocess response — нет ли `user_id` в теле
3. Проверить POST /drafts — реальное количество form-полей
4. Проверить `has_notifications`/`critical_count` в TaskStatusResponse
5. Проверить `estimated_completion` в POST /drafts/{draft_id}/preview
