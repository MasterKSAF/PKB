# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-17 18:09:52 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 8086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 8080 | ✅ | — | ✅ | — | ✅ |
| Orchestrator | 8081 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parser Service | 8087 | ✅ | — | ✅ | ✅ | ✅ |
| Query Service | 8083 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Builder | 8090 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ✅ | ✅ |
| Registry Service | 8084 | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| **Total** | | **10/10** | **6/6** | **10/10** | ✅ | ✅ |

### 📋 Pipeline статусы по сервисам

| Service | Documents | Chat | Registry | Lifecycle | AdminUsers | Quarantine | Orchestrator | MultiDoc | Status |
|---------|:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:|:------:|
| Auth Service | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| Converter-Validator | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| Gateway | — | — | — | — | — | — | — | — | ✅ |
| Orchestrator | — | — | — | — | — | — | ✅ | — | ✅ |
| Parser Service | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| Query Service | — | ✅ | — | — | ✅ | — | — | — | ✅ |
| RAG Builder | ✅ | — | — | ✅ | — | — | — | ✅ | ✅ |
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | ✅ | ✅ |
| Registry Service | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| TEI | — | — | — | — | — | — | — | — | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | **10/10** | **5/5** | **11/11** | **12/12** | **10/10** | **10/10** | **8/8** | **19/19** | ✅ |

#### 🔍 Пояснения к ❌ в проверках

_Нет замечаний_


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 18 | 18 | 0 | 0 | ✅ |
| Converter-Validator | 8086 | ✅ | — | 4 | 4 | 0 | 0 | ✅ |
| Gateway | 8080 | ✅ | — | 120 | 120 | 0 | 0 | ✅ |
| Orchestrator | 8081 | ✅ | ✅ | 32 | 32 | 0 | 0 | ✅ |
| Parser Service | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | ✅ | ✅ | 20 | 20 | 0 | 0 | ✅ |
| RAG Builder | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 33 | 33 | 0 | 0 | ✅ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **243** | **243** | **0** | **0** | ✅ |

### ⚠️ Workaround-предупреждения по сервисам

- **Query Service**: ⚠️ POST /chat/feedback: docs требует rating:int + rating_status:string, но сервис принимает только rating:string (без rating_status). Docs новее реализации.

- **Registry Service**: ⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.


---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
| `admin_user_lifecycle` | Admin управление пользователем (создание → работа → аудит → деактивация) | ✅ | 10 | 10 | 0 | ✅ |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | ✅ | 5 | 5 | 0 | ✅ |
| `document_processing` | Полный цикл обработки документа | ✅ | 10 | 10 | 0 | ✅ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 12 | 0 | ✅ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 19 | 0 | ✅ |
| `orchestrator_draft_lifecycle` | Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление) | ✅ | 8 | 8 | 0 | ✅ |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | ✅ | 11 | 11 | 0 | ✅ |
| `registry_quarantine` | Карантин классификаторов: accept/reject + валидация | ✅ | 10 | 10 | 0 | ✅ |
---

### 🗄️ БД PostgreSQL


Общий статус: **✅**

| Проверка | Статус | Детали |
|----------|:------:|--------|
| База данных `pkb_neuro` | ✅ | существует |
| Расширения | ✅ | ltree, pg_trgm, pgcrypto, plpgsql, uuid-ossp, vector |
| Схемы | ✅ | auth_service, public, rag, registry |
| Registry таблицы | ✅ | 10 таблиц |
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
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация admin | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 240ms | user_id = u-411b220c59e8 |
| 3 | Список пользователей | auth | ✅ | 200 | 10ms | users = [{'user_id': 'u-411b220c59e8', 'email': 'pipeline-user-20260617230919329531@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQxMWIyMjBjNTllOCIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 8ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 11ms | message_id = 6 |
| 7 | Получение истории чата | query | ✅ | 200 | 6ms | messages = [{'message_id': 5, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Журнал аудита | auth | ✅ | 200 | 8ms | events = [{'event_id': 'evt-7033c3eff626', 'user_id': 'u-411b220c59e8', 'action': 'auth.l |
| 9 | Деактивация пользователя | auth | ✅ | 200 | 24ms | is_active = False |
| 10 | Проверка 401 после деактивации | auth | ✅ | 401 | 6ms | ответ: Неверные учётные данные |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 5/5
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 9ms | session_id = 4 |
| 3 | Отправка сообщения | query | ✅ | 202 | 10ms | message_id = 8 |
| 4 | Текстовый поиск | query | ✅ | 200 | 2ms | results = [{'section_id': 420042, 'document_id': 'doc-norm-001', 'document_title': 'Правил |
| 5 | Гибридный поиск RAG Search | rag_search | ✅ | 200 | 22ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 5/5

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18B9F0AEB2608273</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 20ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 38ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 2026ms | Все поля валидны |
| 7 | Конвертация JSON | converter_validator | ✅ | 200 | 33ms | task_id = 12345 |
| 8 | Сохранение документа в Registry | registry | ✅ | 201 | 12ms | {"data":{"id":3,"doc_code":"PIPELINE-TEST-1781719760","title":"Тестовый документ pipeline 1781719760","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"a4860ceb2181533f9bd9b4b398cf6d007a2bac0cb0655de5157a6ec0f9e8e252","classification_status":{},"metadata":{}}} |
| 9 | Построение чанков и индексация | rag_builder | ✅ | 201 | 11ms | {"document_id":1,"status":"completed","indexed_at":"2026-06-17T21:09:22.882708+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1}} |
| 10 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 14ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 16ms | {"data":{"id":4,"doc_code":"LIFECYCLE-1781719762","title":"Lifecycle тест 1781719762","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"def8111b9939a2e39ee07054101af65a58d4475525848cacc6c612bd50b53018","classification_status":{},"metadata":{}}} |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 201 | 11ms | status = completed |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 13ms | data = {'id': '4', 'status': 'uploaded', 'previous_status': None, 'history_id': '2', 'u |
| 5 | Повторное построение индекса | rag_builder | ✅ | 201 | 10ms | status = completed |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 22ms | results = [] |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 11ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 8ms | {"document_id":4,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 11ms | results = [] |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 16ms | {"data":{"id":5,"doc_code":"LIFECYCLE-RECOVER-1781719762","title":"Lifecycle тест восстановленный 1781719762","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"f1adb7de2ba63f0d73cf604a616bfcb1ba2f84b2fdecaf75b2a3e33880e73b44","classification_status":{},"metadata":{}}} |
| 11 | Финальное построение индекса | rag_builder | ✅ | 201 | 13ms | status = completed |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 9ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18B9F0B4528C8E04</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 18ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 38ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 4047ms | Все поля валидны |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 33ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-17T18:09:49.039413Z","parser":{}},"document":{"source":{"file_name":"","file_hash_sha256":"","page_count":1},"metadata":{"doc_code":"","title":"Без названия","normalized_title |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":6,"doc_code":"MULTI1-1781719784","title":"Multi-doc тест 1 1781719784","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"7ebae33daed75754aeb9b4f810f0bf12536366e02b23f131789e219befd4df4b","classification_status":{},"metadata":{}}} |
| 9 | Построение индекса #1 | rag_builder | ✅ | 201 | 11ms | status = completed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 15ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 37ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 2024ms | Все поля валидны |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 33ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-17T18:09:51.182338Z","parser":{}},"document":{"source":{"file_name":"","file_hash_sha256":"","page_count":1},"metadata":{"doc_code":"","title":"Без названия","normalized_title |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 12ms | {"data":{"id":7,"doc_code":"MULTI2-1781719784","title":"Multi-doc тест 2 1781719784","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"3a7681589d2912301df36b8e5c74fb1536344a2fec2476c76fac5867b04db60e","classification_status":{},"metadata":{}}} |
| 16 | Построение индекса #2 | rag_builder | ✅ | 201 | 11ms | status = completed |
| 17 | Поиск по общему запросу | rag_search | ✅ | 200 | 29ms | results = [{'chunk_id': 7, 'document_id': 6, 'document_title': 'Multi-doc тест 1 178171978 |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 12ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ✅ | 200 | 11ms | results = [{'chunk_id': 6, 'document_id': 5, 'document_title': 'Lifecycle тест восстановле |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 8/8
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 247ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 21ms | draft_id = 4 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 38ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 3ms | draft_id = 4 |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 19ms | {"draft_id":4,"task_id":3,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 6ms | status = processing |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 15ms | status = proceeding |
| 8 | Проверка 404 после решения | orchestrator | ✅ | 200 | 3ms | {"draft_id":4,"document_key":"pipeline-draft-key-20260617230951277991","file_key":"f-6c149ba59fef","status":"uploaded","document_id":null,"created_by":"u-mock-001","created_at":"2026-06-08T10:00:00Z","updated_at":"2026-06-08T10:00:00Z"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 8/8

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 6ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 10ms | {"data":{"classifier_system":"MKS","code":"99.666159","full_name":"Pipeline тестовый классификатор 20260617180951666159","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 6ms | data = [{'classifier_system': 'MKS', 'code': '98.719742', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 5ms | data = {'classifier_system': 'MKS', 'code': '99.666159', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 10ms | data = {'classifier_system': 'MKS', 'code': '99.666159', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 10ms | data = {'classifier_system': 'MKS', 'code': '99.666159', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 11ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 11ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260617180951666159","standard_term":"Pipeline тест 20260617180951666159","normalized_value":"pipeline тест 20260617180951666159","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 5ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 10ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260617180951666159', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 232ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTExNzY1YTEzMWZlMCIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 10ms | {"data":{"classifier_system":"MKS","code":"98.018088","full_name":"Pipeline quarantine классификатор 20260617230952018088","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 19ms | data = {'id': 8, 'doc_code': 'QUAR-TEST-20260617230952018088', 'title': 'Pipeline quara |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 11ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.719742', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 17ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.719742', 'status': |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 6ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 19ms | data = {'id': 9, 'doc_code': 'QUAR-TEST2-20260617230952018088', 'title': 'Pipeline quar |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 16ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.719742', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 12ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-17 18:09:52 UTC_
