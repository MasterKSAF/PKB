# Схема базы данных (объединённая)

> Сводная ER-диаграмма, объединяющая принятую схему `docs/` с дополнениями из проекта Purgatory (v2.3 + nsi).

---

## 0. Принятая схема `docs/` (core)

```mermaid
erDiagram
    registry.documents {
        uuid id PK
        text doc_code
        text title
        varchar validity_status
        uuid successor_doc_id FK
        uuid predecessor_doc_id FK
        varchar era
        varchar group
        text title_hash_sha256
    }

    registry.document_sections {
        bigint id PK
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

    rag.chunks {
        uuid id PK
        bigint section_id FK
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

    registry.document_references {
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

    registry.document_history {
        uuid id PK
        uuid document_id FK
        text event_type
        timestamp event_at
        text event_by
        text source_task_id
        text comment
        jsonb document_snapshot
    }

    registry.documents ||--o{ registry.document_sections : has
    registry.document_sections ||--o{ registry.document_sections : parent
    registry.document_sections ||--o{ rag.chunks : contains
    registry.documents ||--o{ registry.document_references : source
    registry.documents ||--o{ registry.document_references : resolved
    registry.documents ||--o{ rag.chunks : has
    registry.documents ||--o{ registry.document_history : has
```

### UNIQUE-ограничения

- `registry.documents.title` — бизнес-ключ документа (через title_hash_sha256)
- `registry.document_references (source_document_id, target_doc_code, reference_type)` — защита от дублей связей

### CHECK-ограничения

- `registry.document_sections.type IN ('section', 'table', 'image', 'formula')`

---

### Примечания

1. **`chunk_container_id`** — staging-only, принадлежит схеме `purgatory`.

2. **Preview-данные** не хранятся в БД. Они живут исключительно в журнале пайплайна Orchestrator (временные артефакты фазы Preview).
3. **`registry.document_sections`** — это **секции** документа (разделы, подразделы, пункты), создаваемые сервисом Registry на этапе сегментации. Не путать с чанками!
4. **`rag.chunks`** — это **чанки**, формируемые сервисом RAG Builder на основе секций. Поле `section_id` ссылается на `registry.document_sections.id`. Одна секция может порождать несколько чанков.
