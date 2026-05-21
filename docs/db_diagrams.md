# Схема базы данных (объединённая)

> Сводная ER-диаграмма, объединяющая принятую схему `docs/` с дополнениями из проекта Purgatory (v2.3 + nsi).

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
        jsonb bbox
        varchar type
        jsonb content
        timestamptz created_at
    }

    nsi_chunks {
        uuid id PK
        uuid section_id FK
        uuid document_id FK
        int chunk_index
        text content
        text embedding "pgvector"
        text tsv "tsvector"
        text strategy
        int page
        jsonb bbox
        float confidence
        text tenant_id
        timestamptz deleted_at
        timestamptz created_at
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
        timestamptz created_at
    }

    nsi_document_history {
        uuid id PK
        uuid document_id FK
        text event_type
        timestamp event_at
        text event_by
        text source_task_id
        text comment
        jsonb document_snapshot
    }

    nsi_documents ||--o{ nsi_document_sections : has
    nsi_document_sections ||--o{ nsi_document_sections : parent
    nsi_document_sections ||--o{ nsi_chunks : contains
    nsi_documents ||--o{ nsi_cross_references : source
    nsi_documents ||--o{ nsi_cross_references : resolved
    nsi_documents ||--o{ nsi_chunks : has
    nsi_documents ||--o{ nsi_document_history : has
```

### UNIQUE-ограничения

- `nsi_documents.title` — бизнес-ключ документа (через title_hash_sha256)
- `nsi_cross_references (source_document_id, target_doc_code, reference_type)` — защита от дублей связей

### CHECK-ограничения

- `nsi_document_sections.type IN ('section', 'table', 'image', 'formula')`
