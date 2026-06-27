# Тесты Pipeline Orchestrator Details

## Статус: ВЫПОЛНЕНО

## Файлы и пункты

### 1. test_drafts_boundaries.py — POST /drafts граничные сценарии
- [x] Неподдерживаемый MIME → 400 BAD_REQUEST
- [x] Поддерживаемые MIME (pdf, png) → 202
- [x] Пустой файл → 422 EMPTY_FILE
- [x] Ответ содержит is_duplicate_file/is_duplicate_document
- [x] title_hash_sha256 и title_key при наличии title
- [x] title_hash_sha256 = null без title

### 2. test_preview_state_validation.py — POST /preview state validation
- [x] Повторный preview с running step → 409 PREVIEW_ALREADY_RUNNING
- [x] Несуществующий черновик → 404 NOT_FOUND
- [x] Нет задачи → 404 NOT_FOUND
- [x] Статус previewing/ready_for_approve/discarded/approved в Registry → 409 CONFLICT

### 3. test_quality_auto_approve.py — Quality / Auto-approve
- [x] Partial preview (preview_not_supported=False) → ready_for_approve
- [x] Full preview + auto-approve условия → approve
- [x] Critical notifications блокируют auto-approve
- [x] Отсутствуют doc_code/title → ready_for_approve
- [x] Converter validation failure (OCR, не Parser) → review_required

### 4. test_decide_edge_cases.py — PATCH /decide edge cases
- [x] reject на completed/failed → 409 TASK_ALREADY_TERMINAL
- [x] stop_duplicate на completed/failed → 409 TASK_ALREADY_TERMINAL
- [x] stop_duplicate вне preview/decision → 409 INVALID_STAGE
- [x] stop_duplicate для preview/decision → 200
- [x] approve с metadata_overrides → document_id в ответе
- [x] proceed (internal) → 200 + action=proceed
- [x] force_new_version → 200 + is_new_document=False

### 5. test_race_conditions.py — Check-uniqueness / Duplicates
- [x] stop_duplicate → task=FAILED, draft=DISCARDED
- [x] Registry.create_document ошибка → ValueError
- [x] Registry.create_document без document_id → ValueError

### 6. test_metadata_patch.py — PATCH /metadata
- [x] Норма → 200
- [x] Пустые поля → no-op
- [x] Невалидный source_type (зависит от Registry mock)
- [x] Несуществующий черновик → не 500

### 7. test_delete_draft.py — DELETE /drafts
- [x] Удаление существующего → 204
- [x] Повторное удаление → 204/404
- [x] Несуществующий → 404
- [x] Разные статусы (uploaded/previewing/ready_for_approve/discarded/approved) → 204

### 8. test_full_phase_errors.py — Full-phase error handling
- [x] on_step_failed для completed задачи → guard (no-op)
- [x] on_step_failed retry → новый pending step
- [x] Parser→OCR fallback на full-фазе
- [x] Registry шаг failure → retry

### 9. test_pipeline2_orchestrator.py — Pipeline 2 (Индексация)
- [x] rag_index completion → pipeline completed
- [x] Reprocess mode=reindex → 202
- [x] Reprocess mode=chunking_only → 202
- [x] GET /tasks с pipeline_type=indexation

### Итог
- **9 новых файлов, 51 новый тест** (сверх существующих)
- **157 passed** в tests/orchestrator/
- **543 passed, 3 failed** в tests/ (3 failed — предсуществующая проблема в test_service_clients_rag.py, не связана с изменениями)
