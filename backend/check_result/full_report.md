# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-15 19:31:28 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Converter-Validator | 8086 | ✅ | — | ✅ | ✅ | ✅ |
| Gateway | 8080 | ✅ | — | ✅ | — | ✅ |
| Orchestrator | 8081 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parser Service | 8087 | ✅ | — | ❌ | ✅ | ❌ |
| Query Service | 8083 | ✅ | ✅ | ✅ | ✅ | ✅ |
| RAG Builder | 8090 | ✅ | ❌ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ❌ | ❌ |
| Registry Service | 8084 | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEI | 8092 | ✅ | — | ✅ | — | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| **Total** | | **10/10** | **5/6** | **9/10** | ❌ | ❌ |

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
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | ❌ | ❌ |
| Registry Service | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | ✅ |
| TEI | — | — | — | — | — | — | — | — | ✅ |
| OCR Service | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | **10/10** | **5/5** | **11/11** | **12/12** | **10/10** | **10/10** | **8/8** | **17/19** | ❌ |

#### 🔍 Пояснения к ❌ в проверках

- **Parser Service**: API: 1 эндпоинт(ов) упало

- **RAG Builder**: CheckDb: RAG Builder использует validate_startup_migrations(), не create_all()

- **RAG Search**: Pipelines: сбой в MultiDoc


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 8082 | ✅ | ✅ | 18 | 18 | 0 | 0 | ✅ |
| Converter-Validator | 8086 | ✅ | — | 4 | 4 | 0 | 0 | ✅ |
| Gateway | 8080 | ✅ | — | 120 | 120 | 0 | 0 | ✅ |
| Orchestrator | 8081 | ✅ | ✅ | 32 | 32 | 0 | 0 | ✅ |
| Parser Service | 8087 | ✅ | — | 5 | 4 | **1** | 0 | ❌ |
| Query Service | 8083 | ✅ | ✅ | 20 | 20 | 0 | 0 | ✅ |
| RAG Builder | 8090 | ✅ | ❌ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 33 | 33 | 0 | 0 | ✅ |
| TEI | 8092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ❌ | **243** | **242** | **1** | **0** | ❌ |

### ⚠️ Workaround-предупреждения по сервисам

- **Converter-Validator**: ⚠️ Converter health на /health, а не /api/v1/health — сервис без префикса.

- **Converter-Validator**: ⚠️ task_id/version_id передаём как str — сервис требует str, docs API — int.

- **Converter-Validator**: ⚠️ document_id/validation_id принимаем как str — сервис возвращает UUID, docs — int.

- **Gateway**: Gateway — отдельный mock-сервис, тестируется независимо от других сервисов.

- **Gateway**: Эндпоинты и prepare определены строго по openapi.json mock'а.

- **Parser Service**: ⚠️ Реальная реализация расходится с docs: process требует version_id (docs: mode+file_key).

- **Parser Service**: ⚠️ Health Parser на /health, а не /api/v1/health — сервис не использует префикс.

- **Query Service**: ⚠️ POST /chat/feedback: docs требует rating:int + rating_status:string, но сервис принимает только rating:string (без rating_status). Docs новее реализации.

- **RAG Builder**: ⚠️ Документация не упоминает JWT, но RAG Builder требует bearer token. Исправлено: supervisord передаёт JWT_SECRET (RAG Builder) = JWT_SECRET_KEY (Auth).

- **RAG Builder**: ⚠️ RAG Builder принимает document_id только как UUID (pydantic: uuid_type). int_to_uuid() конвертирует BIGINT в UUID строку.

- **RAG Builder**: ⚠️ RAG Search падает с `operator does not exist: bigint = uuid` — внутренний SQL JOIN между registry.documents (BIGINT) и rag.document_chunks (UUID). НЕ связан с форматом входных данных.

- **RAG Builder**: ⚠️ RAG Builder падал при старте: alembic migration 20260614_0002 не применилась — FK document_id UUID vs registry.documents.id BIGINT. Migration пропущена, таблица создана вручную с BIGINT document_id.

- **RAG Builder**: ⚠️ Подключена заглушка docker/patch_rag_tables.py — при full-report/coverage/patch-rag проверяет и создаёт таблицы, если их нет.

- **Registry Service**: ⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.


---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
| `admin_user_lifecycle` | Admin управление пользователем (создание → работа → аудит → деактивация) | ✅ | 10 | 10 | 0 | ✅ |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | ✅ | 5 | 5 | 0 | ✅ |
| `document_processing` | Полный цикл обработки документа | ✅ | 10 | 10 | 0 | ✅ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 12 | 0 | ✅ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 17 | 2 | ❌ |
| `orchestrator_draft_lifecycle` | Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление) | ✅ | 8 | 8 | 0 | ✅ |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | ✅ | 11 | 11 | 0 | ✅ |
| `registry_quarantine` | Карантин классификаторов: accept/reject + валидация | ✅ | 10 | 10 | 0 | ✅ |
---

### 🗄️ БД PostgreSQL


Общий статус: **❌**

| Проверка | Статус | Детали |
|----------|:------:|--------|
| База данных `pkb_neuro` | ✅ | существует |
| Расширения | ✅ | ltree, pg_trgm, pgcrypto, plpgsql, uuid-ossp, vector |
| Схемы | ✅ | auth_service, public, rag, registry |
| Registry таблицы | ✅ | 10 таблиц |
| RAG: Таблица `document_chunks` | ✅ |
| RAG: Колонка `embedding` (vector) | ✅ |
| RAG: HNSW индекс `idx_chunks_embedding` | ❌ |
| RAG: GIN индекс `idx_chunks_tsv` | ❌ |
| RAG: Триггер `trg_chunks_tsv` | ❌ |
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
| `rag_builder_service` | rag | ❌ | RAG Builder: document_chunks (HNSW/GIN индексы) |
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
| 1 | Аутентификация admin | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 243ms | user_id = u-495143f8fac5 |
| 3 | Список пользователей | auth | ✅ | 200 | 12ms | users = [{'user_id': 'u-495143f8fac5', 'email': 'pipeline-user-20260616003112364619@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 233ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ5NTE0M2Y4ZmFjNSIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 8ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 15ms | message_id = 6 |
| 7 | Получение истории чата | query | ✅ | 200 | 8ms | messages = [{'message_id': 5, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Журнал аудита | auth | ✅ | 200 | 8ms | events = [{'event_id': 'evt-899df809c620', 'user_id': 'u-495143f8fac5', 'action': 'auth.l |
| 9 | Деактивация пользователя | auth | ✅ | 200 | 25ms | is_active = False |
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
| 1 | Аутентификация | auth | ✅ | 200 | 234ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 9ms | session_id = 4 |
| 3 | Отправка сообщения | query | ✅ | 202 | 10ms | message_id = 8 |
| 4 | Текстовый поиск | query | ✅ | 200 | 2ms | results = [{'section_id': 420042, 'document_id': 'doc-norm-001', 'document_title': 'Правил |
| 5 | Гибридный поиск RAG Search | rag_search | ✅ | 200 | 19ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 5/5

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18B957FD7D027836</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 18ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 39ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 6ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4034ms | Все поля валидны |
| 7 | Конвертация JSON | converter_validator | ✅ | 200 | 34ms | task_id = 12345 |
| 8 | Сохранение документа в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":3,"doc_code":"PIPELINE-TEST-1781551873","title":"Тестовый документ pipeline 1781551873","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"a48206d4a1fef224d4773df1f90926f5e64d9fd3f3631c51f8d4c9b71f2f2252","classification_status":{},"metadata":{}}} |
| 9 | Построение чанков и индексация | rag_builder | ✅ | 201 | 16ms | {"document_id":"00000000-0000-0000-0000-000000000001","status":"completed","indexed_at":"2026-06-15T22:31:18.019990+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1}} |
| 10 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 24ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 236ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 13ms | doc_id=4 → doc_id_uuid=00000000-0000-0000-0000-000000000004 |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 201 | 14ms | status = completed |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 15ms | data = {'id': '4', 'status': 'uploaded', 'previous_status': None, 'history_id': '2', 'u |
| 5 | Повторное построение индекса (recovery) | rag_builder | ✅ | 201 | 13ms | status = completed |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 10ms | results = [] |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 13ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 15ms | {"document_id":"00000000-0000-0000-0000-000000000004","deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 14ms | results = [] |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 21ms | doc_id=4 → doc_id2_uuid=00000000-0000-0000-0000-000000000004 |
| 11 | Финальное построение индекса | rag_builder | ✅ | 201 | 19ms | status = completed |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 15ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 17/19
- Failed: 2
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18B957FEAC925878</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 12ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 39ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 7ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 4065ms | Все поля валидны |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 34ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-15T19:31:23.093370Z","parser":{}},"document":{"source":{"file_name":"","file_hash_sha256":"","page_count":1},"metadata":{"doc_code":"","title":"Без названия","normalized_title |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 15ms | doc_id_1=6 → doc_id_1_uuid=00000000-0000-0000-0000-000000000006 |
| 9 | Построение индекса #1 | rag_builder | ✅ | 201 | 18ms | status = completed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 15ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 39ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 4ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4053ms | Все поля валидны |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 34ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-15T19:31:27.285689Z","parser":{}},"document":{"source":{"file_name":"","file_hash_sha256":"","page_count":1},"metadata":{"doc_code":"","title":"Без названия","normalized_title |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 12ms | doc_id_2=7 → doc_id_2_uuid=00000000-0000-0000-0000-000000000007 |
| 16 | Построение индекса #2 | rag_builder | ✅ | 201 | 18ms | status = completed |
| 17 | Поиск по общему запросу | rag_search | ❌ | 500 | 29ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: operator does not exist: bigint = uuid\nHINT:  No operator matches the given name and argument types. You might need to add explicit type casts.","details":{}}} |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 13ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ❌ | 500 | 19ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: operator does not exist: bigint = uuid\nHINT:  No operator matches the given name and argument types. You might need to add explicit type casts.","details":{}}} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 17/19

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 8/8
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 238ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 26ms | draft_id = 4 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 40ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 3ms | draft_id = 4 |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 19ms | {"draft_id":4,"task_id":3,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 7ms | status = processing |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 18ms | status = proceeding |
| 8 | Проверка 404 после решения | orchestrator | ✅ | 200 | 5ms | {"draft_id":4,"document_key":"pipeline-draft-key-20260616003127458747","file_key":"f-6c149ba59fef","status":"uploaded","document_id":null,"created_by":"u-mock-001","created_at":"2026-06-08T10:00:00Z","updated_at":"2026-06-08T10:00:00Z"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 8/8

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 235ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 8ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 11ms | {"data":{"classifier_system":"MKS","code":"99.866255","full_name":"Pipeline тестовый классификатор 20260615193127866255","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 6ms | data = [{'classifier_system': 'MKS', 'code': '98.551858', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 7ms | data = {'classifier_system': 'MKS', 'code': '99.866255', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 14ms | data = {'classifier_system': 'MKS', 'code': '99.866255', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 12ms | data = {'classifier_system': 'MKS', 'code': '99.866255', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 12ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 11ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260615193127866255","standard_term":"Pipeline тест 20260615193127866255","normalized_value":"pipeline тест 20260615193127866255","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 8ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 14ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260615193127866255', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFlNmFlMjIxOTZhMCIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 15ms | {"data":{"classifier_system":"MKS","code":"98.230181","full_name":"Pipeline quarantine классификатор 20260616003128230181","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 30ms | data = {'id': 8, 'doc_code': 'QUAR-TEST-20260616003128230181', 'title': 'Pipeline quara |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 25ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.551858', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 22ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.551858', 'status': |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 10ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 25ms | data = {'id': 9, 'doc_code': 'QUAR-TEST2-20260616003128230181', 'title': 'Pipeline quar |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 17ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.551858', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 14ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-15 19:31:28 UTC_
