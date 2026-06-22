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

---

## 🔴 Приоритет 1 (новые) — Контракты RAG (по уточнению Павла, 20.06)

### T23. RAG Search API — привести к RS-6
- [x] **Запрос**: убрать `search_type`, `top_k`, `rerank`, `version_id` — только `query`, `valid_at`, `filters`
- [x] **Ответ**: разделить на `source` (doc_id, section_id, clause, path, page, bbox, section_title, content) и `retrieval` (chunk_id, score, mode)
- [x] Убрать `search_type_used` и `confidence` как отдельные поля
- [x] Добавить `context[]` (expansion — внутренний этап RAG Search)
- [x] Зафиксировать: `top_k`, `search_type`, `rerank` — только из `app_settings`
- [x] **Убрано**: `content_hash` из `source` (нет в БД, нечем заполнять)
- [x] **Убрано**: `score` из `context[]` (соседние чанки не проходят rerank, score не вычисляется)

### T24. RAG Builder API — уточнить входной/выходной контракт
- [x] Во входном контракте: добавить `parent_id`, `bbox` в секции
- [x] Зафиксировать page: **1-based** (первая страница документа = 1)
- [x] Зафиксировать bbox: нормализованный 0..1 (ссылка на `common_api.md`)
- [x] `parent_id` ссылается на `section_id` (стабильный ID секции)
- [x] `section_id` стабилен внутри документа (не меняется при переиндексации)
- [x] Builder **полностью удаляет** старый индекс по doc_id перед новой индексацией
- [x] `chunk_id` — только технический retrieval ID (не用于 цитирования)
- [x] В финальный ответ: добавить `indexing_txn_id`
- [x] Добавить `errors[]` / `warnings[]` в ответ
- [x] Обновить пример JSON-запроса

### T25. Query Service API — согласовать структуру источников
- [x] В секцию «Именование полей источников»: добавить `clause`, `path`, `bbox`
- [x] `content_hash` **не добавлен** — нет в БД чанков, нечем заполнять
- [x] В структуру `sources[]` longpoll-ответов: добавить `clause`, `path`
- [x] Источники в ответе — плоская структура (для UI), но цитирование строится по `doc_id + section_id`
- [x] Секция «Обогащение цитирований»: уточнить, что цитирование строится по `doc_id + section_id`, а не по `chunk_id`

### T26. pipeline3-search.md — исправить валидацию цитирований
- [x] Заменить `[source:N]` с chunk_id на `[source:N]` — ссылка на **индекс элемента массива sources** (не chunk_id)
- [x] Этап 3b (LLM генерация): убрать chunk_id из валидации
- [x] Этап 4 (обогащение цитирований): уточнить разделение source/retrieval

### T27. `_data_dictionary.md` — добавить поля RAG
- [x] Добавить `rag_documents`, `rag_document_chunks`
- [x] Добавить `indexing_txn_id`, `chunk_id`, `search_mode`, `embedding_dim`

### T28. README.md — актуализировать описания RAG Builder, RAG Search, Query Service
- [x] Query Service: цитирование по doc_id + section_id
- [x] RAG Builder: архитектурные принципы, chunk size 1024, indexing_txn_id
- [x] RAG Search: source/retrieval разделение, app_settings

### T29. specificity.md — зафиксировать аномалии
- [x] A46: Старый контракт RAG Search конфликтовал с RS-6
- [x] A47: chunk_id использовался как citation ID (исправлено)
- [x] A48: page convention не была зафиксирована
- [x] A49: bbox convention не была зафиксирована для RAG Builder
- [x] A50: content_hash и context.score в RAG Search отсутствуют в БД
