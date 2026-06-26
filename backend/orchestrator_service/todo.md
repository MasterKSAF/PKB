# Todo: тесты для 3 багов в unit-формате

## Статус: ✅ ВЫПОЛНЕНО

### #18 — Drafts создаются от u-mock-001 вместо реального пользователя
- [x] `test_created_by_uses_mock_user_by_default` — по умолчанию u-mock-001
- [x] `test_created_by_uses_custom_user_id` — dependency override → real-user-42
- [x] `test_created_by_not_fallback_object` — created_by строка, не объект

### #16 — Pipeline task: ошибка длины trace_id
- [x] `test_generate_trace_id_is_16_hex_chars` — формат 16 hex
- [x] `test_generate_trace_id_is_unique` — 100 вызовов без коллизий
- [x] `test_trace_id_fits_in_db_column` — 16 и 36 символов влезают в String(64)
- [x] `test_trace_id_stored_in_task_model` — конструктор Task принимает любую длину
- [x] `test_set_trace_id_accepts_uuid_length` — set_trace_id с 36-символьным UUID
- [x] `test_build_headers_with_uuid_length_trace` — build_correlation_headers c UUID

### #15 — Upload draft: 500 ошибка, но draft появляется в списке
- [x] `test_pipeline_failure_orphans_draft_in_registry` — start_pipeline падает → 500 → draft в Registry есть

### #2 — celery-worker unhealthy — ❌ не unit-тест (требует production-кода healthcheck'а Celery)
### #19 — нет e2e документа — ❌ не unit-тест (требует cross-service инфраструктуры)

**Итог: 373 passed (+10 новых, 0 сломанных)**
