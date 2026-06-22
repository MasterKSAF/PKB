# Исправить Parser: создать черновик в Registry перед вызовом

## Проблема
Checker шлёт Parser'у `draft_id: 1` (хардкод), но в чистой БД Registry не содержит черновиков. Parser не может записать статус → 422.

## План
- [x] 1. `core/api_coverage_test.py` — pre-prepare для Parser: создать документ в Registry → draft_id
- [x] 2. `services/parser.py` — заменить хардкод `draft_id: 1` на `draft_id: "{draft_id}"`, mode=preview→full, убрать `preview_not_supported` из response_schema
- [x] 3. Проверка: Parser 5/5 — 0 failed
