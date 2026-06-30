# Todo: Исправление замечаний 5.1-5.3

## 5.1 Preview status — processing вечно
- [x] Прочитать код
- [x] `get_preview_status`: дедуплицировать ранний return
- [x] Тест: `test_preview_status_duplicate_steps_returns_correctly`

## 5.2 PATCH /metadata — не сохраняется
### Шаги 1-4 (Orchestrator)
- [x] `patch_draft_metadata`: изменить сигнатуру — Pydantic-схема, Optional preview_metadata
- [x] `registry_client.update_draft_metadata`: сделать preview_metadata Optional, исключать из body если None
- [x] `_mock_update_draft_metadata`: обрабатывать preview_metadata=None (skip merge)
### Шаг 5
- [x] `_build_preview_status`: применить metadata_overrides из Registry
### Тесты
- [x] `test_patch_metadata_merge` — PATCH с одним полем, другие сохранились
- [x] `test_patch_metadata_empty_body_noop` — пустое тело, metadata не меняется
- [x] `test_patch_metadata_overrides_stored` — PATCH metadata_overrides → проверка хранения

## 5.3 PATCH /decide — approve при processing
- [x] `decide_draft`: добавить проверку preview-шагов перед approve/proceed/force_new_version
- [x] Тест: `test_approve_blocks_on_running_preview` (running → 409, pending → 409, completed → 200)
- [x] Тест: `test_proceed_while_preview_running_returns_409`
- [x] Адаптированы существующие тесты (state machine, consistency, integration)

## Финальная проверка
- [x] Прогнать тесты orchestrator_service — **567 passed, 0 failed**
- [x] Зафиксировать аномалии в specificity.md
- [x] Финальный обзор правок
