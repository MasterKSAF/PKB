# Todo — Синхронизация mock-сервисов с пулом задач (19.06)

## Приоритет
1. Gateway (routing, Idempotency)
2. Orchestrator (draft-first, document_id Registry, uploaded→created)
3. Registry (valid_from/until, search, snapshot)
4. Auth (brute force, password policy)
5. Query (rating int, clean message_count, [source:N])
6. Common seed (title_key, udc→udk_code, uploaded→created)

## Выполнено ✅

### 1. Common — seed-данные
- [x] DB-11: uploaded_by → created_by (SEED_DOCUMENTS, версии, все упоминания)
- [x] DB-28: title_key в SEED_REGISTRY_DOCUMENTS
- [x] DB-27: udc → udk_code в metadata (seed-данные + orch_routes)

### 2. Gateway — routing & Idempotency
- [x] GW-13: убрать "checks" из available_tabs seed-пользователей

### 3. Orchestrator — draft-first
- [x] OR-11: POST /documents → 410 Gone, только POST /drafts как точка входа
- [x] OR-2: 409 при повторном POST /drafts/{id}/preview
- [x] OR-4: uploaded_by → created_by
- [x] OR-7: document_id, version_id, is_new_document в GET /drafts/{id}
- [x] OR-9: preview_metadata 8+ полей (doc_code, title, document_type, source_type, era, jurisdiction, issuing_body, year, revision, mks_oks_code, okstu_code)

### 4. Тесты
- [x] Тесты обновлены под draft-first (test_api.py, test_extended.py, test_tz_coverage.py)
- [x] 502 теста проходят

## Осталось ❌

### 2. Gateway
- [ ] GW-3: CORS demo/prod split + CI-check
- [ ] GW-4: Rate limiting (Nginx)
- [ ] GW-8: Архитектура mock-режима (документ)
- [ ] GW-11: Idempotency-Key /documents* → /drafts*

### 3. Orchestrator
- [ ] OR-3: metadata_overrides в decide
- [ ] OR-6: pipeline.draft_notifications
- [ ] OR-13: document_id от Registry (не Orch)
- [ ] OR-14: MIME branching OCR/Parser

### 4. Registry
- [ ] RG-1: PATCH /registry/documents/{id}/status internal
- [ ] RG-2: current_version_id в ответ
- [ ] RG-5: PATCH разделение полей
- [ ] RG-6: valid_from/valid_until поля
- [ ] RG-7: ?valid_at фильтр
- [ ] RG-8: поиск (mock-BM25)
- [ ] RG-9: source_draft_id, return version_id
- [ ] RG-10: preview_snapshot
- [ ] RG-11: document_id назначается Registry
- [ ] RG-12: RBAC для search

### 5. Auth
- [ ] AU-3: 5 неудачных → 30 мин блокировка
- [ ] AU-4: пароль ≥ 8
- [ ] AU-6: маскировка паролей в логах

### 6. Query
- [ ] QS-3: document_ids, project_id, options
- [ ] QS-6: valid_at, category_ids в /text/search
- [ ] QS-8: [source:N] → machine-readable
- [ ] QS-9: rating int + rating_status + confidence
- [ ] QS-10: engineer → свои сессии
- [ ] QS-11: удалить message_count/session_count

### 7. Тесты
- [ ] T-5: draft_id propagation (400/404/valid)
- [ ] T-7: draft → document → version
- [ ] T-11: корреляционные заголовки
