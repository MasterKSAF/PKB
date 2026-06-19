# DDL-миграции (17.06.2026) — описание изменений схемы БД

> **Источник**: план `5.docs_action_plan_17_06.md` P2-1..P2-11 + P12-5 (valid_from/valid_until).
> **Применяется к**: PostgreSQL 15+ с pgvector 0.7+.
> **Статус**: 📝 документация.

Все миграции идемпотентны — повторный запуск безопасен. Ниже приведено описание требуемых изменений без SQL-кода. Для DBA — эквивалентные SQL-скрипты восстанавливаются из описания однозначно.

---

## P2-1. CHECK/ENUM на enum-поля

На поля таблицы `registry.documents` наложены CHECK-ограничения:

- `source_type` — `'GOST', 'GOST_R', 'OST', 'RD', 'TU', 'ISO', 'DNV', 'ASTM', 'OTHER'`
- `document_type` — `'normative', 'technical', 'drawing', 'specification', 'archival_scan'`
- `era` — `'USSR', 'CIS', 'RF', 'CURRENT'`
- `validity_status` — `'active', 'superseded', 'expired', 'cancelled', 'historical', 'draft'`
- `jurisdiction` — `'RU', 'EU', 'US', 'NO', 'INTL'`
- `processing_status` — `'created', 'pending_index', 'indexing', 'indexed', 'partially_indexed', 'failed'`

**Добавлено 18.06.2026:**

- `preview_snapshot` — новое поле `jsonb`, nullable. Хранит исходный JSON ответа Converter-validator preview, скопированный из `registry.drafts.preview_metadata` при approve документа. Для истории и аудита. Без CHECK (свободный JSONB).

---

## P2-2. file_hash_sha256, title_hash_sha256 → CHAR(64) + VECTOR(2048)

- `registry.documents.file_hash_sha256` и `title_hash_sha256` — тип изменён на `CHAR(64)` (был `text`)
- `registry.document_versions.file_hash_sha256` — также `CHAR(64)`
- `rag.document_chunks.embedding` — тип изменён на `VECTOR(2048)` (был `VECTOR(1536)`). **Требует переиндексации всех документов.** Порядок: удалить IVFFlat индекс → ALTER COLUMN → полная переиндексация → создать IVFFlat заново

---

## P2-3. UNIQUE-индексы

- `registry.documents (doc_code, era)` — уникальность по коду в пределах эпохи (partial, `WHERE doc_code IS NOT NULL`)
- `registry.document_sections (document_id, path)` — уникальность секции по ltree-пути в документе
- `registry.document_versions (document_id, version_number)` — уникальность номера версии в пределах документа
- `rag.document_chunks (section_id, chunk_index)` — уникальность индекса чанка в пределах секции
- `chat.projects (code)` — уникальность кода проекта

---

## P2-5. Soft-delete: deleted_at TIMESTAMPTZ

Поле `deleted_at TIMESTAMPTZ` добавлено в таблицы:
- `registry.documents` (+ partial index `WHERE deleted_at IS NULL`)
- `registry.document_versions`
- `registry.drafts`
- `registry.classifier_registry`
- `registry.terminology`

**Логика:** API Gateway фильтрует `WHERE deleted_at IS NULL` на list-эндпоинтах. Удаление — `UPDATE ... SET deleted_at = NOW()`. Hard-delete — только через `system_admin` с аудит-записью.

---

## P2-6. Индексы

| Индекс | Тип | Назначение |
|--------|-----|------------|
| `idx_documents_doc_code_btree` | B-tree | Поиск по коду документа |
| `idx_document_sections_path_gist` | GiST | Поиск по ltree-иерархии |
| `idx_document_references_target` | B-tree, partial `WHERE is_resolved = FALSE` | Быстрый резолвер ссылок |
| `idx_chat_messages_session_created` | B-tree `(session_id, created_at DESC)` | История чата |
| `idx_documents_pending_index` | B-tree `(created_at)`, partial `WHERE processing_status = 'pending_index'` | Scheduler индексации |
| `idx_documents_failed` | B-tree `(failed_at)`, partial `WHERE processing_status = 'failed'` | Мониторинг ошибок |
| `idx_documents_validity_active` | B-tree `(valid_from, valid_until)`, partial `WHERE validity_status = 'active'` | Поиск активных документов |
| `idx_documents_title_hash` | B-tree `(title_hash_sha256)` | Поиск по бизнес-ключу |

---

## P2-7. CHECK на положительность числовых полей

- `registry.documents.chunk_count` — `>= 0` (nullable)
- `registry.documents.file_size_bytes` — `> 0` (nullable)
- `registry.document_versions.version_number` — `> 0`
- `registry.document_versions.file_size_bytes` — `> 0` (nullable)

---

## P2-8. CHECK на соответствие кодов классификации справочнику

- `mks_oks_code` — проверка существования в `registry.classifier_registry` с `system = 'MKS_OKS'`
- `okstu_code` — проверка существования с `system = 'OKSTU'`

Оба ограничения — через подзапрос.

---

## P2-9. valid_from / valid_until / indexing_txn_id

- Добавлены поля `valid_from DATE NOT NULL DEFAULT '1000-01-01'` и `valid_until DATE NOT NULL DEFAULT '9999-12-31'` в `registry.documents` с CHECK `valid_until >= valid_from`
- Индекс `idx_documents_validity_range` на `(valid_from, valid_until)`
- Поле `indexing_txn_id UUID` в `rag.document_chunks` + partial index `WHERE indexing_txn_id IS NOT NULL`

**Конвенция dateMax:** бессрочные документы — `9999-12-31`, а не `infinity`.

---

## P2-10. Унификация нейминга

- `registry.document_versions.uploaded_at` → `created_at`
- `registry.document_versions.uploaded_by` → `created_by`
- `registry.drafts.uploaded_by` → `created_by` (если поле есть)

**JSON-примеры в API:** `integration_service_api.md` (строки 54, 64 — D20) и `orchestrator_service_api.md` (строки 265–275 — D21) должны быть синхронизированы с переименованными полями.

---

## P2-11. Этот файл

Создан `docs/database/ddl_migrations_17_06.md`.

---

## Приложение. Таблица `audit.events` (P11-4)

Таблица `audit.events` с полями:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL PK | |
| `event_id` | UUID UNIQUE | Сквозной ID события |
| `user_id` | BIGINT FK → `auth.users` | Кто совершил действие (SET NULL) |
| `role` | VARCHAR(64) | Роль пользователя на момент действия |
| `action` | VARCHAR(128) NOT NULL | Тип действия |
| `entity_type` | VARCHAR(64) NOT NULL | Тип объекта |
| `entity_id` | BIGINT | ID объекта |
| `before` | JSONB | Состояние до |
| `after` | JSONB | Состояние после |
| `ip_address` | INET | IP-адрес |
| `user_agent` | TEXT | User-Agent |
| `request_id` | UUID | ID запроса |
| `created_at` | TIMESTAMPTZ | Когда |

Индексы: `(user_id, created_at DESC)`, `(entity_type, entity_id, created_at DESC)`, `(action, created_at DESC)`.

---

## Приложение. Таблица `pipeline.draft_notifications` (P12-3 / P3-5)

Таблица `pipeline.draft_notifications`:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL PK | |
| `draft_id` | BIGINT NOT NULL | Черновик (FK) |
| `source` | VARCHAR(32) CHECK: `parser`, `ocr`, `converter`, `registry` | Какой сервис создал |
| `code` | VARCHAR(128) NOT NULL | Код уведомления |
| `severity` | VARCHAR(16) CHECK: `info`, `warning`, `error`, `critical` | Важность |
| `category` | VARCHAR(16) DEFAULT `quality` CHECK: `security`, `quality` | Категория |
| `message` | TEXT NOT NULL | Описание |
| `location` | JSONB | `{page, block}` |
| `suggested_action` | TEXT | Рекомендация оператору |
| `created_at` | TIMESTAMPTZ DEFAULT NOW() | |

Индекс: `(draft_id, created_at DESC)`.

---

## Порядок применения

1. **P2-1** (CHECK/ENUM) — блокирует невалидные значения
2. **P2-5** (soft-delete) — до UNIQUE, чтобы не мешал
3. **P2-2** (CHAR(64)) — после проверки длин
4. **P2-3** (UNIQUE)
5. **P2-6** (индексы)
6. **P2-7** (CHECK positive)
7. **P2-8** (классификаторы) — опционально
8. **P2-9** (validity + txn_id)
9. **P2-10** (rename)
11. **audit.events** — отдельно
12. **draft_notifications** — отдельно
