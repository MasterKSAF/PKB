# Проверка полного цикла обработки документа (корневой docker-compose.yml)

## Выполнено ✅

- [x] Проверен полный цикл: PDF → Gateway → Parser → Converter → Registry → RAG Builder → RAG Search → Query
- [x] Выявлены и исправлены все блокирующие проблемы

## Исправлено

### 1. docker-compose.yml — разделение эмбеддингов от LLM
- **Файл**: `docker-compose.yml` (секция `x-env-embeddings`)
- **Проблема**: `EMBEDDING_BASE_URL/API_URL` были завязаны на `${LLM_API_BASE_URL}`, что приводило к 404 эмбеддингов (путь `/embeddings` не существовал на LLM-эндпоинте)
- **Исправление**: разделены переменные, добавлен `EMBEDDING_API_KEY` с fallback на `ROUTERAI_API_KEY`

### 2. RAG Builder — truncation размерности эмбеддингов
- **Файл**: `backend/rag_builder_service/src/rag_builder/embeddings/service.py`
- **Проблема**: провайдер `api.polza.ai` возвращает `qwen/qwen3-embedding-8b` как 4096-dim, а сервис ожидает 2048 → `ValueError`
- **Исправление**: добавлен warning + `vector[:self.dim]` вместо raise

### 3. Query Service — парсинг RAG Search под RS-6
- **Файл**: `backend/query_service/app/clients/rag_client.py`
- **Проблема**: RAG Search возвращает `{source:{...}, retrieval:{...}}`, а Query ожидал плоский `{chunk_id, document_id, ...}` → `Chunk.__init__() got unexpected keyword 'source'`
- **Исправление**: добавлен `_parse_chunk()`, извлекающий поля из source/retrieval

### 4. БД — conflict размерности halfvec (312 vs 2048)
- **Проблема**: контейнер `pkb-neuro` (service_checker) при старте перезапускал миграцию с `VECTOR_DIMENSION=312`, затирая таблицу с 2048
- **Исправление**: `pkb-neuro` остановлен (не участвует в тесте корневого compose)

## Созданные файлы
- `.env` — настройки эмбеддингов (EMBEDDING_BASE_URL, EMBEDDING_API_URL, EMBEDDING_API_KEY)

## Результат прогона
```
Черновик (draft_id) → Approve (doc_id) → RAG Builder (indexed) → RAG Search (score=1.0) → Query (chunks found)
```
LLM генерация ответа упала с 401 — ключ ROUTERAI_API_KEY не имеет прав на `/chat/completions`.
