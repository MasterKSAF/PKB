# Схема базы данных (объединённая)

> Сводная ER-диаграмма, объединяющая принятую схему `docs/` с дополнениями из проекта Purgatory (v2.3 + nsi).
> Исправленный синтаксис Mermaid ER без спецсимволов в типах.

---

## 0. Принятая схема `docs/` (core)

```mermaid
erDiagram
    nsi_documents {
        uuid id PK
        text doc_code
        text title
        varchar validity_status
    }

    nsi_document_sections {
        uuid id PK
        uuid document_id FK
        uuid parent_id FK
        text clause
        text title
        int level
        ltree path
        int page
        text bbox
        varchar type
        jsonb content
    }

    nsi_chunks {
        uuid id PK
        uuid section_id FK
        int chunk_index
        text content
        text embedding "pgvector"
        text tsv "tsvector"
        text strategy
        int page
        text bbox
        float confidence
        text tenant_id
        text deleted_at
    }

    nsi_cross_references {
        uuid id PK
        uuid source_document_id FK
        text target_doc_code
        varchar reference_type
        text context
        text current_status
        text replaced_by
        date replacement_date
        bool is_resolved
        uuid resolved_document_id FK
    }

    nsi_document_history {
        uuid id PK
        uuid document_id FK
        text event_type
        timestamp event_at
        text event_by
        text comment
        jsonb document_snapshot
    }

    nsi_documents ||--o{ nsi_document_sections : has
    nsi_document_sections ||--o{ nsi_document_sections : parent
    nsi_document_sections ||--o{ nsi_chunks : contains
    nsi_documents ||--o{ nsi_cross_references : source
    nsi_documents ||--o{ nsi_cross_references : resolved
    nsi_documents ||--o{ nsi_document_history : has
```

### UNIQUE-ограничения

- `nsi_documents.title` — бизнес-ключ документа (через title_hash_sha256)
- `nsi_cross_references (source_document_id, target_doc_code, reference_type)` — защита от дублей связей

---

## 1. Слой staging: `purgatory.*` (c дополнениями)

```mermaid
erDiagram
    purgatory_documents {
        uuid id PK
        text classifier_code
        text doc_code
        text source_type
        text title
        text title_hash_sha256 "UK"
        varchar status
        varchar era
        varchar validity_status
        text jurisdiction
        text issuing_body
        text industry_code
        uuid enterprise_id
        text mks_oks_code
        text okstu_code
        jsonb classification_status
        uuid successor_doc_id FK "self-ref"
        uuid predecessor_doc_id FK "self-ref"
        uuid chunk_container_id FK
        jsonb metadata
        text created_by
        text updated_by
        timestamp created_at
        timestamp updated_at
        varchar mks_system "GENERATED MKS"
        varchar okstu_system "GENERATED OKSTU"
        text user_id
        int total_versions
        int chunk_count
        int order
    }

    purgatory_document_versions {
        uuid id PK
        uuid document_id FK
        text source_filename
        text format_code FK
        text file_path "CAS"
        bigint size_bytes
        text content_hash_sha256 "UK"
        int version_number
        text format_label
        timestamp uploaded_at
        text uploaded_by
    }

    purgatory_chunk_containers {
        uuid id PK
        uuid document_id FK "UK: one per document"
        text version_hash
        jsonb json_payload
        varchar validation_status
        jsonb validation_errors
        timestamp created_at
    }

    purgatory_status_history {
        uuid id PK
        uuid document_id FK
        varchar old_status
        varchar new_status
        jsonb comment
        text changed_by
        timestamp changed_at
    }

    purgatory_classifier_registry {
        varchar classifier_system PK
        text code PK
        text parent_code FK
        text full_name
        text status
        date effective_date
        text replaced_by
        timestamp created_at
    }

    purgatory_classifier_pending {
        uuid id PK
        text system "UK: UNIQUE(system, code)"
        text code "UK: UNIQUE(system, code)"
        uuid found_in_document_id FK
        uuid source_version_id FK
        text status
        text admin_comment
        text found_in_document_title
        text suggested_parent_code
        text suggested_parent_name
        timestamp created_at
    }

    purgatory_format_registry {
        text code PK
        text mime_type
        text parser_plugin
        bool is_active
        timestamp created_at
    }

    purgatory_terminology_registry {
        uuid id PK
        text raw_term "UK"
        text standard_term
        text normalized_value
        text term_type
        bool is_case_sensitive
        text definition
        jsonb synonyms
        jsonb related_docs
        jsonb scope
        bool is_blocked
        timestamp created_at
        timestamp updated_at
    }

    purgatory_documents ||--o{ purgatory_document_versions : has
    purgatory_documents ||--o| purgatory_chunk_containers : contains
    purgatory_documents ||--o{ purgatory_status_history : logs
    purgatory_documents ||--o{ purgatory_classifier_pending : "pending codes"
    purgatory_document_versions ||--|| purgatory_format_registry : "formatted as"
    purgatory_classifier_registry ||--o{ purgatory_classifier_registry : parent
    purgatory_classifier_registry ||--o{ purgatory_documents : classifies
```

---

## 2. Слой Knowledge Base: `nsi.*` (c дополнениями)

```mermaid
erDiagram
    nsi_document_sections {
        uuid id PK
        uuid document_id FK
        uuid parent_id FK "self-ref"
        text clause
        text title
        int level
        ltree path
        int page
        text bbox
        varchar type
        jsonb content
        timestamp created_at
    }

    nsi_chunks {
        uuid id PK
        uuid document_id FK
        uuid section_id FK
        int chunk_index
        text content
        text embedding "pgvector"
        text tsv "tsvector"
        text clause
        text strategy
        int page
        text bbox
        float confidence
        text tenant_id
        timestamp deleted_at
        timestamp created_at
    }

    nsi_images {
        uuid id PK
        uuid document_id FK
        text figure_id
        text title
        text caption
        text description
        text file_path
        text file_type
        jsonb metadata
        int page
        text bbox
        timestamp created_at
    }

    nsi_extracted_tables {
        uuid id PK
        uuid document_id FK
        uuid section_id FK
        text table_id
        text caption
        int page
        text bbox
        text unit
        jsonb headers
        jsonb rows
        jsonb footnotes
        text image_s3_path
        timestamp created_at
    }

    nsi_formulas {
        uuid id PK
        uuid document_id FK
        text formula_id
        text latex
        text image_s3_path
        text meaning
        text context_clause
        int page
        text bbox
        timestamp created_at
    }

    nsi_formula_parameters {
        uuid id PK
        uuid formula_id FK
        text symbol
        text description
        text unit
    }

    nsi_cross_references {
        uuid id PK
        uuid source_document_id FK
        text target_doc_code
        varchar reference_type
        text context
        text current_status
        text replaced_by
        date replacement_date
        bool is_resolved
        uuid resolved_document_id FK
        timestamp created_at
    }

    nsi_promotion_history {
        uuid id PK
        uuid document_id FK
        uuid source_version_id
        uuid source_container_id
        timestamp promoted_at
        text promoted_by
        text comment
    }

    nsi_document_history {
        uuid id PK
        uuid document_id FK
        text event_type
        timestamp event_at
        text event_by
        text comment
        jsonb document_snapshot
    }

    purgatory_documents ||--o{ nsi_document_sections : "has sections"
    nsi_document_sections ||--o{ nsi_document_sections : parent
    nsi_document_sections ||--o{ nsi_chunks : contains
    purgatory_documents ||--o{ nsi_chunks : "has chunks"
    purgatory_documents ||--o{ nsi_images : "has images"
    purgatory_documents ||--o{ nsi_extracted_tables : "has tables"
    purgatory_documents ||--o{ nsi_formulas : "has formulas"
    nsi_formulas ||--o{ nsi_formula_parameters : parameters
    purgatory_documents ||--o{ nsi_cross_references : "source of"
    purgatory_documents ||--o{ nsi_cross_references : "resolved target"
    purgatory_documents ||--o{ nsi_promotion_history : promoted
    purgatory_documents ||--o{ nsi_document_history : events
```

---

## 3. Легенда

| Обозначение | Значение |
|---|---|
| `PK` | Primary Key |
| `FK` | Foreign Key |
| `UK` | Unique Constraint |
| `ENUM` | Перечисление (CREATE TYPE ... AS ENUM) |
| `ltree` | Тип ltree (расширение PostgreSQL) |
| `pgvector` | Тип vector (расширение pgvector) |
| `tsvector` | Полнотекстовый индекс PostgreSQL |
| `jsonb` | Двоичный JSON |
| `GENERATED` | Вычисляемая колонка (GENERATED ALWAYS AS) |
| `CAS` | Content-Addressable Storage (путь = хэш) |

---

## 4. Примечания по схеме

### 4.1. Два варианта history

Схема содержит **обе** таблицы истории:

- **`purgatory_status_history`** — журнал FSM-переходов (триггер на `purgatory_documents.status`)
- **`nsi_promotion_history`** / **`nsi_document_history`** — два альтернативных подхода к логированию промоушенов (специализированный vs event-based)

Требуется согласование: оставить обе, или выбрать одну.

### 4.2. Две связи chunks→document

В схеме показаны оба варианта:

- Прямая: `nsi_chunks.document_id → purgatory_documents.id` (Purgatory-подход)
- Через секцию: `nsi_chunks.section_id → nsi_document_sections.id → nsi_document_sections.document_id` (docs-подход)

Требуется согласование: можно оставить оба (прямой для скорости, через section_id для нормализации), или выбрать один.

### 4.3. Images и Tables

Показаны как отдельные таблицы (`nsi_images`, `nsi_extracted_tables`) по Purgatory-подходу. Альтернатива `docs/` — хранение через `nsi_document_sections` с `type='image'`/`'table'` и `content JSONB`.

### 4.4. ENUM vs TEXT

Все поля с пометкой `ENUM` в легенде — строгие перечисления. В разделах 1 и 2 используется `varchar` без уточнения ENUM. Выбор подхода требует согласования для каждого поля.

### 4.5. bbox: JSONB vs TEXT

Purgatory использует `JSONB` для bbox (гибкость); `docs/` использует `TEXT` (строка координат). В схеме указан `text bbox`, но может быть заменён на `jsonb`.

### 4.6. UNIQUE-ограничения

Отмечены в описаниях полей пометкой `UK`. Ключевые:
- `purgatory_documents.title_hash_sha256` — бизнес-ключ документа
- `purgatory_document_versions.content_hash_sha256` — CAS-ключ файла
- `purgatory_terminology_registry.raw_term` — уникальность термина
- `purgatory_chunk_containers.document_id` — 1 документ = 1 контейнер
- `purgatory_classifier_pending (system, code)` — защита от дублей в карантине
- `nsi_cross_references (source_document_id, target_doc_code, reference_type)` — защита от дублей связей
