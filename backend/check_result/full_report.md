# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-26 16:47:50 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 18082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 18086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 18080 | ✅ | — | ❌ | ✅ | ❌ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 18088 | — | — | — | — | 🟡 dev |
| Orchestrator | 18081 | ✅ | ✅ | ✅ | — | ✅ |
| Parser Service | 18087 | ✅ | — | ✅ | ✅ | ✅ |
| Query Service | 18083 | ✅ | ✅ | ✅ | — | ✅ |
| RAG Builder | 18090 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Search | 18091 | ✅ | — | ✅ | ✅ | ✅ |
| Registry Service | 18084 | ✅ | ✅ | ❌ | ✅ | ❌ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| **Total** | | ✅ | ✅ | ❌ | ❌ | ❌ |

### 📋 Pipeline статусы по сервисам

| Service | Documents | Chat | Registry | Lifecycle | AdminUsers | Quarantine | Orchestrator | MultiDoc | OrchReject | OrchMetadata | OrchDelete | OrchReprocess | OrchVersions | OrchFull | Status |
|---------|:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:|:------:|
| Auth Service | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ |
| Converter-Validator | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| Gateway | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ |
| MinIO | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| Orchestrator | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| Parser Service | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| Query Service | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| RAG Builder | ✅ | — | — | ✅ | — | — | — | ✅ | — | — | — | — | — | ✅ | ✅ |
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — | — | — | — | — | ✅ | ✅ |
| Registry Service | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ |
| TEI | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

#### 🔍 Пояснения к результатам

- **Gateway**: API: 34 эндпоинт(ов) упало; ⏭️ 24 эндпоинтов пропущено — нет контекста (prepare не создал данные)

- **Registry Service**: API: 3 эндпоинт(ов) упало


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 18082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| Converter-Validator | 18086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Gateway | 18080 | ✅ | — | 100 | 42 | **34** | **24** | ❌ |
| Orchestrator | 18081 | ✅ | ✅ | 35 | 35 | 0 | 0 | ✅ |
| Parser Service | 18087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 18083 | ✅ | ✅ | 27 | 27 | 0 | 0 | ✅ |
| RAG Builder | 18090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 18091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 18084 | ✅ | ✅ | 50 | 47 | **3** | 0 | ❌ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **252** | **191** | **37** | **24** | ❌ |

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
| `document_approval` | Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик) | ✅ | 10 | 10 | 0 | ✅ |
| `document_processing` | Полный цикл обработки документа | ✅ | 15 | 15 | 0 | ✅ |
| `full_document_cycle` | Полный сквозной цикл: загрузка PDF через черновик → парсинг → конвертация → валидация → approve → Registry → индексация → поиск | ✅ | 13 | 11 | 2 | ❌ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 12 | 0 | ✅ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 19 | 0 | ✅ |
| `orchestrator_document_reject` | Reject черновика Orchestrator (создание → reject → проверка статуса) | ✅ | 6 | 6 | 0 | ✅ |
| `orchestrator_document_reprocess` | Переиндексация документа Orchestrator (создание документа → reprocess) | ✅ | 6 | 5 | 0 | ✅ |
| `orchestrator_document_versions` | Версионирование документа Orchestrator (создание документа → новая версия) | ✅ | 4 | 4 | 0 | ✅ |
| `orchestrator_draft_delete` | Удаление черновика Orchestrator (создание → удаление → проверка 404) | ✅ | 6 | 6 | 0 | ✅ |
| `orchestrator_draft_lifecycle` | Жизненный цикл черновика через Gateway (создание → превью → решение → удаление) | ✅ | 11 | 10 | 0 | ✅ |
| `orchestrator_full_document_lifecycle` | Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление) | ✅ | 11 | 11 | 0 | ✅ |
| `orchestrator_metadata_update` | Обновление метаданных черновика Orchestrator (PATCH /metadata) | ✅ | 6 | 6 | 0 | ✅ |
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
| query → rag_search | ✅ | 200 | 3328ms | results=5, processing_time_ms=3323, total_found=7 |
| query → registry | ✅ | 200 | 8ms | data=[] — валидный ответ (БД пуста, но эндпоинт работает) |
| rag_search → infinity (TEI) | ✅ | 200 | 14ms | embedding_dim=312 — эмбеддинги работают |
| gateway → query | ✅ | 201 | 25ms | session_id=5 — прокси работает |
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
| 1 | Аутентификация admin (через Gateway) | gateway | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание пользователя (через Gateway) | gateway | ✅ | 201 | 254ms | user_id = u-48cc8b88fe8e |
| 3 | Список пользователей (через Gateway) | gateway | ✅ | 200 | 22ms | users = [{'user_id': 'u-48cc8b88fe8e', 'email': 'pipeline-user-20260626214654350914@test |
| 4 | Аутентификация нового пользователя (через Gateway) | gateway | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ4Y2M4Yjg4ZmU4ZSIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь, через Gateway) | gateway | ✅ | 201 | 22ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь, через Gateway) | gateway | ✅ | 202 | 25ms | message_id = 6 |
| 7 | Получение истории чата (через Gateway) | gateway | ✅ | 200 | 22ms | messages = [{'message_id': 5, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 (через Gateway) | gateway | ✅ | 401 | 229ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 (через Gateway) | gateway | ✅ | 401 | 232ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 (через Gateway) | gateway | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 (через Gateway) | gateway | ✅ | 401 | 227ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 (через Gateway) | gateway | ✅ | 401 | 229ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 13 | Проверка блокировки после 5 неудач (через Gateway) | gateway | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 14 | Журнал аудита (через Gateway) | gateway | ✅ | 200 | 21ms | events = [{'event_id': 'evt-f8fc6839a83c', 'user_id': 'u-48cc8b88fe8e', 'action': 'auth.l |
| 15 | Деактивация пользователя (через Gateway) | gateway | ✅ | 200 | 33ms | is_active = False |
| 16 | Проверка 401 после деактивации (через Gateway) | gateway | ✅ | 401 | 13ms | ответ: пустой detail |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 16/16

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание чат-сессии (через Gateway) | gateway | ✅ | 201 | 22ms | session_id = 4 |
| 3 | Отправка сообщения (через Gateway) | gateway | ✅ | 202 | 29ms | message_id = 8 |
| 4 | Текстовый поиск (через Gateway) | gateway | ✅ | 200 | 17ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped (через Gateway) | gateway | ✅ | 200 | 45ms | enrichment_skipped=False |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 10ms | results=[] (нет результатов, валидация по source не требуется) |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 226ms | draft_id = 6 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 18ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 49ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 82ms | {"draft_id":6,"task_id":7,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1059ms | {"draft_id":6,"task_id":7,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 132ms | {"draft_id":6,"task_id":7,"document_id":5,"version_id":1,"is_new_document":true,"status":"proceeding","action":"approve","message":"Запущена полная обработка документа"} |
| 8 | Проверка document_id после approve (через Gateway) | gateway | ✅ | 200 | 51ms | документ создан (без id в ответе) |
| 9 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 51ms | {"data":{"id":6,"doc_code":"APPROVAL-20260626214657071001","title":"Approval тест 20260626214657071001","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"35f66d2f184da1c8b849 |
| 10 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 18ms | status = indexed |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 238ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCAF695718D199</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 19ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 4ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 35ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 2019ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 5ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 2ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 200 | 9ms | {"data":{"is_duplicate":false,"is_duplicate_file":false,"candidates":[],"file_hash_sha256":null,"title_hash_sha256":"561484bc91ca985c567323ff7e7a7d09b870b6a40fe2eedc0ba707d764de558e","file_size_bytes":null,"checked_at":"2026-06-26T16:47:01.623354+00:00"}} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 37ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 37ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 17ms | {"data":{"id":7,"doc_code":"PIPELINE-TEST-1782492419","title":"Тестовый документ pipeline 1782492419","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"901ab4bdae2986cce08f7f |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 9ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 13ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-26T19:47:01.743637+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3322ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_cycle`

**Полный сквозной цикл: загрузка PDF через черновик → парсинг → конвертация → валидация → approve → Registry → индексация → поиск**

- Ping: ✅
- Passed: 11/13
- Failed: 2
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 246ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика с PDF (через Gateway) | gateway | ✅ | 202 | 241ms | draft_id = 7 |
| 3 | Статус задачи парсинга (через Gateway) | gateway | ✅ | 200 | 16ms | status = active |
| 4 | Результат парсинга (Parser API) | parser | ✅ | 404 | 10ms | результат сохранён как parser_result |
| 5 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 53ms | Все поля валидны |
| 6 | Предпросмотр метаданных (Converter API) | converter_validator | ❌ | 422 | 4ms | Expected HTTP 200, got 422 | body: {"error":{"code":"METADATA_EXTRACTION_FAILED","message":"Failed to extract required metadata: doc_code and title","details":null}} | body: {"error":{"code":"METADATA_EXTRACTION_FAILED","message":"Failed to extract required metadata: doc_code and title","details":null}} |
| 7 | Валидация документа (Converter API) | converter_validator | ❌ | 400 | 2ms | Expected HTTP 200, got 400 | body: {"error":{"code":"VALIDATION_ERROR","message":"doc_code is required","details":null}} | body: {"error":{"code":"VALIDATION_ERROR","message":"doc_code is required","details":null}} |
| 8 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 72ms | {"draft_id":7,"task_id":8,"status":"previewing","message":"Preview phase started"} |
| 9 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1070ms | {"draft_id":7,"task_id":8,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 10 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 120ms | approved_doc_id=8 |
| 11 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 21ms | {"data":{"id":8,"doc_code":"full-cycle-key-20260626214705281459","title":"Draft 7","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"a5673c9389266a3baf6dedf8e862905baefc9d84a1275395914ec0372ef506b3","draft_id":7,"classification_status":{ |
| 12 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 13 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3338ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 11/13

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 238ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 30ms | {"data":{"id":9,"doc_code":"LIFECYCLE-1782492430","title":"Lifecycle тест 1782492430","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"d71e70c40eb76a0bf5bbb3abeb252d26d9eb4f |
| 3 | Первая попытка построения индекса (RAG Builder) | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 4 | Обновление метаданных документа (через Gateway) | gateway | ✅ | 200 | 35ms | data = {'id': '9', 'status': 'uploaded', 'previous_status': None, 'history_id': '1', 'u |
| 5 | Повторное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 12ms | status = indexed |
| 6 | Поиск по индексу RAG Search (RAG Search) | rag_search | ✅ | 200 | 3321ms | results[3/3]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry (через Gateway) | gateway | ✅ | 200 | 27ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG (RAG Builder) | rag_builder | ✅ | 200 | 8ms | {"document_id":9,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата (RAG Search) | rag_search | ✅ | 200 | 3312ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |
| 10 | Воссоздание документа в Registry (через Gateway) | gateway | ✅ | 201 | 29ms | {"data":{"id":10,"doc_code":"LIFECYCLE-RECOVER-1782492430","title":"Lifecycle тест восстановленный 1782492430","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"0bc36ab2fd0ab |
| 11 | Финальное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 12 | Финальный поиск по индексу (RAG Search) | rag_search | ✅ | 200 | 3326ms | results[3/3]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCAF6E6E910859</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 14ms |  |
| 4 | Запуск парсинга #1 (Parser) | parser | ✅ | 202 | 4ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll, Parser) | parser | ✅ | 200 | 34ms | status = accepted |
| 6 | Результат парсинга #1 (Parser) | parser | ✅ | 200 | 2022ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 (Converter) | converter_validator | ✅ | 200 | 37ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-26T16:47:23.509436Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782492441.pdf","file_h |
| 8 | Сохранение документа #1 в Registry (через Gateway) | gateway | ✅ | 201 | 34ms | {"data":{"id":11,"doc_code":"MULTI1-1782492441","title":"Multi-doc тест 1 1782492441","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"62694652017650c4e61c3a05a20196041eae31 |
| 9 | Построение индекса #1 (RAG Builder) | rag_builder | ✅ | 202 | 13ms | status = indexed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 17ms |  |
| 11 | Запуск парсинга #2 (Parser) | parser | ✅ | 202 | 4ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll, Parser) | parser | ✅ | 200 | 16ms | status = accepted |
| 13 | Результат парсинга #2 (Parser) | parser | ✅ | 200 | 4051ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 (Converter) | converter_validator | ✅ | 200 | 40ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-26T16:47:27.729740Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782492441.pdf","file_h |
| 15 | Сохранение документа #2 в Registry (через Gateway) | gateway | ✅ | 201 | 33ms | {"data":{"id":12,"doc_code":"MULTI2-1782492441","title":"Multi-doc тест 2 1782492441","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"5108374c7eeffdcb48a8f6e61fab42e9613cf1 |
| 16 | Построение индекса #2 (RAG Builder) | rag_builder | ✅ | 202 | 14ms | status = indexed |
| 17 | Поиск по общему запросу (RAG Search) | rag_search | ✅ | 200 | 3298ms | results[5/5]: валидация по source-индексам (document_id+section_id) пройдена |
| 18 | Удаление документа #1 из Registry (через Gateway) | gateway | ✅ | 200 | 27ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 (RAG Search) | rag_search | ✅ | 200 | 3303ms | results[4/4]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 279ms | draft_id = 8 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 16ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 53ms | Все поля валидны |
| 5 | Решение по черновику (reject, через Gateway) | gateway | ✅ | 200 | 70ms | status = discarded |
| 6 | Проверка статуса после reject (через Gateway) | gateway | ✅ | 200 | 61ms | {"draft_id":8,"document_id":null,"version_id":null,"is_new_document":true,"status":"discarded","document_key":"reject-key-20260626214734438751","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 5/6
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 27ms | approved_doc_id=13 |
| 3 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 262ms | draft_id = 9 |
| 4 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 17ms | status = active |
| 5 | Переиндексация документа (через Gateway) | gateway | ✅ | 409 | 20ms | {"detail":{"error":{"code":"TASK_ALREADY_EXISTS","message":"Reprocess task for document 13 already exists"}}} |
| 6 | Статус задачи переиндексации (через Gateway) | gateway | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 5/6

### Pipeline: `orchestrator_document_versions`

**Версионирование документа Orchestrator (создание документа → новая версия)**

- Ping: ✅
- Passed: 4/4
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 30ms | approved_doc_id=14 |
| 3 | Загрузка новой версии документа (через Gateway) | gateway | ✅ | 404 | 15ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий (через Gateway) | gateway | ✅ | 200 | 20ms | {"data":[]} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 245ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 231ms | draft_id = 10 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 17ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 52ms | Все поля валидны |
| 5 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 71ms |  |
| 6 | Проверка 404 после удаления (через Gateway) | gateway | ✅ | 404 | 60ms | {"detail":{"error":{"code":"NOT_FOUND","message":"Черновик 10 не найден","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/10'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"}}}} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика через Gateway (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 10/11
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 246ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 287ms | draft_id = 11 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 17ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 50ms | Все поля валидны |
| 5 | Запуск превью (через Gateway) | gateway | ✅ | 202 | 79ms | {"draft_id":11,"task_id":13,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1080ms | status = processing |
| 7 | Решение approve (через Gateway) | gateway | ✅ | 200 | 122ms | status = proceeding |
| 8 | Проверка document_id (через Gateway) | gateway | ✅ | 200 | 48ms | is_new_document=True |
| 9 | Проверка документа в Registry (через Gateway) | gateway | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика image/png (через Gateway) | gateway | ✅ | 202 | 276ms | draft_id = 12 |
| 11 | Статус задачи image (через Gateway) | gateway | ✅ | 200 | 15ms | status = active |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/11

### Pipeline: `orchestrator_full_document_lifecycle`

**Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 261ms | draft_id = 13 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 16ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 55ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 75ms | {"draft_id":13,"task_id":15,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1068ms | {"draft_id":13,"task_id":15,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 115ms | approved_doc_id=16 |
| 8 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 19ms | {"data":{"id":16,"doc_code":"fullcycle-key-20260626214739332911","title":"Draft 13","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"1a0fd9266f05e95d54b962dc85843f805fc873373ff37a2f9a58ea58407042ec","draft_id":13,"classification_status" |
| 9 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 12ms | status = indexed |
| 10 | Поиск RAG Search (RAG Search) | rag_search | ✅ | 200 | 3318ms | {"query":"тестовый документ","results":[{"source":{"document_id":6,"section_id":1,"clause":null,"path":null,"page":1,"bbox":null,"section_title":null,"content":"Содержимое тестового документа approval"},"retrieval":{"chunk_id":3,"score":1.0,"mode":"dense_rerank"},"context":[]},{"source":{"document_i |
| 11 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 52ms |  |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 258ms | draft_id = 14 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 17ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 52ms | Все поля валидны |
| 5 | Обновление метаданных (через Gateway) | gateway | ✅ | 200 | 78ms | Все поля валидны |
| 6 | Проверка обновлённых метаданных (через Gateway) | gateway | ✅ | 200 | 70ms | {"draft_id":14,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260626214744604893","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Профиль пользователя (через Gateway) | gateway | ✅ | 200 | 17ms | Все поля валидны |
| 3 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 26ms | {"data":{"classifier_system":"MKS","code":"99.424324","full_name":"Pipeline тестовый классификатор 20260626164745424324","status":"active"}} |
| 4 | Список классификаторов (через Gateway) | gateway | ✅ | 200 | 21ms | data = [{'classifier_system': 'MKS', 'code': '98.492395', 'full_name': 'Принятый термин |
| 5 | Получить классификатор (через Gateway) | gateway | ✅ | 200 | 21ms | data = {'classifier_system': 'MKS', 'code': '99.424324', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор (через Gateway) | gateway | ✅ | 200 | 27ms | data = {'classifier_system': 'MKS', 'code': '99.424324', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора (через Gateway) | gateway | ✅ | 200 | 25ms | data = {'classifier_system': 'MKS', 'code': '99.424324', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор (через Gateway) | gateway | ✅ | 200 | 30ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин (через Gateway) | gateway | ✅ | 201 | 27ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260626164745424324","standard_term":"Pipeline тест 20260626164745424324","normalized_value":"pipeline тест 20260626164745424324","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина (через Gateway) | gateway | ✅ | 200 | 27ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин (через Gateway) | gateway | ✅ | 200 | 36ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260626164745424324', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 238ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 31ms | {"data":{"classifier_system":"MKS","code":"98.039730","full_name":"Pipeline quarantine классификатор 20260626214746039730","status":"active"}} |
| 3 | Создать документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 40ms | data = {'id': 17, 'doc_code': 'QUAR-TEST-20260626214746039730', 'title': 'Pipeline quar |
| 4 | Список карантина (pending, через Gateway) | gateway | ✅ | 200 | 38ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.492395', 'found_in_document_id': '1',  |
| 5 | Принять из карантина (accept, через Gateway) | gateway | ✅ | 200 | 29ms | data = {'pending_id': '1', 'classifier_system': 'MKS', 'code': '98.492395', 'status': ' |
| 6 | Валидация классификации (accept, через Gateway) | gateway | ✅ | 200 | 22ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 45ms | data = {'id': 18, 'doc_code': 'QUAR-TEST2-20260626214746039730', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending, через Gateway) | gateway | ✅ | 200 | 38ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.492395', 'found_in_document_id': '1' |
| 9 | Отклонить из карантина (reject, через Gateway) | gateway | ✅ | 200 | 36ms | data = {'pending_id': '2', 'status': 'rejected'} |
| 10 | Валидация классификации (reject, через Gateway) | gateway | ✅ | 200 | 21ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-26 16:47:50 UTC_
