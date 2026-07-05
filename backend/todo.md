# Todo на сессию — ✅ ВЫПОЛНЕНО

## Phase 1: Исправить 4 integration-теста
- ✅ 1a. test_draft_to_document_flow.py — assert'ы approve → None
- ✅ 1b. test_draft_to_version.py — assert'ы approve → None
- ✅ 1c. test_draft_to_indexation_flow.py — перестроен под новый flow (Registry mock в full_converter + registry_creation)

## Phase 2: DUPLICATE_FILE — мёртвый код уже удалён ранее

## Phase 3: try/except в _on_full_step_completed — уже удалены ранее

## Phase 4: conftest.py / gateway mocks — корректны, правки не требуются

## Phase 5: MockRegistryClient
- ✅ delete_draft
- ✅ check_uniqueness

## Phase 6: Pre-existing bugs
- ✅ 6a. pipeline_indexation.py — job_id (добавлен параметр, обновлён caller + тесты)
- ⏸️ 6b. test_celery_tasks OCR failure — pre-existing, не запрошено
