# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-20 13:08:47 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ❌ | ❌ | ❌ |
| Converter-Validator | 8086 | ✅ | — | ❌ | ❌ | ❌ |
| Gateway | 8080 | ✅ | — | ❌ | — | ❌ |
| Orchestrator | 8081 | ✅ | ✅ | ❌ | ❌ | ❌ |
| Parser Service | 8087 | ✅ | — | ❌ | ✅ | ❌ |
| Query Service | 8083 | ✅ | ✅ | ❌ | ❌ | ❌ |
| RAG Builder | 8090 | ✅ | ✅ | ❌ | ❌ | ❌ |
| RAG Search | 8091 | ✅ | — | ✅ | ✅ | ✅ |
| Registry Service | 8084 | ✅ | ✅ | ❌ | ❌ | ❌ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| **Total** | | **10/10** | **6/6** | **2/10** | ❌ | ❌ |

> ⚠️ **5 эндпоинтов пропущено** — сервисы в Docker не полностью обновлены до спецификации от 19.06.2026. Пропущенные эндпоинты (из списка KNOWN_NEW_ENDPOINTS) возвращают 404, так как реализация в сервисах ещё не обновлена.


### 📋 Pipeline статусы по сервисам

| Service | Documents | Chat | Registry | Lifecycle | AdminUsers | Quarantine | Orchestrator | MultiDoc | Status |
|---------|:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:|:------:|
| Auth Service | — | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | — | ❌ |
| Converter-Validator | ❌ | — | — | — | — | — | — | ❌ | ❌ |
| Gateway | — | — | — | — | — | — | — | — | ✅ |
| Orchestrator | — | — | — | — | — | — | ❌ | — | ❌ |
| Parser Service | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| Query Service | — | ❌ | — | — | ✅ | — | — | — | ❌ |
| RAG Builder | ❌ | — | — | ❌ | — | — | — | ❌ | ❌ |
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | ✅ | ✅ |
| Registry Service | ❌ | — | ✅ | ✅ | — | ✅ | — | ✅ | ❌ |
| TEI | — | — | — | — | — | — | — | — | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | **8/13** | **5/6** | **11/11** | **9/12** | **15/16** | **10/10** | **1/11** | **15/19** | ❌ |

#### 🔍 Пояснения к ❌ в проверках

- **Auth Service**: API: 1 эндпоинт(ов) упало; Pipelines: сбой в AdminUsers

- **Converter-Validator**: API: 2 эндпоинт(ов) пропущено; Pipelines: сбой в Documents, MultiDoc

- **Gateway**: API: 53 эндпоинт(ов) упало; API: 19 эндпоинт(ов) пропущено

- **Orchestrator**: API: 5 эндпоинт(ов) упало; API: 8 эндпоинт(ов) пропущено; Pipelines: сбой в Orchestrator

- **Parser Service**: API: 2 эндпоинт(ов) упало; API: 2 эндпоинт(ов) пропущено

- **Query Service**: API: 4 эндпоинт(ов) упало; API: 11 эндпоинт(ов) пропущено; Pipelines: сбой в Chat

- **RAG Builder**: API: 2 эндпоинт(ов) упало; API: 2 эндпоинт(ов) пропущено; Pipelines: сбой в Documents, Lifecycle, MultiDoc

- **Registry Service**: API: 1 эндпоинт(ов) упало; API: 1 эндпоинт(ов) пропущено; Pipelines: сбой в Documents, Orchestrator


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 18 | 17 | **1** | 0 | ❌ |
| Converter-Validator | 8086 | ✅ | — | 5 | 3 | 0 | **2** | ❌ |
| Gateway | 8080 | ✅ | — | 76 | 4 | **53** | **19** | ❌ |
| Orchestrator | 8081 | ✅ | ✅ | 22 | 9 | **5** | **8** | ❌ |
| Parser Service | 8087 | ✅ | — | 5 | 1 | **2** | **2** | ❌ |
| Query Service | 8083 | ✅ | ✅ | 21 | 6 | **4** | **11** | ❌ |
| RAG Builder | 8090 | ✅ | ✅ | 9 | 5 | **2** | **2** | ❌ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 34 | 32 | **1** | **1** | ❌ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **194** | **81** | **68** | **45** | ❌ |

### ⚠️ Workaround-предупреждения по сервисам

- **Query Service**: ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

- **Registry Service**: ⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.


---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
| `admin_user_lifecycle` | Admin управление пользователем (создание → работа → аудит → деактивация) | ✅ | 16 | 15 | 1 | ❌ |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | ✅ | 6 | 5 | 1 | ❌ |
| `document_processing` | Полный цикл обработки документа | ✅ | 13 | 8 | 5 | ❌ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 9 | 3 | ❌ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 15 | 4 | ❌ |
| `orchestrator_draft_lifecycle` | Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление) | ✅ | 11 | 1 | 9 | ❌ |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | ✅ | 11 | 11 | 0 | ✅ |
| `registry_quarantine` | Карантин классификаторов: accept/reject + валидация | ✅ | 10 | 10 | 0 | ✅ |
---

### 🗄️ БД PostgreSQL


Общий статус: **❌**

| Проверка | Статус | Детали |
|----------|:------:|--------|
| База данных `pkb_neuro` | ✅ | существует |
| Расширения | ✅ | ltree, pg_trgm, pgcrypto, plpgsql, uuid-ossp, vector |
| Схемы | ❌ | отсутствуют: auth, pipeline |
| Registry таблицы | ❌ | отсутствуют: registry.categories, registry.classifier_registry, registry.document_categories, registry.drafts |
| | | создано: 10 из 12 ожидаемых |
| Pipeline таблицы | ❌ | отсутствуют: pipeline.draft_notifications, pipeline.task_steps, pipeline.tasks |
| Auth таблицы | ❌ | отсутствуют: auth.users |
| UNIQUE-индексы | ❌ | отсутствуют: rag.document_chunks_section_chunk_key, registry.document_versions_doc_id_path_key, registry.document_versions_doc_id_version_key, registry.documents_doc_code_era_key, registry.documents_title_hash_sha256_key, registry.documents_title_key_key |
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
- Passed: 15/16
- Failed: 1
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация admin | auth | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 244ms | user_id = u-6e3c34318df1 |
| 3 | Список пользователей | auth | ✅ | 200 | 16ms | users = [{'user_id': 'u-6e3c34318df1', 'email': 'pipeline-user-20260620180830618933@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTZlM2MzNDMxOGRmMSIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 12ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 21ms | message_id = 2 |
| 7 | Получение истории чата | query | ✅ | 200 | 46ms | messages = [{'message_id': 1, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 | auth | ✅ | 401 | 222ms | {"detail":"Неверные учётные данные"} |
| 9 | Брутфорс попытка 2/5 | auth | ✅ | 401 | 222ms | {"detail":"Неверные учётные данные"} |
| 10 | Брутфорс попытка 3/5 | auth | ✅ | 401 | 218ms | {"detail":"Неверные учётные данные"} |
| 11 | Брутфорс попытка 4/5 | auth | ✅ | 401 | 220ms | {"detail":"Неверные учётные данные"} |
| 12 | Брутфорс попытка 5/5 | auth | ✅ | 401 | 220ms | {"detail":"Неверные учётные данные"} |
| 13 | Проверка блокировки после 5 неудач | auth | ❌ | 401 | 222ms | Expected HTTP {429, 423}, got 401 | body: {"detail":"Неверные учётные данные"} |
| 14 | Журнал аудита | auth | ✅ | 200 | 8ms | events = [{'event_id': 'evt-57feedacabd1', 'user_id': 'u-6e3c34318df1', 'action': 'auth.l |
| 15 | Деактивация пользователя | auth | ✅ | 200 | 29ms | is_active = False |
| 16 | Проверка 401 после деактивации | auth | ✅ | 401 | 7ms | ответ: Неверные учётные данные |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 15/16

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 5/6
- Failed: 1
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 10ms | session_id = 4 |
| 3 | Отправка сообщения | query | ✅ | 202 | 12ms | message_id = 4 |
| 4 | Текстовый поиск | query | ✅ | 200 | 2ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped | query | ❌ | 200 | 3ms | Поле 'enrichment_skipped' не найдено в ответе | body: {"original_text":"толщина обшивки","analysis":{"normalized_query":"толщина обшивки","entities":[{"type":"query","value":"толщина обшивки"}],"subqueries":["толщина обшивки"]},"results":[{"section_id":420042,"document_id":1,"document_title":"Правила РС, часть I","page":42,"content":"Для ледового класс |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 13ms | results = [] |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 5/6

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 8/13
- Failed: 5
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 4ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BACC026C4B8BCF</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 21ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 39ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 13ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4044ms | Все поля валидны |
| 7 | Валидация метаданных (бизнес-ключ) | converter_validator | ❌ | 404 | 2ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} |
| 8 | Проверка уникальности документа | registry | ❌ | 307 | 2ms | Expected HTTP {200, 422}, got 307 |
| 9 | Конвертация JSON | converter_validator | ❌ | 422 | 3ms | Expected HTTP 200, got 422 | body: {"error":{"code":"VALIDATION_ERROR","message":"Invalid request data","details":{"errors":[{"type":"missing","loc":["body","version_id"],"msg":"Field required","input":{"task_id":"12345","raw_json":{"pages":[],"blocks":[],"text":"тестовый текст"}}}]}}} |
| 10 | Сохранение документа в Registry | registry | ✅ | 201 | 13ms | {"data":{"id":3,"doc_code":"PIPELINE-TEST-1781960913","title":"Тестовый документ pipeline 1781960913","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"6a6d109ba0c55cf7bcc455c797f878b328330483937fd8b7e2409dc3d91f5764","classification_status":{},"metadata":{}}} |
| 11 | Проверка preview_snapshot в документе | registry | ❌ | 307 | 5ms | Expected HTTP 200, got 307 |
| 12 | Построение чанков и индексация | rag_builder | ❌ | 500 | 13ms | Expected HTTP {200, 202}, got 500 | body: Internal Server Error |
| 13 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 20ms | results = [] |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 8/13

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 9/12
- Failed: 3
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 16ms | {"data":{"id":4,"doc_code":"LIFECYCLE-1781960917","title":"Lifecycle тест 1781960917","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"0edcb9f094249fce2f04a1c69884b4cfec64096ff3d93f73b922f6a15bbf83d2","classification_status":{},"metadata":{}}} |
| 3 | Первая попытка построения индекса | rag_builder | ❌ | 500 | 13ms | Expected HTTP {200, 201}, got 500 | body: Internal Server Error |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 16ms | data = {'id': '4', 'status': 'uploaded', 'previous_status': None, 'history_id': '2', 'u |
| 5 | Повторное построение индекса | rag_builder | ❌ | 500 | 15ms | Expected HTTP {200, 201}, got 500 | body: Internal Server Error |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 15ms | results = [] |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 15ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 8ms | {"document_id":4,"deleted_count":0,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 15ms | results = [] |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 17ms | {"data":{"id":5,"doc_code":"LIFECYCLE-RECOVER-1781960917","title":"Lifecycle тест восстановленный 1781960917","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"ee0b72a5c7729c8cf32ac70b723681b124afe22d5e9b11c23351e1481067fa99","classification_status":{},"metadata":{}}} |
| 11 | Финальное построение индекса | rag_builder | ❌ | 500 | 15ms | Expected HTTP {200, 201}, got 500 | body: Internal Server Error |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 15ms | results = [] |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 9/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 15/19
- Failed: 4
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BACC038E40771A</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 15ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 37ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 3ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 4049ms | Все поля валидны |
| 7 | Конвертация JSON #1 | converter_validator | ❌ | 422 | 2ms | Expected HTTP 200, got 422 | body: {"error":{"code":"VALIDATION_ERROR","message":"Invalid request data","details":{"errors":[{"type":"missing","loc":["body","version_id"],"msg":"Field required","input":{"task_id":"20001","raw_json":{"pages":[],"blocks":[],"text":"Текст документа 1 1781960917"}}}]}}} |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 12ms | {"data":{"id":6,"doc_code":"MULTI1-1781960917","title":"Multi-doc тест 1 1781960917","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"1940ee47330b85ca9e68d3d137a6931fffb48483cb818234b150b979bfb1827b","classification_status":{},"metadata":{}}} |
| 9 | Построение индекса #1 | rag_builder | ❌ | 500 | 15ms | Expected HTTP {200, 201}, got 500 | body: Internal Server Error |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 13ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 38ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 5ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4061ms | Все поля валидны |
| 14 | Конвертация JSON #2 | converter_validator | ❌ | 422 | 2ms | Expected HTTP 200, got 422 | body: {"error":{"code":"VALIDATION_ERROR","message":"Invalid request data","details":{"errors":[{"type":"missing","loc":["body","version_id"],"msg":"Field required","input":{"task_id":"20002","raw_json":{"pages":[],"blocks":[],"text":"Текст документа 2 1781960917"}}}]}}} |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":7,"doc_code":"MULTI2-1781960917","title":"Multi-doc тест 2 1781960917","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"60a606da32ac5af6ff416785f3c7c1b6fda1d83bb58e195ceb948c58c2067011","classification_status":{},"metadata":{}}} |
| 16 | Построение индекса #2 | rag_builder | ❌ | 500 | 15ms | Expected HTTP {200, 201}, got 500 | body: Internal Server Error |
| 17 | Поиск по общему запросу | rag_search | ✅ | 200 | 22ms | results = [] |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 13ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ✅ | 200 | 12ms | results = [] |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 15/19

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 1/11
- Failed: 9
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 422 | 6ms | Expected HTTP 202, got 422 | body: {"detail":[{"type":"missing","loc":["body","source_type"],"msg":"Field required","input":null}]} |
| 3 | Статус задачи (longpoll) | orchestrator | ❌ | 404 | 2ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} |
| 4 | Детали черновика | orchestrator | ❌ | 422 | 6ms | Expected HTTP 200, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 5 | Запуск превью черновика | orchestrator | ❌ | 422 | 5ms | Expected HTTP {200, 202, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 6 | Статус превью | orchestrator | ❌ | 422 | 6ms | Expected HTTP {200, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 7 | Решение по черновику (approve) | orchestrator | ❌ | 422 | 8ms | Expected HTTP {200, 409}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 8 | Проверка document_id после approve | orchestrator | ❌ | 422 | 2ms | Expected HTTP {200, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 9 | Проверка документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика (image/png для OR-14) | orchestrator | ❌ | 422 | 4ms | Expected HTTP 202, got 422 | body: {"detail":[{"type":"missing","loc":["body","source_type"],"msg":"Field required","input":null}]} |
| 11 | Статус задачи image (OR-14) | orchestrator | ❌ | 404 | 3ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/11

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 6ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 14ms | {"data":{"classifier_system":"MKS","code":"99.874303","full_name":"Pipeline тестовый классификатор 20260620130846874303","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 7ms | data = [{'classifier_system': 'MKS', 'code': '98.960891', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 5ms | data = {'classifier_system': 'MKS', 'code': '99.874303', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 14ms | data = {'classifier_system': 'MKS', 'code': '99.874303', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 14ms | data = {'classifier_system': 'MKS', 'code': '99.874303', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 12ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 13ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260620130846874303","standard_term":"Pipeline тест 20260620130846874303","normalized_value":"pipeline тест 20260620130846874303","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 5ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 12ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260620130846874303', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWQ0ZWE5NjJjM2MwNiIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 11ms | {"data":{"classifier_system":"MKS","code":"98.223956","full_name":"Pipeline quarantine классификатор 20260620180847223956","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 23ms | data = {'id': 8, 'doc_code': 'QUAR-TEST-20260620180847223956', 'title': 'Pipeline quara |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 14ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.960891', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 20ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.960891', 'status': |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 6ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 24ms | data = {'id': 9, 'doc_code': 'QUAR-TEST2-20260620180847223956', 'title': 'Pipeline quar |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 17ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.960891', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 12ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 6ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-20 13:08:47 UTC_
