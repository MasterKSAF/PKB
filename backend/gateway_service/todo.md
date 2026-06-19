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

### 5. Rate Limiting + IDOR protection (4 задачи)
- [x] CM-2 / GW-4: Rate limiting middleware (InMemory + Redis backend)
- [x] CM-3 / GW-6: IDOR protection — rate limit по draft_id / document_id / session_id
- [x] docker-compose.yml: сетевая изоляция L2–L4 (GW-1, GW-2, GW-5, CM-4)
- [x] gateway/rate_limiter.py: модуль с InMemoryRateLimiter + RedisRateLimiter + rule matching
- [x] mocks/gateway.py: RateLimitMiddleware синхронизирован с production
- [x] test_rate_limiting.py: 22 теста (общий rate limit, IDOR, unit)

### 6. Mock-структуры: DB-1, DB-2, DB-25, DB-26 (5 задач)
- [x] DB-1: 6-польная формула title_hash_sha256 — функция compute_title_hash_sha256() в common.py
- [x] DB-2: CHECK/ENUM валидация source_type, era, validity_status, jurisdiction, status в RegistryDocCreate/Update
- [x] DB-25: revision, source_filename, file_path, updated_at в document_versions
- [x] DB-26: draft_id FK в registry.documents (seed + модели + хендлеры)
- [x] DB-12: проверено — uploaded_at/uploaded_by не осталось в моках

### Статус тестов
- **530 passed, 1 skipped** (+22 rate limiting, + enum валидация в моках)
