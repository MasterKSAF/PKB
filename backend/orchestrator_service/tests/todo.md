# Обновление тестовых ассертов после изменений в production-коде

## Изменения:

1. **TASK_ALREADY_TERMINAL → DRAFT_ALREADY_DECIDED** (decide_draft)
2. **PREVIEW_ALREADY_RUNNING → PREVIEW_IN_PROGRESS** (start_preview)
3. **BAD_REQUEST (400) → UNSUPPORTED_FILE_TYPE (422)** (create_draft, unsupported MIME)

## Файлы:

- [x] `tests/orchestrator/test_decide_edge_cases.py` — TASK_ALREADY_TERMINAL → DRAFT_ALREADY_DECIDED
- [x] `tests/orchestrator/test_preview_state_validation.py` — PREVIEW_ALREADY_RUNNING → PREVIEW_IN_PROGRESS
- [x] `tests/orchestrator/test_drafts_boundaries.py` — BAD_REQUEST(400) → UNSUPPORTED_FILE_TYPE(422)
- [x] `tests/orchestrator/test_drafts_state_machine.py` — TASK_ALREADY_TERMINAL → DRAFT_ALREADY_DECIDED
- [x] `tests/orchestrator/test_drafts_consistency.py` — PREVIEW_ALREADY_RUNNING → PREVIEW_IN_PROGRESS
- [x] `tests/test_drafts.py` — 400 → 422 for unsupported MIME
- [x] `tests/test_error_handling.py` — BAD_REQUEST(400) → UNSUPPORTED_FILE_TYPE(422)

- [x] Финальная проверка: перепросмотр всех правок, оценка целостности

## Результат

Все изменения выполнены. Оставшиеся `BAD_REQUEST` в `test_error_handling.py` (test_get_status_all_codes, test_api_exception_default_message, test_error_response_with_details) — это тесты общей схемы ошибок APIException, не endpoint-specific, их изменения не требуется.
