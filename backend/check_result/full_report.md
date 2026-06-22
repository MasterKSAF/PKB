# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-22 14:47:05 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 8086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 8080 | ✅ | — | ✅ | — | ✅ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| Orchestrator | 8081 | ✅ | ✅ | ❌ | ❌ | ❌ |
| Parser Service | 8087 | ✅ | — | ✅ | ✅ | ✅ |
| Query Service | 8083 | ✅ | ✅ | ❌ | ✅ | ❌ |
| RAG Builder | 8090 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ❌ | ❌ |
| Registry Service | 8084 | ✅ | ✅ | ❌ | ❌ | ❌ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| **Total** | | **10/10** | **6/6** | **7/10** | ❌ | ❌ |

### 📋 Pipeline статусы по сервисам

| Service | Documents | Chat | Registry | Lifecycle | AdminUsers | Quarantine | Orchestrator | MultiDoc | Status |
|---------|:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:|:------:|
| Auth Service | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| Converter-Validator | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| Gateway | — | — | — | — | — | — | — | — | 🟡 dev |
| MinIO | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | 🟡 dev |
| Orchestrator | — | — | — | — | — | — | ❌ | — | ❌ |
| Parser Service | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| Query Service | — | ✅ | — | — | ✅ | — | — | — | ✅ |
| RAG Builder | ✅ | — | — | ✅ | — | — | — | ✅ | ✅ |
| RAG Search | ❌ | ✅ | — | ❌ | — | — | — | ❌ | ❌ |
| Registry Service | ❌ | — | ✅ | ❌ | — | ✅ | ❌ | ✅ | ❌ |
| TEI | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | **12/15** | **6/6** | **11/11** | **8/12** | **16/16** | **10/10** | **1/11** | **17/19** | ❌ |

#### 🔍 Пояснения к результатам

- **Orchestrator**: API: 4 эндпоинт(ов) упало; ⏭️ 10 эндпоинтов пропущено — нет контекста (prepare не создал данные); Pipelines: сбой в Orchestrator

- **Query Service**: API: 3 эндпоинт(ов) упало

- **RAG Search**: Pipelines: сбой в Documents, Lifecycle, MultiDoc

- **Registry Service**: API: 9 эндпоинт(ов) упало; ⏭️ 8 эндпоинтов пропущено — нет контекста (prepare не создал данные); Pipelines: сбой в Documents, Lifecycle, Orchestrator


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| Converter-Validator | 8086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Gateway | 8080 | ✅ | — | 72 | 72 | 0 | 0 | ✅ |
| Orchestrator | 8081 | ✅ | ✅ | 34 | 20 | **4** | **10** | ❌ |
| Parser Service | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | ✅ | ✅ | 26 | 23 | **3** | 0 | ❌ |
| RAG Builder | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 50 | 33 | **9** | **8** | ❌ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **222** | **188** | **16** | **18** | ❌ |

### ⚠️ Workaround-предупреждения по сервисам

- **Auth Service**: PATCH /admin/users/{id}: docs ожидает audit_log_id, но сервис его не возвращает

- **Query Service**: ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

- **Registry Service**: ⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.


---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
| `admin_user_lifecycle` | Admin управление пользователем (создание → работа → аудит → деактивация) | ✅ | 16 | 16 | 0 | ✅ |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | ✅ | 6 | 6 | 0 | ✅ |
| `document_approval` | Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик) | ✅ | 10 | 1 | 1 | ❌ |
| `document_processing` | Полный цикл обработки документа | ✅ | 15 | 12 | 3 | ❌ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 8 | 4 | ❌ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 17 | 2 | ❌ |
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
- Passed: 16/16
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация admin | auth | ✅ | 200 | 229ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 234ms | user_id = u-da52813aa0bc |
| 3 | Список пользователей | auth | ✅ | 200 | 11ms | users = [{'user_id': 'u-da52813aa0bc', 'email': 'pipeline-user-20260622194629977937@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWRhNTI4MTNhYTBiYyIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 9ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 10ms | message_id = 6 |
| 7 | Получение истории чата | query | ✅ | 200 | 8ms | messages = [{'message_id': 5, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 | auth | ✅ | 401 | 224ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 | auth | ✅ | 401 | 221ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 | auth | ✅ | 401 | 225ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 | auth | ✅ | 401 | 224ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 | auth | ✅ | 401 | 222ms | {"error":{"code":"ACCOUNT_LOCKED","message":"Аккаунт заблокирован после нескольких неудачных попыток входа","details":{"retry_after_seconds":1800}}} |
| 13 | Проверка блокировки после 5 неудач | auth | ✅ | 401 | 7ms | {"error":{"code":"ACCOUNT_LOCKED","message":"Аккаунт заблокирован после нескольких неудачных попыток входа","details":{"retry_after_seconds":1800}}} |
| 14 | Журнал аудита | auth | ✅ | 200 | 7ms | events = [{'event_id': 'evt-197a35a4e3ce', 'user_id': 'u-da52813aa0bc', 'action': 'auth.l |
| 15 | Деактивация пользователя | auth | ✅ | 200 | 29ms | is_active = False |
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
| 1 | Аутентификация | auth | ✅ | 200 | 229ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 9ms | session_id = 4 |
| 3 | Отправка сообщения | query | ✅ | 202 | 10ms | message_id = 8 |
| 4 | Текстовый поиск | query | ✅ | 200 | 3ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped | query | ✅ | 200 | 3ms | enrichment_skipped=False |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 12ms | results=[] (нет результатов, валидация по source не требуется) |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 1/10
- Failed: 1
- Skipped: 8

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 61ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Stat |
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
- Passed: 12/15
- Failed: 3
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BB6E8483B19931</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 20ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 36ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 3ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4047ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 5ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 2ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ❌ | 307 | 2ms | Expected HTTP {200, 422}, got 307 |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 36ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 36ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 19ms | {"data":{"id":4,"doc_code":"PIPELINE-TEST-1782139592","title":"Тестовый документ pipeline 1782139592","source_type":"GOST","mks_oks_code":"47.020","era":"RF","validity_status":"active","title_hash_sha256":"e77fed6bf1bbc0eb2be008bb560a9d6279b511ed818c25f6882ef1c2c4b08771","classification_status":{}," |
| 13 | Проверка preview_snapshot в документе | registry | ❌ | 307 | 2ms | Expected HTTP 200, got 307 |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 201 | 11ms | {"document_id":1,"status":"completed","indexed_at":"2026-06-22T17:46:37.208530+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1}} |
| 15 | Поиск по индексу RAG Search | rag_search | ❌ | 500 | 3324ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: column d.valid_from does not exist","details":{}}} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 12/15

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 8/12
- Failed: 4
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 14ms | {"data":{"id":5,"doc_code":"LIFECYCLE-1782139600","title":"Lifecycle тест 1782139600","source_type":"GOST","mks_oks_code":"47.020","era":"RF","validity_status":"active","title_hash_sha256":"7733f597e53ed52c53affc0609faaa3f92a7b21791b91af356784784da2dd4e7","classification_status":{},"metadata":{}}} |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 201 | 10ms | status = completed |
| 4 | Обновление метаданных документа | registry | ❌ | 422 | 5ms | Expected HTTP 200, got 422 | body: {"detail":{"error":{"code":"VALIDATION_ERROR","message":"Missing status"}}} |
| 5 | Повторное построение индекса | rag_builder | ✅ | 201 | 10ms | status = completed |
| 6 | Поиск по индексу RAG Search | rag_search | ❌ | 500 | 3321ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: column d.valid_from does not exist","details":{}}} |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 13ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 9ms | {"document_id":5,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ❌ | 500 | 3329ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: column d.valid_from does not exist","details":{}}} |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 13ms | {"data":{"id":6,"doc_code":"LIFECYCLE-RECOVER-1782139600","title":"Lifecycle тест восстановленный 1782139600","source_type":"GOST","mks_oks_code":"47.020","era":"RF","validity_status":"active","title_hash_sha256":"bd128f23962e53b1f5be65de98961f722f2c8fff520124ca1d5f4b1fa4d426a8","classification_stat |
| 11 | Финальное построение индекса | rag_builder | ✅ | 201 | 10ms | status = completed |
| 12 | Финальный поиск по индексу | rag_search | ❌ | 500 | 3321ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: column d.valid_from does not exist","details":{}}} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 8/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 17/19
- Failed: 2
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 229ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BB6E88CAD3DF15</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 14ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 39ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 3ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 2019ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 36ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-22T14:46:53.469252Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782139611.pdf","file_h |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 14ms | {"data":{"id":7,"doc_code":"MULTI1-1782139611","title":"Multi-doc тест 1 1782139611","source_type":"GOST","mks_oks_code":"47.020","era":"RF","validity_status":"active","title_hash_sha256":"7236cbddeacd5c9a8781d10e3dbea3ba95c921de9b4a26ff274271e259d67cfe","classification_status":{},"metadata":{}}} |
| 9 | Построение индекса #1 | rag_builder | ✅ | 201 | 11ms | status = completed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 12ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 38ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 3ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4030ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 37ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-22T14:46:57.621087Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782139611.pdf","file_h |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":8,"doc_code":"MULTI2-1782139611","title":"Multi-doc тест 2 1782139611","source_type":"GOST","mks_oks_code":"47.020","era":"RF","validity_status":"active","title_hash_sha256":"d08b99b79f5d77a8df1ceddb55544d57ed6f4876e65812acf8d806bc308dfdcb","classification_status":{},"metadata":{}}} |
| 16 | Построение индекса #2 | rag_builder | ✅ | 201 | 11ms | status = completed |
| 17 | Поиск по общему запросу | rag_search | ❌ | 500 | 3316ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: column d.valid_from does not exist","details":{}}} |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 11ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ❌ | 500 | 3319ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: column d.valid_from does not exist","details":{}}} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 17/19

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 1/11
- Failed: 9
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ❌ | 500 | 64ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Stat |
| 3 | Статус задачи (longpoll) | orchestrator | ❌ | 404 | 2ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} |
| 4 | Детали черновика | orchestrator | ❌ | 422 | 5ms | Expected HTTP 200, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 5 | Запуск превью черновика | orchestrator | ❌ | 422 | 5ms | Expected HTTP {200, 202, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 6 | Статус превью | orchestrator | ❌ | 422 | 4ms | Expected HTTP {200, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 7 | Решение по черновику (approve) | orchestrator | ❌ | 422 | 6ms | Expected HTTP {200, 409}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 8 | Проверка document_id после approve | orchestrator | ❌ | 422 | 2ms | Expected HTTP {200, 404}, got 422 | body: {"detail":[{"type":"int_parsing","loc":["path","draft_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"{draft_id}"}]} |
| 9 | Проверка документа в Registry | registry | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика (image/png для OR-14) | orchestrator | ❌ | 500 | 60ms | Expected HTTP 202, got 500 | body: {"detail":{"error":{"code":"DRAFT_CREATION_FAILED","message":"Ошибка при создании черновика в Registry","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Stat |
| 11 | Статус задачи image (OR-14) | orchestrator | ❌ | 404 | 2ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 1/11

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 7ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 10ms | {"data":{"classifier_system":"MKS","code":"99.702162","full_name":"Pipeline тестовый классификатор 20260622144704702162","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 5ms | data = [{'classifier_system': 'MKS', 'code': '98.139575', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 5ms | data = {'classifier_system': 'MKS', 'code': '99.702162', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 9ms | data = {'classifier_system': 'MKS', 'code': '99.702162', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 10ms | data = {'classifier_system': 'MKS', 'code': '99.702162', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 11ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 9ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260622144704702162","standard_term":"Pipeline тест 20260622144704702162","normalized_value":"pipeline тест 20260622144704702162","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 5ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 9ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260622144704702162', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTdjNDU4NTEyMTA4ZiIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 11ms | {"data":{"classifier_system":"MKS","code":"98.032202","full_name":"Pipeline quarantine классификатор 20260622194705032202","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 18ms | data = {'id': 9, 'doc_code': 'QUAR-TEST-20260622194705032202', 'title': 'Pipeline quara |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 11ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.139575', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 19ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.139575', 'status': |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 17ms | data = {'id': 10, 'doc_code': 'QUAR-TEST2-20260622194705032202', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 15ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.139575', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 10ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-22 14:47:05 UTC_
