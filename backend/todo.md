# RAG Builder — результаты

## Тесты: 103/103 ✅

| Уровень | Тестов | Зависимости | Статус |
|---------|--------|-------------|--------|
| Unit | 93 | Нет | ✅ 93 passed |
| Integration | 8 | Docker (pgvector) | ✅ 8 passed |
| E2E | 2 | Docker (pgvector) | ✅ 2 passed |

## Что сделано

### Требования (11/11)
- **RB-4** — `chunk_default_strategy = "semantic_1024"` ✅
- **RB-5** — `embedding_dim = 2048`, `vector_dimension = 2048` ✅
- **RB-6** — провайдер `infinity` (через OpenAI-совместимый протокол) ✅
- **RB-7** — `POST /build` → `202 Accepted` ✅
- **RB-8** — финальный статус `"indexed"` вместо `"completed"` ✅
- **RB-9** — валидаторы: `page ≥ 1`, `section_id` уникальность, `parent_id` существует ✅
- **RB-10** — `errors: list[str]`, `warnings: list[str]` в `BuildResponse` ✅
- **DB-15** — `embedding_dim` — параметр конструктора ✅
- **DB-18** — колонка `indexing_txn_id UUID` + миграция `0004` ✅
- **DB-10** — `document_id` проставляется из `Section` ✅
- **DB-4** — `UNIQUE(section_id, chunk_index)` + миграция `0004` ✅

### Миграции
- `0004` — `indexing_txn_id UUID`, `UNIQUE(section_id, chunk_index)`
- `0005` — приведение `embedding` к `vector(2048)` (без ivfflat — лимит 2000)

### Auth удалён
- service.py, dependencies.py, auth_routes.py, auth-модели, test_auth.py

### Покрытие тестами
- **Chunking**: все 7 типов секций (text, table, list, image, formula, textBlock, headerFooter), protected spans, граничные случаи
- **IndexingService**: build/delete/status с mocked DB
- **Вектора**: размерность 2048, roundtrip, cosine similarity, indexing_txn_id
- **Контракты**: document_id, section_id, parent_id, page, response models
