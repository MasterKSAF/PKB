# Fix: Duplicate Detection + Registry Sections + bbox

## D1 — Детекция дублей не работает
- [x] 1.1 Добавить `file_hash_sha256` в `CheckUniquenessRequest` schema
- [x] 1.2 Обновить `check_uniqueness()` — принимать и передавать `file_hash_sha256`
- [x] 1.3 Обновить `create_draft` endpoint — передавать `file_hash_sha256` в вызов
- [x] 1.4 Исправить `_mock_check_uniqueness` — проверять `file_hash_sha256` среди Drafts+Documents для `is_duplicate_file`
- [x] 1.5 Убрать хардкод `is_duplicate_file: False` из `_mock_check_uniqueness`

## R5 — Секции не сохраняются в Registry
- [x] 2.1 В `run_registry_step`: при 409 (already_approved) — пробовать читать секции через `get_document_sections`
- [x] 2.2 В `run_registry_step`: при отсутствии `document_data` — пробовать читать секции из Registry (вынесено из `if document_data:`)

## S1 — bbox строка вместо списка (HTTP 500 в Search)
- [x] 3.1 В `run_parser_full_step`: нормализовать `bbox` из строки в список `[x1,y1,x2,y2]`
      через `_normalize_bbox()` (str → list, str с `;` → list, tuple → list, None → None)

## Проверки
- [x] 4.1 Прогнать тесты — 688 passed, 2 skipped, 1 xfailed
- [x] 4.2 Финальный обзор правок — все изменения корректны, целостность соблюдена
