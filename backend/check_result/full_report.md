# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-26 10:05:31 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 8086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 8080 | ✅ | — | ❌ | — | ❌ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| Orchestrator | 8081 | ✅ | ✅ | ❌ | ❌ | ❌ |
| Parser Service | 8087 | ✅ | — | ✅ | ✅ | ✅ |
| Query Service | 8083 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Builder | 8090 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ✅ | ✅ |
| Registry Service | 8084 | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| **Total** | | ✅ | ✅ | ❌ | ❌ | ❌ |

### 📋 Pipeline статусы по сервисам

| Service | Documents | Chat | Registry | Lifecycle | AdminUsers | Quarantine | Orchestrator | MultiDoc | OrchReject | OrchMetadata | OrchDelete | OrchReprocess | OrchVersions | OrchFull | Status |
|---------|:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:|:------:|
| Auth Service | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| Gateway | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| MinIO | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| Orchestrator | — | — | — | — | — | — | ❌ | — | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Parser Service | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| Query Service | — | ✅ | — | — | ✅ | — | — | — | — | — | — | — | — | — | ✅ |
| RAG Builder | ✅ | — | — | ✅ | — | — | — | ✅ | — | — | — | — | — | ✅ | ✅ |
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — | — | — | — | — | ✅ | ✅ |
| Registry Service | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ | ✅ | ✅ |
| TEI | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

#### 🔍 Пояснения к результатам

- **Gateway**: API: 15 эндпоинт(ов) упало; ⏭️ 13 эндпоинтов пропущено — нет контекста (prepare не создал данные)

- **Orchestrator**: API: 3 эндпоинт(ов) упало; ⏭️ 10 эндпоинтов пропущено — нет контекста (prepare не создал данные); Pipelines: сбой в Orchestrator, OrchReject, OrchMetadata, OrchDelete, OrchReprocess, OrchFull


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| Converter-Validator | 8086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Gateway | 8080 | ✅ | — | 77 | 49 | **15** | **13** | ❌ |
| Orchestrator | 8081 | ✅ | ✅ | 35 | 22 | **3** | **10** | ❌ |
| Parser Service | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | ✅ | ✅ | 27 | 27 | 0 | 0 | ✅ |
| RAG Builder | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 50 | 50 | 0 | 0 | ✅ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **229** | **188** | **18** | **23** | ❌ |

### ⚠️ Workaround-предупреждения по сервисам

- **Auth Service**: PATCH /admin/users/{id}: docs ожидает audit_log_id, но сервис его не возвращает

- **Query Service**: ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

- **Registry Service**: ⚠️ Registry не поддерживает trailing slash — эндпоинты /classifiers, /documents, /terminology без / в конце.

- **Registry Service**: ⚠️ PATCH /documents/{id}/status — internal API (только Orchestrator), checker ожидает 403.

- **Registry Service**: ⚠️ PATCH /drafts/{id}/metadata — internal API (только Orchestrator), checker ожидает 404.


---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
| `admin_user_lifecycle` | Admin управление пользователем (создание → работа → аудит → деактивация) | ✅ | 16 | 16 | 0 | ✅ |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | ✅ | 6 | 6 | 0 | ✅ |
| `document_approval` | Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик) | ✅ | 10 | 1 | 1 | ❌ |
| `document_processing` | Полный цикл обработки документа | ✅ | 15 | 15 | 0 | ✅ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 12 | 0 | ✅ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 19 | 0 | ✅ |
| `orchestrator_document_reject` | Reject черновика Orchestrator (создание → reject → проверка статуса) | ✅ | 6 | 1 | 1 | ❌ |
| `orchestrator_document_reprocess` | Переиндексация документа Orchestrator (создание документа → reprocess) | ✅ | 6 | 3 | 1 | ❌ |
| `orchestrator_document_versions` | Версионирование документа Orchestrator (создание документа → новая версия) | ✅ | 4 | 4 | 0 | ✅ |
| `orchestrator_draft_delete` | Удаление черновика Orchestrator (создание → удаление → проверка 404) | ✅ | 6 | 1 | 1 | ❌ |
| `orchestrator_draft_lifecycle` | Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление) | ✅ | 11 | 1 | 9 | ❌ |
| `orchestrator_full_document_lifecycle` | Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление) | ✅ | 11 | 1 | 1 | ❌ |
| `orchestrator_metadata_update` | Обновление метаданных черновика Orchestrator (PATCH /metadata) | ✅ | 6 | 1 | 1 | ❌ |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | ✅ | 11 | 11 | 0 | ✅ |
| `registry_quarantine` | Карантин классификаторов: accept/reject + валидация | ✅ | 10 | 10 | 0 | ✅ |
---

### 🗄️ БД PostgreSQL


Общий статус: **✅**

| Проверка | Статус | Детали |
|----------|:------:|--------|
| База данных `pkb_neuro` | ✅ | существует |
| Расширения | ✅ | ltree, pg_trgm, pgcrypto, plpgsql, uuid-ossp, vector |
| Схемы | ✅ | auth, pipeline, public, rag, registry |
| Registry таблицы | ✅ | 17 таблиц |
| Pipeline таблицы | ✅ | 3 таблиц |
| Auth таблицы | ✅ | 6 таблиц |
| UNIQUE-индексы | ✅ | 28 найдено |
| RAG: Таблица `document_chunks` | ✅ |
| RAG: Колонка `embedding` (vector) | ✅ |
| RAG: HNSW индекс `ix_rag_doc_chunks_embedding_hnsw` | ✅ |
| RAG: GIN индекс `ix_rag_doc_chunks_tsv` | ✅ |
| RAG: Колонка `created_at` | ✅ |
| SELECT из Registry | ✅ | доступно |

### 🔍 Статический анализ: сервисы и create_all()

| Сервис | Схема | Статус | create_all |
|--------|:-----:|:------:|:----------:|
| `auth_service` | public | ✅ | Auth: users, roles, audit_log |
| `query_service` | public | ✅ | Query: sessions, messages |
| `orchestrator_service` | public | ✅ | Orchestrator: pipeline, steps |
| `integration_service` | public | ✅ | Integration: documents, tasks |
| `registry_service` | registry | ✅ | Registry: ~18 таблиц (documents, classifiers, terminology) |
| `rag_builder_service` | rag | ✅ | RAG Builder: document_chunks (HNSW/GIN индексы) |
| `rag_search_service` | rag | ✅ | consumer, без create_all |

---

## 🔗 Service Contracts Check

Проверка реального взаимодействия сервисов друг с другом.


| Contract | Status | Code | Time | Детали |
|----------|:------:|:----:|:----:|--------|
| query → rag_search | ✅ | 200 | 3338ms | results=2, processing_time_ms=3333, total_found=4 |
| query → registry | ✅ | 200 | 6ms | data=[] — валидный ответ (БД пуста, но эндпоинт работает) |
| rag_search → infinity (TEI) | ✅ | 200 | 13ms | embedding_dim=312 — эмбеддинги работают |
| gateway → query | ✅ | 201 | 20ms | session_id=7 — прокси работает |
| **Total** | ✅ | | | 4/4 passed, 0 failed |


---

## 📋 Pipeline Testing — Пошаговая детализация

### Pipeline: `admin_user_lifecycle`

**Admin управление пользователем (создание → работа → аудит → деактивация)**

- Ping: ✅
- Passed: 16/16
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация admin | auth | ✅ | 200 | 248ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 247ms | user_id = u-d43b8800a3e9 |
| 3 | Список пользователей | auth | ✅ | 200 | 12ms | users = [{'user_id': 'u-d43b8800a3e9', 'email': 'pipeline-user-20260626150447484912@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0M2I4ODAwYTNlOSIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 11ms | session_id = 5 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 12ms | message_id = 8 |
| 7 | Получение истории чата | query | ✅ | 200 | 7ms | messages = [{'message_id': 7, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 | auth | ✅ | 401 | 233ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 | auth | ✅ | 401 | 231ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 | auth | ✅ | 401 | 233ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 | auth | ✅ | 401 | 228ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 | auth | ✅ | 401 | 231ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 13 | Проверка блокировки после 5 неудач | auth | ✅ | 401 | 233ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 14 | Журнал аудита | auth | ✅ | 200 | 14ms | events = [{'event_id': 'evt-b2b7fead4b5e', 'user_id': 'u-d43b8800a3e9', 'action': 'auth.l |
| 15 | Деактивация пользователя | auth | ✅ | 200 | 28ms | is_active = False |
| 16 | Проверка 401 после деактивации | auth | ✅ | 401 | 8ms | ответ: пустой detail |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 16/16

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 11ms | session_id = 6 |
| 3 | Отправка сообщения | query | ✅ | 202 | 16ms | message_id = 10 |
| 4 | Текстовый поиск | query | ✅ | 200 | 4ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped | query | ✅ | 200 | 3ms | enrichment_skipped=False |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 17ms | results=[] (нет результатов, валидация по source не требуется) |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 1/10
- Failed: 1
- Skipped: 8

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 244ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 66ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 3 | Статус задачи (longpoll) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 4 | Детали черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 5 | Запуск превью черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 6 | Статус превью | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 7 | Решение по черновику (approve) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 8 | Проверка document_id после approve | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 9 | Создание документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Индексация документа | rag_builder | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BC99777725DBA3</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 34ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 4ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 41ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4134ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 5ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 3ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 200 | 8ms | {"data":{"is_duplicate":false,"is_duplicate_file":false,"candidates":[],"file_hash_sha256":null,"title_hash_sha256":"561484bc91ca985c567323ff7e7a7d09b870b6a40fe2eedc0ba707d764de558e","file_size_bytes":null,"checked_at":"2026-06-26T10:04:55.145870+00:00"}} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 34ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 36ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 29ms | {"data":{"id":4,"doc_code":"PIPELINE-TEST-1782468290","title":"Тестовый документ pipeline 1782468290","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"6ecf2dc2a74b5c9367d6da |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 8ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 14ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-26T13:04:55.269797+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3326ms | results=[] (нет результатов, валидация по source не требуется) |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 26ms | {"data":{"id":5,"doc_code":"LIFECYCLE-1782468298","title":"Lifecycle тест 1782468298","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"00c5fe14ae4f6f61a52c4db4b1efd1365e3871 |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 202 | 18ms | status = indexed |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 24ms | data = {'id': '5', 'status': 'uploaded', 'previous_status': None, 'history_id': '1', 'u |
| 5 | Повторное построение индекса | rag_builder | ✅ | 202 | 14ms | status = indexed |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3305ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 21ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 11ms | {"document_id":5,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 3315ms | results=[] (нет результатов, валидация по source не требуется) |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 17ms | {"data":{"id":6,"doc_code":"LIFECYCLE-RECOVER-1782468298","title":"Lifecycle тест восстановленный 1782468298","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"7286f5134e1967 |
| 11 | Финальное построение индекса | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 3317ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BC997BC9B69173</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 14ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 3ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 108ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 4145ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 38ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-26T10:05:13.785480Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782468309.pdf","file_h |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 22ms | {"data":{"id":7,"doc_code":"MULTI1-1782468309","title":"Multi-doc тест 1 1782468309","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"eedcc88bef8985dd56eed830494debbfd0c4423 |
| 9 | Построение индекса #1 | rag_builder | ✅ | 202 | 12ms | status = indexed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 15ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 6ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 42ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4198ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 37ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-26T10:05:18.125978Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782468309.pdf","file_h |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 18ms | {"data":{"id":8,"doc_code":"MULTI2-1782468309","title":"Multi-doc тест 2 1782468309","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"271361bed52d55f2c6242cb96d1f4f2aa8754fc |
| 16 | Построение индекса #2 | rag_builder | ✅ | 202 | 16ms | status = indexed |
| 17 | Поиск по общему запросу | rag_search | ✅ | 200 | 3309ms | results[3/3]: валидация по source-индексам (document_id+section_id) пройдена |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 16ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ✅ | 200 | 3355ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 1/6
- Failed: 1
- Skipped: 4

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 66ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 3 | Статус задачи (longpoll) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 4 | Детали черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 5 | Решение по черновику (reject) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 6 | Проверка статуса после reject | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 3/6
- Failed: 1
- Skipped: 2

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 17ms | approved_doc_id=9 |
| 3 | Создание черновика | orchestrator | ❌ | 500 | 69ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 4 | Статус задачи (longpoll) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 5 | Переиндексация документа | orchestrator | ✅ | 409 | 12ms | {"detail":{"error":{"code":"TASK_ALREADY_EXISTS","message":"Reprocess task for document 9 already exists"}}} |
| 6 | Статус задачи переиндексации | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 3/6

### Pipeline: `orchestrator_document_versions`

**Версионирование документа Orchestrator (создание документа → новая версия)**

- Ping: ✅
- Passed: 4/4
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 23ms | approved_doc_id=10 |
| 3 | Загрузка новой версии документа | orchestrator | ✅ | 404 | 3ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий | orchestrator | ✅ | 404 | 3ms | {"detail":"Not Found"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 1/6
- Failed: 1
- Skipped: 4

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 71ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 3 | Статус задачи (longpoll) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 4 | Детали черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 5 | Удаление черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 6 | Проверка 404 после удаления | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 1/11
- Failed: 9
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 72ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 3 | Статус задачи (longpoll) | orchestrator | ❌ | 422 | 8ms | Expected HTTP 200, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","task_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{task_id}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","task_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{task_id}"}]} |
| 4 | Детали черновика | orchestrator | ❌ | 422 | 7ms | Expected HTTP 200, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 5 | Запуск превью черновика | orchestrator | ❌ | 422 | 6ms | Expected HTTP {200, 202, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 6 | Статус превью | orchestrator | ❌ | 422 | 9ms | Expected HTTP {200, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 7 | Решение по черновику (approve) | orchestrator | ❌ | 422 | 9ms | Expected HTTP {200, 409}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 8 | Проверка document_id после approve | orchestrator | ❌ | 422 | 3ms | Expected HTTP {200, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 9 | Проверка документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика (image/png для OR-14) | orchestrator | ❌ | 500 | 72ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 11 | Статус задачи image (OR-14) | orchestrator | ❌ | 422 | 3ms | Expected HTTP 200, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","task_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{task_id_2}"}]} | body: {"detail":[{"type":"int_parsing","loc":["path","task_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{task_id_2}"}]} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/11

### Pipeline: `orchestrator_full_document_lifecycle`

**Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)**

- Ping: ✅
- Passed: 1/11
- Failed: 1
- Skipped: 9

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 72ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 3 | Статус задачи (longpoll) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 4 | Детали черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 5 | Запуск превью черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 6 | Статус превью | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 7 | Решение по черновику (approve) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 8 | Проверка документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 9 | Индексация документа | rag_builder | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Поиск RAG Search | rag_search | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 11 | Удаление черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 1/6
- Failed: 1
- Skipped: 4

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 66ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registr | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404" |
| 3 | Статус задачи (longpoll) | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 4 | Детали черновика | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 5 | Обновление метаданных | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 6 | Проверка обновлённых метаданных | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 14ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 12ms | {"data":{"classifier_system":"MKS","code":"99.362875","full_name":"Pipeline тестовый классификатор 20260626100527362875","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 7ms | data = [{'classifier_system': 'MKS', 'code': '98.468268', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 6ms | data = {'classifier_system': 'MKS', 'code': '99.362875', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 12ms | data = {'classifier_system': 'MKS', 'code': '99.362875', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 10ms | data = {'classifier_system': 'MKS', 'code': '99.362875', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 17ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 12ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260626100527362875","standard_term":"Pipeline тест 20260626100527362875","normalized_value":"pipeline тест 20260626100527362875","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 8ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 15ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260626100527362875', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ3ODBmN2FhN2VlNCIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 17ms | {"data":{"classifier_system":"MKS","code":"98.733396","full_name":"Pipeline quarantine классификатор 20260626150527733396","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 24ms | data = {'id': 11, 'doc_code': 'QUAR-TEST-20260626150527733396', 'title': 'Pipeline quar |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 17ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.468268', 'found_in_document_id': '1',  |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 17ms | data = {'pending_id': '1', 'classifier_system': 'MKS', 'code': '98.468268', 'status': ' |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 6ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 25ms | data = {'id': 12, 'doc_code': 'QUAR-TEST2-20260626150527733396', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 20ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.468268', 'found_in_document_id': '1' |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 18ms | data = {'pending_id': '2', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 7ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-26 10:05:31 UTC_
