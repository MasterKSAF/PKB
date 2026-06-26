# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-26 12:35:12 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 8082 | — | ✅ | — | ✅ | ✅ |
| Converter-Validator | 8086 | — | — | — | ✅ | ✅ |
| Gateway | 8080 | — | — | — | ❌ | ✅ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 8088 | — | — | — | — | 🟡 dev |
| Orchestrator | 8081 | — | ✅ | — | — | 🟡 dev |
| Parser Service | 8087 | — | — | — | ✅ | ✅ |
| Query Service | 8083 | — | ✅ | — | — | 🟡 dev |
| RAG Builder | 8090 | — | ✅ | — | ✅ | ✅ |
| RAG Search | 8091 | — | — | — | ✅ | ✅ |
| Registry Service | 8084 | — | ✅ | — | ✅ | ✅ |
| TEI | 18092 | — | — | — | — | 🟡 dev |
| **Total** | | ✅ | ✅ | ✅ | ❌ | ❌ |

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
| RAG Builder | ✅ | — | — | ✅ | — | — | — | — | — | — | — | — | — | ✅ | ✅ |
| RAG Search | ✅ | ✅ | — | ✅ | — | — | — | — | — | — | — | — | — | ✅ | ✅ |
| Registry Service | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — | ✅ |
| TEI | — | — | — | — | — | — | — | — | — | — | — | — | — | — | 🟡 dev |
| **Total** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

#### 🔍 Пояснения к результатам

_Нет замечаний_


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| **Total** | | **0/0** | ✅ | **0** | **0** | **0** | **0** | ✅ |

### ⚠️ Workaround-предупреждения по сервисам

_Нет предупреждений_


---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
| `admin_user_lifecycle` | Admin управление пользователем (создание → работа → аудит → деактивация) | ✅ | 16 | 16 | 0 | ✅ |
| `chat_inference` | Чат-сессия с поиском по проиндексированным документам | ✅ | 6 | 6 | 0 | ✅ |
| `document_approval` | Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик) | ✅ | 10 | 10 | 0 | ✅ |
| `document_processing` | Полный цикл обработки документа | ✅ | 15 | 15 | 0 | ✅ |
| `full_document_lifecycle` | Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание) | ✅ | 12 | 12 | 0 | ✅ |
| `multi_document_cross_search` | Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация | ✅ | 19 | 15 | 4 | ❌ |
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
| query → rag_search | ✅ | 200 | 3303ms | results=3, processing_time_ms=3298, total_found=4 |
| query → registry | ✅ | 200 | 8ms | data=[] — валидный ответ (БД пуста, но эндпоинт работает) |
| rag_search → infinity (TEI) | ✅ | 200 | 4ms | embedding_dim=312 — эмбеддинги работают |
| gateway → query | ❌ | — | — | Не удалось создать или получить project_id для проверки прокси |
| **Total** | ❌ | | | 3/4 passed, 1 failed |

#### ❌ Детали ошибок

- **gateway → query**: Не удалось создать или получить project_id для проверки прокси


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
| 1 | Аутентификация admin (через Gateway) | gateway | ✅ | 200 | 311ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание пользователя (через Gateway) | gateway | ✅ | 201 | 262ms | user_id = u-9bf89ddd7e1f |
| 3 | Список пользователей (через Gateway) | gateway | ✅ | 200 | 29ms | users = [{'user_id': 'u-9bf89ddd7e1f', 'email': 'pipeline-user-20260626173428453874@test |
| 4 | Аутентификация нового пользователя (через Gateway) | gateway | ✅ | 200 | 249ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTliZjg5ZGRkN2UxZiIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь, через Gateway) | gateway | ✅ | 201 | 42ms | session_id = 1 |
| 6 | Отправка сообщения (новый пользователь, через Gateway) | gateway | ✅ | 202 | 40ms | message_id = 2 |
| 7 | Получение истории чата (через Gateway) | gateway | ✅ | 200 | 142ms | messages = [{'message_id': 1, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 (через Gateway) | gateway | ✅ | 401 | 236ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 (через Gateway) | gateway | ✅ | 401 | 234ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 (через Gateway) | gateway | ✅ | 401 | 239ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 (через Gateway) | gateway | ✅ | 401 | 241ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 (через Gateway) | gateway | ✅ | 401 | 235ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 13 | Проверка блокировки после 5 неудач (через Gateway) | gateway | ✅ | 401 | 233ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 14 | Журнал аудита (через Gateway) | gateway | ✅ | 200 | 24ms | events = [{'event_id': 'evt-af53c1f80874', 'user_id': 'u-9bf89ddd7e1f', 'action': 'auth.l |
| 15 | Деактивация пользователя (через Gateway) | gateway | ✅ | 200 | 45ms | is_active = False |
| 16 | Проверка 401 после деактивации (через Gateway) | gateway | ✅ | 401 | 12ms | ответ: пустой detail |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 16/16

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 245ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание чат-сессии (через Gateway) | gateway | ✅ | 201 | 27ms | session_id = 2 |
| 3 | Отправка сообщения (через Gateway) | gateway | ✅ | 202 | 28ms | message_id = 4 |
| 4 | Текстовый поиск (через Gateway) | gateway | ✅ | 200 | 29ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped (через Gateway) | gateway | ✅ | 200 | 37ms | enrichment_skipped=False |
| 6 | Поиск RAG Search (напрямую) | rag_search | ✅ | 200 | 493ms | results=[] (нет результатов, валидация по source не требуется) |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 244ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 128ms | draft_id = 6 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 20ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 55ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 85ms | {"draft_id":6,"task_id":6,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1084ms | {"draft_id":6,"task_id":6,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 151ms | {"draft_id":6,"task_id":6,"document_id":3,"version_id":1,"is_new_document":true,"status":"proceeding","action":"approve","message":"Запущена полная обработка документа"} |
| 8 | Проверка document_id после approve (через Gateway) | gateway | ✅ | 200 | 72ms | документ создан (без id в ответе) |
| 9 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 52ms | {"data":{"id":4,"doc_code":"APPROVAL-20260626173431919857","title":"Approval тест 20260626173431919857","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"b3a5fb729b88b190a434 |
| 10 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 50ms | status = indexed |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 244ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCA1A311EE8785</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 21ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 8ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 38ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4099ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 5ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 3ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 200 | 12ms | {"data":{"is_duplicate":false,"is_duplicate_file":false,"candidates":[],"file_hash_sha256":null,"title_hash_sha256":"561484bc91ca985c567323ff7e7a7d09b870b6a40fe2eedc0ba707d764de558e","file_size_bytes":null,"checked_at":"2026-06-26T12:34:38.472018+00:00"}} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 40ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 40ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 20ms | {"data":{"id":5,"doc_code":"PIPELINE-TEST-1782477274","title":"Тестовый документ pipeline 1782477274","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"71c8e9fd9e6a65a03ce842 |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 19ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 20ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-26T15:34:38.618405+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3360ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 31ms | {"data":{"id":6,"doc_code":"LIFECYCLE-1782477281","title":"Lifecycle тест 1782477281","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"3c5f7df9ec0da4cbd6445cb5349b10cd09ebb9 |
| 3 | Первая попытка построения индекса (RAG Builder) | rag_builder | ✅ | 202 | 11ms | status = indexed |
| 4 | Обновление метаданных документа (через Gateway) | gateway | ✅ | 200 | 42ms | data = {'id': '6', 'status': 'uploaded', 'previous_status': None, 'history_id': '1', 'u |
| 5 | Повторное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 13ms | status = indexed |
| 6 | Поиск по индексу RAG Search (RAG Search) | rag_search | ✅ | 200 | 3322ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry (через Gateway) | gateway | ✅ | 200 | 34ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG (RAG Builder) | rag_builder | ✅ | 200 | 10ms | {"document_id":6,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата (RAG Search) | rag_search | ✅ | 200 | 3295ms | results[1/1]: валидация по source-индексам (document_id+section_id) пройдена |
| 10 | Воссоздание документа в Registry (через Gateway) | gateway | ✅ | 201 | 35ms | {"data":{"id":7,"doc_code":"LIFECYCLE-RECOVER-1782477281","title":"Lifecycle тест восстановленный 1782477281","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"d595c4b386debf |
| 11 | Финальное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 15ms | status = indexed |
| 12 | Финальный поиск по индексу (RAG Search) | rag_search | ✅ | 200 | 3341ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 15/19
- Failed: 4
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 239ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCA1A757A04251</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 12ms |  |
| 4 | Запуск парсинга #1 (Parser) | parser | ✅ | 202 | 5ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll, Parser) | parser | ✅ | 200 | 90ms | status = accepted |
| 6 | Результат парсинга #1 (Parser) | parser | ✅ | 200 | 2029ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 (Converter) | converter_validator | ✅ | 200 | 37ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-26T12:34:54.810182Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782477292.pdf","file_h |
| 8 | Сохранение документа #1 в Registry (через Gateway) | gateway | ✅ | 201 | 32ms | {"data":{"id":8,"doc_code":"MULTI1-1782477292","title":"Multi-doc тест 1 1782477292","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"7c5c50ffa80dcf4b4454455ac97c25071c2b17f |
| 9 | Построение индекса #1 (через Gateway) | gateway | ❌ | 404 | 16ms | Expected HTTP {200, 201, 202}, got 404 | body: {"detail":"Not Found"} | body: {"detail":"Not Found"} |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 15ms |  |
| 11 | Запуск парсинга #2 (Parser) | parser | ✅ | 202 | 4ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll, Parser) | parser | ✅ | 200 | 35ms | status = accepted |
| 13 | Результат парсинга #2 (Parser) | parser | ✅ | 200 | 2025ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 (Converter) | converter_validator | ✅ | 200 | 37ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-26T12:34:56.978793Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782477292.pdf","file_h |
| 15 | Сохранение документа #2 в Registry (через Gateway) | gateway | ✅ | 201 | 35ms | {"data":{"id":9,"doc_code":"MULTI2-1782477292","title":"Multi-doc тест 2 1782477292","source_type":"GOST","mks_oks_code":"47.020","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"21df4e2dc00ec134883667633f447e3aa701377 |
| 16 | Построение индекса #2 (через Gateway) | gateway | ❌ | 404 | 14ms | Expected HTTP {200, 201, 202}, got 404 | body: {"detail":"Not Found"} | body: {"detail":"Not Found"} |
| 17 | Поиск по общему запросу (через Gateway) | gateway | ❌ | 404 | 9ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} | body: {"detail":"Not Found"} |
| 18 | Удаление документа #1 из Registry (через Gateway) | gateway | ✅ | 200 | 30ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 (через Gateway) | gateway | ❌ | 404 | 9ms | Expected HTTP 200, got 404 | body: {"detail":"Not Found"} | body: {"detail":"Not Found"} |

**Итог:** ❌ Сбой | Ping: ✅ | Steps: 15/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 108ms | draft_id = 7 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 19ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 53ms | Все поля валидны |
| 5 | Решение по черновику (reject, через Gateway) | gateway | ✅ | 200 | 68ms | status = discarded |
| 6 | Проверка статуса после reject (через Gateway) | gateway | ✅ | 200 | 52ms | {"draft_id":7,"document_id":null,"version_id":null,"is_new_document":true,"status":"discarded","document_key":"reject-key-20260626173457084268","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 5/6
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 244ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 33ms | approved_doc_id=10 |
| 3 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 127ms | draft_id = 8 |
| 4 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 21ms | status = active |
| 5 | Переиндексация документа (через Gateway) | gateway | ✅ | 409 | 25ms | {"detail":{"error":{"code":"TASK_ALREADY_EXISTS","message":"Reprocess task for document 10 already exists"}}} |
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
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 252ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 29ms | approved_doc_id=11 |
| 3 | Загрузка новой версии документа (через Gateway) | gateway | ✅ | 404 | 14ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий (через Gateway) | gateway | ✅ | 200 | 22ms | {"data":[]} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 104ms | draft_id = 9 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 16ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 49ms | Все поля валидны |
| 5 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 74ms |  |
| 6 | Проверка 404 после удаления (через Gateway) | gateway | ✅ | 404 | 53ms | {"detail":{"error":{"code":"NOT_FOUND","message":"Черновик 9 не найден","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/9'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"}}}} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика через Gateway (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 10/11
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 107ms | draft_id = 10 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 18ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 49ms | Все поля валидны |
| 5 | Запуск превью (через Gateway) | gateway | ✅ | 202 | 78ms | {"draft_id":10,"task_id":11,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1067ms | status = processing |
| 7 | Решение approve (через Gateway) | gateway | ✅ | 200 | 131ms | status = proceeding |
| 8 | Проверка document_id (через Gateway) | gateway | ✅ | 200 | 51ms | is_new_document=True |
| 9 | Проверка документа в Registry (через Gateway) | gateway | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика image/png (через Gateway) | gateway | ✅ | 202 | 132ms | draft_id = 11 |
| 11 | Статус задачи image (через Gateway) | gateway | ✅ | 200 | 29ms | status = active |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/11

### Pipeline: `orchestrator_full_document_lifecycle`

**Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 248ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 109ms | draft_id = 12 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 19ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 51ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 72ms | {"draft_id":12,"task_id":13,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1079ms | {"draft_id":12,"task_id":13,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 137ms | approved_doc_id=13 |
| 8 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 22ms | {"data":{"id":13,"doc_code":"fullcycle-key-20260626173500894434","title":"Draft 12","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"7eaa6de4a08f3ed13702088b27ca7226471f58f78f7ad309b768ff0bb708c927","draft_id":12,"classification_status" |
| 9 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 14ms | status = indexed |
| 10 | Поиск RAG Search (RAG Search) | rag_search | ✅ | 200 | 3310ms | {"query":"тестовый документ","results":[{"source":{"document_id":4,"section_id":1,"clause":null,"path":null,"page":1,"bbox":null,"section_title":null,"content":"Содержимое тестового документа approval"},"retrieval":{"chunk_id":1,"score":1.0,"mode":"dense_rerank"},"context":[]},{"source":{"document_i |
| 11 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 53ms |  |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 106ms | draft_id = 13 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 17ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 50ms | Все поля валидны |
| 5 | Обновление метаданных (через Gateway) | gateway | ✅ | 200 | 75ms | Все поля валидны |
| 6 | Проверка обновлённых метаданных (через Gateway) | gateway | ✅ | 200 | 61ms | {"draft_id":13,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260626173506020636","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Профиль пользователя (через Gateway) | gateway | ✅ | 200 | 18ms | Все поля валидны |
| 3 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 24ms | {"data":{"classifier_system":"MKS","code":"99.582864","full_name":"Pipeline тестовый классификатор 20260626123506582864","status":"active"}} |
| 4 | Список классификаторов (через Gateway) | gateway | ✅ | 200 | 18ms | data = [{'classifier_system': 'MKS', 'code': '98.477251', 'full_name': 'Принятый термин |
| 5 | Получить классификатор (через Gateway) | gateway | ✅ | 200 | 21ms | data = {'classifier_system': 'MKS', 'code': '99.582864', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор (через Gateway) | gateway | ✅ | 200 | 26ms | data = {'classifier_system': 'MKS', 'code': '99.582864', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора (через Gateway) | gateway | ✅ | 200 | 23ms | data = {'classifier_system': 'MKS', 'code': '99.582864', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор (через Gateway) | gateway | ✅ | 200 | 26ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин (через Gateway) | gateway | ✅ | 201 | 27ms | {"data":{"id":2,"raw_term":"Pipeline тест 20260626123506582864","standard_term":"Pipeline тест 20260626123506582864","normalized_value":"pipeline тест 20260626123506582864","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина (через Gateway) | gateway | ✅ | 200 | 21ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин (через Gateway) | gateway | ✅ | 200 | 28ms | data = {'id': 2, 'raw_term': 'Pipeline тест 20260626123506582864', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 244ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTViYzRlZmViNWVjMSIsInJvbGVzIjp |
| 2 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 25ms | {"data":{"classifier_system":"MKS","code":"98.071074","full_name":"Pipeline quarantine классификатор 20260626173507071074","status":"active"}} |
| 3 | Создать документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 34ms | data = {'id': 14, 'doc_code': 'QUAR-TEST-20260626173507071074', 'title': 'Pipeline quar |
| 4 | Список карантина (pending, через Gateway) | gateway | ✅ | 200 | 32ms | data = [{'id': '2', 'system': 'OKSTU', 'code': '88.477251', 'found_in_document_id': '1' |
| 5 | Принять из карантина (accept, через Gateway) | gateway | ✅ | 200 | 31ms | data = {'pending_id': '2', 'classifier_system': 'OKSTU', 'code': '88.477251', 'status': |
| 6 | Валидация классификации (accept, через Gateway) | gateway | ✅ | 200 | 19ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 40ms | data = {'id': 15, 'doc_code': 'QUAR-TEST2-20260626173507071074', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending, через Gateway) | gateway | ✅ | 200 | 41ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.477251', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject, через Gateway) | gateway | ✅ | 200 | 28ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject, через Gateway) | gateway | ✅ | 200 | 26ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-26 12:35:12 UTC_
