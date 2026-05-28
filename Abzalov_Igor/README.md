# RAG Builder Service

## Назначение
RAG Builder Service строит векторный индекс документа:
1. принимает нормализованный JSON документа,
2. режет его на чанки,
3. считает embeddings,
4. сохраняет данные в PostgreSQL + pgvector,
5. отдает статус индексации и поддерживает удаление индекса.

Базовый API prefix: `/api/v1`

## Эндпоинты
- `POST /api/v1/rag/build`
- `DELETE /api/v1/rag/build/{doc_id}`
- `GET /api/v1/rag/build/{doc_id}/status?longpoll=15`
- `GET /api/v1/rag/health/live`
- `GET /api/v1/rag/health/ready`

## Как работает система

### Поток данных
1. Входной JSON (по контракту Source of Truth) приходит в `POST /rag/build`.
2. Роут принимает запрос и передает его в `IndexingService`.
3. `IndexingService` вызывает `ChunkingService` для детерминированной нарезки.
4. `IndexingService` вызывает `EmbeddingService` для генерации векторов.
5. `ChunkRepository` в транзакции удаляет старые чанки документа и вставляет новые в `rag.document_chunks`.
6. Сервис обновляет in-memory статус (`pending/indexing/indexed/failed`).
7. `GET /status` читает статус (longpoll до таймаута), `DELETE` удаляет индекс документа.

## Архитектура по файлам

### API слой
- `src/rag_builder/api/app.py`: создание FastAPI приложения, подключение роутов/мидлвари.
- `src/rag_builder/api/v1/rag_routes.py`: HTTP-эндпоинты, только orchestration-вызовы.
- `src/rag_builder/api/middleware.py`: request/correlation id, тайминг запросов.

### Service слой
- `src/rag_builder/services/indexing_service.py`: бизнес-оркестрация пайплайна build/delete/status.

### Domain/Contracts
- `src/rag_builder/models/contracts.py`: Pydantic-контракты API.
- `src/rag_builder/models/domain.py`: доменная сущность чанка.
- `src/rag_builder/models/db.py`: SQLAlchemy модель таблицы `rag.document_chunks`.

### Infrastructure
- `src/rag_builder/repositories/chunk_repository.py`: DB-операции (insert/delete/count/has_embeddings).
- `src/rag_builder/db/session.py`: async SQLAlchemy engine/session.
- `src/rag_builder/chunking/service.py`: chunking логика.
- `src/rag_builder/embeddings/service.py`: embeddings логика.

### Конфиг и логирование
- `src/rag_builder/core/config.py`: загрузка env-настроек.
- `src/rag_builder/core/logging.py`: настройка `loguru`, запись в `./logs/rag_builder.log`.

## Конфигурация (env)
Смотри `.env.example`.
Ключевые переменные:
- `APP_PORT`
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DATABASE_URL`
- `LOG_LEVEL`, `LOG_DIR`, `LOG_FILE`
- `EMBEDDING_API_URL`, `EMBEDDING_MODEL`, `EMBEDDING_TIMEOUT`
- `EMBEDDING_DIM`, `VECTOR_DIMENSION`
- `CHUNK_SIZE`, `CHUNK_MAX_TOKENS`, `MAX_TOKENS`

## Пример OpenAI-Compatible Endpoint
Для OpenAI API:

- `Authorization: Bearer OPENAI_API_KEY`
- `URL: https://api.openai.com/v1/embeddings`

## Локальный запуск (без Docker)
1. Установить Python 3.13.
2. Установить зависимости:
```powershell
py -3.13 -m pip install -e .[dev]
```
3. Запустить API:
```powershell
py -3.13 -m uvicorn rag_builder.main:app --host 0.0.0.0 --port 8090
```
4. Проверить OpenAPI:
- `http://127.0.0.1:8090/openapi.json`

## Логи
- Папка логов: `./logs`
- Файл: `logs/rag_builder.log`
- В логах есть request id, correlation id, шаги пайплайна и исключения.
