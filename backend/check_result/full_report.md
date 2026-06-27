# Full Report — API Coverage + Pipeline Testing + Gateway Tests

**Generated:** 2026-06-27 13:18:06 UTC

---

## 📊 Итоговая сводная таблица

| Service | Port | Ping | CheckDb | API | Pipelines | Status |
|---------|:----:|:----:|:-------:|:---:|:--------:|:------:|
| Auth Service | 18082 | ✅ | ✅ | ✅ | — | ✅ |
| Converter-Validator | 18086 | ✅ | — | ✅ | — | ✅ |
| Gateway | 18080 | ✅ | — | ❌ | — | ❌ |
| MinIO | 19000 | — | — | — | — | 🟡 dev |
| OCR Service | 18088 | — | — | — | — | 🟡 dev |
| Orchestrator | 18081 | ✅ | ✅ | ✅ | — | ✅ |
| Parser Service | 18087 | ✅ | — | ✅ | — | ✅ |
| Query Service | 18083 | ✅ | ✅ | ✅ | — | ✅ |
| RAG Builder | 18090 | ✅ | ✅ | ✅ | — | ✅ |
| RAG Search | 18091 | ✅ | — | ✅ | — | ✅ |
| Registry Service | 18084 | ✅ | ✅ | ❌ | — | ❌ |
| TEI | 18092 | ✅ | — | ✅ | — | ✅ |
| **Total** | | ✅ | ✅ | ❌ | ✅ | ❌ |

### 📋 Pipeline статусы по сервисам

| Service |  | Status |
|---------||:------:|
| Auth Service |  | 🟡 dev |
| Converter-Validator |  | 🟡 dev |
| Gateway |  | 🟡 dev |
| MinIO |  | 🟡 dev |
| OCR Service |  | 🟡 dev |
| Orchestrator |  | 🟡 dev |
| Parser Service |  | 🟡 dev |
| Query Service |  | 🟡 dev |
| RAG Builder |  | 🟡 dev |
| RAG Search |  | 🟡 dev |
| Registry Service |  | 🟡 dev |
| TEI |  | 🟡 dev |
| **Total** |  | ✅ |

#### 🔍 Пояснения к результатам

- **Gateway**: API: 20 эндпоинт(ов) упало; ⏭️ 3 эндпоинтов пропущено — нет контекста (prepare не создал данные)

- **Registry Service**: API: 3 эндпоинт(ов) упало


---

## 🔬 API Coverage — Детализация

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| Auth Service | 18082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| Converter-Validator | 18086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Gateway | 18080 | ✅ | — | 101 | 78 | **20** | **3** | ❌ |
| Orchestrator | 18081 | ✅ | ✅ | 35 | 35 | 0 | 0 | ✅ |
| Parser Service | 18087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 18083 | ✅ | ✅ | 27 | 27 | 0 | 0 | ✅ |
| RAG Builder | 18090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| RAG Search | 18091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| Registry Service | 18084 | ✅ | ✅ | 50 | 47 | **3** | 0 | ❌ |
| TEI | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | ✅ | **253** | **227** | **23** | **3** | ❌ |

### ⚠️ Workaround-предупреждения по сервисам

- **Auth Service**: PATCH /admin/users/{id}: docs ожидает audit_log_id, но сервис его не возвращает

- **Query Service**: ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

- **Registry Service**: ⚠️ Registry не поддерживает trailing slash — эндпоинты /classifiers, /documents, /terminology без / в конце.

- **Registry Service**: ⚠️ PATCH /documents/{id}/status — internal API (только Orchestrator), checker ожидает 403.

- **Registry Service**: ⚠️ PATCH /drafts/{id}/metadata — internal API (только Orchestrator), checker ожидает 404.


---

## 🌐 Gateway Integration Tests

| Metric | Value |
|--------|-------|
| **Status** | ✅ |
| **Total tests** | 251 |
| **Passed** | 251 |
| **Failed** | **0** |
| **Detail report** | [H:\Projects\PKB_neuroassistant_develop\backend\check_result\gateway_tests.md](H:\Projects\PKB_neuroassistant_develop\backend\check_result\gateway_tests.md) |

---

## 📋 Pipeline Testing — Детализация

| Pipeline | Описание | Ping | Шаги | ✅ Passed | ❌ Failed | Status |
|----------|----------|:----:|:----:|:---------:|:---------:|:------:|
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
| query → rag_search | ✅ | 200 | 27ms | results=0, processing_time_ms=20, total_found=0 |
| query → registry | ✅ | 200 | 15ms | data=[] — валидный ответ (БД пуста, но эндпоинт работает) |
| rag_search → infinity (TEI) | ✅ | 200 | 3ms | embedding_dim=312 — эмбеддинги работают |
| gateway → query | ✅ | 201 | 24ms | session_id=5 — прокси работает |
| **Total** | ✅ | | | 4/4 passed, 0 failed |


---

## 📋 Pipeline Testing — Пошаговая детализация


---

_Report generated by `service_checker.py` at 2026-06-27 13:18:06 UTC_
