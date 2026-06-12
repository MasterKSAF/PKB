# TODO.md

## Контракт контейнера

### Высокий приоритет

- [ ] Добавить обработку диапазонов ГОСТов
      ГОСТ 20862-81 – ГОСТ 20867-81

- [ ] Определить окончательный формат references

- [ ] Уточнить необходимость document_version_id внутри section

### Средний приоритет

- [ ] Зафиксировать формат bbox

- [ ] Добавить тесты для ссылок на внешние документы

### Низкий приоритет

- [ ] Проверить необходимость headerFooter в индексе

- Проверить, нужен ли path вообще.
Возможно section_id + parent_id достаточно.

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