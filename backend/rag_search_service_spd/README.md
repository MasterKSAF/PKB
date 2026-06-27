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

RAG Search SPD предоставляет endpoint-ы проверки состояния сервиса и поиска по готовому индексу.

Поддерживаемые endpoint-ы:

```text
GET  /api/v1/health
GET  /api/v1/ready
GET  /ready

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

Проверка работоспособности HTTP-сервиса.

`/health` не обязан проверять БД. Для проверки готовности read model используется `/ready`.

### GET /api/v1/ready

Readiness endpoint.

Проверяет, что RAG Builder-managed read model доступна для поиска:

```text
nsi.chunks
nsi.document_sections
PostgreSQL extensions: vector, ltree
```

Если read model готова, возвращает:

```json
{
  "status": "ready",
  "service": "rag_search_service_spd"
}
```

Если схема не готова, возвращает `503` с описанием отсутствующей таблицы, колонки или extension.

### GET /ready

Локальный alias для readiness check.

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

Builder и Search должны быть запущены с одинаковым значением `EMBEDDING_DIM`.
В текущем локальном стенде проверялось `EMBEDDING_DIM=2048`; фактическое значение нужно смотреть в `.env` конкретного сервиса.

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

Если сервис запущен с `EMBEDDING_PROVIDER=stub`, dense search не является полноценным семантическим поиском.
Для production/smoke dense нужен реальный embedding provider.

### sparse

Sparse search использует PostgreSQL full-text search:

```sql
content_tsv @@ websearch_to_tsquery('russian', query)
```

и ранжирование:

```sql
ts_rank_cd(content_tsv, websearch_to_tsquery('russian', query))
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

RAG Search только читает это поле и не пересобирает `content_tsv`.

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

## 12. Local smoke test

Перед локальным smoke-тестом нужно убедиться, что применены Alembic migrations RAG Builder,
потому что RAG Search сам не создаёт и не изменяет схему.

### Запуск сервиса

```powershell
cd D:\ISZF\UAI\Internships\PKB\PKB_develop\backend\rag_search_service_spd

.\venv\Scripts\Activate.ps1

$env:POSTGRES_HOST="127.0.0.1"
$env:POSTGRES_PORT="15432"
$env:POSTGRES_DB="pkb_neuro"
$env:POSTGRES_USER="pkb"

$env:NO_PROXY="127.0.0.1,localhost"
$env:no_proxy="127.0.0.1,localhost"

python -m uvicorn rag_search.api.app:app --reload
```

### Health / readiness

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/ready
```

Ожидаемый результат:

```text
status  service
------  -------
ok      rag_search_service_spd
ready   rag_search_service_spd
```

### Sparse search smoke

Для локальных Python smoke-скриптов нужно использовать `trust_env=False`,
чтобы `httpx` не отправлял запросы к `127.0.0.1` через proxy-env.

```powershell
@'
import httpx

queries = [
    "допуск соосности",
    "стойки",
    "ГОСТ 20862",
    "отверстия",
    "крепежные установочные стойки",
]

with httpx.Client(trust_env=False, timeout=10) as client:
    for query in queries:
        payload = {
            "query": query,
            "top_k": 5,
            "search_type": "sparse",
            "expand_context": False,
        }

        response = client.post(
            "http://127.0.0.1:8000/api/v1/rag/search",
            json=payload,
        )

        print("=" * 80)
        print("query:", query)
        print("status:", response.status_code)

        data = response.json()
        print("total_found:", data.get("total_found"))
        for item in data.get("results", []):
            print("chunk_id:", item.get("chunk_id"))
            print("score:", item.get("score"))
            print("content:", item.get("content"))
            print()
'@ | python
```

Пример подтверждённого локального результата на тестовом индексе:

```text
допуск соосности -> chunk 168
стойки -> chunks 166, 167
ГОСТ 20862 -> chunk 167
отверстия -> chunk 168
крепежные установочные стойки -> chunks 166, 167
```

Если `httpx` возвращает пустой `503` без `content-type`, а Uvicorn не показывает входящий запрос,
почти всегда причина в proxy-env. Использовать `trust_env=False` или `NO_PROXY=127.0.0.1,localhost`.

---

## 13. Текущий статус тестов

```text
20 passed, 1 warning
```

---

## 14. Разделение ответственности с RAG Builder

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
- citation metadata;
- Alembic migrations для Builder-managed read model.

RAG Search отвечает за:

- readiness check готовой read model;
- dense retrieval;
- sparse retrieval;
- hybrid retrieval;
- context expansion;
- возврат source chunks с citation metadata.

RAG Search не владеет DDL индекса и не содержит собственных Alembic migrations для таблиц индекса.
