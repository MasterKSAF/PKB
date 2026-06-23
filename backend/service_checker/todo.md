# План исправления всех выявленных проблем

## Статус (2026-06-23, recheck #4)

**Pipeline статус**: 15 пайплайнов
- ✅ 10 пройдено
- ❌ 5 падают (все из-за Orchestrator → Registry 422)
- 🎉 2 пайплайна исправлено чекером: `full_document_lifecycle`, `multi_document_cross_search`

---

## БЛОК 1: Уже исправлено в чекере (3 файла)

### ✅ RAG Builder 500 — workaround

**Файлы**: `core/api_coverage_test.py`, `pipelines/base.py`
**Суть**: Добавлен DROP CONSTRAINT для `uq_rag_chunks_section_chunk` перед тестами RAG Builder.
**Корневая причина**: UNIQUE(section_id, chunk_index) — все пайплайны шлют `section_id=1`, второй документ вызывает duplicate key.
**⚠️ Это workaround**. Нужен permanent fix в RAG Builder (см. Блок 3).

### ✅ Query Service — prepare для проекта

**Файл**: `services/query.py`
**Суть**: 
- Добавлен prepare endpoint `POST /chat/projects` → `extract project_id`
- DELETE /chat/projects перенесён в конец списка endpoints

---

## БЛОК 2: Критические проблемы сервисов (блокируют пайплайны)

### 🔴 P0: Orchestrator → Registry 422 на POST /drafts

**Симптом**: checker → `POST /api/v1/drafts` → Orchestrator 500 → внутри `POST /registry/drafts` → Registry 422.
**Затрагивает**: 9 пайплайнов, Gateway 3 skipped.

**Лог Orchestrator**:
```
HTTP error: POST /registry/drafts -> 422 (0.006s, retries exhausted)
HTTP error: POST /registry/documents/check-uniqueness -> 422 (0.008s, retries exhausted)
```

**Проверено**: checker напрямую в Registry `POST /registry/drafts` работает (201/409).
**Проблема в Orchestrator**: он неправильно преобразует запрос checker'а при отправке в Registry.

**Что делать**:
1. Посмотреть код Orchestrator — как он формирует тело для `POST /registry/drafts`
2. Registry ожидает: `{"file_key": "...", "document_key": "...", "status": "uploaded", "created_by": "..."}`
3. Сверить, что именно Orchestrator отправляет

**Ожидаемый фикс**: Orchestrator.

### 🟡 P1: RAG Builder — смержить 5 миграций в одну базовую

**Текущее состояние**: 5 последовательных Alembic миграций, которые исторически фиксили
проблемы с типами (UUID→BIGINT, vector dim 1536→2048), FK и UNIQUE constraint.

**Задача**: удалить все существующие миграции, оставить одну — финальную, правильную.
Это решит:
- Проблему с UNIQUE constraint `uq_rag_chunks_section_chunk` (не включать его в новую миграцию)
- Проблему с FK `fk_rag_document_chunks_section_id` (не включать)
- Упростит поддержку (история не нужна)

**Новая единая миграция должна**:
1. Создать схему `rag`
2. Создать `rag.document_chunks` с BIGINT для id/section_id/document_id
3. `embedding VECTOR({VECTOR_DIMENSION})` — брать размерность из env
4. `indexing_txn_id UUID` — колонка из 0004 миграции
5. Индексы: `ix_rag_doc_chunks_doc_id`, `ix_rag_doc_chunks_tsv` (GIN), `ix_rag_doc_chunks_embedding_ivfflat`
6. **НЕ включать** UNIQUE(section_id, chunk_index) — ломает индексацию нескольких документов
7. **НЕ включать** FK на registry — опциональные и не обязательные для работы

**Где править**: `rag_builder_service/alembic/versions/` — удалить 5 файлов, создать 1 новый

---

## БЛОК 3: DB — миграции Alembic (5 проблем)

### 3a. Схема `auth` не создана (таблицы в `auth_service`)

| Ожидание | Реальность |
|----------|-----------|
| Схема `auth`, таблица `auth.users` | Схема `auth_service`, таблица `auth_service.users` |

В БД есть все таблицы Auth (users, roles, audit_events и др.) но в схеме `auth_service`, а checker ищет `auth`.

**Варианты**:
1. **Исправить checker**: заменить `EXPECTED_SCHEMAS: "auth" → "auth_service"` и `EXPECTED_AUTH_TABLES: "auth.users" → "auth_service.users"` (в `core/db_check.py`)
2. **Исправить сервис**: создать синоним/алиас `auth` → `auth_service` или переименовать схему

### 3b. Схема `pipeline` не существует

Трёх таблиц нет нигде:
- `pipeline.tasks` 
- `pipeline.task_steps`
- `pipeline.draft_notifications`

**Причина**: Orchestrator не использует ни Alembic, ни `create_all` для этой схемы.

**Что делать**: добавить в Orchestrator:
- Либо Alembic миграцию для создания `pipeline` схемы и таблиц
- Либо `Base.metadata.create_all()` при старте

### 3c. 4 UNIQUE-индекса Registry не созданы

| Индекс | Таблица | Статус |
|--------|---------|:------:|
| `documents_doc_code_era_key` | `registry.documents` | ❌ |
| `documents_title_hash_sha256_key` | `registry.documents` | ❌ |
| `document_versions_doc_id_path_key` | `registry.document_versions` | ❌ |
| `document_versions_doc_id_version_key` | `registry.document_versions` | ❌ |

**Что делать**: Registry не использует Alembic — таблицы создаются через `create_all`. Индексы нужно определить в SQLAlchemy моделях:
- `registry_service/app/models.py` или `registry_service/app/db/models.py`
- Добавить `__table_args__` с `UniqueConstraint` для каждого индекса

### 3d. UNIQUE-индекс `rag.document_chunks_section_chunk_key` — дропнут чекером

См. Блок 2 (P1). После мержа миграций — новая миграция его не создаёт,
костыль в чекере можно будет убрать.

---

## БЛОК 4: Некритичные проблемы сервисов

### 🟡 Registry: preview_snapshot не возвращается

**Симптом**: `document_processing` pipeline падает на шаге "Проверка preview_snapshot".
**Причина**: `GET /registry/documents/{id}` не возвращает `data.preview_snapshot`.
**Где править**: `registry_service` — эндпоинт получения документа.

### 🟡 Registry: Categories (7 CRUD) не реализованы

**Симптом**: 2 failed в API Coverage Registry.
**Что делать**: реализовать CRUD для `/api/v1/registry/categories/*`.

### ⚪ OpenTelemetry UNAVAILABLE

**Симптом**: Все сервисы пишут ошибки OTLP exporter.
**Причина**: signoz-otel-collector не запущен.
**Влияние**: только observability, бизнес-логика не страдает.
**Что делать**: запустить signoz контейнер.

---

## Рекомендуемый порядок исправления

```
🔴 P0  Orchestrator → Registry 422       [9 пайплайнов]
   │
🔴 P0  DB: схема auth + pipeline         [DB Check красный]
   │
🔴 P0  DB: 4 UNIQUE индекса Registry     [DB Check красный]
   │
🟡 P1  RAG Builder: смержить 5 миграций в 1  [убрать костыль чекера]
   │
🟡 P2  Registry: preview_snapshot         [1 пайплайн]
   │
🟡 P2  Registry: Categories               [2 failed API Coverage]
   │
⚪ P3  OpenTelemetry signoz               [observability]
```

## Структура Alembic миграций в проекте

| Сервис | Использует Alembic | Версия |
|--------|:------------------:|:------:|
| RAG Builder | ✅ (будет 1) | 20260528_0001 → ... → 20260622_0005 (5 шт → 1 базовая) |
| Registry | ❌ | create_all при старте |
| Auth | ❌ | create_all при старте |
| Orchestrator | ❌ | create_all при старте |
| Query | ❌ | create_all при старте |
