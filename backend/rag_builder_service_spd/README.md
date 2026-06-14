# RAG Builder SPD

## 1. Назначение сервиса

RAG Builder получает JSON-контейнер документа, преобразует его в набор чанков, вычисляет эмбеддинги и сохраняет результат в PostgreSQL.

Текущий pipeline:

```text
BuildRequest
    ↓
ChunkingService
    ↓
EmbeddingService
    ↓
PostgresChunkRepository
    ↓
nsi.chunks
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
17 passed
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

* ChunkingService
* EmbeddingService (stub)
* InMemoryChunkRepository
* PostgresChunkRepository
* PostgreSQL persistence
* Reindex without duplicates
* FastAPI API
* Swagger UI
* Healthcheck
* Logging
* Docker
* Docker Compose
* API tests
* Integration tests

### Тестирование

```text
17 passed
```

### Следующие шаги

* Реальная embedding-модель
* Startup migrations
* README refinement
* CI/CD pipeline
* Интеграция с остальными сервисами платформы

```
```
