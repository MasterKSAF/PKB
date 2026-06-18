# DDL-миграции (17.06.2026)

> **Источник**: план `5.docs_action_plan_17_06.md` P2-1..P2-11 + P12-5 (valid_from/valid_until).
> **Применяется к**: PostgreSQL 15+ с pgvector 0.7+.
> **Статус**: 📝 документация готова, миграции должны быть выполнены DBA.

Все миграции приведены для применения через `psql` или миграционный фреймворк
(например, `alembic upgrade head`). Миграции **идемпотентны** — повторный запуск
безопасен (используется `IF NOT EXISTS`, `DROP IF EXISTS`).

---

## P2-1. CHECK/ENUM на enum-поля

```sql
-- source_type
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_source_type
  CHECK (source_type IN ('GOST', 'GOST_R', 'OST', 'RD', 'TU', 'ISO', 'DNV', 'ASTM', 'OTHER'));

-- document_type
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_document_type
  CHECK (document_type IN ('normative', 'technical', 'drawing', 'specification', 'archival_scan'));

-- era
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_era
  CHECK (era IN ('USSR', 'CIS', 'RF', 'CURRENT'));

-- validity_status (юридический)
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_validity_status
  CHECK (validity_status IN ('active', 'superseded', 'expired', 'cancelled', 'historical', 'draft'));

-- jurisdiction
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_jurisdiction
  CHECK (jurisdiction IN ('RU', 'EU', 'US', 'NO', 'INTL'));

-- processing_status (FSM)
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_processing_status
  CHECK (processing_status IN ('created', 'pending_index', 'indexing', 'indexed', 'partially_indexed', 'failed'));
```

---

## P2-2. file_hash_sha256, title_hash_sha256 → CHAR(64) + VECTOR(2048) (D10, P13-1)

```sql
-- ВАЖНО: миграция требует предварительной проверки, что длина всех значений = 64 символам
-- SELECT length(file_hash_sha256), count(*) FROM registry.documents GROUP BY length(file_hash_sha256);
-- SELECT length(title_hash_sha256), count(*) FROM registry.documents GROUP BY length(title_hash_sha256);

-- P2-2: file_hash_sha256 / title_hash_sha256 → CHAR(64)
ALTER TABLE registry.documents
  ALTER COLUMN file_hash_sha256 TYPE CHAR(64),
  ALTER COLUMN title_hash_sha256 TYPE CHAR(64);

ALTER TABLE registry.document_versions
  ALTER COLUMN file_hash_sha256 TYPE CHAR(64);

-- cas_storage_specification.md (см. P5-9): SHA-256 ключ без расширения

-- D10, P13-1: embedding VECTOR(2048) для Qwen3-Embedding-4B
-- ВНИМАНИЕ: меняется размерность! Требуется переиндексация ВСЕХ документов.
-- Шаги:
--  1. Удалить IVFFlat индекс
--  2. ALTER COLUMN на VECTOR(2048) — старые данные стираются (default NULL)
--  3. Запустить полную переиндексацию (POST /rag/build для всех документов)
--  4. После завершения — создать IVFFlat заново

DROP INDEX IF EXISTS idx_document_chunks_embedding;
ALTER TABLE rag.document_chunks
  ALTER COLUMN embedding TYPE VECTOR(2048);
-- После переиндексации:
-- CREATE INDEX idx_document_chunks_embedding ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## P2-3. UNIQUE-индексы

```sql
-- Уникальность (doc_code, era) — невозможно иметь два документа с одинаковым кодом в одной эпохе
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_doc_code_era
  ON registry.documents (doc_code, era)
  WHERE doc_code IS NOT NULL;

-- Уникальность (document_id, path) — невозможно дублирование секций по ltree-пути
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_sections_doc_path
  ON registry.document_sections (document_id, path)
  WHERE path IS NOT NULL;

-- Уникальность (document_id, version_number) — невозможно две версии с одним номером
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_versions_doc_ver
  ON registry.document_versions (document_id, version_number);

-- Уникальность (section_id, chunk_index) — невозможно дублирование чанков
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_chunks_section_idx
  ON rag.document_chunks (section_id, chunk_index);

-- Уникальность chat.projects.code
CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_projects_code
  ON chat.projects (code);
```

---

## P2-4. ON DELETE/ON UPDATE для всех FK

```sql
-- document_sections → documents (CASCADE)
ALTER TABLE registry.document_sections
  DROP CONSTRAINT IF EXISTS document_sections_document_id_fkey,
  ADD CONSTRAINT document_sections_document_id_fkey
    FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- document_sections → document_sections (parent_id, SET NULL)
ALTER TABLE registry.document_sections
  DROP CONSTRAINT IF EXISTS document_sections_parent_id_fkey,
  ADD CONSTRAINT document_sections_parent_id_fkey
    FOREIGN KEY (parent_id) REFERENCES registry.document_sections(id) ON DELETE SET NULL ON UPDATE CASCADE;

-- document_references → documents (source, RESTRICT)
ALTER TABLE registry.document_references
  DROP CONSTRAINT IF EXISTS document_references_source_document_id_fkey,
  ADD CONSTRAINT document_references_source_document_id_fkey
    FOREIGN KEY (source_document_id) REFERENCES registry.documents(id) ON DELETE RESTRICT ON UPDATE CASCADE;

-- document_references → documents (resolved, SET NULL)
ALTER TABLE registry.document_references
  DROP CONSTRAINT IF EXISTS document_references_resolved_document_id_fkey,
  ADD CONSTRAINT document_references_resolved_document_id_fkey
    FOREIGN KEY (resolved_document_id) REFERENCES registry.documents(id) ON DELETE SET NULL ON UPDATE CASCADE;

-- document_versions → documents (CASCADE)
ALTER TABLE registry.document_versions
  DROP CONSTRAINT IF EXISTS document_versions_document_id_fkey,
  ADD CONSTRAINT document_versions_document_id_fkey
    FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- document_categories (CASCADE на обеих сторонах — см. db_diagrams.md §13)
ALTER TABLE registry.document_categories
  DROP CONSTRAINT IF EXISTS document_categories_document_id_fkey,
  ADD CONSTRAINT document_categories_document_id_fkey
    FOREIGN KEY (document_id) REFERENCES registry.documents(id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE registry.document_categories
  DROP CONSTRAINT IF EXISTS document_categories_category_id_fkey,
  ADD CONSTRAINT document_categories_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES registry.categories(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- chat.sessions → users, projects
ALTER TABLE chat.sessions
  DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey,
  ADD CONSTRAINT chat_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE chat.sessions
  DROP CONSTRAINT IF EXISTS chat_sessions_project_id_fkey,
  ADD CONSTRAINT chat_sessions_project_id_fkey
    FOREIGN KEY (project_id) REFERENCES chat.projects(id) ON DELETE SET NULL ON UPDATE CASCADE;

-- chat.messages → sessions (CASCADE)
ALTER TABLE chat.messages
  DROP CONSTRAINT IF EXISTS chat_messages_session_id_fkey,
  ADD CONSTRAINT chat_messages_session_id_fkey
    FOREIGN KEY (session_id) REFERENCES chat.sessions(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- rag.document_chunks → sections
ALTER TABLE rag.document_chunks
  DROP CONSTRAINT IF EXISTS document_chunks_section_id_fkey,
  ADD CONSTRAINT document_chunks_section_id_fkey
    FOREIGN KEY (section_id) REFERENCES registry.document_sections(id) ON DELETE CASCADE ON UPDATE CASCADE;
```

---

## P2-5. Soft-delete: deleted_at TIMESTAMPTZ

```sql
-- documents
ALTER TABLE registry.documents
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_documents_deleted_at
  ON registry.documents (deleted_at)
  WHERE deleted_at IS NULL;  -- partial index: только активные

-- document_versions
ALTER TABLE registry.document_versions
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- drafts
ALTER TABLE registry.drafts
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- classifier_registry
ALTER TABLE registry.classifier_registry
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- terminology
ALTER TABLE registry.terminology
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
```

> **Логика soft-delete**: API Gateway фильтрует `WHERE deleted_at IS NULL` на всех list-эндпоинтах. Удаление — `UPDATE ... SET deleted_at = NOW()`. Hard-delete выполняется только через `system_admin` с аудит-записью.

---

## P2-6. Индексы

```sql
-- B-tree на doc_code (поиск по коду)
CREATE INDEX IF NOT EXISTS idx_documents_doc_code_btree
  ON registry.documents (doc_code);

-- GiST на ltree path (поиск по иерархии)
CREATE INDEX IF NOT EXISTS idx_document_sections_path_gist
  ON registry.document_sections USING GIST (path);

-- target_doc_code (быстрый резолвер)
CREATE INDEX IF NOT EXISTS idx_document_references_target
  ON registry.document_references (target_doc_code)
  WHERE is_resolved = FALSE;

-- chat: (session_id, created_at)
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
  ON chat.messages (session_id, created_at DESC);

-- Частичные индексы по FSM-статусам (для Scheduler'ов)
CREATE INDEX IF NOT EXISTS idx_documents_pending_index
  ON registry.documents (created_at)
  WHERE processing_status = 'pending_index';

CREATE INDEX IF NOT EXISTS idx_documents_failed
  ON registry.documents (failed_at)
  WHERE processing_status = 'failed';

-- Дополнительные индексы
CREATE INDEX IF NOT EXISTS idx_documents_validity_active
  ON registry.documents (valid_from, valid_until)
  WHERE validity_status = 'active';

CREATE INDEX IF NOT EXISTS idx_documents_title_hash
  ON registry.documents (title_hash_sha256);
```

---

## P2-7. CHECK на положительность числовых полей

```sql
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_chunk_count_positive
  CHECK (chunk_count IS NULL OR chunk_count >= 0),
  ADD CONSTRAINT chk_documents_file_size_positive
  CHECK (file_size_bytes IS NULL OR file_size_bytes > 0);

ALTER TABLE registry.document_versions
  ADD CONSTRAINT chk_doc_versions_version_number_positive
  CHECK (version_number > 0),
  ADD CONSTRAINT chk_doc_versions_file_size_positive
  CHECK (file_size_bytes IS NULL OR file_size_bytes > 0);

-- processing_time_ms отсутствует в текущей схеме; добавляется при расширении
-- (если потребуется в pipeline.task_steps):
-- ALTER TABLE pipeline.task_steps
--   ADD CONSTRAINT chk_task_steps_processing_time_positive
--   CHECK (processing_time_ms IS NULL OR processing_time_ms > 0);
```

---

## P2-8. CHECK на mks_oks_code/okstu_code

```sql
-- Коды должны соответствовать справочнику classifier_registry
ALTER TABLE registry.documents
  ADD CONSTRAINT chk_documents_mks_oks_valid
  CHECK (
    mks_oks_code IS NULL
    OR EXISTS (
      SELECT 1 FROM registry.classifier_registry cr
      WHERE cr.code = mks_oks_code AND cr.system = 'MKS_OKS' AND cr.deleted_at IS NULL
    )
  ),
  ADD CONSTRAINT chk_documents_okstu_valid
  CHECK (
    okstu_code IS NULL
    OR EXISTS (
      SELECT 1 FROM registry.classifier_registry cr
      WHERE cr.code = okstu_code AND cr.system = 'OKSTU' AND cr.deleted_at IS NULL
    )
  );
```

> **Замечание**: CHECK с подзапросом — на больших объёмах (миллионы документов) может замедлить INSERT. В этом случае заменить на **триггер** `BEFORE INSERT OR UPDATE` (см. P2-9 ниже).

---

## P2-9. Триггер синхронизации document_chunks.document_id и valid_from/valid_until (P12-5)

```sql
-- 1. Новые поля valid_from / valid_until (P12-5)
--
-- valid_from: дата начала действия документа.
--   NOT NULL. Если дата начала неизвестна, устанавливается в `dateMin = '1000-01-01'`
--   (символическая константа, аналог `dateMax`). Альтернатива NULL отвергнута:
--   фильтр `?valid_at=...` требует NOT NULL для индексов и простых сравнений.
-- valid_until: дата окончания действия.
--   NOT NULL. Для бессрочных — `dateMax = '9999-12-31'` (выбрано 17.06).
ALTER TABLE registry.documents
  ADD COLUMN IF NOT EXISTS valid_from DATE NOT NULL DEFAULT '1000-01-01',
  ADD COLUMN IF NOT EXISTS valid_until DATE NOT NULL DEFAULT '9999-12-31',
  ADD CONSTRAINT chk_documents_valid_range CHECK (valid_until >= valid_from);

CREATE INDEX IF NOT EXISTS idx_documents_validity_range
  ON registry.documents (valid_from, valid_until);

-- 2. Синхронизация document_id между chunks и sections
CREATE OR REPLACE FUNCTION rag.sync_chunk_document_id()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.section_id IS NOT NULL THEN
    SELECT document_id INTO NEW.document_id
    FROM registry.document_sections
    WHERE id = NEW.section_id;
    IF NEW.document_id IS NULL THEN
      RAISE EXCEPTION 'section_id % not found', NEW.section_id;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_chunk_document_id ON rag.document_chunks;
CREATE TRIGGER trg_sync_chunk_document_id
  BEFORE INSERT OR UPDATE OF section_id ON rag.document_chunks
  FOR EACH ROW
  EXECUTE FUNCTION rag.sync_chunk_document_id();

-- 3. Колонка indexing_txn_id (для компенсации в P1-18)
ALTER TABLE rag.document_chunks
  ADD COLUMN IF NOT EXISTS indexing_txn_id UUID;

CREATE INDEX IF NOT EXISTS idx_document_chunks_txn
  ON rag.document_chunks (indexing_txn_id)
  WHERE indexing_txn_id IS NOT NULL;
```

> **Конвенция dateMax (P12-5, решение 17.06)**: бессрочные документы получают `valid_until = '9999-12-31'::date` (выбрано пользователем 17.06 как универсальная конвенция, совместимая с любыми SQL-клиентами и ORM). Альтернатива `'infinity'::date` отвергнута. Зафиксировано в `glossary.md` и `validity_dates_spec.md` (NEW).

---

## P2-10. Унификация нейминга uploaded_at/event_at → created_at/updated_at

```sql
-- document_versions
ALTER TABLE registry.document_versions
  RENAME COLUMN uploaded_at TO created_at;
ALTER TABLE registry.document_versions
  RENAME COLUMN uploaded_by TO created_by;

-- drafts
ALTER TABLE registry.drafts
  RENAME COLUMN uploaded_by TO created_by;  -- если поле есть

-- Также для консистентности: pipeline.tasks / task_steps, если есть uploaded_*
-- (применять после ревизии схемы)
```

> **Связанные файлы**: `integration_service_api.md:54,64` (D20), `orchestrator_service_api.md:265-275` (D21) — JSON-примеры должны быть синхронизированы.

---

## P2-11. Этот файл

Создан `docs/database/ddl_migrations_17_06.md` (P2-11, 17.06.2026).

---

## Приложение. Полный DDL для новой таблицы `audit.events` (P11-4)

```sql
CREATE TABLE IF NOT EXISTS audit.events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    user_id         BIGINT REFERENCES auth.users(id) ON DELETE SET NULL,
    role            VARCHAR(64),
    action          VARCHAR(128) NOT NULL,
    entity_type     VARCHAR(64) NOT NULL,
    entity_id       BIGINT,
    before          JSONB,
    after           JSONB,
    ip_address      INET,
    user_agent      TEXT,
    request_id      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit.events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit.events (entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit.events (action, created_at DESC);

COMMENT ON TABLE audit.events IS 'Журнал действий пользователей (отдельно от системных логов). См. P11-4.';
```

---

## Приложение. Полный DDL для `pipeline.draft_notifications` (P12-3 / P3-5)

```sql
CREATE TABLE IF NOT EXISTS pipeline.draft_notifications (
    id               BIGSERIAL PRIMARY KEY,
    draft_id         BIGINT NOT NULL,
    source           VARCHAR(32) NOT NULL CHECK (source IN ('parser', 'ocr', 'converter', 'registry')),
    code             VARCHAR(128) NOT NULL,
    severity         VARCHAR(16) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    category         VARCHAR(16) NOT NULL DEFAULT 'quality' CHECK (category IN ('security', 'quality')),
    message          TEXT NOT NULL,
    location         JSONB,  -- {page, block}
    suggested_action TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_draft_notifications_draft ON pipeline.draft_notifications (draft_id, created_at DESC);

-- Связь с черновиком (поле operator_review_required не нужно — статус review_required в registry.drafts.status уже кодирует это)
```

---

## Порядок применения

1. **P2-1** (CHECK/ENUM) — критично: блокирует сохранение невалидных значений.
2. **P2-5** (soft-delete) — нужен до P2-3 (UNIQUE), чтобы UNIQUE не мешал soft-delete.
3. **P2-2** (CHAR(64)) — после проверки длин.
4. **P2-3** (UNIQUE).
5. **P2-4** (FK ON DELETE/UPDATE).
6. **P2-6** (индексы).
7. **P2-7** (CHECK positive).
8. **P2-8** (классификаторы) — **опционально** для больших объёмов, заменить триггером.
9. **P2-9** (validity + sync trigger + txn_id).
10. **P2-10** (rename).
11. **audit.events** (P11-4) — отдельно.
12. **draft_notifications** (P12-3 / P3-5) — отдельно.
