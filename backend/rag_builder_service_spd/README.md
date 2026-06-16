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
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
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
18 passed
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

Принимает JSON-контейнер документа.

Пример:

```json
{
  "metadata": {
    "document_id": 420000,
    "document_version_id": 420001
  }
}
```

Пример ответа:

```json
{
  "status": "indexed",
  "document_id": 420000,
  "document_version_id": 420001,
  "chunks_count": 3
}
```

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
18 passed
```

---

## Database Writes

На текущем этапе сервис записывает данные в следующие таблицы:

```text
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

- 18 тестов проходят
- PostgreSQL persistence реализован
- pgvector поддерживается
- ltree поддерживается
- document hierarchy реализована (без связи c id внешних документов)
- references/images/tables/formulas реализованы
- batch embeddings реализованы

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

### Stage 7 — Search Integration

* интеграция с RAG Search Service
* Hybrid Search
* RRF
* Citation Engine
* Context Expansion через ltree

