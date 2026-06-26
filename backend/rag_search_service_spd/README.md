# RAG Search SPD

> README описывает текущий сервис `backend/rag_search_service_spd`.
>
> RAG Search логически отделён от RAG Builder.
> RAG Builder подготавливает `document_sections`, `chunks`, embeddings, `content_tsv`, `path_ltree`, citation metadata и связанные объекты.
> RAG Search читает подготовленный индекс и выполняет retrieval.
>
> Сервис является read-only: он не изменяет индекс и не пишет данные в `nsi`.

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

### Карта endpoint-ов

RAG Search SPD предоставляет только endpoint-ы поиска и чтения индекса.

Поддерживаемые endpoint-ы:

```text
GET  /api/v1/health

POST /api/v1/rag/search
POST /rag/search
POST /search
```

Legacy endpoint `GET /health` не поддерживается:

```text
GET /health
```

RAG Search не изменяет индекс.
Запись индекса выполняет `backend/rag_builder_service_spd`.

### GET /api/v1/health

Проверка работоспособности сервиса.

### POST /api/v1/rag/search

Основной контрактный endpoint поиска.

### POST /search

Legacy/local endpoint.

### POST /rag/search

Совместимый endpoint для старых локальных интеграций.

Все три search endpoint-а используют один `SearchRequest` и возвращают один `SearchResponse`.

Текущая политика endpoint-ов:

```text
POST /api/v1/rag/search  # основной API v1 endpoint
POST /rag/search         # совместимый alias
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

| Поле | Тип | Описание |
|---|---|---|
| `query` | string | поисковый запрос |
| `top_k` | integer | количество результатов |
| `search_type` | string | `dense`, `sparse` или `hybrid` |
| `expand_context` | boolean | добавить parent/direct children context |
| `filters` | object/null | будущие фильтры по документу, секции, типу chunk и т.п. |

---

## 5. Совместимость dense-поиска с ANN-индексом

Dense-поиск использует то же SQL-выражение, под которое RAG Builder создаёт ANN-индекс:

```sql
embedding::halfvec(EMBEDDING_DIM) <=> query::halfvec(EMBEDDING_DIM)
```

Это нужно, чтобы PostgreSQL мог использовать индекс:

```text
idx_chunks_embedding_hnsw_halfvec
```

Размерность берётся из `EMBEDDING_DIM`.

Локально сейчас Builder и Search используют `EMBEDDING_DIM=312`.
В боевом окружении при `EMBEDDING_DIM=2048` оба сервиса должны быть запущены с одинаковым значением.

Причина использования `halfvec`: pgvector HNSW по обычному `vector` ограничен 2000 измерениями.
`halfvec` поддерживает индексирование до 4000 измерений, поэтому подходит для embedding-ов размерности 2048.

---

## 6. Режимы поиска

| search_type | Описание |
|---|---|
| `dense` | vector search по `nsi.chunks.embedding` |
| `sparse` | PostgreSQL full-text search по `nsi.chunks.content_tsv` с ранжированием `ts_rank_cd` |
| `hybrid` | объединение sparse и dense результатов через RRF, дубликаты удаляются |

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

## 7. Context expansion

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

## 8. Пример ответа

```json
{
  "query": "допуск соосности",
  "search_type_used": "hybrid",
  "results": [
    {
      "chunk_id": 151,
      "document_id": 420000,
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

## 9. Ускорение sparse-поиска

RAG Builder готовит `content_tsv` во время индексации.

Ожидаемые поля и индексы в БД:

```text
nsi.chunks.content_tsv
idx_chunks_content_tsv
USING GIN (content_tsv)
```

Значение заполняется из текста chunk-а:

```sql
to_tsvector('russian'::regconfig, content)
```

---

## 10. Embeddings

Dense и hybrid search требуют query embeddings.

Поддерживаемые варианты deployment:

```text
stub               — тестовый/local technical режим
openai             — официальный OpenAI API
openai_compatible  — OpenAI-compatible endpoint
infinity           — локальный Infinity-compatible endpoint
external           — внешний OpenAI-compatible API
```

С учётом ограничений сервера production search не должен требовать локальную GPU.
Dense query embeddings должны приходить через внешний API или другой backend-provided embedding endpoint.

---

## 11. Ограничения MVP

- `hybrid` использует Reciprocal Rank Fusion с `k=60`.
- `sparse` использует PostgreSQL full-text ranking через `ts_rank_cd`; отдельный BM25 engine пока не реализован.
- `context expansion` возвращает только parent + direct children.
- Context deduplication пока частичная.
- При `EMBEDDING_PROVIDER=stub` dense search является техническим режимом и может добавлять в hybrid results несемантические candidates.
- RAG Search не генерирует LLM-ответы.
- RAG Search не изменяет индекс.

---

## 12. Текущий статус тестов

```text
18 passed, 1 warning
```

---

## 13. Разделение ответственности с RAG Builder

RAG Builder отвечает за:

- индексацию документа;
- chunking;
- генерацию embeddings для chunks;
- `document_sections`;
- `chunks`;
- `images`;
- `extracted_tables`;
- `formulas`;
- `cross_references`;
- `content_tsv`;
- `path_ltree`;
- citation metadata.

RAG Search отвечает за:

- dense retrieval;
- sparse retrieval;
- hybrid retrieval;
- context expansion;
- возврат source chunks с citation metadata.
