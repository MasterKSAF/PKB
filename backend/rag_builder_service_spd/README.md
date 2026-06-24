# RAG Builder SPD

## 1. Назначение сервиса

RAG Builder получает JSON-контейнер документа, преобразует его в набор чанков, вычисляет эмбеддинги
и сохраняет результат в PostgreSQL.

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

Поиск, retrieval, vector search, rerank и генерация ответов находятся вне зоны ответственности данного сервиса.
RAG Builder только подготавливает данные для последующего сервиса RAG Search.
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
git clone https://github.com/NeuronsUII/PKB_neuroassistant.git
cd PKB_neuroassistant/backend/rag_builder_service_spd
```
Если репозиторий уже склонирован, достаточно перейти в папку сервиса:

cd backend/rag_builder_service_spd

Создать виртуальное окружение:

```bash
python -m venv venv
```

Активировать окружение:

### Windows

```bash
venv\Scripts\activate
```

Установить зависимости и сам локальный пакет в режиме разработки:

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

INDEXING_JOB_STALE_AFTER_SECONDS=3600
MAX_ACTIVE_INDEXING_JOBS=10
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
60 passed, 1 skipped
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
http://127.0.0.1:8000/api/v1/health
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
http://127.0.0.1:8001/api/v1/health
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

### GET /api/v1/health

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

### POST /api/v1/rag/build

Основной контрактный endpoint для запуска индексации документа. Индексация выполняется в фоне.
Принимает flat Registry payload:
Минимальный пример запроса:

```json
{
  "document_id": 420000,
  "sections": [
    {
      "section_id": 1,
      "parent_id": null,
      "clause": "1",
      "title": null,
      "level": 1,
      "path": "1",
      "page": 1,
      "bbox": null,
      "type": "text",
      "content": {
        "text": "Настоящий стандарт распространяется..."
      },
      "references": []
    }
  ],
  "protected_spans": [],
  "options": {
    "strategy": "semantic_1024"
  }
}
```

Если входной JSON проходит Pydantic-валидацию, сервис возвращает ответ
`202 Accepted`:

```json
{
  "status": "indexing",
  "document_id": 420000,
  "task_id": 1,
  "indexing_txn_id": "2f7b0a2e-5b7f-4a45-8f87-9f3c5a9b1e2d"
}
```
Если входной JSON не проходит Pydantic-валидацию, сервис возвращает стандартный
FastAPI/Pydantic ответ
`422 Unprocessable Entity`.

В этом случае:

индексация не запускается;
background task не создаётся;
indexing_txn_id не выдаётся;
данные в nsi.* таблицы не записываются.

Ошибки, возникшие уже после успешной валидации и запуска задачи, отражаются в статусе
индексации через GET /api/v1/rag/build/{document_id}/status.

Перед созданием новой indexing job сервис выполняет защитные проверки в следующем порядке:

1. Помечает зависшие `pending_index` / `indexing` jobs как `failed`, если они старше `INDEXING_JOB_STALE_AFTER_SECONDS`.
2. Проверяет, нет ли уже активной job для того же `document_id`.
3. Проверяет глобальный лимит активных jobs через `MAX_ACTIVE_INDEXING_JOBS`.
4. Только после этого создаёт новую indexing job и ставит background task.

Если для того же `document_id` уже есть свежая активная job, сервис возвращает `409 Conflict`:

```json
{
  "detail": {
    "code": "ALREADY_PROCESSING",
    "message": "Document indexing is already in progress",
    "details": {
      "document_id": 420000,
      "indexing_txn_id": "2f7b0a2e-5b7f-4a45-8f87-9f3c5a9b1e2d",
      "status": "indexing"
    }
  }
}
```

Если количество свежих активных jobs достигло `MAX_ACTIVE_INDEXING_JOBS`, сервис возвращает `429 Too Many Requests`:

```json
{
  "detail": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Too many active indexing jobs",
    "details": {
      "active_jobs": 10,
      "max_active_jobs": 10
    }
  }
}
```

Расширенный пример с разными типами секций:

```json
{
  "document_id": 420000,
  "sections": [
    {
      "section_id": 1,
      "parent_id": null,
      "clause": "1",
      "title": "Область применения",
      "level": 1,
      "path": "1",
      "page": 1,
      "bbox": [0.12, 0.18, 0.88, 0.26],
      "type": "text",
      "content": {
        "text": "Настоящий стандарт распространяется..."
      },
      "references": []
    },
    {
      "section_id": 2,
      "parent_id": 1,
      "clause": "1.1",
      "title": "Таблица 1",
      "level": 2,
      "path": "1/1.1",
      "page": 1,
      "bbox": [0.10, 0.30, 0.90, 0.55],
      "type": "table",
      "content": {
        "caption": "Таблица 1 — Основные параметры",
        "headers": ["Параметр", "Значение", "Единица"],
        "rows": [
          ["Диаметр", "10", "мм"],
          ["Длина", "25", "мм"]
        ],
        "markdown": "| Параметр | Значение | Единица |\n|---|---:|---|\n| Диаметр | 10 | мм |\n| Длина | 25 | мм |"
      },
      "references": []
    },
    {
      "section_id": 3,
      "parent_id": 1,
      "clause": "1.2",
      "title": "Рисунок 1",
      "level": 2,
      "path": "1/1.2",
      "page": 2,
      "bbox": [0.15, 0.20, 0.85, 0.70],
      "type": "image",
      "content": {
        "image_key": "minio://documents/420000/page_2_image_1.png",
        "caption": "Рисунок 1 — Схема установки",
        "description": "Схематическое изображение установочной стойки."
      },
      "references": []
    },
    {
      "section_id": 4,
      "parent_id": 1,
      "clause": "1.3",
      "title": "Формула 1",
      "level": 2,
      "path": "1/1.3",
      "page": 2,
      "bbox": [0.20, 0.72, 0.80, 0.82],
      "type": "formula",
      "content": {
        "latex": "F = m \\cdot a",
        "meaning": "Сила равна произведению массы на ускорение.",
        "parameters": [
          {
            "symbol": "F",
            "description": "сила",
            "unit": "Н"
          },
          {
            "symbol": "m",
            "description": "масса",
            "unit": "кг"
          },
          {
            "symbol": "a",
            "description": "ускорение",
            "unit": "м/с²"
          }
        ]
      },
      "references": []
    }
  ],
  "protected_spans": [
    {
      "section_id": 1,
      "start_offset": 120,
      "end_offset": 260,
      "reason": "do_not_split_normative_clause"
    }
  ],
  "options": {
    "strategy": "semantic_1024"
  }
}
```

Для таблиц Builder сохраняет исходную структуру и формирует индексируемое текстовое/Markdown-представление.
Для сложных таблиц авторитетным источником остаётся JSON-структура во входном контейнере.

Для изображений Builder использует только те текстовые поля, которые уже есть во входном JSON:
`caption`, `description`, `image_key`.
Автоматическое описание изображения через multimodal LLM не входит в ответственность RAG Builder MVP.

Для формул Builder использует уже переданные `latex`, `meaning`, `markdown` и `parameters`.
Автоматическое распознавание смысла формул не выполняется внутри RAG Builder.

### `references`

Поле `sections[].references` содержит ссылки, найденные внутри конкретной секции документа.

RAG Builder не использует `references` для формирования текста чанка, но сохраняет их:

* в metadata соответствующего chunk;
* в таблицу `nsi.cross_references`.

Это нужно для будущего графа ссылок между документами, нормативными актами, пунктами, таблицами и другими объектами.

Минимальный пример:

```json
"references": [
  {
    "type": "range",
    "target_doc_code": "ГОСТ 20862-81 – ГОСТ 20867-81",
    "context": "Размеры и предельные отклонения — по ГОСТ 20862-81 – ГОСТ 20867-81.",
    "note": "Нормативная ссылка на диапазон стандартов"
  }
]
```

Пример ссылки на один документ:

```json
"references": [
  {
    "type": "normative_document",
    "target_document_id": 420123,
    "target_doc_code": "ГОСТ 20862-81",
    "context": "Технические требования — по ГОСТ 20862-81.",
    "note": "Связь с известным документом Registry"
  }
]
```

Поля `references[]`:

| Поле                 | Тип           | Обязательность | Описание                                                                                   |
| -------------------- | ------------- | -------------: | ------------------------------------------------------------------------------------------ |
| `type`               | string        |             Да | Тип ссылки: например `normative_document`, `range`, `table`, `formula`, `image`, `unknown` |
| `target_doc_code`    | string        |             Да | Код целевого документа или текстовое обозначение ссылки, например `ГОСТ 20862-81`          |
| `target_document_id` | bigint | null |            Нет | ID целевого документа в Registry, если он уже известен                                     |
| `context`            | string | null |            Нет | Фрагмент исходного текста, в котором была найдена ссылка                                   |
| `note`               | string | null |            Нет | Дополнительное пояснение                                                                   |

Если ссылка найдена, но целевой документ ещё не сопоставлен с Registry, `target_document_id` можно оставить `null`,
а `target_doc_code` сохранить как текстовое обозначение.


---

### GET /api/v1/rag/build/jobs

Возвращает список indexing jobs с пагинацией и опциональной фильтрацией по статусу.

Параметры запроса:

| Параметр | Тип | По умолчанию | Описание |
| -------- | --- | ------------ | -------- |
| `status` | string | `null` | Фильтр по статусу: `pending_index`, `indexing`, `indexed`, `failed` |
| `page` | int | `1` | Номер страницы |
| `page_size` | int | `50` | Размер страницы, максимум `200` |

Пример:

```text
GET /api/v1/rag/build/jobs?status=indexed&page=1&page_size=10
```

Пример ответа:

```json
{
  "items": [
    {
      "id": 26,
      "indexing_txn_id": "5c2d9d45-2e02-44ad-a2d7-806ba5158341",
      "document_id": 420000,
      "status": "indexed",
      "chunks_count": 3,
      "has_embeddings": true,
      "indexed_at": "2026-06-24T12:00:00Z",
      "index_stats": {
        "sections": 3,
        "chunks": 3,
        "embeddings": 3
      },
      "warnings": [],
      "errors": [],
      "created_at": "2026-06-24T12:00:00Z",
      "updated_at": "2026-06-24T12:00:00Z"
    }
  ],
  "meta": {
    "total": 11,
    "page": 1,
    "page_size": 10
  }
}
```

---

### GET /api/v1/rag/build/{document_id}/status

Проверяет статус индексации документа.

Пример:

```text
GET /api/v1/rag/build/420000/status?longpoll=15
```

Пример ответа:

```json
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

---

### DELETE /api/v1/rag/build/{document_id}

Удаляет индекс документа из таблиц RAG Builder.

Пример ответа:

```json
{
  "document_id": 420000,
  "deleted_count": 18,
  "status": "completed"
}
```

---

### Legacy/local compatibility endpoints

Для обратной совместимости также поддерживаются:

```text
POST /index
GET /index/status/{indexing_txn_id}

POST /rag/build
GET /rag/build/{document_id}/status
```

Текущий legacy-вход всё ещё использует `BuildRequest` / chunk-container.
`document_version_id` больше не является обязательным входным полем.
Если legacy-контейнер всё ещё передаёт `document_version_id`, Builder принимает его для обратной совместимости.
Если поле отсутствует, Builder временно использует `document_id` как legacy/audit `document_version_id` внутри Chunk/DB.

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
* batch embeddings для всех чанков документа
* OpenAIEmbeddingProvider
* StubEmbeddingProvider
* PostgreSQL persistence
* Reindex без дубликатов
* async indexing jobs
* indexing jobs list endpoint
* stale indexing jobs cleanup
* duplicate active job guard per `document_id`
* active jobs limit
* delete/reindex endpoint

#### Chunking

* поддержка subchunks
* overlap 20%
* разбиение по предложениям
* fallback-разбиение по пробелам
* `protected_spans` не разрываются между chunks
* `protected_spans` фильтруются по `section_id`

Supported chunk strategies:

- `semantic_512` — approximately 512 tokens, sentence-aware split, 20% overlap.
- `semantic_1024` — default strategy, approximately 1024 tokens, sentence-aware split, 20% overlap.
- `semantic_2048` — approximately 2048 tokens, sentence-aware split, 20% overlap.
- `fixed_256` — approximately 256 tokens, fixed-size split, 10% overlap.
- `fixed_512` — approximately 512 tokens, fixed-size split, 10% overlap.

MVP uses character-based approximation until tokenizer-based chunking is added.

#### Embeddings

* OpenAI Embeddings
* Stub Embeddings
* OpenAI-compatible external API
* Infinity-compatible API
* Batch Embeddings для всех чанков документа
* Usage Accounting
* подсчёт суммарных tokens/cost по batch-результату


Supported embedding providers:

- `stub` — local zero-vector provider for tests and offline development.
- `openai` — official OpenAI API, uses `OPENAI_API_KEY`.
- `openai_compatible` — OpenAI-compatible embeddings endpoint, uses `EMBEDDING_API_BASE_URL` and `EMBEDDING_API_KEY`.
- `infinity` — alias for OpenAI-compatible local Infinity embeddings service.
- `external` — alias for external OpenAI-compatible embeddings API.

Example for local Infinity:

```env
EMBEDDING_PROVIDER=infinity
EMBEDDING_MODEL=qwen3-embedding-4b
EMBEDDING_DIM=2048
EMBEDDING_API_BASE_URL=http://localhost:7997/v1
EMBEDDING_API_KEY=
```

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
60 passed, 1 skipped
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

- 60 тестов проходят, 1 skipped
- PostgreSQL persistence реализован
- pgvector поддерживается
- ltree поддерживается
- document hierarchy реализована (без связи c id внешних документов)
- references/images/tables/formulas реализованы
- batch embeddings реализованы
- protected_spans реализованы

Статус: MVP v1 Ready

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

### Stage 7 — Integration with RAG Search Service

* интеграция с RAG Search Service
* Hybrid Search
* RRF
* Citation Engine
* Context Expansion через ltree
* context expansion применяется к каждому result из top_k
