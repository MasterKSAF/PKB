# Orchestrator Service — тесты

**Директория:** `backend/orchestrator_service/tests/` (дополнить существующую)

---

## 1. `tests/orchestrator/test_drafts_crud.py` (~300 строк)

CRUD черновиков через Orchestrator API.

**Сценарии:**

| #   | Тест                                                     | Описание                                                                     |
| --- | -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | POST `/api/v1/drafts` с PDF-файлом                       | → 202, ответ содержит draft_id, task_id, status="uploaded", file_hash_sha256 |
| 2   | POST `/api/v1/drafts` с metadata                         | → 202, metadata в ответе                                                     |
| 3   | POST `/api/v1/drafts` без файла                          | → 422 Validation Error                                                       |
| 4   | POST `/api/v1/drafts` с пустым файлом                    | → 422                                                                        |
| 5   | GET `/api/v1/drafts` — список                            | → 200, items + pagination meta                                               |
| 6   | GET `/api/v1/drafts?status=uploaded` — фильтр по статусу | → только uploaded                                                            |
| 7   | GET `/api/v1/drafts?document_key=xxx` — фильтр по ключу  | → соответствующие drafts                                                     |
| 8   | GET `/api/v1/drafts?page=1&page_size=10` — пагинация     | → meta.page, meta.page_size, meta.total                                      |
| 9   | GET `/api/v1/drafts/{id}` — существующий                 | → 200, все поля draft                                                        |
| 10  | GET `/api/v1/drafts/{id}` — несуществующий               | → 404                                                                        |
| 11  | GET `/api/v1/drafts/abc` — нечисловой                    | → 400 INVALID_DRAFT_ID                                                       |
| 12  | PATCH `/api/v1/drafts/{id}/metadata` — полное обновление | → 200, metadata обновлена                                                    |
| 13  | PATCH `/api/v1/drafts/{id}/metadata` — частичное         | → только переданные поля                                                     |
| 14  | PATCH `/api/v1/drafts/{id}/metadata` — несуществующий    | → 404                                                                        |
| 15  | DELETE `/api/v1/drafts/{id}` — существующий              | → 200/204                                                                    |
| 16  | DELETE `/api/v1/drafts/{id}` — несуществующий            | → 404                                                                        |

---

## 2. `tests/orchestrator/test_drafts_preview.py` (~150 строк)

Preview и decision черновиков.

**Сценарии:**

| #   | Тест                                                      | Описание                             |
| --- | --------------------------------------------------------- | ------------------------------------ |
| 1   | POST `/api/v1/drafts/{id}/preview` — запуск               | → 202, task_id                       |
| 2   | POST `/api/v1/drafts/{id}/preview` — несуществующий       | → 404                                |
| 3   | GET `/api/v1/drafts/{id}/preview/status` — pending        | status="pending"                     |
| 4   | GET `/api/v1/drafts/{id}/preview/status` — completed      | status="completed", preview_metadata |
| 5   | GET `/api/v1/drafts/{id}/preview/status` — failed         | status="failed", error info          |
| 6   | GET `/api/v1/drafts/{id}/preview/status` — несуществующий | → 404                                |
| 7   | PATCH `/api/v1/drafts/{id}/decide` — approve              | → 200, status → "approved"           |
| 8   | PATCH `/api/v1/drafts/{id}/decide` — approve с comment    | comment в ответе                     |
| 9   | PATCH `/api/v1/drafts/{id}/decide` — reject с comment     | → 200, status → "discarded"          |
| 10  | PATCH `/api/v1/drafts/{id}/decide` — reject без comment   | → 200                                |
| 11  | PATCH `/api/v1/drafts/{id}/decide` — несуществующий       | → 404                                |
| 12  | PATCH `/api/v1/drafts/{id}/decide` — невалидный action    | → 422                                |

---

## 3. `tests/orchestrator/test_drafts_tasks.py` (~100 строк)

Задачи черновиков.

**Сценарии:**

| #   | Тест                                                                 | Описание                   |
| --- | -------------------------------------------------------------------- | -------------------------- |
| 1   | GET `/api/v1/drafts/{id}/tasks` — есть задачи                        | → 200, список task         |
| 2   | GET `/api/v1/drafts/{id}/tasks` — пустой список                      | → 200, []                  |
| 3   | GET `/api/v1/drafts/{id}/tasks` — несуществующий                     | → 404                      |
| 4   | GET `/api/v1/tasks/{id}` — детали задачи                             | → 200, status, steps, logs |
| 5   | GET `/api/v1/tasks/{id}` — несуществующая                            | → 404                      |
| 6   | GET `/api/v1/tasks/{id}` — статусы: pending/running/completed/failed | разные статусы             |
| 7   | GET `/api/v1/tasks/{id}` — retry_status                              | поле retryStatus           |
| 8   | GET `/api/v1/tasks/{id}` — audit logs                                | logs с time, event, stage  |

---

## 4. `tests/orchestrator/test_documents_pipeline.py` (~200 строк)

Pipeline-операции с документами.

**Сценарии:**

| #   | Тест                                                     | Описание                            |
| --- | -------------------------------------------------------- | ----------------------------------- |
| 1   | POST `/api/v1/documents` — deprecated                    | → 410 Gone, ENDPOINT_DEPRECATED     |
| 2   | POST `/api/v1/documents/{id}/reprocess` — full mode      | → 202, status="parsing"             |
| 3   | POST `/api/v1/documents/{id}/reprocess` — partial mode   | → 202                               |
| 4   | POST `/api/v1/documents/{id}/reprocess` — несуществующий | → 404                               |
| 5   | POST `/api/v1/documents/{id}/versions` — новая версия    | → 202, version_id, version_number>1 |
| 6   | POST `/api/v1/documents/{id}/versions` — без файла       | → 422                               |
| 7   | GET `/api/v1/documents/{id}/versions` — есть версии      | → 200, список versions              |
| 8   | GET `/api/v1/documents/{id}/versions` — нет версий       | → 200, []                           |
| 9   | GET `/api/v1/documents/{id}/versions` — несуществующий   | → 404                               |
| 10  | GET `/api/v1/documents/{id}/tasks` — задачи документа    | → 200                               |
| 11  | GET `/api/v1/documents/{id}/tasks` — несуществующий      | → 404                               |

---

## 5. `tests/orchestrator/test_documents_status.py` (~80 строк)

Статусы документов.

**Сценарии:**

| #   | Тест                                                 | Описание                                                                                   |
| --- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1   | GET `/api/v1/documents/{id}/status` — completed      | → 200, steps.pipeline.formation.preview + decision, steps.pipeline.indexation.rag_indexing |
| 2   | GET `/api/v1/documents/{id}/status` — parsing        | status="parsing"                                                                           |
| 3   | GET `/api/v1/documents/{id}/status` — failed         | status="failed", error info                                                                |
| 4   | GET `/api/v1/documents/{id}/status` — несуществующий | → 404                                                                                      |
| 5   | Поле chunk_summary                                   | chunk_summary присутствует в ответе                                                        |

---

## 6. `tests/integration/test_draft_to_document_flow.py` (~120 строк)

Интеграционный тест полного цикла.

**Сценарии:**

| #   | Шаг                                             | Описание                           |
| --- | ----------------------------------------------- | ---------------------------------- |
| 1   | POST `/api/v1/drafts` (file)                    | Загружаем файл → получаем draft_id |
| 2   | GET `/api/v1/drafts/{id}`                       | Проверяем status="uploaded"        |
| 3   | POST `/api/v1/drafts/{id}/preview`              | Запускаем preview → task_id        |
| 4   | GET `/api/v1/drafts/{id}/preview/status` (poll) | Ждём completed                     |
| 5   | PATCH `/api/v1/drafts/{id}/decide` (approve)    | Утверждаем черновик                |
| 6   | GET `/api/v1/drafts/{id}`                       | Проверяем promoted_document_id     |
| 7   | GET `/api/v1/documents/{doc_id}`                | Документ создан, статус "approved" |
