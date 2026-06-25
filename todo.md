# todo: Настройки эмбеддингов, LLM, реранка в корневом docker-compose.yml

## Выполнено
- [x] **x-env-embeddings** — все параметры явно: `PROVIDER`, `BASE_URL`, `API_URL`, `MODEL`, `DIM`, `VECTOR_DIMENSION`, `API_KEY`, `TIMEOUT`, `INSTRUCTION`
- [x] **x-env-rerank** — новый блок с `RERANKER_BASE_URL`, `RERANKER_MODEL`, `RERANKER_TIMEOUT`, `RERANK_TOP_N`
- [x] **tei** — переключён на reranker `BAAI/bge-reranker-v2-m3-int8`, убран `tei-init`
- [x] **rag-builder** — явно: `CHUNK_SIZE`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_RETRIES`
- [x] **rag-search** — явно: `SEARCH_STRATEGY`, `SEARCH_TOP_K`, `CONTEXT_EXPANSION`
- [x] **query** — явно: `LLM_MODEL`, `LLM_API_URL`, `LLM_API_KEY`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TOP_P`, `MOCK_*`
- [x] **converter-validator** — явно: `DEFAULT_LLM_MODEL`, `DEFAULT_LLM_MAX_TOKENS`, `DEFAULT_LLM_TIMEOUT`, `CONFIDENCE_THRESHOLD`
- [x] **app_settings.yaml** — `rerank_url` → `http://tei:80`

## Что осталось / к сведению
- Размерность эмбеддингов 2048 — проверить совместимость схемы БД (pgvector) при миграции
