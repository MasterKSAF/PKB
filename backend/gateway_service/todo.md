# Todo — Доработка моков: API, структуры данных, логика

## Выполнено ✅

### 1. Auth Service (4 задачи)
- [x] AU-3: Брутфорс-защита (failed_attempts, locked_until, блокировка 30 мин, сброс при успехе)
- [x] AU-4: Парольная политика (длина ≥ 8 символов)
- [x] AU-5: PATCH /admin/users/{id}: приоритет roles[] над role
- [x] AU-6: Маскировка PII в audit-логах (IP → xxx.xxx.xxx.xxx)

### 2. Orchestrator (2 задачи)
- [x] OR-3: metadata_overrides в DecideRequest + применение при approve
- [x] OR-6: has_notifications, critical_count, notifications[] в GET /drafts/{id}

### 3. Query Service (4 задачи)
- [x] QS-6: valid_at (date) + filters.category_ids[] в POST /text/search
- [x] QS-9: confidence в sources[] (mapped from score)
- [x] QS-10: engineer → только свои сессии при DELETE
- [x] QS-11: Удалён message_count из ответов create_session, list_sessions, send_message

### 4. Registry Service (7 задач)
- [x] RG-2: current_version_id в ответах GET /documents и GET /documents/{id}
- [x] RG-5: PATCH /registry/documents/{id} с разделением editable/immutable
- [x] RG-6: valid_from, valid_until в RegistryDocCreate, RegistryDocUpdate, seed
- [x] RG-7: ?valid_at фильтр в GET /registry/documents
- [x] RG-8: GET /registry/search?q= (поиск по title + doc_code)
- [x] RG-9: source_draft_id в POST /documents + version_id в ответе
- [x] RG-10: preview_snapshot (JSONB, nullable) в GET /documents/{id}

### Статус тестов
- **529 passed, 1 skipped**
