# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-16 11:20:42 UTC

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
| RAG Builder | 8090 | ✅ | ❌ | ✅ | ✅ | ✅ |
| RAG Search | 8091 | ✅ | — | ✅ | ❌ | ❌ |
| Registry Service | 8084 | ✅ | ✅ | ✅ | ✅ | ✅ |
| TEI | 8092 | ✅ | — | ✅ | — | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| **Total** | | **10/10** | **5/6** | **10/10** | ❌ | ❌ |

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
| Parser Service | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | ✅ | ✅ | 20 | 20 | 0 | 0 | ✅ |
| RAG Builder | 8090 | ✅ | ❌ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 8084 | ✅ | ✅ | 33 | 33 | 0 | 0 | ✅ |
| TEI | 8092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ❌ | **243** | **243** | **0** | **0** | ✅ |

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
| 1 | Аутентификация admin | auth | ✅ | 200 | 248ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создание пользователя | auth | ✅ | 201 | 246ms | user_id = u-f98ee049500b |
| 3 | Список пользователей | auth | ✅ | 200 | 16ms | users = [{'user_id': 'u-f98ee049500b', 'email': 'pipeline-user-20260616162026920256@test |
| 4 | Аутентификация нового пользователя | auth | ✅ | 200 | 238ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWY5OGVlMDQ5NTAwYiIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь) | query | ✅ | 201 | 8ms | session_id = 3 |
| 6 | Отправка сообщения (новый пользователь) | query | ✅ | 202 | 13ms | message_id = 6 |
| 7 | Получение истории чата | query | ✅ | 200 | 8ms | messages = [{'message_id': 5, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Журнал аудита | auth | ✅ | 200 | 10ms | events = [{'event_id': 'evt-af91ac3630db', 'user_id': 'u-f98ee049500b', 'action': 'auth.l |
| 9 | Деактивация пользователя | auth | ✅ | 200 | 31ms | is_active = False |
| 10 | Проверка 401 после деактивации | auth | ✅ | 401 | 5ms | ответ: Неверные учётные данные |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 5/5
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создание чат-сессии | query | ✅ | 201 | 10ms | session_id = 4 |
| 3 | Отправка сообщения | query | ✅ | 202 | 18ms | message_id = 8 |
| 4 | Текстовый поиск | query | ✅ | 200 | 4ms | results = [{'section_id': 420042, 'document_id': 'doc-norm-001', 'document_title': 'Правил |
| 5 | Гибридный поиск RAG Search | rag_search | ✅ | 200 | 26ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 5/5

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18B98BCA3E522B2D</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 24ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 41ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 3ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4034ms | Все поля валидны |
| 7 | Конвертация JSON | converter_validator | ✅ | 200 | 43ms | task_id = 12345 |
| 8 | Сохранение документа в Registry | registry | ✅ | 201 | 15ms | {"data":{"id":3,"doc_code":"PIPELINE-TEST-1781608828","title":"Тестовый документ pipeline 1781608828","source_type":"GOST","era":"RF","validity_status":"active","title_hash_sha256":"ae7835c4f5f58da6b2d58a05058005ab66d9e1432aea000aed02ba91208365a3","classification_status":{},"metadata":{}}} |
| 9 | Построение чанков и индексация | rag_builder | ✅ | 201 | 16ms | {"document_id":"00000000-0000-0000-0000-000000000001","status":"completed","indexed_at":"2026-06-16T14:20:32.524424+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1}} |
| 10 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 15ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создание документа в Registry | registry | ✅ | 201 | 19ms | doc_id=4 → doc_id_uuid=00000000-0000-0000-0000-000000000004 |
| 3 | Первая попытка построения индекса | rag_builder | ✅ | 201 | 17ms | status = completed |
| 4 | Обновление метаданных документа | registry | ✅ | 200 | 13ms | data = {'id': '4', 'status': 'uploaded', 'previous_status': None, 'history_id': '2', 'u |
| 5 | Повторное построение индекса (recovery) | rag_builder | ✅ | 201 | 16ms | status = completed |
| 6 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 19ms | results = [] |
| 7 | Удаление документа из Registry | registry | ✅ | 200 | 11ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG | rag_builder | ✅ | 200 | 11ms | {"document_id":"00000000-0000-0000-0000-000000000004","deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата | rag_search | ✅ | 200 | 23ms | results = [] |
| 10 | Воссоздание документа в Registry | registry | ✅ | 201 | 24ms | doc_id=4 → doc_id2_uuid=00000000-0000-0000-0000-000000000004 |
| 11 | Финальное построение индекса | rag_builder | ✅ | 201 | 15ms | status = completed |
| 12 | Финальный поиск по индексу | rag_search | ✅ | 200 | 13ms | results = [] |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 17/19
- Failed: 2
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18B98BCB645C35D1</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 14ms |  |
| 4 | Запуск парсинга #1 | parser | ✅ | 202 | 44ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll) | parser | ✅ | 200 | 3ms | status = accepted |
| 6 | Результат парсинга #1 | parser | ✅ | 200 | 4028ms | Все поля валидны |
| 7 | Конвертация JSON #1 | converter_validator | ✅ | 200 | 38ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-16T11:20:37.412197Z","parser":{}},"document":{"source":{"file_name":"","file_hash_sha256":"","page_count":1},"metadata":{"doc_code":"","title":"Без названия","normalized_title |
| 8 | Сохранение документа #1 в Registry | registry | ✅ | 201 | 24ms | doc_id_1=6 → doc_id_1_uuid=00000000-0000-0000-0000-000000000006 |
| 9 | Построение индекса #1 | rag_builder | ✅ | 201 | 24ms | status = completed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 16ms |  |
| 11 | Запуск парсинга #2 | parser | ✅ | 202 | 65ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll) | parser | ✅ | 200 | 7ms | status = accepted |
| 13 | Результат парсинга #2 | parser | ✅ | 200 | 4066ms | Все поля валидны |
| 14 | Конвертация JSON #2 | converter_validator | ✅ | 200 | 33ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-16T11:20:41.655159Z","parser":{}},"document":{"source":{"file_name":"","file_hash_sha256":"","page_count":1},"metadata":{"doc_code":"","title":"Без названия","normalized_title |
| 15 | Сохранение документа #2 в Registry | registry | ✅ | 201 | 12ms | doc_id_2=7 → doc_id_2_uuid=00000000-0000-0000-0000-000000000007 |
| 16 | Построение индекса #2 | rag_builder | ✅ | 201 | 11ms | status = completed |
| 17 | Поиск по общему запросу | rag_search | ❌ | 500 | 17ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: operator does not exist: bigint = uuid\nHINT:  No operator matches the given name and argument types. You might need to add explicit type casts.","details":{}}} |
| 18 | Удаление документа #1 из Registry | registry | ✅ | 200 | 12ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 | rag_search | ❌ | 500 | 12ms | Expected HTTP 200, got 500 | body: {"error":{"code":"SEARCH_FAILED","message":"Search failed: operator does not exist: bigint = uuid\nHINT:  No operator matches the given name and argument types. You might need to add explicit type casts.","details":{}}} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 17/19

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика Orchestrator (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 8/8
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 231ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создание черновика | orchestrator | ✅ | 202 | 18ms | draft_id = 4 |
| 3 | Статус задачи (longpoll) | orchestrator | ✅ | 200 | 37ms | status = active |
| 4 | Детали черновика | orchestrator | ✅ | 200 | 2ms | draft_id = 4 |
| 5 | Запуск превью черновика | orchestrator | ✅ | 202 | 15ms | {"draft_id":4,"task_id":3,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью | orchestrator | ✅ | 200 | 6ms | status = processing |
| 7 | Решение по черновику (approve) | orchestrator | ✅ | 200 | 14ms | status = proceeding |
| 8 | Проверка 404 после решения | orchestrator | ✅ | 200 | 2ms | {"draft_id":4,"document_key":"pipeline-draft-key-20260616162041732466","file_key":"f-6c149ba59fef","status":"uploaded","document_id":null,"created_by":"u-mock-001","created_at":"2026-06-08T10:00:00Z","updated_at":"2026-06-08T10:00:00Z"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 8/8

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 229ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Профиль пользователя | auth | ✅ | 200 | 6ms | Все поля валидны |
| 3 | Создать классификатор | registry | ✅ | 201 | 9ms | {"data":{"classifier_system":"MKS","code":"99.068453","full_name":"Pipeline тестовый классификатор 20260616112042068453","status":"active"}} |
| 4 | Список классификаторов | registry | ✅ | 200 | 6ms | data = [{'classifier_system': 'MKS', 'code': '98.608807', 'full_name': 'Принятый термин |
| 5 | Получить классификатор | registry | ✅ | 200 | 5ms | data = {'classifier_system': 'MKS', 'code': '99.068453', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор | registry | ✅ | 200 | 9ms | data = {'classifier_system': 'MKS', 'code': '99.068453', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора | registry | ✅ | 200 | 9ms | data = {'classifier_system': 'MKS', 'code': '99.068453', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор | registry | ✅ | 200 | 10ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин | registry | ✅ | 201 | 10ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260616112042068453","standard_term":"Pipeline тест 20260616112042068453","normalized_value":"pipeline тест 20260616112042068453","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина | registry | ✅ | 200 | 5ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин | registry | ✅ | 200 | 9ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260616112042068453', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 230ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTI3NTRmYmM3YmUwNiIsInJvbGVzIjp |
| 2 | Создать классификатор | registry | ✅ | 201 | 9ms | {"data":{"classifier_system":"MKS","code":"98.388680","full_name":"Pipeline quarantine классификатор 20260616162042388680","status":"active"}} |
| 3 | Создать документ с неизвестным кодом | registry | ✅ | 201 | 18ms | data = {'id': 8, 'doc_code': 'QUAR-TEST-20260616162042388680', 'title': 'Pipeline quara |
| 4 | Список карантина (pending) | registry | ✅ | 200 | 11ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.608807', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept) | registry | ✅ | 200 | 15ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.608807', 'status': |
| 6 | Валидация классификации (accept) | registry | ✅ | 200 | 5ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом | registry | ✅ | 201 | 18ms | data = {'id': 9, 'doc_code': 'QUAR-TEST2-20260616162042388680', 'title': 'Pipeline quar |
| 8 | Список карантина (второй pending) | registry | ✅ | 200 | 11ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.608807', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject) | registry | ✅ | 200 | 10ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject) | registry | ✅ | 200 | 4ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-16 11:20:42 UTC_
