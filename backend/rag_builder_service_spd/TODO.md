# TODO.md

## Контракт контейнера

### Высокий приоритет


- [ ] Определить окончательный формат references

- [ ] Добавить обработку диапазонов ГОСТов ГОСТ 20862-81 – ГОСТ 20867-81

- [ ] Подтвердить, что document_version_id хранится только на уровне Chunk

### Средний приоритет

- [ ] Зафиксировать формат bbox

- [ ] Добавить тесты для ссылок на внешние документы

- Проверить, нужен ли path вообще. Возможно section_id + parent_id достаточно.

### Низкий приоритет

- [ ] Проверить необходимость headerFooter в индексе

- # TODO:
# поддержать разбиение секции на несколько чанков

# MVP-0

- [x] Контракт контейнера
- [x] Domain Model
- [x] Chunking Service
- [x] Embedding Service (stub)
- [x] Unit tests

Текущее покрытие:
- test_contracts.py
- test_chunking.py
- test_embeddings.py

# MVP-1 completed

[x] BuildRequest
[x] Chunk
[x] ChunkingService
[x] EmbeddingService (stub)
[x] IndexingService
[x] Unit tests
[x] Example container

# MVP-2 completed

[x] PostgreSQL configuration
[x] PostgreSQL connectivity
[x] Schema initialization
[x] PostgresChunkRepository
[x] Chunk persistence
[x] Integration tests

# MVP-3

[ ] FastAPI application
[ ] POST /index
[ ] Receive BuildRequest JSON
[ ] Call IndexingService
[ ] Save chunks to PostgreSQL
[ ] Return indexing statistics

# MVP-4

- [ ] Dockerfile
- [ ] docker-compose integration
- [ ] Healthcheck endpoint
- [ ] CI/CD readiness
- [ ] Service README

## Out of scope / для RAG Search

- [ ] Read chunks from PostgreSQL
- [ ] Search by document_id
- [ ] Full-text search
- [ ] Vector search (pgvector)
- [ ] Citation DTO
