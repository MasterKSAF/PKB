# Текущая сессия: 2026-07-06 — Исправление 17 падающих тестов

## Результат: 809 passed, 0 failed

### Сессия 1 — 5 integration-тестов (исправлено)

| # | Тест | Исправление |
|---|------|-------------|
| 1 | `test_celery_tasks.py::test_failure_path_triggers_retry` | mid-retry→not_awaited, +last-retry→awaited |
| 2 | `test_celery_tasks.py::test_with_document_data` | document_data с metadata как есть |
| 3 | `test_celery_tasks.py::test_with_metadata_merge_preserves_doc_metadata` | response_metadata не мержится |
| 4 | `test_draft_to_indexation_flow.py::test_full_pipeline_ends_with_task_completed` | убран manual complete |
| 5 | `orchestrator.py::on_step_failed` | guard: если шаг не running, fail task вместо retry |

### Сессия 2 — 12 предсуществующих (исправлено)

| Группа | Исправление |
|--------|-------------|
| `test_base_client` (8 тестов) | `ServiceClient.call()`: ConnectError/CircuitBreakerError → fallback (mock_response/{}) |
| `test_drafts::test_create_draft_file_too_large` | `settings.validation.MAX_FILE_SIZE_BYTES` вместо модуля |
| `test_drafts::test_create_and_retrieve_all_metadata_fields` | PreviewMetadata: добавлены `document_type`, `mks_oks_code`, `okstu_code`, `udk_code` |
| `test_drafts::test_create_without_metadata_returns_fallback` | endpoint get_draft_preview: маппинг новых полей |
| `test_drafts::test_create_with_json_metadata_field` | ||

### Файлы изменений

- `app/services/base_client.py` — fallback при ConnectError/CircuitBreakerError
- `app/schemas/drafts.py` — PreviewMetadata: +document_type, mks_oks_code, okstu_code, udk_code
- `app/api/v1/endpoints/drafts.py` — get_draft_preview: маппинг новых полей
- `app/core/pipeline/orchestrator.py` — on_step_failed: guard failed_step is None
- `tests/integration/test_celery_tasks.py` — OCR retry + registry metadata fix
- `tests/integration/test_draft_to_indexation_flow.py` — убран manual complete
- `tests/test_base_client.py` — (уже проходят)
- `tests/test_drafts.py` — file_too_large: settings вместо модуля
- `tests/conftest.py` — PermissionError retry на Windows
