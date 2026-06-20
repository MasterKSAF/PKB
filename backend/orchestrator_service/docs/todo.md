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

## 🔵 Новая задача: Поиск по истории сообщений в сессии

- [x] **T17.** Добавить endpoint `POST /chat/sessions/{session_id}/messages/search` в `query_service_api.md`
- [x] **T18.** Обновить `README.md` — добавить в функции Query Service: поиск по истории сообщений
- [x] **T19.** Зафиксировать в `guide.md` решение: редактирование сообщений не поддерживается (ответ консультанта становится устаревшим)
- [x] **T20.** Проверить `_data_dictionary.md` и `_schemas.md` — нужны ли изменения (не требуются — поля специфичны для Query Service)
- [x] **T21.** Финальная проверка целостности и связности

### T22. Конфиг LLM в Query Service (QS-13)
- [x] Добавлена таблица параметров LLM (модель, temperature, max_tokens=8196, top_p) в секцию «Генерация ответа LLM» `query_service_api.md`
- [x] Убраны дублирующиеся строки про max_tokens=1024 из `rag_search_service_api.md` — заменены ссылкой на Query Service
