# Testing README

## Цель
Проверка корректности RAG Builder Service на всех уровнях.

## Уровни тестов

### Unit-тесты (без БД)
**93 теста**, запуск без внешних зависимостей:
```powershell
python -m pytest tests/unit/ -v
```

Покрывают:
- **Контракты** (`test_contracts.py`): 45 тестов — валидация document_id, section_id, parent_id, page, response models
- **Chunking** (`test_chunking.py`, `test_chunking_full.py`): 28 тестов — все типы секций (text, table, list, image, formula, textBlock, headerFooter), protected spans, граничные случаи
- **Embeddings** (`test_embeddings.py`, `test_embeddings_openai.py`): 5 тестов — детерминизм, размерность, retry, batching, ошибки
- **IndexingService** (`test_indexing_service.py`): 14 тестов — build/delete/status с mocked DB
- **API контракт** (`test_api_contract.py`): 3 теста — OpenAPI shape, payload validation

### Integration-тесты (нужен Docker)
**8 тестов**, требуют PostgreSQL 16 + pgvector на `localhost:5433`:
```powershell
docker compose up -d postgres
python -m pytest tests/integration/ -v
```

Покрывают:
- **DB flow** (`test_db_flow.py`): вставка/удаление чанков
- **Vector flow** (`test_vector_flow.py`): размерность 2048, roundtrip, cosine similarity, indexing_txn_id, chunk indices, delete

### E2E-тесты (нужен Docker)
**2 теста**, требуют полный стек:
```powershell
python -m pytest tests/e2e/ -v
```

Покрывают:
- **Smoke API** (`test_smoke_api.py`): build → status → delete через HTTP, health endpoint

## Быстрый запуск
```powershell
# Только unit (без БД)
python -m pytest tests/unit/

# Всё (с Docker)
docker compose up -d postgres
python -m pytest
```

## Покрытие (текущее)
- Unit: 93 теста, 0 failures
- Integration + E2E: 10 тестов (нужен Docker с pgvector)
- Порог покрытия: 80% (через pytest-cov)
