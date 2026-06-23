# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-23 14:04:02 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 8086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 8080 | ✅ | — | ⏭️ | — | ✅ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| Orchestrator | 8081 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parser Service | 8087 | ✅ | — | ✅ | ✅ | ✅ |
| Query Service | 8083 | ✅ | ✅ | ❌ | ✅ | ❌ |
| RAG Builder | 8090 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ✅ | ✅ |
| Registry Service | 8084 | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| **Total** | | ✅ | ✅ | ❌ | ✅ | ❌ |

### 📋 Pipeline статусы по сервисам

| Service | Documents | Chat | Registry | Lifecycle | AdminUsers | Quarantine | Orchestrator | MultiDoc | OrchReject | OrchMetadata | OrchDelete | OrchReprocess | OrchVersions | OrchFull | Status |
|---------|:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:|:------:|
| Auth Service | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| Gateway | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| MinIO | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| Orchestrator | — | — | — | — | — | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parser Service | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | ✅ |
| Query Service | — | ✅ | — | — | ✅ | — | — | — | — | — | — | — | — | — | ✅ |
| RAG Builder | ✅ | — | — | ✅ | — | — | — | ✅ | — | — | — | — | — | ✅ | ✅ |
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — | — | — | — | — | ✅ | ✅ |
| Registry Service | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ | ✅ | ✅ |
| TEI | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

#### 🔍 Пояснения к результатам

- **Gateway**: ⏭️ 3 эндпоинтов пропущено — нет контекста (prepare не создал данные)

- **Query Service**: API: 1 эндпоинт(ов) упало


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| Converter-Validator | 8086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Gateway | 8080 | ✅ | — | 77 | 74 | 0 | **3** | ⏭️ |
| Orchestrator | 8081 | ✅ | ✅ | 35 | 35 | 0 | 0 | ✅ |
| Parser Service | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | ✅ | ✅ | 27 | 26 | **1** | 0 | ❌ |
| RAG Builder | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 50 | 50 | 0 | 0 | ✅ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **229** | **225** | **1** | **3** | ❌ |

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
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 12 | 0 | ✅ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 19 | 0 | ✅ |
| `orchestrator_document_reject` | Reject черновика Orchestrator (создание → reject → проверка статуса) | ✅ | 6 | 6 | 0 | ✅ |
| `orchestrator_document_reprocess` | Переиндексация документа Orchestrator (создание документа → reprocess) | ✅ | 6 | 5 | 0 | ✅ |
| `orchestrator_document_versions` | Версионирование документа Orchestrator (создание документа → новая версия) | ✅ | 4 | 4 | 0 | ✅ |
| `orchestrator_draft_delete` | Удаление черновика Orchestrator (создание → удаление → проверка 404) | ✅ | 6 | 6 | 0 | ✅ |
| `orchestrator_draft_lifecycle` | Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление) | ✅ | 11 | 10 | 0 | ✅ |
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
| RAG: IVFFlat индекс `ix_rag_doc_chunks_embedding_ivfflat` | ✅ |
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

## 📋 Pipeline Testing — Пошаговая детализация

### Pipeline: `admin_user_lifecycle`

**Admin управление пользователем (создание → работа → аудит → деактивация)**

- Ping: ✅
- Passed: 16/16
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация admin | auth | ✅ | 200 | 248ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 246ms | user_id = u-8959eaf99f0a |
| 3 | Список пользователей | auth | ✅ | 200 | 16ms | users = [{'user_id': 'u-8959eaf99f0a', 'email': 'pipeline-user-20260623190313855696@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTg5NTllYWY5OWYwYSIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 9ms | session_id = 19 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 15ms | message_id = 38 |
| 7 | Получение истории чата | query | ✅ | 200 | 7ms | messages = [{'message_id': 37, 'role': 'user', 'content': 'Тестовое сообщение от pipeline п |
| 8 | Брутфорс попытка 1/5 | auth | ✅ | 401 | 233ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 | auth | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 | auth | ✅ | 401 | 231ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 | auth | ✅ | 401 | 233ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 | auth | ✅ | 401 | 231ms | {"error":{"code":"ACCOUNT_LOCKED","message":"Аккаунт заблокирован после нескольких неудачных попыток входа","details":{"retry_after_seconds":1800}}} |
| 13 | Проверка блокировки после 5 неудач | auth | ✅ | 401 | 8ms | {"error":{"code":"ACCOUNT_LOCKED","message":"Аккаунт заблокирован после нескольких неудачных попыток входа","details":{"retry_after_seconds":1800}}} |
| 14 | Журнал аудита | auth | ✅ | 200 | 10ms | events = [{'event_id': 'evt-bb8783528252', 'user_id': 'u-8959eaf99f0a', 'action': 'auth.l |
| 15 | Деактивация пользователя | auth | ✅ | 200 | 26ms | is_active = False |
| 16 | Проверка 401 после деактивации | auth | ✅ | 401 | 12ms | ответ: пустой detail |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 16/16

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 10ms | session_id = 20 |
| 3 | Отправка сообщения | query | ✅ | 202 | 11ms | message_id = 40 |
| 4 | Текстовый поиск | query | ✅ | 200 | 3ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped | query | ✅ | 200 | 4ms | enrichment_skipped=False |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 3335ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 95ms | draft_id = 54 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 6ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 36ms | Все поля валидны |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 61ms | {"draft_id":54,"task_id":60,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 1053ms | {"draft_id":54,"task_id":60,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 106ms | {"draft_id":54,"task_id":60,"document_id":72,"version_id":1,"is_new_document":true,"status":"proceeding","action":"approve","message":"Запущена полная обработка документа"} |
| 8 | Проверка document_id после approve | orchestrator | ✅ | 200 | 38ms | документ создан (без id в ответе) |
| 9 | Создание документа в Registry | registry | ✅ | 201 | 18ms | {"data":{"id":73,"doc_code":"APPROVAL-20260623190319624015","title":"Approval тест 20260623190319624015","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Принятый термин","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash |
| 10 | Индексация документа | rag_builder | ✅ | 202 | 12ms | status = indexed |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 238ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BBBABDBF53B8DC</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 27ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 36ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 2025ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 4ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 2ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 422 | 4ms | {"detail":[{"type":"missing","loc":["query","mapping"],"msg":"Field required","input":null},{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 36ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 34ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 14ms | {"data":{"id":74,"doc_code":"PIPELINE-TEST-1782223401","title":"Тестовый документ pipeline 1782223401","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Принятый термин","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_s |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 7ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 15ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-23T17:03:23.893446+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3328ms | results[9/9]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 16ms | {"data":{"id":75,"doc_code":"LIFECYCLE-1782223407","title":"Lifecycle тест 1782223407","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Принятый термин","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"6d80610d |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 202 | 10ms | status = indexed |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 17ms | data = {'id': '75', 'status': 'uploaded', 'previous_status': None, 'history_id': '5', ' |
| 5 | Повторное построение индекса | rag_builder | ✅ | 202 | 10ms | status = indexed |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3313ms | results[9/9]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 12ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 7ms | {"document_id":75,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 3311ms | results[9/9]: валидация по source-индексам (document_id+section_id) пройдена |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 14ms | {"data":{"id":76,"doc_code":"LIFECYCLE-RECOVER-1782223407","title":"Lifecycle тест восстановленный 1782223407","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Принятый термин","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","titl |
| 11 | Финальное построение индекса | rag_builder | ✅ | 202 | 10ms | status = indexed |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 3303ms | results[9/9]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BBBAC18AB40F05</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 11ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 38ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 5ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 4033ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 37ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-23T14:03:42.101092Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782223417.pdf","file_h |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 20ms | {"data":{"id":77,"doc_code":"MULTI1-1782223417","title":"Multi-doc тест 1 1782223417","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Принятый термин","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"2c420ebd2 |
| 9 | Построение индекса #1 | rag_builder | ✅ | 202 | 13ms | status = indexed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 15ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 39ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 5ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4069ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 35ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-23T14:03:46.299388Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782223417.pdf","file_h |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 21ms | {"data":{"id":78,"doc_code":"MULTI2-1782223417","title":"Multi-doc тест 2 1782223417","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Принятый термин","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"39784276a |
| 16 | Построение индекса #2 | rag_builder | ✅ | 202 | 14ms | status = indexed |
| 17 | Поиск по общему запросу | rag_search | ✅ | 200 | 3298ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 13ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ✅ | 200 | 3310ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 99ms | draft_id = 55 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 5ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 39ms | Все поля валидны |
| 5 | Решение по черновику (reject) | orchestrator | ✅ | 200 | 50ms | status = discarded |
| 6 | Проверка статуса после reject | orchestrator | ✅ | 200 | 42ms | {"draft_id":55,"document_id":null,"version_id":null,"is_new_document":true,"status":"discarded","document_key":"reject-key-20260623190352972192","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 5/6
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 255ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 17ms | approved_doc_id=79 |
| 3 | Создание черновика | orchestrator | ✅ | 202 | 95ms | draft_id = 56 |
| 4 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 9ms | status = active |
| 5 | Переиндексация документа | orchestrator | ✅ | 409 | 5ms | {"detail":{"error":{"code":"TASK_ALREADY_EXISTS","message":"Reprocess task for document 79 already exists"}}} |
| 6 | Статус задачи переиндексации | orchestrator | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 5/6

### Pipeline: `orchestrator_document_versions`

**Версионирование документа Orchestrator (создание документа → новая версия)**

- Ping: ✅
- Passed: 4/4
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 13ms | approved_doc_id=80 |
| 3 | Загрузка новой версии документа | orchestrator | ✅ | 404 | 2ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий | orchestrator | ✅ | 404 | 1ms | {"detail":"Not Found"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 359ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 94ms | draft_id = 57 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 5ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 35ms | Все поля валидны |
| 5 | Удаление черновика | orchestrator | ✅ | 204 | 38ms |  |
| 6 | Проверка 404 после удаления | orchestrator | ✅ | 404 | 38ms | {"detail":{"error":{"code":"NOT_FOUND","message":"Черновик 57 не найден","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/57'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"}}}} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 10/11
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 86ms | draft_id = 58 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 5ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 36ms | Все поля валидны |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 47ms | {"draft_id":58,"task_id":65,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 1055ms | status = processing |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 99ms | status = proceeding |
| 8 | Проверка document_id после approve | orchestrator | ✅ | 200 | 36ms | is_new_document=True |
| 9 | Проверка документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика (image/png для OR-14) | orchestrator | ✅ | 202 | 140ms | draft_id = 59 |
| 11 | Статус задачи image (OR-14) | orchestrator | ✅ | 200 | 7ms | status = active |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/11

### Pipeline: `orchestrator_full_document_lifecycle`

**Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 91ms | draft_id = 60 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 5ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 35ms | Все поля валидны |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 47ms | {"draft_id":60,"task_id":67,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 1047ms | {"draft_id":60,"task_id":67,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 98ms | approved_doc_id=82 |
| 8 | Проверка документа в Registry | registry | ✅ | 200 | 6ms | {"data":{"id":82,"doc_code":"fullcycle-key-20260623190356586614","title":"Draft 60","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"7565fa4760b4985a56a39523354155d008371d85605845a1746b1c68c34d570f","draft_id":60,"classification_status" |
| 9 | Индексация документа | rag_builder | ✅ | 202 | 10ms | status = indexed |
| 10 | Поиск RAG Search | rag_search | ✅ | 200 | 3310ms | {"query":"тестовый документ","results":[{"source":{"document_id":73,"section_id":1,"clause":null,"path":null,"page":1,"bbox":null,"section_title":null,"content":"Содержимое тестового документа approval"},"retrieval":{"chunk_id":43,"score":1.0,"mode":"dense_rerank"},"context":[]},{"source":{"document |
| 11 | Удаление черновика | orchestrator | ✅ | 204 | 44ms |  |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 95ms | draft_id = 61 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 5ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 35ms | Все поля валидны |
| 5 | Обновление метаданных | orchestrator | ✅ | 200 | 41ms | Все поля валидны |
| 6 | Проверка обновлённых метаданных | orchestrator | ✅ | 200 | 36ms | {"draft_id":61,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260623190401530432","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 250ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 7ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 11ms | {"data":{"classifier_system":"MKS","code":"99.989223","full_name":"Pipeline тестовый классификатор 20260623140401989223","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 7ms | data = [{'classifier_system': 'MKS', 'code': '98.222408', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 7ms | data = {'classifier_system': 'MKS', 'code': '99.989223', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 11ms | data = {'classifier_system': 'MKS', 'code': '99.989223', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 11ms | data = {'classifier_system': 'MKS', 'code': '99.989223', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 10ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 9ms | {"data":{"id":10,"raw_term":"Pipeline тест 20260623140401989223","standard_term":"Pipeline тест 20260623140401989223","normalized_value":"pipeline тест 20260623140401989223","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms": |
| 10 | Нормализация термина | registry | ✅ | 200 | 4ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 9ms | data = {'id': 10, 'raw_term': 'Pipeline тест 20260623140401989223', 'standard_term': 'P |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWUzNWY4NzYxYjdhOCIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 10ms | {"data":{"classifier_system":"MKS","code":"98.335050","full_name":"Pipeline quarantine классификатор 20260623190402335050","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 21ms | data = {'id': 83, 'doc_code': 'QUAR-TEST-20260623190402335050', 'title': 'Pipeline quar |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 24ms | data = [{'id': '9', 'system': 'MKS', 'code': '96.597009', 'found_in_document_id': '26', |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 16ms | data = {'pending_id': '9', 'classifier_system': 'MKS', 'code': '96.597009', 'status': ' |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 20ms | data = {'id': 84, 'doc_code': 'QUAR-TEST2-20260623190402335050', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 25ms | data = [{'id': '10', 'system': 'MKS', 'code': '98.223154', 'found_in_document_id': '35' |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 10ms | data = {'pending_id': '10', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-23 14:04:02 UTC_
