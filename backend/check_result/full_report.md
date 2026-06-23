# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-23 16:22:46 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 8086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 8080 | ✅ | — | ✅ | — | ✅ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| Orchestrator | 8081 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parser Service | 8087 | ✅ | — | ✅ | ✅ | ✅ |
| Query Service | 8083 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Builder | 8090 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ✅ | ✅ |
| Registry Service | 8084 | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| **Total** | | ✅ | ✅ | ✅ | ✅ | ✅ |

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

_Нет замечаний_


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| Converter-Validator | 8086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Gateway | 8080 | ✅ | — | 77 | 77 | 0 | 0 | ✅ |
| Orchestrator | 8081 | ✅ | ✅ | 35 | 35 | 0 | 0 | ✅ |
| Parser Service | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | ✅ | ✅ | 27 | 27 | 0 | 0 | ✅ |
| RAG Builder | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 50 | 50 | 0 | 0 | ✅ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **229** | **229** | **0** | **0** | ✅ |

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
| 1 | Аутентификация admin | auth | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 240ms | user_id = u-968f540f54f3 |
| 3 | Список пользователей | auth | ✅ | 200 | 12ms | users = [{'user_id': 'u-968f540f54f3', 'email': 'pipeline-user-20260623212203545083@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTk2OGY1NDBmNTRmMyIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 9ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 11ms | message_id = 6 |
| 7 | Получение истории чата | query | ✅ | 200 | 7ms | messages = [{'message_id': 5, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 | auth | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 | auth | ✅ | 401 | 228ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 | auth | ✅ | 401 | 228ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 | auth | ✅ | 401 | 228ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 | auth | ✅ | 401 | 232ms | {"error":{"code":"ACCOUNT_LOCKED","message":"Аккаунт заблокирован после нескольких неудачных попыток входа","details":{"retry_after_seconds":1800}}} |
| 13 | Проверка блокировки после 5 неудач | auth | ✅ | 401 | 7ms | {"error":{"code":"ACCOUNT_LOCKED","message":"Аккаунт заблокирован после нескольких неудачных попыток входа","details":{"retry_after_seconds":1800}}} |
| 14 | Журнал аудита | auth | ✅ | 200 | 8ms | events = [{'event_id': 'evt-61969eaf7c0f', 'user_id': 'u-968f540f54f3', 'action': 'auth.l |
| 15 | Деактивация пользователя | auth | ✅ | 200 | 27ms | is_active = False |
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
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 8ms | session_id = 4 |
| 3 | Отправка сообщения | query | ✅ | 202 | 13ms | message_id = 8 |
| 4 | Текстовый поиск | query | ✅ | 200 | 3ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped | query | ✅ | 200 | 4ms | enrichment_skipped=False |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 12ms | results=[] (нет результатов, валидация по source не требуется) |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 91ms | draft_id = 4 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 6ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 36ms | Все поля валидны |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 50ms | {"draft_id":4,"task_id":4,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 1052ms | {"draft_id":4,"task_id":4,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 102ms | {"draft_id":4,"task_id":4,"document_id":4,"version_id":1,"is_new_document":true,"status":"proceeding","action":"approve","message":"Запущена полная обработка документа"} |
| 8 | Проверка document_id после approve | orchestrator | ✅ | 200 | 36ms | документ создан (без id в ответе) |
| 9 | Создание документа в Registry | registry | ✅ | 201 | 23ms | {"data":{"id":5,"doc_code":"APPROVAL-20260623212205947435","title":"Approval тест 20260623212205947435","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"8d3042612bf8bc9407a6 |
| 10 | Индексация документа | rag_builder | ✅ | 202 | 11ms | status = indexed |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BBC2505DDF786A</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 18ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 37ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 2020ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 5ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 2ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 422 | 5ms | {"detail":[{"type":"missing","loc":["query","mapping"],"msg":"Field required","input":null},{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 34ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 36ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 18ms | {"data":{"id":6,"doc_code":"PIPELINE-TEST-1782231727","title":"Тестовый документ pipeline 1782231727","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"15b684886c4edb8f904870 |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 8ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 12ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-23T19:22:10.191501+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3329ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":7,"doc_code":"LIFECYCLE-1782231733","title":"Lifecycle тест 1782231733","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"c181ba8875dddb958292e432a5add137717e4c |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 19ms | data = {'id': '7', 'status': 'uploaded', 'previous_status': None, 'history_id': '1', 'u |
| 5 | Повторное построение индекса | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3308ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 11ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 8ms | {"document_id":7,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 3313ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":8,"doc_code":"LIFECYCLE-RECOVER-1782231733","title":"Lifecycle тест восстановленный 1782231733","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"9893fc57f78100 |
| 11 | Финальное построение индекса | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 3283ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BBC2542711C35D</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 10ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 39ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 2011ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 33ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-23T16:22:26.344476Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782231744.pdf","file_h |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 18ms | {"data":{"id":9,"doc_code":"MULTI1-1782231744","title":"Multi-doc тест 1 1782231744","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"80c57f13583f0d8f75a534c3a048d852f0debe7 |
| 9 | Построение индекса #1 | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 13ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 39ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4029ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 34ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-23T16:22:30.498161Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782231744.pdf","file_h |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 16ms | {"data":{"id":10,"doc_code":"MULTI2-1782231744","title":"Multi-doc тест 2 1782231744","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"41ef536813b9fbe0ee62d8f987726c76f7c051 |
| 16 | Построение индекса #2 | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 17 | Поиск по общему запросу | rag_search | ✅ | 200 | 3311ms | results[4/4]: валидация по source-индексам (document_id+section_id) пройдена |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 13ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ✅ | 200 | 3303ms | results[3/3]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 96ms | draft_id = 5 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 6ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 36ms | Все поля валидны |
| 5 | Решение по черновику (reject) | orchestrator | ✅ | 200 | 50ms | status = discarded |
| 6 | Проверка статуса после reject | orchestrator | ✅ | 200 | 40ms | {"draft_id":5,"document_id":null,"version_id":null,"is_new_document":true,"status":"discarded","document_key":"reject-key-20260623212237176147","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 5/6
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 12ms | approved_doc_id=11 |
| 3 | Создание черновика | orchestrator | ✅ | 202 | 89ms | draft_id = 6 |
| 4 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 5ms | status = active |
| 5 | Переиндексация документа | orchestrator | ✅ | 409 | 4ms | {"detail":{"error":{"code":"TASK_ALREADY_EXISTS","message":"Reprocess task for document 11 already exists"}}} |
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
| 1 | Аутентификация | auth | ✅ | 200 | 235ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 14ms | approved_doc_id=12 |
| 3 | Загрузка новой версии документа | orchestrator | ✅ | 404 | 2ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий | orchestrator | ✅ | 404 | 2ms | {"detail":"Not Found"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 99ms | draft_id = 7 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 6ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 35ms | Все поля валидны |
| 5 | Удаление черновика | orchestrator | ✅ | 204 | 42ms |  |
| 6 | Проверка 404 после удаления | orchestrator | ✅ | 404 | 42ms | {"detail":{"error":{"code":"NOT_FOUND","message":"Черновик 7 не найден","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/7'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"}}}} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 10/11
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 90ms | draft_id = 8 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 7ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 36ms | Все поля валидны |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 50ms | {"draft_id":8,"task_id":9,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 1058ms | status = processing |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 100ms | status = proceeding |
| 8 | Проверка document_id после approve | orchestrator | ✅ | 200 | 37ms | is_new_document=True |
| 9 | Проверка документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика (image/png для OR-14) | orchestrator | ✅ | 202 | 100ms | draft_id = 9 |
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
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 96ms | draft_id = 10 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 6ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 38ms | Все поля валидны |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 54ms | {"draft_id":10,"task_id":11,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 1048ms | {"draft_id":10,"task_id":11,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 97ms | approved_doc_id=14 |
| 8 | Проверка документа в Registry | registry | ✅ | 200 | 7ms | {"data":{"id":14,"doc_code":"fullcycle-key-20260623212240631053","title":"Draft 10","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"533038efe740aeccc69d2e0792a00b592ec4a2c83d0b86873c2af1c5b793d555","draft_id":10,"classification_status" |
| 9 | Индексация документа | rag_builder | ✅ | 202 | 10ms | status = indexed |
| 10 | Поиск RAG Search | rag_search | ✅ | 200 | 3312ms | {"query":"тестовый документ","results":[{"source":{"document_id":10,"section_id":1,"clause":null,"path":null,"page":1,"bbox":null,"section_title":null,"content":"Содержимое документа 2 1782231744"},"retrieval":{"chunk_id":9,"score":1.0,"mode":"dense_rerank"},"context":[]},{"source":{"document_id":5, |
| 11 | Удаление черновика | orchestrator | ✅ | 204 | 42ms |  |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 99ms | draft_id = 11 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 7ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 36ms | Все поля валидны |
| 5 | Обновление метаданных | orchestrator | ✅ | 200 | 43ms | Все поля валидны |
| 6 | Проверка обновлённых метаданных | orchestrator | ✅ | 200 | 44ms | {"draft_id":11,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260623212245591220","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 6ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 11ms | {"data":{"classifier_system":"MKS","code":"99.071561","full_name":"Pipeline тестовый классификатор 20260623162246071561","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 9ms | data = [{'classifier_system': 'MKS', 'code': '98.231705', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 7ms | data = {'classifier_system': 'MKS', 'code': '99.071561', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 12ms | data = {'classifier_system': 'MKS', 'code': '99.071561', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 15ms | data = {'classifier_system': 'MKS', 'code': '99.071561', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 12ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 11ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260623162246071561","standard_term":"Pipeline тест 20260623162246071561","normalized_value":"pipeline тест 20260623162246071561","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 5ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 10ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260623162246071561', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 237ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWEzYzc1YWE3NDMxOCIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 9ms | {"data":{"classifier_system":"MKS","code":"98.432680","full_name":"Pipeline quarantine классификатор 20260623212246432680","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 20ms | data = {'id': 15, 'doc_code': 'QUAR-TEST-20260623212246432680', 'title': 'Pipeline quar |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 15ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.231705', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 16ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.231705', 'status': |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 6ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 20ms | data = {'id': 16, 'doc_code': 'QUAR-TEST2-20260623212246432680', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 20ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.231705', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 12ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-23 16:22:46 UTC_
