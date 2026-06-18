# Схема базы данных (объединённая)

> Сводная ER-диаграмма.

---

## ER-диаграмма

```mermaid
erDiagram
    registry.documents {
        bigint id PK
        bigint draft_id FK
        text doc_code
        text title
        text normalized_title
        varchar source_type
        varchar document_type
        text mks_oks_code
        text okstu_code
        text udk_code
        date valid_from
        date valid_until
        timestamptz deleted_at
        varchar era
        varchar validity_status
        varchar jurisdiction
        text issuing_body
        date adoption_date
        date effective_from
        text replaces
        text status_note
        char64 file_hash_sha256
        char64 title_hash_sha256
        jsonb preview_snapshot
        bigint file_size_bytes
        varchar processing_status
        int chunk_count
        bigint successor_doc_id FK
        bigint predecessor_doc_id FK
        bigint current_version_id FK
        text created_by
        text updated_by
        timestamptz created_at
        timestamptz updated_at
    }

    registry.document_sections {
        bigint id PK
        bigint document_id FK
        bigint parent_id FK
        text clause
        text title
        int level
        ltree path
        int page
        jsonb bbox
        varchar type
        jsonb content
        timestamptz created_at
        timestamptz updated_at
    }

    registry.document_references {
        bigint id PK
        bigint source_document_id FK
        text target_doc_code
        varchar reference_type
        text context
        text current_status
        text replaced_by
        date replacement_date
        boolean is_resolved
        bigint resolved_document_id FK
        timestamptz created_at
        timestamptz updated_at
    }

    registry.document_versions {
        bigint id PK
        bigint document_id FK
        int version_number
        varchar(50) revision
        text source_filename "original file name"
        char64 file_hash_sha256 UNIQUE "CAS-дедупликация"
        bigint file_size_bytes
        text format_code
        text format_label
        text file_path "CAS path in MinIO"
        text uploaded_by
        timestamptz uploaded_at
        timestamptz updated_at
    }

    registry.drafts {
        bigint id PK
        varchar file_key
        varchar document_key
        varchar status
        float confidence
        jsonb preview_metadata
        jsonb raw_data
        varchar error_code
        varchar error_message
        text source_filename "original file name"
        varchar created_by
        varchar updated_by
        varchar uploaded_by
        timestamptz created_at
        timestamptz updated_at
    }

    registry.categories {
        bigint id PK
        varchar name
        text description
        varchar color
        timestamptz created_at
        timestamptz updated_at
    }

    registry.document_categories {
        bigint document_id PK, FK
        bigint category_id PK, FK
    }

    registry.classifier_registry {
        varchar classifier_system PK "ENUM: MKS, OKSTU, UDC, EXTERNAL"
        text code PK
        text parent_code FK "FK -> self (same classifier_system)"
        text full_name
        varchar status "DEFAULT 'active'"
        date effective_date
        text replaced_by
        timestamptz created_at
    }

    pipeline.tasks {
        bigint id PK
        bigint draft_id
        bigint document_id FK
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    pipeline.task_steps {
        bigint id PK
        bigint task_id FK
        varchar step_name
        varchar service_name
        varchar status
        jsonb input_data
        jsonb output_data
        varchar error_code
        varchar error_message
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }

    pipeline.draft_notifications {
        bigint id PK
        bigint draft_id FK "FK -> registry.drafts.id"
        varchar source
        varchar code
        varchar severity
        varchar category
        text message
        jsonb location
        text suggested_action
        timestamptz created_at
    }

    registry.document_history {
        bigint id PK
        bigint document_id FK
        text event_type
        text old_status
        text new_status
        text comment
        text changed_by
        jsonb document_snapshot
        timestamptz event_at
    }

    rag.document_chunks {
        bigint id PK
        bigint section_id FK
        bigint document_id FK
        int chunk_index
        text content
        vector embedding
        tsvector tsv
        varchar strategy
        int page
        jsonb bbox
        float confidence
        timestamptz created_at
        timestamptz updated_at
    }

    auth.users {
        bigint id PK
        varchar email
        text full_name
        text password_hash
        jsonb roles
        text position
        boolean is_active
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }

    registry.terminology {
        bigint id PK
        text raw_term
        text standard_term
        text normalized_value
        varchar term_type
        boolean is_case_sensitive
        text definition
        jsonb synonyms
        text[] related_docs
        text[] scope
        boolean is_blocked
        timestamptz created_at
        timestamptz updated_at
    }

    chat.projects {
        bigint id PK
        text code
        text name
        text description
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    chat.sessions {
        bigint id PK
        text title
        bigint user_id FK
        bigint project_id FK
        bigint[] document_ids
        jsonb options
        timestamptz created_at
        timestamptz updated_at
    }
    %% FK user_id -> auth.users.id

    chat.messages {
        bigint id PK
        bigint session_id FK
        text role
        text content
        text status
        jsonb sources
        jsonb attachments
        jsonb options
        jsonb feedback
        int processing_time_ms
        timestamptz created_at
        timestamptz updated_at
    }

    registry.documents ||--o{ registry.document_sections : has
    registry.document_sections ||--o{ registry.document_sections : parent_of
    registry.document_sections ||--o{ rag.document_chunks : contains
    registry.documents ||--o{ registry.document_references : source_of
    registry.documents ||--o{ registry.document_history : audited_by
    registry.documents ||--o{ registry.document_versions : versioned_by
    registry.documents ||--o{ rag.document_chunks : chunked_by
    chat.projects ||--o{ chat.sessions : has_sessions
    chat.sessions ||--o{ chat.messages : has_messages

    registry.categories ||--o{ registry.document_categories : has_documents
    registry.documents ||--o{ registry.document_categories : categorized_by

    pipeline.tasks ||--o{ pipeline.task_steps : has
    pipeline.tasks }o--|o registry.documents : produces  (FK document_id nullable)
    registry.documents }o--|o registry.drafts : originates_from  (FK draft_id nullable)
    registry.classifier_registry ||--o{ registry.classifier_registry : parent_of  (self-reference via parent_code)
    registry.documents }o--|| registry.classifier_registry : mks_classified_by  (FK mks_oks_code -> code + generated mks_system)
    registry.documents }o--|| registry.classifier_registry : okstu_classified_by  (FK okstu_code -> code + generated okstu_system)

    pipeline.draft_notifications ||--|| registry.drafts : logged_for  (FK draft_id -> registry.drafts.id)
```

---

### Индексы

| Таблица | Поле | Тип индекса | Назначение |
|---------|------|------------|-----------|
| `chat.sessions` | `user_id` | B-tree | Фильтрация сессий по пользователю |
| `chat.sessions` | `created_at` | B-tree | Сортировка по дате |
| `chat.messages` | `session_id` | B-tree | Поиск сообщений сессии |
| `chat.messages` | `created_at` | B-tree | Сортировка по времени |
| `registry.documents` | `processing_status` | B-tree | Фильтрация по статусу |
| `registry.documents` | `created_at` | B-tree | Сортировка по дате загрузки |
| `registry.documents` | `draft_id` | B-tree | Поиск документа по черновику |
| `registry.drafts` | `file_key` | B-tree | Поиск по ключу MinIO |
| `registry.drafts` | `document_key` | B-tree | Поиск по бизнес-ключу |
| `pipeline.tasks` | `draft_id` | B-tree | Поиск задачи по черновику |
| `pipeline.tasks` | `document_id` | B-tree | Поиск задачи по документу |
| `pipeline.task_steps` | `task_id` | B-tree | Поиск этапов задачи |
| `registry.document_versions` | `document_id` | B-tree | Поиск версий документа |
| `registry.documents` | `title_hash_sha256` | B-tree UNIQUE | Дедупликация по бизнес-ключу |
| `registry.documents` | `(valid_from, valid_until)` | B-tree | Поиск документов по дате действия |
| `registry.drafts` | `status` | B-tree | Фильтрация черновиков по статусу |
| `registry.document_categories` | `category_id` | B-tree | Поиск категорий документа (обратная сторона many-to-many) |
| `registry.document_categories` | `content` | GIN | Поиск по JSONB-полям (например, `content.amendments[].type`) |
| `pipeline.draft_notifications` | `(draft_id, created_at DESC)` | B-tree | Поиск уведомлений черновика, сортировка по времени |

## Ключевые условия и ограничения

| Таблица | Поле | Условие |
|---------|------|---------|
| `registry.document_sections` | `type` | `CHECK (type IN ('text','textBlock','headerFooter','table','list','image','formula'))` |
| `registry.documents` | `file_hash_sha256` | Для быстрого дубликат-детекта (`WHERE file_hash_sha256 = ? AND file_size_bytes = ?`) |
| `registry.documents` | `title_hash_sha256` | **P2-3**: UNIQUE — дедупликация по бизнес-ключу документа |
| `registry.documents` | `source_type` | **P2-1**: CHECK IN ('gost','gost_r','ost','rd','tu','iso','dnv','astm') |
| `registry.documents` | `document_type` | **P2-1**: CHECK IN ('normative','drawing','project','contract','reference') |
| `registry.documents` | `era` | **P2-1**: CHECK IN ('USSR','CIS','RF','CURRENT') |
| `registry.documents` | `validity_status` | **P2-1**: CHECK IN ('active','superseded','cancelled','historical','draft') |
| `registry.documents` | `jurisdiction` | **P2-1**: CHECK IN ('RF','CIS','USSR','NO','INT') |
| `registry.documents` | `processing_status` | **P2-1**: CHECK IN ('created','pending_index','indexing','indexed','partially_indexed','failed') |
| `registry.document_versions` | `file_hash_sha256` | UNIQUE — CAS-дедупликация: один хэш = одна версия файла в системе |
| `registry.document_versions` | `file_size_bytes` | **P2-7**: CHECK (file_size_bytes > 0) |
| `registry.document_versions` | `version_number` | **P2-7**: CHECK (version_number > 0) |
| `registry.document_chunks` | `chunk_count` | **P2-7**: CHECK (chunk_count >= 0) |
| `registry.classifier_registry` | `mks_oks_code` | **P2-8**: CHECK (mks_oks_code ~ '^\d{2}\.\d{3}$') — формат МКС/ОКС: две цифры, точка, три цифры |
| `registry.classifier_registry` | `okstu_code` | **P2-8**: CHECK (okstu_code ~ '^\d{4}$') — формат ОКСТУ: четыре цифры |
| `pipeline.tasks` | `processing_time_ms` | **P2-7**: CHECK (processing_time_ms >= 0) |
| `rag.document_chunks` | `embedding` | **D10, P13-1**: `VECTOR(2048)` (не `VECTOR(1536)`!) — pgvector, размерность по умолчанию для Qwen3-Embedding-4B. Параметр конфигурации `app_settings.rag.embedding_dim` (альтернативы для экспериментов: 1536, 2560, 4096). `IVFFlat` индекс для `cosine_similarity` |
| `rag.document_chunks` | `tsv` | `tsvector` — GIN-индекс для полнотекстового поиска (`ts_rank`) |

### P2-9: valid_from / valid_until / indexing_txn_id

- Поля `valid_from DATE NOT NULL DEFAULT '1000-01-01'` и `valid_until DATE NOT NULL DEFAULT '9999-12-31'` в `registry.documents` с CHECK `valid_until >= valid_from`
- Поле `indexing_txn_id UUID` в `rag.document_chunks` + partial index `WHERE indexing_txn_id IS NOT NULL`

### P2-10: Конвенция нейминга

- **timestamps**: `created_at`, `updated_at`, `started_at`, `completed_at`, `deleted_at` (везде `timestamptz`)
- **status**: поле `status` (`varchar`) с CHECK на конечный список значений
- **FK**: именование `{parent_table}_id` (исключение — `parent_id` для самоссылок)
- `uploaded_at`/`uploaded_by` → `created_at`/`created_by` (унифицировано)

---

## Сводная таблица FK-связей

| Дочерняя таблица | Поле | Родительская таблица | Поле | Тип связи |
|-----------------|------|---------------------|------|----------|
| `registry.documents` | `draft_id` | `registry.drafts` | `id` | M:1 (nullable) |
| `registry.documents` | `current_version_id` | `registry.document_versions` | `id` | M:1 (nullable) |
| `registry.documents` | `successor_doc_id` | `registry.documents` | `id` | самоссылка (nullable) |
| `registry.documents` | `predecessor_doc_id` | `registry.documents` | `id` | самоссылка (nullable) |
| `registry.document_sections` | `document_id` | `registry.documents` | `id` | M:1 |
| `registry.document_sections` | `parent_id` | `registry.document_sections` | `id` | самоссылка (nullable) |
| `registry.document_references` | `source_document_id` | `registry.documents` | `id` | M:1 |
| `registry.document_references` | `resolved_document_id` | `registry.documents` | `id` | M:1 (nullable) |
| `registry.document_versions` | `document_id` | `registry.documents` | `id` | M:1 CASCADE |
| `registry.document_history` | `document_id` | `registry.documents` | `id` | M:1 CASCADE |
| `rag.document_chunks` | `section_id` | `registry.document_sections` | `id` | M:1 |
| `rag.document_chunks` | `document_id` | `registry.documents` | `id` | M:1 |
| `registry.document_categories` | `document_id` | `registry.documents` | `id` | M:1 CASCADE |
| `registry.document_categories` | `category_id` | `registry.categories` | `id` | M:1 CASCADE |
| `pipeline.tasks` | `document_id` | `registry.documents` | `id` | M:1 (nullable) |
| `pipeline.draft_notifications` | `draft_id` | `registry.drafts` | `id` | M:1 |
| `pipeline.task_steps` | `task_id` | `pipeline.tasks` | `id` | M:1 |
| `chat.sessions` | `user_id` | `auth.users` | `id` | M:1 |
| `chat.sessions` | `project_id` | `chat.projects` | `id` | M:1 (nullable) |
| `chat.messages` | `session_id` | `chat.sessions` | `id` | M:1 CASCADE |
| `registry.documents` | `mks_oks_code` | `registry.classifier_registry` | `code` | M:1 (через generated column `mks_system`) SET NULL |
| `registry.documents` | `okstu_code` | `registry.classifier_registry` | `code` | M:1 (через generated column `okstu_system`) SET NULL |

---

## Примечания

### 0. Черновики документов (`registry.drafts`)

| Поле | Примечание |
|------|------------|
| `file_key` | Ключ в MinIO для исходного файла черновика. |
| `document_key` | Бизнес-ключ документа (SHA-256). |
| `status` | Статус черновика: `uploaded`, `previewing`, `ready_for_approve`, `approved`, `discarded`. |
| `confidence` | Оценка качества распознавания (0..1). |
| `preview_metadata` | JSONB — **весь исходный JSON ответа Converter-validator preview** (`POST /converter/preview/metadata`). Содержит `doc_code`, `title`, `mks_oks_code`, `okstu_code`, `udk_code`, `pkb_codes`, `document_type`, `year`, `era`, `validity_status`, `issuing_body`, `jurisdiction`, `source_type`, `language`, `title_hash_sha256`. Хранится целиком для истории и аудита. При approve копируется в `registry.documents.preview_snapshot`. |
| `raw_data` | JSONB с сырыми данными от Parser (schema: `raw_ocr_v4`) или Converter (`validated_v3`). |
| `error_code` / `error_message` | Код и описание ошибки при `discarded`. |
| `source_filename` | Оригинальное имя загруженного файла (до очистки для CAS). |
| `created_by` / `updated_by` | Кто создал/обновил запись. |
| `uploaded_by` | Кто загрузил файл (может отличаться от `created_by` при перезагрузке). |
| `created_at` | Дата создания черновика. |
| `updated_at` | Дата последнего обновления черновика. |

### 0a. Задачи пайплайна (`pipeline.tasks`) и этапы (`pipeline.task_steps`)

**`pipeline.tasks`** — заголовок задачи пайплайна:

| Поле | Примечание |
|------|------------|
| `draft_id` | Plain bigint (без FK) — ID черновика в `registry.drafts`. Разные БД, FK не ставится. |
| `document_id` | FK → `registry.documents.id`, nullable. Заполняется после approve. |
| `status` | Статус задачи: `active`, `completed`, `failed`. |

**`pipeline.task_steps`** — этапы задачи с промежуточными данными:

| Поле | Примечание |
|------|------------|
| `task_id` | FK → `pipeline.tasks.id`. |
| `step_name` | Название этапа: `upload`, `preview_ocr`, `preview_converter`, `full_ocr`, `full_converter`, `registry_creation`. |
| `service_name` | Какой сервис вызывался: OCR, Parser, Converter-validator, Registry. |
| `status` | Статус этапа: `pending`, `running`, `completed`, `failed`. |
| `input_data` | JSONB — входные данные для этапа (JSON-контейнер). |
| `output_data` | JSONB — выходные данные от сервиса (промежуточный JSON-контейнер). |
| `error_code` / `error_message` | Код и описание ошибки при `failed`. |
| `started_at` / `completed_at` | Время начала и завершения этапа. |

### 0б. Уведомления черновика (`pipeline.draft_notifications`)

**`pipeline.draft_notifications`** — замечания для оператора (P12-3 / P3-5):

| Поле | Примечание |
|------|------------|
| `draft_id` | FK → `registry.drafts.id`. Связь с черновиком. |
| `source` | Какой сервис создал уведомление: `parser`, `ocr`, `converter`, `registry`. |
| `code` | Код уведомления. Security: `EMBEDDED_JS`, `EMBEDDED_FILE`, ... Quality: `LOW_CONFIDENCE_PAGE`, `TABLE_CORRUPTED`, ... |
| `severity` | `info`, `warning`, `error`, `critical`. |
| `category` | `security` или `quality`. |
| `message` | Человекочитаемое описание. |
| `location` | JSONB — `{page, block}`. |
| `suggested_action` | `reprocess`, `manual_edit`, `review`, `ignore`. |

### 1. Реестр документов (`registry.documents`)

| Поле | Примечание |
|------|------------|
| `source_type` | **P2-1**: enum `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `OTHER` |
| `document_type` | **P2-1**: enum `normative`, `technical`, `drawing`, `specification`, `archival_scan`. Не путать с `source_type` |
| `group` | **D-32/D-33**: **удалено** из модели (см. P5 — A36). Ранее использовалось для группы проекта (например, `ПО4`). Заменено на `registry_document_classifier_links` (M:N) |
| `era` | **P2-1**: enum `USSR`, `CIS`, `RF`, `CURRENT` |
| `validity_status` | **P2-1**: enum `active`, `superseded`, `expired`, `cancelled`, `historical`, `draft` (юридический статус, **не путать** с `valid_from/valid_until`) |
| `jurisdiction` | Юрисдикция: `RU`, `EU`, `US`, `NO`, `INTL` |
| `udk_code` | **D-51**: переименовано из `udc` для консистентности с `mks_oks_code` / `okstu_code`. Код УДК (универсальная десятичная классификация). nullable |
| `valid_from` | **P12-5**: дата начала действия документа. NOT NULL, default `dateMin = '1000-01-01'::date` (для документов с неопределённой датой начала). См. конвенцию в `glossary.md` |
| `valid_until` | **P12-5**: дата окончания действия документа. NOT NULL, default `dateMax = '9999-12-31'::date` (для бессрочных документов). См. конвенцию в `glossary.md` |
| `file_hash_sha256` | **P2-2**: `CHAR(64)` (а не `text`). Хэш бинарного файла (вычисляется при загрузке) |
| `title_hash_sha256` | Хэш 6-польной формулы: `SHA-256(era | source_type | mks_oks_code | okstu_code | doc_code | normalized_title)` (вычисляется в Converter). Алгоритм нормализации и нормализация полей — см. `specifications/normalizer_specification.md` |
| `preview_snapshot` | JSONB — исходный JSON ответа Converter-validator preview, скопированный из `registry.drafts.preview_metadata` при approve. Хранится для истории и аудита. Не используется в поиске — только для просмотра исходных метаданных. |
| `processing_status` | **P2-1, P1-16**: FSM статус конвейера (не путать с `validity_status` — юридическим статусом документа). Возможные значения: `created`, `pending_index`, `indexing`, `indexed`, `partially_indexed`, `failed`. **P1-16**: `partially_indexed` — промежуточный статус при частичной индексации (часть чанков в БД, часть пропущена). Исключён из RAG Search. Статусы черновика (`uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation`, `approved`, `discarded` — см. P1-20) хранятся в `registry.drafts.status`, не в `registry.documents`. |
| `chunk_count` | **P2-7**: `CHECK (chunk_count IS NULL OR chunk_count >= 0)`. Обновляется после индексации. Если `chunk_count_actual < chunk_count_expected` — переход в `partially_indexed` (P1-16) или `failed` (P1-17) |

### 2. Разделы документов (`registry.document_sections`)

| Поле | Примечание |
|------|------------|
| `id` | Назначается Registry (sequence) |
| `parent_id` | Ссылка на родительскую секцию (`registry.document_sections.id`) |
| `clause` | Номер раздела (например, `1`, `6.1`, `6.1.table1`) |
| `level` | Уровень вложенности (`1`, `2`, `3`, ...) |
| `path` | Ltree-путь в иерархии |
| `bbox` | Координаты на странице: `[x1, y1, x2, y2]` |
| `type` | Тип секции: `text`, `textBlock`, `headerFooter`, `table`, `list`, `image`, `formula` — CHECK (type IN ('text','textBlock','headerFooter','table','list','image','formula')) |
| `content` | JSONB с разнородной структурой, зависящей от `type`:
  - `text` → `{ text, amendments }`
  - `textBlock` → `{ block[] }`
  - `headerFooter` → `{ text }`
  - `table` → `{ caption, columns, rows, footnotes, amendments, image_key }`
  - `list` → `{ numbering_style, items[] }`
  - `image` → `{ caption, image_key, description }`
  - `formula` → `{ latex, meaning, image_key, parameters }` |

### 3. Ссылки между документами (`registry.document_references`)

| Поле | Примечание |
|------|------------|
| `source_document_id` | Документ-источник |
| `target_doc_code` | Целевой ГОСТ/ТУ |
| `reference_type` | Тип ссылки: `single`, `range` |
| `context` | Контекст ссылки |
| `current_status` | Статус целевого документа: `active`, `superseded` |

### 4. Версии документов (`registry.document_versions`)

| Поле | Примечание |
|------|------------|
| `revision` | Обозначение редакции (напр. «Изм. 1», «Изд. 2»), извлекается при обработке документа |
| `format_code` | Формат файла: `pdf`, `doc`, `tiff`, ... |
| `file_path` | CAS-путь в MinIO (см. `specifications/cas_storage_specification.md`). Ранее называлось `file_key` |
| `source_filename` | Оригинальное имя загруженного файла (до очистки для CAS) |
| `created_by` | **P2-10 (D3)**: переименовано из `uploaded_by`. Идентификатор пользователя или сервиса, создавшего версию |

> **В модели данных** поле называется `file_path` (CAS-путь). В API может использоваться как `file_key` для обратной совместимости.

> **Примечание**: `revision` (обозначение редакции, напр. «Изм. 1», «Изд. 2») извлекается при обработке документа.

**Связь с `registry.documents`:** поле `current_version_id` в `registry.documents` (FK → `registry.document_versions.id`, nullable) указывает на текущую активную версию документа. Если не задано — текущая версия определяется как последняя по `uploaded_at`.

### 5. История обработки (`registry.document_history`)

| Поле | Примечание |
|------|------------|
| `event_type` | Тип события: `created`, `preview_failed`, `decided`, `parsed`, `validated`, `approved`, `indexed`, `failed` |
| `document_snapshot` | Слепок enriched JSON на момент события |

### 6. Чанки документов (`rag.document_chunks`)

| Поле | Примечание |
|------|------------|
| `section_id` | `registry.document_sections.id` |
| `chunk_index` | Порядковый номер чанка в секции |
| `content` | Текст чанка: plain text для `section`, Markdown для `table` |
| `embedding` | **D10, P13-1**: `VECTOR(2048)` (не `VECTOR(1536)`!) — pgvector, размерность по умолчанию для Qwen3-Embedding-4B. `IVFFlat` индекс для `cosine_similarity` |
| `tsv` | Полнотекстовый индекс (`to_tsvector('russian', content)`), GIN-индекс |
| `strategy` | Стратегия чанкинга: **`semantic_1024`** (не `semantic_512`!) — **P13-1**: новый дефолт 1024 токена. Альтернативы: `semantic_512`, `semantic_2048`, `fixed_256`, `fixed_512` |

Связь с секциями: чанк всегда привязан к конкретной секции документа. Одна секция может порождать несколько чанков (для `type=section` с разбивкой на ≤512 токенов) или один чанк (для `type=table/image/formula`).

> **Денормализация**: Поле `document_id` в `document_chunks` дублирует `document_sections.document_id` для ускорения запросов «все чанки документа». Синхронизация обеспечивается на уровне приложения (RAG Builder проставляет `document_id` при вставке чанка).

### 7. Проекты (`chat.projects`)

| Поле | Примечание |
|------|------------|
| `code` | Уникальный код проекта (например, `21900M2`, `Arc4`) |
| `name` | Человекочитаемое название проекта |
| `description` | Описание/примечания |
| `status` | Статус: `active`, `archived`, `draft` |

### 8. Сессии чата (`chat.sessions`)

| Поле | Примечание |
|------|------------|
| `project_id` | FK → `chat.projects.id`. Сессия привязана к судостроительному проекту. Может быть `NULL` для общих вопросов. |
| `user_id` | FK → пользователь (Auth Service) |
| `document_ids` | Массив ID документов (bigint), ограничивающих область поиска в сессии |
| `options` | JSONB с дополнительными параметрами сессии |

### 9. Сообщения чата (`chat.messages`)

| Поле | Примечание |
|------|------------|
| `role` | Роль отправителя: `user`, `assistant` |
| `status` | FSM статус сообщения: `pending`, `enriching`, `searching`, `generating`, `enriching_citations`, `answered`, `failed`. CHECK (status IN ('pending','enriching','searching','generating','enriching_citations','answered','failed')). Статус `idle` — виртуальный, не хранится в БД. |
| `sources` | Массив источников: `[{chunk_id, section_id, document_id, excerpt, score, confidence}]` |

Таблицы `chat.sessions` и `chat.messages` не относятся к реестру документов, выделены в отдельную схему `chat`.

### 10. Пользователи (`auth.users`)

| Поле | Примечание |
|------|------------|
| `email` | Уникальный email пользователя |
| `full_name` | Полное имя |
| `password_hash` | Хэш пароля (bcrypt, cost factor ≥ 12). Не логируется, не возвращается в API |
| `roles` | JSONB-массив ролей: `["engineer"]`, `["knowledge_admin"]`, `["system_admin"]` |
| `position` | Должность пользователя |
| `is_active` | Флаг активности. При `false` пользователь не может аутентифицироваться |
| `last_login_at` | Время последнего входа |

> **Связь:** `chat.sessions.user_id` → `auth.users.id` (FK).

### 11. Терминология (`registry.terminology`)

| Поле | Примечание |
|------|------------|
| `raw_term` | Исходный термин (как встретился в документе) |
| `standard_term` | Эталонное написание термина |
| `normalized_value` | Приведённая форма для поиска (нижний регистр) |
| `term_type` | Тип термина: `acronym`, `foreign_term`, `standard_code`, `avatar`, `symbol` |
| `is_case_sensitive` | Чувствительность к регистру |
| `definition` | Определение/описание термина |
| `synonyms` | JSONB-массив синонимов |
| `related_docs` | Связанные документы (обозначения) |
| `scope` | Области применения |
| `is_blocked` | Блокировка устаревшего термина |

### 12. Общее

- **`document_id` (bigint)** назначается только в Registry при создании документа. До этого — `draft_id` (bigint) и `task_id` (bigint) используются всеми начальными сервисами (OCR/Parser, Converter-Validator).
- **`draft_id` (bigint)** назначается Registry при создании записи черновика. Orchestrator хранит маппинг `draft_id → task_id → document_id`.
- **`registry.drafts` и `pipeline.tasks`** не связаны FK (разные БД), логическая связь по `draft_id`.
- **`rag.document_chunks.content`** — унифицированное хранение. `content` — строка (plain text или Markdown). `tsv` строится через `to_tsvector('russian', content)` при вставке.

### 13. Категории документов (`registry.categories`, `registry.document_categories`)

Пользовательские категории для группировки документов в разделы «Базы знаний». Many-to-many: один документ может относиться к нескольким категориям, одна категория — к нескольким документам.

**`registry.categories`** — справочник категорий:

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | bigint | PK, sequence |
| `name` | varchar(255) | NOT NULL, UNIQUE |
| `description` | text | nullable |
| `color` | varchar(7) | nullable, hex-код (#RRGGBB) |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

**`registry.document_categories`** — связь документа с категориями:

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `document_id` | bigint | PK (составной), FK → `registry.documents.id` ON DELETE CASCADE |
| `category_id` | bigint | PK (составной), FK → `registry.categories.id` ON DELETE CASCADE |

> **Каскадное удаление:** при удалении категории или документа связанные записи в `document_categories` удаляются автоматически.
