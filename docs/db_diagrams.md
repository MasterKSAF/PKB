# Схема базы данных (объединённая)

> Сводная ER-диаграмма.

---

## ER-диаграмма

```mermaid
erDiagram
    registry.documents {
        uuid id PK
        text doc_code
        text title
        text normalized_title
        varchar source_type "GOST, OST, TU, ISO..."
        varchar group "ПО4"
        text mks_oks_code
        text okstu_code
        text udc
        varchar era "USSR, CIS, RF, CURRENT"
        varchar validity_status "active, superseded, expired"
        varchar jurisdiction "RU, EU, US, NO, INTL"
        text issuing_body
        date adoption_date
        date effective_from
        text replaces
        text status_note
        text content_hash_sha256 "хэш бинарного файла (вычисляется при загрузке)"
        text title_hash_sha256 "хэш doc_code+title+era (вычисляется в Converter)"
        text file_hash_sha256 "хэш файла (дублирует content_hash)"
        bigint file_size_bytes
        varchar processing_status "FSM: draft, uploaded, previewing, awaiting_decision, parsing, validation, ready_for_promotion, review_required, approved, registry, pending_index, indexed, duplicate, new_version, archived, failed"
        int chunk_count "обновляется RAG Builder после индексации"
        uuid successor_doc_id FK
        uuid predecessor_doc_id FK
        text created_by
        text updated_by
        timestamptz created_at
        timestamptz updated_at
    }

    registry.document_sections {
        bigint id PK "назначается Registry (sequence)"
        uuid document_id FK
        bigint parent_id FK "ссылка на родительскую секцию (id)"
        text clause "1, 6.1, 6.1.table1"
        text title
        int level "уровень вложенности (1, 2, 3...)"
        ltree path "ltree-путь в иерархии"
        int page
        jsonb bbox "[x1,y1,x2,y2]"
        varchar type "section, table, image, formula"
        jsonb content "разнородный: свои поля для каждого type"
        timestamptz created_at
    }

    registry.document_references {
        uuid id PK
        uuid source_document_id FK "документ-источник"
        text target_doc_code "целевой ГОСТ/ТУ"
        varchar reference_type "single, range"
        text context "контекст ссылки"
        text current_status "active, superseded"
        text replaced_by
        date replacement_date
        boolean is_resolved
        uuid resolved_document_id FK
        timestamptz created_at
    }

    registry.document_versions {
        uuid id PK
        uuid document_id FK
        int version_number
        text content_hash_sha256
        text file_hash_sha256
        bigint file_size_bytes
        text format_code "pdf, doc, tiff..."
        text format_label
        text file_key "ссылка на MinIO"
        text uploaded_by
        timestamptz uploaded_at
    }

    registry.document_history {
        uuid id PK
        uuid document_id FK
        text event_type "created, preview_failed, decided, parsed, validated, promoted, indexed, failed"
        text old_status
        text new_status
        text comment
        text changed_by
        jsonb document_snapshot "слепок enriched JSON на момент события"
        timestamptz event_at
    }

    rag.document_chunks {
        bigint id PK
        bigint section_id FK "registry.document_sections.id"
        uuid document_id FK
        int chunk_index "порядковый номер чанка в секции"
        text content "текст чанка (plain text для section, Markdown для table)"
        vector embedding "dim=1536, pgvector"
        tsvector tsv "полнотекстовый индекс (to_tsvector)"
        varchar strategy "semantic_512, fixed_256"
        int page
        jsonb bbox
        float confidence
        timestamptz created_at
    }

    chat.sessions {
        uuid id PK
        text title
        uuid user_id FK
        uuid[] document_ids
        jsonb options
        int message_count
        timestamptz created_at
        timestamptz updated_at
    }

    chat.messages {
        bigint id PK
        uuid session_id FK
        text role "user, assistant"
        text content
        text status "FSM: idle, pending, enriching, searching, generating, enriching_citations, answered, failed"
        jsonb sources "[{chunk_id, section_id, document_id, excerpt, score}]"
        jsonb attachments
        jsonb options
        jsonb feedback
        int processing_time_ms
        timestamptz created_at
    }

    registry.documents ||--o{ registry.document_sections : has
    registry.document_sections ||--o{ registry.document_sections : parent_of
    registry.document_sections ||--o{ rag.document_chunks : contains
    registry.documents ||--o{ registry.document_references : source_of
    registry.documents ||--o{ registry.document_history : audited_by
    registry.documents ||--o{ registry.document_versions : versioned_by
    registry.documents ||--o{ rag.document_chunks : chunked_by
    chat.sessions ||--o{ chat.messages : has_messages
```

---

## Ключевые условия и ограничения

| Таблица | Поле | Условие |
|---------|------|---------|
| `registry.document_sections` | `type` | `CHECK (type IN ('section','table','image','formula'))` |
| `registry.documents` | `content_hash_sha256` | Для быстрого дубликат-детекта (`WHERE content_hash_sha256 = ? AND file_size_bytes = ?`) |
| `registry.documents` | `title_hash_sha256` | Индекс для полнотекстового поиска дубликатов по `doc_code + title + era` |
| `rag.document_chunks` | `embedding` | `VECTOR(1536)` — pgvector, `IVFFlat` индекс для `cosine_similarity` |
| `rag.document_chunks` | `tsv` | `tsvector` — GIN-индекс для полнотекстового поиска (`ts_rank`) |

---

## Примечания

1. **`document_id` (UUID)** назначается только в Registry при создании документа. До этого — `task_id` (UUID), который используется всеми начальными сервисами (OCR/Parser, Converter-Validator).

2. **`registry.document_sections.content`** — JSONB с разнородной структурой, зависящей от `type`:
   - `section` → `{ text, amendments }`
   - `table` → `{ caption, columns, rows, footnotes, amendments, image_key }`
   - `image` → `{ caption, image_key, description }`
   - `formula` → `{ latex, meaning, image_key, parameters }`

3. **`rag.document_chunks`** — унифицированное хранение. `content` — строка (plain text или Markdown). `tsv` строится через `to_tsvector('russian', content)` при вставке.

4. **`registry.documents.processing_status`** — FSM-статус конвейера (не путать с `validity_status` — юридическим статусом документа).

5. **Связь `rag.document_chunks → registry.document_sections`**: чанк всегда привязан к конкретной секции документа. Одна секция может порождать несколько чанков (для `type=section` с разбивкой на ≤512 токенов) или один чанк (для `type=table/image/formula`).

6. **Таблицы `chat.sessions` и `chat.messages`** не относятся к реестру документов, выделены в отдельную схему `chat`.
