# RAG Builder SPD

## 1. Назначение сервиса

RAG Builder получает JSON-контейнер документа, преобразует его в набор чанков, вычисляет эмбеддинги и сохраняет результат в PostgreSQL.

Текущий pipeline:

```text
BuildRequest
    ↓
ChunkingService
    ↓
EmbeddingService (batch)
    ↓
PostgresChunkRepository
    ↓
nsi.document_sections
    nsi.chunks
    nsi.cross_references
    nsi.images
    nsi.extracted_tables
    nsi.formulas
```

Сервис является частью RAG-платформы и отвечает только за индексацию документов.

Поиск, retrieval, vector search и генерация ответов находятся вне зоны ответственности данного сервиса.

---

## 2. Требования

* Python 3.12+
* PostgreSQL 16+
* Docker Desktop (опционально)
* Git

---

## 3. Установка

Клонировать репозиторий:

```bash
git clone <repository_url>
cd backend/rag_builder_service_spd
```

Создать виртуальное окружение:

```bash
python -m venv venv
```

Активировать окружение:

### Windows

```bash
venv\Scripts\activate
```

Установить зависимости:

```bash
pip install -e .
```

---

## 4. Настройка окружения

Создать файл `.env`:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433

POSTGRES_DB=nsi_dev
POSTGRES_USER=nsi_dev
POSTGRES_PASSWORD=SecureP@ssw0rd_2026_Dev

POSTGRES_SCHEMA=nsi

EMBEDDING_PROVIDER=stub
EMBEDDING_MODEL=qwen3-embedding-4b
EMBEDDING_DIM=2048

EMBEDDING_API_MODE=infinity
EMBEDDING_API_BASE_URL=
EMBEDDING_API_KEY=

CHUNK_STRATEGY=semantic_1024
```

Проверить настройки:

```bash
python -c "from rag_builder.core.config import settings; print(settings.POSTGRES_HOST)"
```

---

## 5. Запуск тестов

Запуск всех тестов:

```bash
pytest
```

Текущее состояние:

```text
29 passed
```

---

## 6. Запуск через Uvicorn

Из корня проекта:

```bash
uvicorn rag_builder.api.app:app --reload
```

После запуска доступны:

```text
Swagger UI:
http://127.0.0.1:8000/docs

Healthcheck:
http://127.0.0.1:8000/health
```

---

## 7. Запуск через Docker

Сборка образа:

```bash
docker build -t rag-builder-spd .
```

Запуск контейнера:

```bash
docker run --rm \
  -p 8001:8000 \
  --env-file .env \
  -e POSTGRES_HOST=host.docker.internal \
  rag-builder-spd
```

Проверка:

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/docs
```

---

## 8. Запуск через Docker Compose

Запуск:

```bash
docker compose up
```

Запуск в фоне:

```bash
docker compose up -d
```

Просмотр логов:

```bash
docker compose logs -f
```

Остановка:

```bash
docker compose down
```

---

## 9. API

### GET /health

Проверка работоспособности сервиса и подключения к PostgreSQL.

Пример ответа:

```json
{
  "status": "ok",
  "service": "rag_builder_service_spd",
  "database": "ok"
}
```

---

### POST /index

Запускает индексацию документа в асинхронном режиме.

Текущий MVP-вход всё ещё использует `BuildRequest` / chunk-container.
`document_version_id` временно остаётся во входном контейнере как legacy/audit-поле до отдельного PR по синхронизации полного контракта Builder.

Пример запроса:

```json
{
  "metadata": {
    "document_id": 420000,
    "document_version_id": 420001
  }
}
```

Пример ответа 202 Accepted:

```
{
  "status": "indexing",
  "document_id": 420000,
  "task_id": 1,
  "indexing_txn_id": "2f7b0a2e-5b7f-4a45-8f87-9f3c5a9b1e2d"
}
```

Индексация выполняется в фоне. Результат проверяется через:

GET /index/status/{indexing_txn_id}

Пример ответа статуса:

```
{
  "document_id": 420000,
  "status": "indexed",
  "indexing_txn_id": "2f7b0a2e-5b7f-4a45-8f87-9f3c5a9b1e2d",
  "chunks_count": 18,
  "has_embeddings": true,
  "indexed_at": "2026-06-20T12:00:00Z",
  "index_stats": {
    "sections": 8,
    "chunks": 18,
    "embeddings": 18
  },
  "warnings": [],
  "errors": []
}
```
Дополнительно поддерживается совместимый endpoint:

POST /rag/build
GET /rag/build/{document_id}/status


---

### POST /search

RAG Search MVP endpoint.

Search reads indexed chunks from PostgreSQL and returns source chunks with citation metadata. It does not generate LLM answers.

Supported search types:

| search_type | Description |
|---|---|
| `dense` | Vector search by `nsi.chunks.embedding` |
| `sparse` | PostgreSQL full-text search by `nsi.chunks.content_tsv` with `ts_rank_cd` |
| `hybrid` | RRF fusion of sparse and dense results, duplicates removed |

Request example:

```json
{
  "query": "допуск соосности",
  "top_k": 5,
  "search_type": "hybrid",
  "expand_context": false
}
```

Context expansion request example:

```json
{
  "query": "допуск соосности",
  "top_k": 5,
  "search_type": "hybrid",
  "expand_context": true
}
```

When `expand_context=true`, each result may include a `context` array with:

- `parent` section
- direct `child` sections such as tables, images, formulas or text sections

Response contains chunks with citation fields:

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
      "content": "Допуск соосности оси отверстия...",
      "context": []
    }
  ],
  "total_found": 1,
  "context_expanded": false
}
```

MVP limitations:

- `hybrid` uses Reciprocal Rank Fusion with `k=60`.
- `sparse` uses PostgreSQL full-text ranking via `ts_rank_cd`; a dedicated BM25 engine is not implemented yet.
- `context expansion` uses `document_sections.path_ltree` and returns parent + direct children for each result.
- Context deduplication is partial: context items already present in main `results` are removed.
- With `EMBEDDING_PROVIDER=stub`, dense search is technical only and may add non-semantic candidates to hybrid results.

Sparse search acceleration:

- `nsi.chunks` has a materialized `tsvector` column:
  - `content_tsv`
- `content_tsv` is filled during chunk indexing with:
  - `to_tsvector('russian'::regconfig, content)`
- `nsi.chunks` has a GIN index:
  - `idx_chunks_content_tsv`
  - `USING GIN (content_tsv)`
- The index accelerates PostgreSQL full-text sparse search.

---

## 10. Структура проекта

```text
src/
└── rag_builder/
    ├── api/
    ├── core/
    ├── models/
    ├── repositories/
    └── services/

tests/
examples/
sql/
```

---

## 11. Текущий статус MVP

### Реализовано

#### Индексация документа

* BuildRequest (chunk-container)
* ChunkingService
* EmbeddingService
* OpenAIEmbeddingProvider
* StubEmbeddingProvider
* PostgreSQL persistence
* Reindex без дубликатов

#### Chunking

* поддержка subchunks
* overlap 20%
* разбиение по предложениям
* fallback-разбиение по пробелам

#### Embeddings

* OpenAI Embeddings
* Stub Embeddings
* Batch Embeddings
* Usage Accounting
* batch embeddings для всех чанков документа

#### Хранение структуры документа

* nsi.document_sections
* parent-child иерархия
* path
* path_ltree
* GIST индекс для ltree
* content_tsv + GIN index for sparse full-text search

#### Хранение чанков

* nsi.chunks
* embeddings (pgvector)
* связь с document_sections через FK

#### Междокументные связи

* nsi.cross_references
* нормативные ссылки
* ссылки на таблицы
* граф ссылок между документами

#### Изображения

* nsi.images
* caption
* metadata
* привязка к document_sections

#### Таблицы

* nsi.extracted_tables
* JSON представление таблицы
* Markdown представление таблицы
* привязка к document_sections

#### Формулы

* nsi.formulas
* nsi.formula_parameters
* LaTeX
* параметры формул
* связь с document_sections

#### API

* FastAPI
* Swagger UI
* Healthcheck
* Logging

#### Инфраструктура

* Docker
* Docker Compose
* PostgreSQL
* pgvector
* ltree

### Тестирование

Текущее состояние:

```text
29 passed
```

---

## Database Writes

На текущем этапе сервис записывает данные в следующие таблицы:

```text
nsi.indexing_jobs
nsi.document_sections
nsi.chunks
nsi.cross_references
nsi.images
nsi.extracted_tables
nsi.formulas
nsi.formula_parameters
```

---

## Knowledge Base Schema

```text
indexing_jobs

document_sections
│
├── chunks
├── cross_references
├── images
├── extracted_tables
└── formulas
    └── formula_parameters
```

---

## MVP Status

Текущее состояние:

- 29 тестов проходят
- PostgreSQL persistence реализован
- pgvector поддерживается
- ltree поддерживается
- document hierarchy реализована (без связи c id внешних документов)
- references/images/tables/formulas реализованы
- batch embeddings реализованы

Статус: MVP v1 Ready

---

#### RAG Search MVP

* `POST /search`
* dense vector search
* sparse full-text search with `content_tsv` and `ts_rank_cd`
* hybrid RRF fusion with `k=60`
* citation/source fields: `document_id`, `section_id`, `clause`, `path`, `page`, `bbox`, `content`
* retrieval metadata: `chunk_id`, `score`, `mode`
* context expansion via `document_sections.path_ltree`
* parent + direct children context
* partial context deduplication by `document_section_id`

---

## 13. Roadmap

### Stage 1 — Core Indexing ✅

* ChunkingService
* EmbeddingService
* PostgreSQL persistence
* FastAPI API

### Stage 2 — Document Structure ✅

* nsi.document_sections
* parent-child hierarchy
* path_ltree

### Stage 3 — References Graph ✅

* nsi.cross_references
* нормативные ссылки
* междокументные связи

### Stage 4 — Rich Content Extraction ✅

* nsi.images
* nsi.extracted_tables
* nsi.formulas
* nsi.formula_parameters

### Stage 5 — Embeddings ✅

* OpenAI Embeddings
* Batch Embeddings
* Usage Accounting

### Stage 6 — Production Embeddings

* локальные embedding-модели
* мониторинг стоимости эмбеддингов

### Stage 7 — Search Integration

* интеграция с RAG Search Service
* Hybrid Search
* RRF
* Citation Engine
* Context Expansion через ltree
* context expansion применяется к каждому result из top_k

