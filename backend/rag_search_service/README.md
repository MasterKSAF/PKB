# RAG Search Service

Микросервис гибридного поиска релевантных чанков по базе знаний (Knowledge Base).
Отвечает **только за поиск и выдачу чанков** с метаданными. Генерация ответа LLM выполняется в Query Service.

## Архитектура

Сервис реализует **гибридный поиск** с объединением результатов через алгоритм **Reciprocal Rank Fusion (RRF)**:

1. **Dense Search (Векторный):** Семантический поиск через `pgvector` (HNSW индекс, cosine distance).
2. **Sparse Search (Полнотекстовый):** Лексический поиск через `tsvector` (GIN индекс, `ts_rank`, русский язык).
3. **Reciprocal Rank Fusion (RRF):** Объединение двух ранжированных списков в единый скор без необходимости нормализации метрик.
4. **Metadata Enrichment:** JOIN с таблицами `registry.documents` и `registry.document_sections` для получения названий документов, разделов и кодов.
5. **Retry / Fallback:** При ошибке dense или sparse поиска — 2 retry (exponential backoff 500ms → 1s). Если dense упал — fallback на sparse, если sparse упал — fallback на dense. Если оба упали — ошибка пробрасывается.

### Стек технологий

- **Язык:** Python 3.11+
- **Фреймворк:** FastAPI (async)
- **БД:** PostgreSQL 16 + `pgvector` + `ltree`
- **Эмбеддинги:** Infinity (OpenAI-compatible API, модель Qwen3-Embedding-0.6B)
- **Драйвер БД:** `asyncpg`

## Быстрый старт

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
docker-compose up -d

# Проверить, что БД готова и данные инициализированы
docker-compose exec postgres psql -U rag_user -d knowledge_base -c "SELECT COUNT(*) FROM rag.document_chunks;"
```

### 3. Запуск сервиса

```bash
# Запустить сервис
uvicorn app.main:app --reload --port 8091
```

Сервис доступен по адресу: <http://127.0.0.1:8091>
Swagger UI: <http://127.0.0.1:8091/docs>
Health Check: <http://127.0.0.1:8091/api/v1/health>

## Развёртывание через Docker

### Инструкция для деплоера

#### 1. Подготовка файлов

```bash
git clone <repo>
cd ваше-приложение

# Скопировать .env для сервиса из шаблона
cp rag_search/.env.example rag_search/.env
nano rag_search/.env              # при необходимости изменить dev-дефолты

# Создать корневой .env с продакшен-переменными
nano .env
```

После подготовки структура выглядит так:

```
ваше-приложение/
├── .env                          # создан deployer'ом, НЕ в git
├── docker-compose.yaml
└── rag_search/
    ├── .env                      # скопирован из .env.example
    ├── .env.example              # шаблон (в git)
    └── Dockerfile
```

**Корневой** **`.env`** для продакшена (создаётся deployer'ом):

```env
# --- Database (должны совпадать с postgres service) ---
DB_USERNAME=rag_user
DB_PASSWORD=prod_secret
DB_DATABASE=knowledge_base

# --- Embeddings (обязательно) ---
EMBEDDING_BASE_URL=http://infinity:7997
EMBEDDING_API_KEY=
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
```

#### 2. Добавьте сервис в `docker-compose.yaml`

```yaml
  rag-search:
    build: ./rag_search
    image: rag-search:latest
    ports:
      - "8091:8091"
    env_file: ./rag_search/.env
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      DB_USERNAME: ${DB_USERNAME}
      DB_PASSWORD: ${DB_PASSWORD}
      DB_DATABASE: ${DB_DATABASE}
      EMBEDDING_BASE_URL: ${EMBEDDING_BASE_URL}
      EMBEDDING_API_KEY: ${EMBEDDING_API_KEY}
      EMBEDDING_MODEL: ${EMBEDDING_MODEL}
    depends_on:
      postgres:
        condition: service_healthy
```

Docker Compose сам читает корневой `.env` и подставляет `${VAR}`.
`env_file: ./rag_search/.env` загружает dev-дефолты, а `environment:` переопределяет
только нужные переменные для прода.

#### 3. Запуск

```bash
# Первый запуск — сборка + старт
docker-compose up -d --build

# Перезапуск только rag-search
docker-compose up -d --build rag-search
```

#### 4. Проверка

```bash
# Здоровье сервиса
curl http://127.0.0.1:8091/api/v1/health

# Поисковый запрос
curl -X POST http://127.0.0.1:8091/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "правила безопасности", "top_k": 3}'
```

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

Все переменные окружения задаются в `.env`. Полный список:

### Сервис

| Переменная        | Описание                                    | По умолчанию                          |
| ----------------- | ------------------------------------------- | ------------------------------------- |
| `SERVICE_NAME`    | Имя сервиса (для логов, метрик)             | `rag-search`                          |
| `SERVICE_VERSION` | Версия сервиса                              | `0.1.0`                               |
| `SERVICE_PORT`    | Порт HTTP                                   | `8091`                                |
| `LOG_LEVEL`       | Уровень логирования                         | `INFO`                                |
| `LOG_PII_FIELDS`  | Поля для маскировки в логах (через запятую) | `password,access_token,refresh_token` |

### База данных

Имена `DB_*` — стандарт PKB. `POSTGRES_*` поддерживается для обратной совместимости.

| Переменная    | Описание                              | По умолчанию     |
| ------------- | ------------------------------------- | ---------------- |
| `DB_USERNAME` | Пользователь БД                       | `rag_user`       |
| `DB_PASSWORD` | Пароль БД                             | `rag_password`   |
| `DB_DATABASE` | Имя БД                                | `knowledge_base` |
| `DB_HOST`     | Хост БД                               | `127.0.0.1`      |
| `DB_PORT`     | Порт БД (локально 5433, в проде 5432) | `5432`           |
| `DB_POOL_MIN` | Мин. размер пула соединений           | `2`              |
| `DB_POOL_MAX` | Макс. размер пула соединений          | `10`             |

### Провайдер эмбеддингов

| Переменная              | Описание                                                             | По умолчанию                |
| ----------------------- | -------------------------------------------------------------------- | --------------------------- |
| `EMBEDDING_API_KEY`     | API-ключ (опционален для Infinity)                                   | `""`                        |
| `EMBEDDING_BASE_URL`    | Базовый URL Infinity API (в Docker)                                  | `http://infinity:7997`      |
| `EMBEDDING_MODEL`       | Модель эмбеддингов                                                   | `Qwen/Qwen3-Embedding-0.6B` |
| `EMBEDDING_DIM`         | Размерность вектора (должна совпадать с моделью и VECTOR в БД)       | `1024`                      |
| `EMBEDDING_TIMEOUT`     | Таймаут запроса к API эмбеддингов (сек)                              | `60`                        |
| `EMBEDDING_INSTRUCTION` | Инструкция для query-запросов (Qwen3-Embedding). Пусто — без промпта | `""`                        |

### Поиск

| Переменная                | Описание                                                | По умолчанию |
| ------------------------- | ------------------------------------------------------- | ------------ |
| `SEARCH_DEFAULT_TOP_K`    | Количество результатов по умолчанию                     | `10`         |
| `SEARCH_MAX_TOP_K`        | Максимальное количество результатов                     | `100`        |
| `SEARCH_RRF_K`            | Константа k для алгоритма RRF                           | `60`         |
| `SEARCH_FETCH_MULTIPLIER` | Множитель выборки для каждого подзапроса (dense/sparse) | `2`          |

### Health Check

| Переменная             | Описание                           | По умолчанию |
| ---------------------- | ---------------------------------- | ------------ |
| `HEALTH_CHECK_TIMEOUT` | Таймаут проверки здоровья БД (сек) | `5`          |

## API Endpoints

POST /api/v1/rag/search
Гибридный поиск чанков.

Запрос:

```json
{
  "query": "правила безопасности",
  "top_k": 5,
  "search_type": "hybrid",
  "rerank": true
}
```

Ответ:

```json
{
  "query": "правила безопасности",
  "results": [
    {
      "chunk_id": 1,
      "document_id": 1,
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
  "total_found": 6
}
```

## Структура проекта

```
app/
├── api/v1/          # Эндпоинты (health, search)
├── core/
│   ├── database.py  # Пул asyncpg
│   ├── embeddings/  # Провайдер эмбеддингов (OpenAI-compatible)
│   ├── search/      # Логика поиска (dense, sparse, rrf, hybrid)
│   └── logging.py   # PII-фильтр
├── models/          # Pydantic схемы
└── main.py          # FastAPI app + lifespan
migrations/          # SQL DDL и сиды
tests/               # Unit и Integration тесты
```

## Известные ограничения

### Нечёткий поиск по title / doc\_code

Не реализован. В текущей схеме БД нет отдельного индекса для нечёткого поиска по
`registry.documents.title` или `registry.documents.doc_code`. Кроме того, не определён
порядок взаимодействия с найденными документами: если пользователь ввёл название
стандарта, непонятно, какие чанки подтягивать в результаты и как их ранжировать
относительно результатов гибридного поиска. Требуется уточнение логики на уровне
Query Service или Orchestrator.

### Размерность embedding (1024 vs 1536)

В текущей реализации используется размерность `VECTOR(1024)` (модель
`Qwen/Qwen3-Embedding-0.6B`). В ТЗ (`db_diagrams.md`) указана размерность
`VECTOR(1536)`. При интеграции с RAG Builder необходимо обеспечить согласованность
размерности.

### pg\_trgm

Упомянут в ТЗ как часть гибридного поиска, но в текущей реализации не используется.
