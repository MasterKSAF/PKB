# Full Report — API Coverage + Pipeline Testing + Gateway Tests

**Generated:** 2026-06-27 16:12:41 UTC

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
| База данных `pkb_neuro_check` | ✅ | существует |
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
| query → rag_search | ✅ | 200 | 3301ms | results=6, processing_time_ms=3296, total_found=7 |
| query → registry | ✅ | 200 | 22ms | data=[] — валидный ответ (БД пуста, но эндпоинт работает) |
| rag_search → infinity (TEI) | ✅ | 200 | 4ms | embedding_dim=312 — эмбеддинги работают |
| gateway → query | ✅ | 201 | 26ms | session_id=3 — прокси работает |
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
| 1 | Аутентификация admin (через Gateway) | gateway | ✅ | 200 | 329ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание пользователя (через Gateway) | gateway | ✅ | 201 | 274ms | user_id = u-abdf4a9a6abd |
| 3 | Список пользователей (через Gateway) | gateway | ✅ | 200 | 27ms | users = [{'user_id': 'u-abdf4a9a6abd', 'email': 'pipeline-user-20260627211144045663@test |
| 4 | Аутентификация нового пользователя (через Gateway) | gateway | ✅ | 200 | 243ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWFiZGY0YTlhNmFiZCIsInJvbGVzIjp |
| 5 | Создание чат-сессии (новый пользователь, через Gateway) | gateway | ✅ | 201 | 34ms | session_id = 1 |
| 6 | Отправка сообщения (новый пользователь, через Gateway) | gateway | ✅ | 202 | 33ms | message_id = 2 |
| 7 | Получение истории чата (через Gateway) | gateway | ✅ | 200 | 190ms | messages = [{'message_id': 1, 'role': 'user', 'content': 'Тестовое сообщение от pipeline по |
| 8 | Брутфорс попытка 1/5 (через Gateway) | gateway | ✅ | 401 | 235ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 9 | Брутфорс попытка 2/5 (через Gateway) | gateway | ✅ | 401 | 236ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 10 | Брутфорс попытка 3/5 (через Gateway) | gateway | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 11 | Брутфорс попытка 4/5 (через Gateway) | gateway | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 12 | Брутфорс попытка 5/5 (через Gateway) | gateway | ✅ | 401 | 236ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 13 | Проверка блокировки после 5 неудач (через Gateway) | gateway | ✅ | 401 | 230ms | {"error":{"code":"INVALID_CREDENTIALS","message":"Неверные учётные данные","details":{}}} |
| 14 | Журнал аудита (через Gateway) | gateway | ✅ | 200 | 29ms | events = [{'event_id': 'evt-ca41f96e31f2', 'user_id': 'u-abdf4a9a6abd', 'action': 'auth.l |
| 15 | Деактивация пользователя (через Gateway) | gateway | ✅ | 200 | 39ms | is_active = False |
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
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 240ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание чат-сессии (через Gateway) | gateway | ✅ | 201 | 19ms | session_id = 2 |
| 3 | Отправка сообщения (через Gateway) | gateway | ✅ | 202 | 22ms | message_id = 4 |
| 4 | Текстовый поиск (через Gateway) | gateway | ✅ | 200 | 163ms | results = [{'section_id': 420042, 'document_id': 1, 'document_title': 'Правила РС, часть I |
| 5 | Проверка enrichment_skipped (через Gateway) | gateway | ✅ | 200 | 124ms | enrichment_skipped=False |
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
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 745ms | draft_id = 1 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 64ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 58ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 115ms | {"draft_id":1,"task_id":1,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1114ms | {"draft_id":1,"task_id":1,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 244ms | {"draft_id":1,"task_id":1,"document_id":1,"version_id":1,"is_new_document":true,"status":"proceeding","action":"approve","message":"Запущена полная обработка документа"} |
| 8 | Проверка document_id после approve (через Gateway) | gateway | ✅ | 200 | 59ms | документ создан (без id в ответе) |
| 9 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 38ms | {"data":{"id":2,"doc_code":"APPROVAL-20260627211147490157","title":"Approval тест 20260627211147490157","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Судостроение и морские сооружения в целом","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until" |
| 10 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 139ms | status = indexed |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `document_processing`

**Полный цикл обработки документа**

- Ping: ✅
- Passed: 15/15
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация | auth | ✅ | 200 | 242ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 2ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCFC12ED6934BE</RequestId><HostId>dd902 |
| 3 | Загрузка PDF в MinIO | minio | ✅ | 200 | 23ms | file_key = test-document.pdf |
| 4 | Запуск парсинга | parser | ✅ | 202 | 19ms | task_id = 12345 |
| 5 | Статус парсинга (longpoll) | parser | ✅ | 200 | 60ms | status = accepted |
| 6 | Результат парсинга | parser | ✅ | 200 | 2030ms | результат сохранён как parser_result |
| 7 | Предпросмотр метаданных | converter_validator | ✅ | 200 | 13ms | Все поля валидны |
| 8 | Валидация метаданных (бизнес-ключ) | converter_validator | ✅ | 200 | 11ms | Все поля валидны |
| 9 | Проверка уникальности документа | registry | ✅ | 200 | 13ms | {"data":{"is_duplicate":false,"is_duplicate_file":false,"candidates":[],"file_hash_sha256":null,"title_hash_sha256":"561484bc91ca985c567323ff7e7a7d09b870b6a40fe2eedc0ba707d764de558e","file_size_bytes":null,"checked_at":"2026-06-27T16:11:52.926530+00:00"}} |
| 10 | Конвертация JSON | converter_validator | ✅ | 200 | 75ms | task_id = 12345 |
| 11 | Валидация документа | converter_validator | ✅ | 200 | 46ms | Все поля валидны |
| 12 | Сохранение документа в Registry | registry | ✅ | 201 | 24ms | {"data":{"id":3,"doc_code":"PIPELINE-TEST-1782576710","title":"Тестовый документ pipeline 1782576710","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Судостроение и морские сооружения в целом","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":" |
| 13 | Проверка preview_snapshot в документе | registry | ✅ | 200 | 15ms | Поле 'data.preview_snapshot' не найдено (пропущено) |
| 14 | Построение чанков и индексация | rag_builder | ✅ | 202 | 46ms | {"document_id":1,"status":"indexed","indexed_at":"2026-06-27T19:11:53.137607+03:00","chunks_count":1,"index_stats":{"sections":1,"chunks":1,"embeddings":1},"errors":[],"warnings":[]} |
| 15 | Поиск по индексу RAG Search | rag_search | ✅ | 200 | 3352ms | results[2/2]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 15/15

### Pipeline: `full_document_cycle`

**Полный сквозной цикл: загрузка PDF через черновик → парсинг → preview → approve → Registry → индексация → поиск**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика с PDF (через Gateway) | gateway | ✅ | 202 | 278ms | draft_id = 2 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 56ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 50ms | Все поля валидны |
| 5 | Запуск превью (через Gateway) | gateway | ✅ | 202 | 105ms | {"draft_id":2,"task_id":2,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1131ms | {"draft_id":2,"task_id":2,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 264ms | approved_doc_id=4 |
| 8 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 22ms | {"data":{"id":4,"doc_code":"full-cycle-key-20260627211156632164","title":"Draft 2","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"9588d92d5655dfcd7e436da36a5d07c204f09e45218f222ef6eb7c10bd1072a9","draft_id":2,"classification_status":{ |
| 9 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 66ms | status = indexed |
| 10 | Поиск по индексу (RAG Search) | rag_search | ✅ | 200 | 3317ms | results[3/3]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10

### Pipeline: `full_document_lifecycle`

**Полный жизненный цикл документа (создание → ошибка → восстановление → удаление → пересоздание)**

- Ping: ✅
- Passed: 12/12
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 249ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 32ms | {"data":{"id":5,"doc_code":"LIFECYCLE-1782576722","title":"Lifecycle тест 1782576722","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Судостроение и морские сооружения в целом","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","tit |
| 3 | Первая попытка построения индекса (RAG Builder) | rag_builder | ✅ | 202 | 60ms | status = indexed |
| 4 | Обновление метаданных документа (через Gateway) | gateway | ✅ | 200 | 38ms | data = {'id': '5', 'status': 'uploaded', 'previous_status': None, 'history_id': '1', 'u |
| 5 | Повторное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 59ms | status = indexed |
| 6 | Поиск по индексу RAG Search (RAG Search) | rag_search | ✅ | 200 | 3312ms | results[4/4]: валидация по source-индексам (document_id+section_id) пройдена |
| 7 | Удаление документа из Registry (через Gateway) | gateway | ✅ | 200 | 35ms | {"data":{"message":"Document deleted"}} |
| 8 | Удаление индекса RAG (RAG Builder) | rag_builder | ✅ | 200 | 13ms | {"document_id":5,"deleted_count":1,"status":"completed"} |
| 9 | Поиск — проверка пустого результата (RAG Search) | rag_search | ✅ | 200 | 3332ms | results[3/3]: валидация по source-индексам (document_id+section_id) пройдена |
| 10 | Воссоздание документа в Registry (через Gateway) | gateway | ✅ | 201 | 33ms | {"data":{"id":6,"doc_code":"LIFECYCLE-RECOVER-1782576722","title":"Lifecycle тест восстановленный 1782576722","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Судостроение и морские сооружения в целом","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_ |
| 11 | Финальное построение индекса (RAG Builder) | rag_builder | ✅ | 202 | 58ms | status = indexed |
| 12 | Финальный поиск по индексу (RAG Search) | rag_search | ✅ | 200 | 3290ms | results[4/4]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 12/12

### Pipeline: `multi_document_cross_search`

**Мульти-документный поиск: 2 документа → индексация → кросс-поиск → удаление → фильтрация**

- Ping: ✅
- Passed: 19/19
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание bucket documents | minio | ✅ | 409 | 3ms | <?xml version="1.0" encoding="UTF-8"?>
<Error><Code>BucketAlreadyOwnedByYou</Code><Message>Your previous request to create the named bucket succeeded and you already own it.</Message><BucketName>documents</BucketName><Resource>/documents</Resource><RequestId>18BCFC1827514B26</RequestId><HostId>dd902 |
| 3 | Загрузка PDF #1 в MinIO | minio | ✅ | 200 | 12ms |  |
| 4 | Запуск парсинга #1 (Parser) | parser | ✅ | 202 | 4ms | task_id = 20001 |
| 5 | Статус парсинга #1 (longpoll, Parser) | parser | ✅ | 200 | 35ms | status = accepted |
| 6 | Результат парсинга #1 (Parser) | parser | ✅ | 200 | 2023ms | результат сохранён как parser_result_1 |
| 7 | Конвертация JSON #1 (Converter) | converter_validator | ✅ | 200 | 39ms | {"task_id":20001,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20001,"created_at":"2026-06-27T16:12:15.316794Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-1-1782576732.pdf","file_h |
| 8 | Сохранение документа #1 в Registry (через Gateway) | gateway | ✅ | 201 | 42ms | {"data":{"id":7,"doc_code":"MULTI1-1782576732","title":"Multi-doc тест 1 1782576732","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Судостроение и морские сооружения в целом","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","titl |
| 9 | Построение индекса #1 (RAG Builder) | rag_builder | ✅ | 202 | 48ms | status = indexed |
| 10 | Загрузка PDF #2 в MinIO | minio | ✅ | 200 | 14ms |  |
| 11 | Запуск парсинга #2 (Parser) | parser | ✅ | 202 | 4ms | task_id = 20002 |
| 12 | Статус парсинга #2 (longpoll, Parser) | parser | ✅ | 200 | 101ms | status = accepted |
| 13 | Результат парсинга #2 (Parser) | parser | ✅ | 200 | 2029ms | результат сохранён как parser_result_2 |
| 14 | Конвертация JSON #2 (Converter) | converter_validator | ✅ | 200 | 50ms | {"task_id":20002,"version_id":1,"document_id":null,"metadata":{"schema":"validated_v3","task_id":20002,"created_at":"2026-06-27T16:12:17.612385Z","parser":{"name":"unknown","version":"1.0","ocr_engine":null,"ocr_fallback":false}},"document":{"source":{"file_name":"multi-doc-2-1782576732.pdf","file_h |
| 15 | Сохранение документа #2 в Registry (через Gateway) | gateway | ✅ | 201 | 32ms | {"data":{"id":8,"doc_code":"MULTI2-1782576732","title":"Multi-doc тест 2 1782576732","source_type":"GOST","mks_oks_code":"47.020","mks_name":"Судостроение и морские сооружения в целом","total_versions":0,"era":"RF","validity_status":"active","valid_from":"1970-01-01","valid_until":"2999-12-31","titl |
| 16 | Построение индекса #2 (RAG Builder) | rag_builder | ✅ | 202 | 59ms | status = indexed |
| 17 | Поиск по общему запросу (RAG Search) | rag_search | ✅ | 200 | 3293ms | results[6/6]: валидация по source-индексам (document_id+section_id) пройдена |
| 18 | Удаление документа #1 из Registry (через Gateway) | gateway | ✅ | 200 | 38ms | {"data":{"message":"Document deleted"}} |
| 19 | Поиск после удаления документа #1 (RAG Search) | rag_search | ✅ | 200 | 3307ms | results[5/5]: валидация по source-индексам (document_id+section_id) пройдена |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 19/19

### Pipeline: `orchestrator_document_reject`

**Reject черновика Orchestrator (создание → reject → проверка статуса)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 241ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 273ms | draft_id = 3 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 60ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 54ms | Все поля валидны |
| 5 | Решение по черновику (reject, через Gateway) | gateway | ✅ | 200 | 109ms | status = discarded |
| 6 | Проверка статуса после reject (через Gateway) | gateway | ✅ | 200 | 70ms | {"draft_id":3,"document_id":null,"version_id":null,"is_new_document":true,"status":"discarded","document_key":"reject-key-20260627211224354639","file_key":"f-6c149ba59fef","preview_metadata":{},"created_at":"2026-06-27T16:12:24.809959","updated_at":"2026-06-27T16:12:25.076850"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_document_reprocess`

**Переиндексация документа Orchestrator (создание документа → reprocess)**

- Ping: ✅
- Passed: 5/6
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 249ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 32ms | approved_doc_id=9 |
| 3 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 370ms | draft_id = 4 |
| 4 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 77ms | status = active |
| 5 | Переиндексация документа (через Gateway) | gateway | ✅ | 202 | 84ms | {"mode":"full","document_id":"9","task_id":"5","status":"reprocessing_queued","created_at":"2026-06-27T16:12:25.992434Z"} |
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
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 264ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание документа в Registry (через Gateway) | gateway | ✅ | 201 | 38ms | approved_doc_id=10 |
| 3 | Загрузка новой версии документа (через Gateway) | gateway | ✅ | 404 | 17ms | {"detail":"Not Found"} |
| 4 | Проверка списка версий (через Gateway) | gateway | ✅ | 200 | 25ms | {"data":[]} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 4/4

### Pipeline: `orchestrator_draft_delete`

**Удаление черновика Orchestrator (создание → удаление → проверка 404)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 247ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 288ms | draft_id = 5 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 70ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 70ms | Все поля валидны |
| 5 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 68ms |  |
| 6 | Проверка 404 после удаления (через Gateway) | gateway | ✅ | 404 | 79ms | {"detail":{"error":{"code":"NOT_FOUND","message":"Черновик 5 не найден","details":{"original_error":"Client error '404 Not Found' for url 'http://127.0.0.1:8084/api/v1/registry/drafts/5'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"}}}} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `orchestrator_draft_lifecycle`

**Жизненный цикл черновика через Gateway (создание → превью → решение → удаление)**

- Ping: ✅
- Passed: 10/11
- Failed: 0
- Skipped: 1

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 245ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 302ms | draft_id=6 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 69ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 59ms | Все поля валидны |
| 5 | Запуск превью (через Gateway) | gateway | ✅ | 202 | 132ms | {"draft_id":6,"task_id":7,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1126ms | status = processing |
| 7 | Решение approve (через Gateway) | gateway | ✅ | 200 | 223ms | status = proceeding |
| 8 | Проверка document_id (через Gateway) | gateway | ✅ | 200 | 77ms | is_new_document=True |
| 9 | Проверка документа в Registry (через Gateway) | gateway | ⏭️ | 0 | 0ms | Шаг пропущен по условию skip_if |
| 10 | Создание черновика image/png (через Gateway) | gateway | ✅ | 202 | 392ms | draft_id = 7 |
| 11 | Статус задачи image (через Gateway) | gateway | ✅ | 200 | 84ms | status = active |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/11

### Pipeline: `orchestrator_full_document_lifecycle`

**Полный сквозной цикл документа через Orchestrator (создание → preview → approve → Registry → индексация → удаление)**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 252ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 304ms | draft_id = 8 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 86ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 59ms | Все поля валидны |
| 5 | Запуск превью черновика (через Gateway) | gateway | ✅ | 202 | 112ms | {"draft_id":8,"task_id":9,"status":"previewing","message":"Preview phase started"} |
| 6 | Статус превью (через Gateway) | gateway | ✅ | 200 | 1121ms | {"draft_id":8,"task_id":9,"status":"processing","progress_percent":10,"preview":null,"decision_required":false} |
| 7 | Решение по черновику (approve, через Gateway) | gateway | ✅ | 200 | 242ms | approved_doc_id=12 |
| 8 | Проверка документа в Registry (через Gateway) | gateway | ✅ | 200 | 40ms | {"data":{"id":12,"doc_code":"fullcycle-key-20260627211230078194","title":"Draft 8","status":"uploaded","total_versions":0,"valid_from":"1970-01-01","valid_until":"2999-12-31","title_hash_sha256":"6f9c8d02c7e0d87a03958c4d88ae1575fe504a812e3b3e48b1eedf58e18159f5","draft_id":8,"classification_status":{ |
| 9 | Индексация документа (RAG Builder) | rag_builder | ✅ | 202 | 83ms | status = indexed |
| 10 | Поиск RAG Search (RAG Search) | rag_search | ✅ | 200 | 3325ms | {"query":"тестовый документ","results":[{"source":{"document_id":1,"section_id":1,"clause":null,"path":null,"page":1,"bbox":null,"section_title":null,"content":"Содержимое тестового документа"},"retrieval":{"chunk_id":2,"score":1.0,"mode":"dense_rerank"},"context":[]},{"source":{"document_id":2,"sec |
| 11 | Удаление черновика (через Gateway) | gateway | ✅ | 204 | 55ms |  |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `orchestrator_metadata_update`

**Обновление метаданных черновика Orchestrator (PATCH /metadata)**

- Ping: ✅
- Passed: 6/6
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 251ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создание черновика (через Gateway) | gateway | ✅ | 202 | 386ms | draft_id = 9 |
| 3 | Статус задачи (через Gateway) | gateway | ✅ | 200 | 53ms | status = active |
| 4 | Детали черновика (через Gateway) | gateway | ✅ | 200 | 50ms | {"draft_id":9,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260627211235771913","file_key":"f-6c149ba59fef","preview_metadata":{},"created_at":"2026-06-27T16:12:36.312044","updated_at":"2026-06-27T16:12:36.312044"} |
| 5 | Обновление метаданных (через Gateway) | gateway | ✅ | 200 | 75ms | Все поля валидны |
| 6 | Проверка обновлённых метаданных (через Gateway) | gateway | ✅ | 200 | 52ms | {"draft_id":9,"document_id":null,"version_id":null,"is_new_document":true,"status":"uploaded","document_key":"meta-key-20260627211235771913","file_key":"f-6c149ba59fef","preview_metadata":{},"created_at":"2026-06-27T16:12:36.312044","updated_at":"2026-06-27T16:12:36.574672"} |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 6/6

### Pipeline: `registry_lifecycle`

**CRUD + импорт классификаторов и терминов**

- Ping: ✅
- Passed: 11/11
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 258ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Профиль пользователя (через Gateway) | gateway | ✅ | 200 | 20ms | Все поля валидны |
| 3 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 36ms | {"data":{"classifier_system":"MKS","code":"99.653169","full_name":"Pipeline тестовый классификатор 20260627161236653169","status":"active"}} |
| 4 | Список классификаторов (через Gateway) | gateway | ✅ | 200 | 33ms | data = [{'classifier_system': 'OKSTU', 'code': 'OKSTU_ROOT', 'full_name': '🏛 ОБЩЕСОЮЗНЫ |
| 5 | Получить классификатор (через Gateway) | gateway | ✅ | 200 | 32ms | data = {'classifier_system': 'MKS', 'code': '99.653169', 'full_name': 'Pipeline тестовы |
| 6 | Обновить классификатор (через Gateway) | gateway | ✅ | 200 | 33ms | data = {'classifier_system': 'MKS', 'code': '99.653169', 'full_name': 'Обновлённый pipe |
| 7 | Частичное обновление классификатора (через Gateway) | gateway | ✅ | 200 | 45ms | data = {'classifier_system': 'MKS', 'code': '99.653169', 'full_name': 'Обновлённый pipe |
| 8 | Удалить классификатор (через Gateway) | gateway | ✅ | 200 | 37ms | {"data":{"message":"Classifier deleted"}} |
| 9 | Создать термин (через Gateway) | gateway | ✅ | 201 | 42ms | {"data":{"id":1,"raw_term":"Pipeline тест 20260627161236653169","standard_term":"Pipeline тест 20260627161236653169","normalized_value":"pipeline тест 20260627161236653169","term_type":"abbreviation","is_blocked":false,"is_case_sensitive":false,"definition":"Тестовый термин из pipeline","synonyms":[ |
| 10 | Нормализация термина (через Gateway) | gateway | ✅ | 200 | 29ms | {"data":{"raw_term":"Pipeline тест","standard_term":"Pipeline тест","normalized_value":"pipeline тест","term_type":"unknown"}} |
| 11 | Обновить термин (через Gateway) | gateway | ✅ | 200 | 79ms | data = {'id': 1, 'raw_term': 'Pipeline тест 20260627161236653169', 'standard_term': 'Pi |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 11/11

### Pipeline: `registry_quarantine`

**Карантин классификаторов: accept/reject + валидация**

- Ping: ✅
- Passed: 10/10
- Failed: 0
- Skipped: 0

| # | Step | Service | Status | Code | Time | Проверка |
|---|------|---------|:------:|:----:|:----:|----------|
| 1 | Аутентификация (через Gateway) | gateway | ✅ | 200 | 257ms | access_token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LWVmNmRhMjE0YjRjZCIsInJvbGVzIjp |
| 2 | Создать классификатор (через Gateway) | gateway | ✅ | 201 | 23ms | {"data":{"classifier_system":"MKS","code":"98.318794","full_name":"Pipeline quarantine классификатор 20260627211237318794","status":"active"}} |
| 3 | Создать документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 45ms | data = {'id': 13, 'doc_code': 'QUAR-TEST-20260627211237318794', 'title': 'Pipeline quar |
| 4 | Список карантина (pending, через Gateway) | gateway | ✅ | 200 | 28ms | data = [{'id': '1', 'system': 'MKS', 'code': '97.318794', 'found_in_document_id': '13', |
| 5 | Принять из карантина (accept, через Gateway) | gateway | ✅ | 200 | 47ms | data = {'pending_id': '1', 'classifier_system': 'MKS', 'code': '97.318794', 'status': ' |
| 6 | Валидация классификации (accept, через Gateway) | gateway | ✅ | 200 | 35ms | data.mks_status = CONFIRMED |
| 7 | Создать второй документ с неизвестным кодом (через Gateway) | gateway | ✅ | 201 | 41ms | data = {'id': 14, 'doc_code': 'QUAR-TEST2-20260627211237318794', 'title': 'Pipeline qua |
| 8 | Список карантина (второй pending, через Gateway) | gateway | ✅ | 200 | 36ms | data = [{'id': '1', 'system': 'MKS', 'code': '97.318794', 'found_in_document_id': '13', |
| 9 | Отклонить из карантина (reject, через Gateway) | gateway | ✅ | 200 | 41ms | data = {'pending_id': '1', 'status': 'rejected'} |
| 10 | Валидация классификации (reject, через Gateway) | gateway | ✅ | 200 | 30ms | data.mks_status = NOT_FOUND |

**Итог:** ✅ Пройден | Ping: ✅ | Steps: 10/10


---

_Report generated by `service_checker.py` at 2026-06-27 16:12:41 UTC_
