# RAG Search Service

Микросервис гибридного поиска релевантных чанков по базе знаний (Knowledge Base).
Отвечает **только за поиск и выдачу чанков** с метаданными. Генерация ответа LLM выполняется в Query Service.

## Архитектура

Сервис реализует **гибридный поиск** с объединением результатов через алгоритм **Reciprocal Rank Fusion (RRF)**:

1.  **Dense Search (Векторный):** Семантический поиск через `pgvector` (HNSW индекс, cosine distance).
2.  **Sparse Search (Полнотекстовый):** Лексический поиск через `tsvector` (GIN индекс, `ts_rank`, русский язык).
3.  **Reciprocal Rank Fusion (RRF):** Объединение двух ранжированных списков в единый скор без необходимости нормализации метрик.
4.  **Metadata Enrichment:** JOIN с таблицами `registry.documents` и `registry.document_sections` для получения названий документов, разделов и кодов.
5.  **Retry / Fallback:** При ошибке dense или sparse поиска — 2 retry (exponential backoff 500ms → 1s). Если dense упал — fallback на sparse, если sparse упал — fallback на dense. Если оба упали — ошибка пробрасывается.

### Стек технологий
*   **Язык:** Python 3.11+
*   **Фреймворк:** FastAPI (async)
*   **БД:** PostgreSQL 16 + `pgvector` + `ltree` + `pg_trgm`
*   **Эмбеддинги:**
    *   Локально: `sentence-transformers` (модель `intfloat/multilingual-e5-large`, dim=1024)
    *   Удаленно: OpenAI-compatible API
*   **Драйвер БД:** `asyncpg`

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонировать/перейти в директорию сервиса
cd services/rag_search

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Установить зависимости
pip install -e ".[dev]"

# Скопировать конфиг
cp .env.example .env
```
### 2. Запуск базы данных для тестирования

Сервис использует PostgreSQL с расширением pgvector. Для локальной разработки используется Docker Compose.

```bash
# Поднять контейнер с БД (порт 5433, чтобы не конфликтовать с локальным Postgres)
docker compose up -d

# Проверить, что БД готова и данные инициализированы
docker compose exec postgres psql -U rag_user -d knowledge_base -c "SELECT COUNT(*) FROM rag.document_chunks;"
# Ожидается: 20 (тестовые данные)
```

### 3. Запуск сервиса
```bash
# Запустить сервис
uvicorn app.main:app --reload --port 8091
```

Сервис доступен по адресу: http://127.0.0.1:8091
Swagger UI: http://127.0.0.1:8091/docs
Health Check: http://127.0.0.1:8091/api/v1/health

## Тестирование сервиса

```bash
# Запустить все тесты
pytest tests/ -v

# Запустить только unit-тесты (без БД)
pytest tests/unit/ -v

# Запустить integration-тесты (требует запущенную БД)
pytest tests/integration/ -v
```

## Конфигурация
Основные параметры в .env:
Переменная | Описание | По умолчанию
--- | --- | ---
POSTGRES_PORT | Порт БД (локально 5433, в проде 5432) | 5432
EMBEDDING_API_KEY | Ключ для OpenAI API. Если пустой — используется локальная модель HF. | (пусто)
EMBEDDING_DIM | Размерность вектора. Должна совпадать с моделью и схемой БД! | 1024
SEARCH_RRF_K | Константа k для алгоритма RRF. | 60

## API Endpoints
POST /api/v1/rag/search
Гибридный поиск чанков.

Запрос:
```json
{
  "query": "ледовый класс Arc4",
  "top_k": 5,
  "search_type": "hybrid",
  "rerank": true
}
```
Ответ:
```json
{
  "query": "безопасность оборудования",
  "results": [
    {
      "chunk_id": 1,
      "document_id": "11111111-1111-1111-1111-111111111111",
      "document_title": "ССБТ. Оборудование производственное. Общие требования безопасности",
      "doc_code": "ГОСТ 12.2.003-91",
      "section_id": 1,
      "section_title": "Область распространения",
      "page": 2,
      "content": "Настоящий стандарт распространяется на оборудование всех отраслей промышленности...",
      "score": 0.032,
      "clause": "1",
      "confidence": 0.95
    }
  ],
  "search_type_used": "hybrid",
  "processing_time_ms": 245,
  "total_found": 10
}
```

## Структура проекта
```
app/
├── api/v1/          # Эндпоинты (health, search)
├── core/
│   ├── database.py  # Пул asyncpg
│   ├── embeddings/  # Провайдеры эмбеддингов (HF / OpenAI)
│   ├── search/      # Логика поиска (dense, sparse, rrf, hybrid)
│   └── logging.py   # PII-фильтр
├── models/          # Pydantic схемы
└── main.py          # FastAPI app + lifespan
migrations/          # SQL DDL и сиды
tests/               # Unit и Integration тесты
```

## Известные ограничения

### Нечёткий поиск по title / doc_code
Не реализован. В текущей схеме БД нет отдельного индекса для нечёткого поиска по
`registry.documents.title` или `registry.documents.doc_code`. Кроме того, не определён
порядок взаимодействия с найденными документами: если пользователь ввёл название
стандарта, непонятно, какие чанки подтягивать в результаты и как их ранжировать
относительно результатов гибридного поиска. Требуется уточнение логики на уровне
Query Service или Orchestrator.

### Размерность embedding (1024 vs 1536)
В текущей реализации используется размерность `VECTOR(1024)` (модель
`intfloat/multilingual-e5-large`). В ТЗ (`db_diagrams.md`) указана размерность
`VECTOR(1536)`. При интеграции с RAG Builder необходимо обеспечить согласованность
размерности.

### pg_trgm
Упомянут в ТЗ как часть гибридного поиска, но в текущей реализации не используется.