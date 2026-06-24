# RAG Search MVP — SPD Notes

> This document describes the SPD RAG Search MVP contract and implementation notes.
>
> RAG Search is logically separate from RAG Builder.
> RAG Builder prepares `document_sections`, `chunks`, embeddings, `content_tsv`, `path_ltree`, citation metadata and source objects.
> RAG Search reads the prepared index and performs retrieval.
>
> This README describes the current `backend/rag_search_service_spd` service.
> RAG Search is a read-only retrieval service over the index prepared by RAG Builder.

---

## 1. Назначение сервиса

RAG Search — read-only сервис поиска по уже построенному индексу.

Он не парсит документы, не строит chunks, не пересобирает индекс и не генерирует LLM-ответы.

```text
SearchRequest
    ↓
SearchService
    ↓
PostgresSearchRepository
    ↓
nsi.chunks
nsi.document_sections
    ↓
SearchResponse with citation metadata
```

RAG Builder отвечает за запись индекса.
RAG Search отвечает за чтение индекса.

---

## 2. Источник данных

RAG Search читает таблицы, подготовленные RAG Builder:

```text
nsi.document_sections
nsi.chunks
nsi.cross_references
nsi.images
nsi.extracted_tables
nsi.formulas
```

Основные поля для retrieval:

```text
nsi.chunks.content
nsi.chunks.embedding
nsi.chunks.content_tsv
nsi.document_sections.path
nsi.document_sections.path_ltree
```

Основные поля для цитирования:

```text
document_id
document_version_id
document_section_id
section_id
clause
path
page
bbox
chunk_index
chunk_type
content
```

---

## 3. API contract

### POST /api/v1/rag/search

Main contract endpoint for RAG Search SPD.

### POST /search

Legacy/local endpoint.

### POST /rag/search

Compatibility endpoint used by earlier local integrations.

All three endpoints use the same `SearchRequest` and return the same `SearchResponse`.

Current endpoint policy:

```text
POST /api/v1/rag/search  # preferred API v1 contract
POST /rag/search         # compatibility alias
POST /search             # legacy/local alias
```

---

## 4. SearchRequest

```json
{
  "query": "допуск соосности",
  "top_k": 5,
  "search_type": "hybrid",
  "expand_context": false,
  "filters": null
}
```

| field | type | description |
|---|---|---|
| `query` | string | поисковый запрос |
| `top_k` | integer | количество результатов |
| `search_type` | string | `dense`, `sparse` или `hybrid` |
| `expand_context` | boolean | добавить parent/direct children context |
| `filters` | object/null | будущие фильтры по документу, версии, типу и т.п. |

---

## 5. Search modes

| search_type | Description |
|---|---|
| `dense` | vector search by `nsi.chunks.embedding` |
| `sparse` | PostgreSQL full-text search by `nsi.chunks.content_tsv` with `ts_rank_cd` |
| `hybrid` | RRF fusion of sparse and dense results, duplicates removed |

### dense

Dense search:

1. получает embedding для `query`;
2. ищет ближайшие chunks по `nsi.chunks.embedding`;
3. возвращает chunks с citation metadata.

Production embeddings должны идти через внешний OpenAI-compatible API или другой согласованный embedding endpoint.

### sparse

Sparse search использует PostgreSQL full-text search:

```sql
to_tsquery('russian', ...)
```

и ранжирование:

```sql
ts_rank_cd(content_tsv, query)
```

### hybrid

Hybrid search объединяет sparse и dense результаты через Reciprocal Rank Fusion.

MVP параметры:

```text
rrf_k = 60
```

---

## 6. Context expansion

Если `expand_context=true`, каждый result может получить `context` array.

Context expansion использует `nsi.document_sections.path_ltree`.

MVP semantics:

```text
result section
    ├── parent section
    └── direct child sections
        ├── text
        ├── table
        ├── image
        └── formula
```

Context deduplication:

- context items already present in main `results` are removed;
- deduplication key: `document_section_id`.

---

## 7. Response example

```json
{
  "query": "допуск соосности",
  "search_type_used": "hybrid",
  "results": [
    {
      "chunk_id": 151,
      "document_id": 420000,
      "document_version_id": 420001,
      "document_section_id": 151,
      "section_id": 3,
      "clause": "6.1",
      "path": "6/6.1",
      "page": 2,
      "bbox": [0.12, 0.18, 0.88, 0.26],
      "chunk_index": 0,
      "chunk_type": "text",
      "content": "Допуск соосности оси отверстия...",
      "score": 0.0317,
      "distance": null,
      "context": []
    }
  ],
  "total_found": 1,
  "processing_time_ms": 42,
  "embedding_tokens": 12,
  "embedding_cost_usd": 0.00000024,
  "context_expanded": false
}
```

---

## 8. Sparse search acceleration

RAG Builder prepares `content_tsv` during indexing.

Expected DB fields/indexes:

```text
nsi.chunks.content_tsv
idx_chunks_content_tsv
USING GIN (content_tsv)
```

The value is filled from chunk content:

```sql
to_tsvector('russian'::regconfig, content)
```

---

## 9. Embeddings

Dense and hybrid search need query embeddings.

Supported deployment options:

```text
stub               — tests/local technical mode
openai             — official OpenAI API
openai_compatible  — OpenAI-compatible endpoint
infinity           — local Infinity-compatible endpoint
external           — external OpenAI-compatible API
```

Given current server constraints, production search should not require a local GPU. Dense query embeddings should use an external API or another backend-provided embedding endpoint.

---

## 10. MVP limitations

- `hybrid` uses Reciprocal Rank Fusion with `k=60`.
- `sparse` uses PostgreSQL full-text ranking via `ts_rank_cd`; a dedicated BM25 engine is not implemented yet.
- `context expansion` returns parent + direct children only.
- Context deduplication is partial.
- With `EMBEDDING_PROVIDER=stub`, dense search is technical only and may add non-semantic candidates to hybrid results.
- RAG Search does not generate LLM answers.
- RAG Search does not modify the index.

---

## 11. Current test status

```text
18 passed, 1 warning
```

---

## 12. Separation from RAG Builder

RAG Builder remains responsible for:

- document indexing;
- chunking;
- embeddings generation for chunks;
- `document_sections`;
- `chunks`;
- `images`;
- `extracted_tables`;
- `formulas`;
- `cross_references`;
- `content_tsv`;
- `path_ltree`;
- citation metadata.

RAG Search is responsible for:

- dense retrieval;
- sparse retrieval;
- hybrid retrieval;
- context expansion;
- returning source chunks with citation metadata.
