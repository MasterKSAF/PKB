# Сессия: проверка pdf_check + фикс дублей file_hash_sha256

## Сделано
- [x] `data/tests/config.py` — `cleanup_enabled()` через `TEST_CLEANUP`, обратная совместимость с `TEST_SKIP_REBUILD`
- [x] `data/tests/test_pdf_tests_full.py` — параметризуемая директория (pdf_check/pdf_tests/pdf), auto-approve
- [x] **Фикс дублей**: orchestrator `create_draft` → сохраняет `file_hash_sha256` в `metadata_fields`
- [x] **Фикс дублей**: orchestrator `approve_draft` → передаёт `file_hash_sha256` в `doc_payload`
- [x] **Фикс дублей**: registry_service → модель Draft + CRUD + endpoint сохраняют `file_hash_sha256`, колонки добавлены в БД
- [x] `data/tests/test_file_hash_dedup.py` — E2E тест: file_hash_sha256 propagation + dedup
- [x] `specificity.md` — D1 обновлён

## Результаты тестов
- `test_file_hash_dedup.py`: **6/9 PASS** — file_hash сохранён, дубли блокируются (409). 3 fail — очередь забита (16 queued), не баг фикса
- `test_pdf_tests_full.py data/pdf_check`: 20/20 upload + auto-approve, pipeline частично (8/20 registry)

## Причина дублей (исправлена)
1. `approve_draft` не передавал `file_hash_sha256` в `doc_payload` → `registry.documents.file_hash_sha256 = NULL`
2. PostgreSQL UNIQUE constraint на NULL не срабатывает → каждый approve создаёт новый document
3. В `registry.drafts` не было колонки `file_hash_sha256` — хэш терялся
