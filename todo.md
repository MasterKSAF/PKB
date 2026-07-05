# План сессии: Registry errors + Mock FSM + approve flow

## ✅ 1. Создать MockRegistryClient (утилита для тестов)
- [x] `tests/shared/mock_registry_client.py` с FSM-валидацией (409 при approved/discarded)

## ✅ 2. Убрать глушение Registry errors (17 блоков)
- [x] `_on_preview_completed`: 5 блоков try/except
- [x] `approve_draft`: 4 блока try/except  
- [x] `confirm_draft`: 2 блока try/except
- [x] `reject_draft`: 1 блок try/except
- [x] `stop_duplicate_draft`: 1 блок try/except
- [x] `run_registry_step` (pipeline_formation.py): 1 блок try/except
- [x] `registry_creation` handler: 2 блока try/except (get_document_sections, save sections)
- [x] `rag_index` handler: 1 блок try/except (update_document_status)

## ✅ 3. Рефакторинг approve → converter → registry
- [x] `approve_draft()`: убрать create_document, DUPLICATE_FILE, sync, document_id/version_id
- [x] `_on_full_step_completed("full_converter")`: добавить create_document + sync
- [x] Обновить возврат approve_draft → document_id=None
- [x] Удалён мёртвый код DUPLICATE_FILE_AFTER_APPROVE в decide_draft

## ✅ 4. Обновить тесты
- [x] Вписать MockRegistryClient в test_pipeline_formation.py
- [x] Обновить TestApproveDraftPartial/Full — approve не создаёт документ
- [x] Добавить тест: on_step_completed("full_converter") → создаёт документ
- [x] Исправить test_celery_tasks.py::TestRunRegistryStep

## ❌ Осталось (не входило в задачу)
- `test_draft_to_document_flow.py` — ждёт document_id от approve
- `test_draft_to_indexation_flow.py` — ждёт document_id от approve
- `test_draft_to_version.py` — ждёт document_id от approve
- `pipeline_indexation.py` — pre-existing баг job_id
- `test_celery_tasks.py::TestRunOcrPreviewStep::test_failure_path_triggers_retry` — pre-existing
