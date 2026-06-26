# Full Report — API Coverage + Pipeline Testing

**Generated:** 2026-06-26 17:15:39 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 18082 | — | ✅ | — | ✅ | ✅ |
| Converter-Validator | 18086 | — | — | — | ✅ | ✅ |
| Gateway | 18080 | — | — | — | ✅ | ✅ |
| MinIO | 19000 | — | — | — | ✅ | ✅ |
| OCR Service | 18088 | — | — | — | — | 🟡 dev |
| Orchestrator | 18081 | — | ✅ | — | — | 🟡 dev |
| Parser Service | 18087 | — | — | — | ✅ | ✅ |
| Query Service | 18083 | — | ✅ | — | — | 🟡 dev |
| RAG Builder | 18090 | — | ✅ | — | ✅ | ✅ |
| RAG Search | 18091 | — | — | — | ✅ | ✅ |
| Registry Service | 18084 | — | ✅ | — | ✅ | ✅ |
| TEI | 18092 | — | — | — | — | 🟡 dev |
| **Total** | | ✅ | ✅ | ✅ | ✅ | ✅ |

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
| **Total** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

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
| `full_document_cycle` | Полный сквозной цикл: загрузка PDF через черновик → парсинг → preview → approve → Registry → индексация → поиск | ✅ | 10 | 10 | 0 | ✅ |
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
| query → rag_search | ✅ | 200 | 3360ms | results=7, processing_time_ms=3352, total_found=22 |
| query → registry | ✅ | 200 | 18ms | data=[] — валидный ответ (БД пуста, но эндпоинт работает) |
| rag_search → infinity (TEI) | ✅ | 200 | 13ms | embedding_dim=312 — эмбеддинги работают |
| gateway → query | ✅ | 201 | 26ms | session_id=14 — прокси работает |
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
| 1 | Аутентификация admin (через Gateway) | gateway | ✅ | 200 | 332ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание пользователя (через Gateway) | gateway | ✅ | 201 | 269ms | user_id = u-1cfda0dab63d |
| 3 | Список пользователей (через Gateway) | gateway | ✅ | 200 | 35ms | users = [{'user_id': 'u-1cfda0dab63d', 'email': 'pipeline-user-20260626221424773811@test |
| 4 | Аутентификация нового пользователя (через Gateway) | gateway | ✅ | 200 | 251ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTFjZmRhMGRhYjYzZCIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь, через Gateway) | gateway | ✅ | 201 | 34ms | session_id = 12 |
| 6 | Отправка сообщения (новый пользователь, через Gateway) | gateway | ✅ | 202 | 42ms | message_id = 14 |
| 7 | Получение истории чата (через Gateway) | gateway | ✅ | 200 | 35ms | messages = [{'message_id': 13, 'role': 'user', 'content': 'Тестовое сообщение от pipeline п |
| 8 | Брутфорс попытка 1/5 (через Gateway) | gateway | ✅ | 401 | 249ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 (через Gateway) | gateway | ✅ | 401 | 245ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 (через Gateway) | gateway | ✅ | 401 | 254ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 (через Gateway) | gateway | ✅ | 401 | 242ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 (через Gateway) | gateway | ✅ | 401 | 251ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 13 | Проверка блокировки после 5 неудач (через Gateway) | gateway | ✅ | 401 | 236ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 14 | Журнал аудита (через Gateway) | gateway | ✅ | 200 | 33ms | events = [{'event_id': 'evt-d12a80fe874d', 'user_id': 'u-1cfda0dab63d', 'action': 'auth.l |
| 15 | Деактивация пользователя (через Gateway) | gateway | ✅ | 200 | 46ms | is_active = False |
| 16 | Проверка 401 после деактивации (через Gateway) | gateway | ✅ | 401 | 14ms | ответ: пустой detail |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 16/16

### Pipeline: `chat_inference`

**Чат-сессия с поиском по проиндексированным документам**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 248ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание чат-сессии (через Gateway) | gateway | ✅ | 201 | 26ms | session_id = 13 |
| 3 | Отправка сообщения (через Gateway) | gateway | ✅ | 202 | 27ms | message_id = 16 |
| 4 | Текстовый поиск (через Gateway) | gateway | ✅ | 200 | 22ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped (через Gateway) | gateway | ✅ | 200 | 37ms | enrichment_skipped=False |
| 6 | Поиск RAG Search | rag_search | ✅ | 200 | 3370ms | results[7/7]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `document_approval`

**Подтверждение документа: черновик → preview → решение пользователя → full-фаза → индексация (документ только через черновик)**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 250ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 2409ms | draft_id = 32 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 42ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 104ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 128ms | {"draft_id":32,"task_id":35,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1336ms | {"draft_id":32,"task_id":35,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 223ms | {"draft_id":32,"task_id":35,"document_id":36,"version_id":1,"is_new_document":true,"status":"proceeding","action":"approve","message":"Запущена полная обработка документа"} |
| 8 | Проверка document_id после approve (через Gateway) | gateway | ✅ | 200 | 140ms | документ создан (без id в ответе) |
| 9 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 114ms | {"data":{"id":37,"doc_code":"APPROVAL-20260626221431091741","title":"Approval тест 20260626221431091741","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Pipeline принятый классификатор 20260626220226282656","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01"," |
| 10 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 34ms | status = indexed |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 365ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCB0EB2D154147</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 26ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 6ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 51ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 4042ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 7ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 4ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 200 | 13ms | {"data":{"is_duplicate":false,"is_duplicate_file":false,"candidates":[],"file_hash_sha256":null,"title_hash_sha256":"561484bc91ca985c567323ff7e7a7d09b870b6a40fe2eedc0ba707d764de558e","file_size_bytes":null,"checked_at":"2026-06-26T17:14:40.801423+00:00"}} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 59ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 59ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 30ms | {"data":{"id":38,"doc_code":"PIPELINE-TEST-1782494076","title":"Тестовый документ pipeline 1782494076","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Pipeline принятый классификатор 20260626220226282656","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","va |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 17ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 23ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-26T20:14:40.997262+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3329ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_cycle`

**Полный сквозной цикл: загрузка PDF через черновик → парсинг → preview → approve → Registry → индексация → поиск**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 281ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика с PDF (через Gateway) | gateway | ✅ | 202 | 488ms | draft_id = 33 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 47ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 155ms | Все поля валидны |
| 5 | Запуск превью (через Gateway) | gateway | ✅ | 202 | 212ms | {"draft_id":33,"task_id":36,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1173ms | {"draft_id":33,"task_id":36,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 400ms | approved_doc_id=39 |
| 8 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 53ms | {"data":{"id":39,"doc_code":"full-cycle-key-20260626221444337294","title":"Draft 33","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"5cc9380c210f06965ad765acdba8da990ace1a3ffb9d2b29f2a2c6d27925ea87","draft_id":33,"classification_status |
| 9 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 35ms | status = indexed |
| 10 | Поиск по индексу (RAG Search) | rag_search | ✅ | 200 | 3373ms | results[7/7]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 281ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 66ms | {"data":{"id":40,"doc_code":"LIFECYCLE-1782494090","title":"Lifecycle тест 1782494090","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Pipeline принятый классификатор 20260626220226282656","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999 |
| 3 | Первая попытка построения индекса (RAG Builder) | rag_builder | ✅ | 202 | 27ms | status = indexed |
| 4 | Обновление метаданных документа (через Gateway) | gateway | ✅ | 200 | 75ms | data = {'id': '40', 'status': 'uploaded', 'previous_status': None, 'history_id': '3', ' |
| 5 | Повторное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 23ms | status = indexed |
| 6 | Поиск по индексу RAG Search (RAG Search) | rag_search | ✅ | 200 | 3316ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry (через Gateway) | gateway | ✅ | 200 | 69ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG (RAG Builder) | rag_builder | ✅ | 200 | 23ms | {"document_id":40,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата (RAG Search) | rag_search | ✅ | 200 | 3352ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |
| 10 | Воссоздание документа в Registry (через Gateway) | gateway | ✅ | 201 | 47ms | {"data":{"id":41,"doc_code":"LIFECYCLE-RECOVER-1782494090","title":"Lifecycle тест восстановленный 1782494090","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Pipeline принятый классификатор 20260626220226282656","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01 |
| 11 | Финальное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 18ms | status = indexed |
| 12 | Финальный поиск по индексу (RAG Search) | rag_search | ✅ | 200 | 3330ms | results[8/8]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 259ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 4ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCB0F0FFF699DB</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 15ms |  |
| 4 | Запуск парсинга #1 (Parser) | parser | ✅ | 202 | 4ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll, Parser) | parser | ✅ | 200 | 46ms | status = accepted |
| 6 | Результат парсинга #1 (Parser) | parser | ✅ | 200 | 4042ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 (Converter) | converter_validator | ✅ | 200 | 53ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-26T17:15:05.827428Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782494101.pdf","file_h |
| 8 | Сохранение документа #1 в Registry (через Gateway) | gateway | ✅ | 201 | 59ms | {"data":{"id":42,"doc_code":"MULTI1-1782494101","title":"Multi-doc тест 1 1782494101","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Pipeline принятый классификатор 20260626220226282656","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999- |
| 9 | Построение индекса #1 (RAG Builder) | rag_builder | ✅ | 202 | 18ms | status = indexed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 17ms |  |
| 11 | Запуск парсинга #2 (Parser) | parser | ✅ | 202 | 8ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll, Parser) | parser | ✅ | 200 | 43ms | status = accepted |
| 13 | Результат парсинга #2 (Parser) | parser | ✅ | 200 | 4049ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 (Converter) | converter_validator | ✅ | 200 | 46ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-26T17:15:10.073181Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782494101.pdf","file_h |
| 15 | Сохранение документа #2 в Registry (через Gateway) | gateway | ✅ | 201 | 45ms | {"data":{"id":43,"doc_code":"MULTI2-1782494101","title":"Multi-doc тест 2 1782494101","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Pipeline принятый классификатор 20260626220226282656","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999- |
| 16 | Построение индекса #2 (RAG Builder) | rag_builder | ✅ | 202 | 22ms | status = indexed |
| 17 | Поиск по общему запросу (RAG Search) | rag_search | ✅ | 200 | 3327ms | results[7/7]: валидация по source-индексам (document_id+section_id) пройдена |
| 18 | Удаление документа #1 из Registry (через Gateway) | gateway | ✅ | 200 | 50ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 (RAG Search) | rag_search | ✅ | 200 | 3323ms | results[7/7]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 262ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 343ms | draft_id = 34 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 30ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 65ms | Все поля валидны |
| 5 | Решение по черновику (reject, через Gateway) | gateway | ✅ | 200 | 132ms | status = discarded |
| 6 | Проверка статуса после reject (через Gateway) | gateway | ✅ | 200 | 109ms | {"draft_id":34,"document_id":null,"version_id":null,"is_new_document":true,"status":"discarded","document_key":"reject-key-20260626221516848998","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 5/6
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 284ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 72ms | approved_doc_id=44 |
| 3 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 744ms | draft_id = 35 |
| 4 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 39ms | status = active |
| 5 | Переиндексация документа (через Gateway) | gateway | ✅ | 409 | 38ms | {"detail":{"error":{"code":"TASK_ALREADY_EXISTS","message":"Reprocess task for document 44 already exists"}}} |
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
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 346ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 65ms | approved_doc_id=45 |
| 3 | Загрузка новой версии документа (через Gateway) | gateway | ✅ | 404 | 40ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий (через Gateway) | gateway | ✅ | 200 | 77ms | {"data":[]} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 364ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 675ms | draft_id = 36 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 51ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 124ms | Все поля валидны |
| 5 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 159ms |  |
| 6 | Проверка 404 после удаления (через Gateway) | gateway | ✅ | 404 | 162ms | {"detail":{"error":{"code":"NOT_FOUND","message":"Черновик 36 не найден","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/36'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"}}}} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика через Gateway (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 10/11
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 386ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 679ms | draft_id = 37 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 149ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 142ms | Все поля валидны |
| 5 | Запуск превью (через Gateway) | gateway | ✅ | 202 | 192ms | {"draft_id":37,"task_id":41,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1206ms | status = processing |
| 7 | Решение approve (через Gateway) | gateway | ✅ | 200 | 379ms | status = proceeding |
| 8 | Проверка document_id (через Gateway) | gateway | ✅ | 200 | 109ms | is_new_document=True |
| 9 | Проверка документа в Registry (через Gateway) | gateway | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика image/png (через Gateway) | gateway | ✅ | 202 | 791ms | draft_id = 38 |
| 11 | Статус задачи image (через Gateway) | gateway | ✅ | 200 | 47ms | status = active |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/11

### Pipeline: `orchestrator_full_document_lifecycle`

**Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 320ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 508ms | draft_id = 39 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 36ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 114ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 214ms | {"draft_id":39,"task_id":43,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1197ms | {"draft_id":39,"task_id":43,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 267ms | approved_doc_id=47 |
| 8 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 48ms | {"data":{"id":47,"doc_code":"fullcycle-key-20260626221525241653","title":"Draft 39","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"89fa4c1a7f145dade83dbfb57a504eba997ba533409110315d4f9a3dc28cc636","draft_id":39,"classification_status" |
| 9 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 26ms | status = indexed |
| 10 | Поиск RAG Search (RAG Search) | rag_search | ✅ | 200 | 3379ms | {"query":"тестовый документ","results":[{"source":{"document_id":43,"section_id":1,"clause":null,"path":null,"page":1,"bbox":null,"section_title":null,"content":"Содержимое документа 2 1782494101"},"retrieval":{"chunk_id":31,"score":1.0,"mode":"dense_rerank"},"context":[]},{"source":{"document_id":2 |
| 11 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 98ms |  |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 348ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 1054ms | draft_id = 40 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 69ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 176ms | Все поля валидны |
| 5 | Обновление метаданных (через Gateway) | gateway | ✅ | 200 | 192ms | Все поля валидны |
| 6 | Проверка обновлённых метаданных (через Gateway) | gateway | ✅ | 200 | 143ms | {"draft_id":40,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260626221531461546","file_key":"f-6c149ba59fef"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 392ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Профиль пользователя (через Gateway) | gateway | ✅ | 200 | 80ms | Все поля валидны |
| 3 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 74ms | {"data":{"classifier_system":"MKS","code":"99.453805","full_name":"Pipeline тестовый классификатор 20260626171533453805","status":"active"}} |
| 4 | Список классификаторов (через Gateway) | gateway | ✅ | 200 | 79ms | data = [{'classifier_system': 'MKS', 'code': '98.492395', 'full_name': 'Принятый термин |
| 5 | Получить классификатор (через Gateway) | gateway | ✅ | 200 | 63ms | data = {'classifier_system': 'MKS', 'code': '99.453805', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор (через Gateway) | gateway | ✅ | 200 | 92ms | data = {'classifier_system': 'MKS', 'code': '99.453805', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора (через Gateway) | gateway | ✅ | 200 | 47ms | data = {'classifier_system': 'MKS', 'code': '99.453805', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор (через Gateway) | gateway | ✅ | 200 | 65ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин (через Gateway) | gateway | ✅ | 201 | 111ms | {"data":{"id":4,"raw_term":"Pipeline тест 20260626171533453805","standard_term":"Pipeline тест 20260626171533453805","normalized_value":"pipeline тест 20260626171533453805","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина (через Gateway) | gateway | ✅ | 200 | 46ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин (через Gateway) | gateway | ✅ | 200 | 64ms | data = {'id': 4, 'raw_term': 'Pipeline тест 20260626171533453805', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 306ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWZhZmY4N2YxN2FmZCIsInJvbGVzIjp |
| 2 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 56ms | {"data":{"classifier_system":"MKS","code":"98.586141","full_name":"Pipeline quarantine классификатор 20260626221534586141","status":"active"}} |
| 3 | Создать документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 59ms | data = {'id': 48, 'doc_code': 'QUAR-TEST-20260626221534586141', 'title': 'Pipeline quar |
| 4 | Список карантина (pending, через Gateway) | gateway | ✅ | 200 | 80ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.492395', 'found_in_document_id': '1',  |
| 5 | Принять из карантина (accept, через Gateway) | gateway | ✅ | 200 | 40ms | data = {'pending_id': '1', 'classifier_system': 'MKS', 'code': '98.492395', 'status': ' |
| 6 | Валидация классификации (accept, через Gateway) | gateway | ✅ | 200 | 34ms | data.mks_status = NOT_FOUND |
| 7 | Создать второй документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 63ms | data = {'id': 49, 'doc_code': 'QUAR-TEST2-20260626221534586141', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending, через Gateway) | gateway | ✅ | 200 | 94ms | data = [{'id': '1', 'system': 'MKS', 'code': '98.492395', 'found_in_document_id': '1',  |
| 9 | Отклонить из карантина (reject, через Gateway) | gateway | ✅ | 200 | 44ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject, через Gateway) | gateway | ✅ | 200 | 46ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-26 17:15:39 UTC_
