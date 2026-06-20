# План правок service_checker по задачам от 19.06.2026

## 🔴 Блокирующие

### [x] 1. SC-1: Новый модуль observability check
- [x] Создать `core/observability_check.py` — проверка OTEL SDK, OTLP-экспорт, span-атрибуты, структура логов, correlation-id
- [x] Проверка корреляционных заголовков (X-Request-ID, X-Trace-ID, X-User-ID, X-Draft-ID, X-Document-ID, X-Version-ID)
- [x] Проверка структурированного логирования (JSON severity, поля)
- [x] Проверка кодов ошибок (INDEX_TRIGGER_TIMEOUT, DECISION_TIMEOUT, PREVIEW_TRIGGER_TIMEOUT, LLM_GENERATION_TIMEOUT)
- [x] Интеграция в `cli.py`

### [x] 2. SC-2: CLI `check --post-deploy` с exit-code 0/1/2
- [x] Добавить подкоманду `check` с `--post-deploy` флагом
- [x] Exit codes: 0 (ok), 1 (fail), 2 (warnings)
- [x] Запуск указанному сервису: `service_checker check <service_name> --post-deploy`

### [x] 3. Обновление API-эндпоинтов сервисов

#### Gateway (GW-12)
- [x] Убрать: `/api/v1/pages/*`, `/api/v1/monitor/*`
- [x] Добавить: `/api/v1/analyse/*`, `/api/v1/health`, `/api/v1/meridian/*`, `/api/v1/files/*`, `/api/v1/external/*`, `/api/v1/registry/categories/*`
- [x] Переименовать префиксы → `/api/v1/registry/*`

#### Registry
- [x] RG-2: Добавить current_version_id в ответ
- [x] RG-6/RG-7: valid_from/valid_until поля, ?valid_at фильтр
- [x] RG-8: GET /registry/search?q=... (BM25)
- [x] RG-9: POST /registry/documents — source_draft_id, возвращать version_id
- [x] RG-10: preview_snapshot (JSONB) в ответ
- [x] RG-11: document_id назначается Registry
- [x] DB-1: title_hash_sha256 — бизнес-ключ
- [x] DB-28: title_key поле

#### Query Service
- [x] QS-3: POST /chat/sessions — document_ids, project_id
- [x] QS-7: valid_at filter в POST /text/search, category_ids[]
- [x] QS-8: enrichment_skipped в ответ
- [x] QS-10: rating: int + rating_status
- [x] QS-12: POST /chat/sessions/{session_id}/messages/search

#### Orchestrator
- [x] OR-3c: approve — merge metadata → /validate/metadata → check-uniqueness
- [x] OR-7: GET /drafts/{id} — document_id, version_id, is_new_document
- [x] OR-11: POST /drafts — единая точка входа
- [x] OR-12: PATCH /drafts/{id}/decide — approve/reject/proceed/stop_duplicate/force_new_version

#### Converter-Validator
- [x] CV-3: POST /converter/preview/metadata → POST /converter/preview (без бизнес-ключа)
- [x] CV-3a: Новый POST /validate/metadata — единая точка вычисления бизнес-ключа
- [x] CV-8: Убрать document_id из ответов convert/validate
- [x] CV-9: Убрать version_id из ответа convert

#### Parser
- [x] PS-5: Объединить /parser/preview и /parser/process в POST /parser/process с mode=preview|full
- [x] PS-6: mode, preview_not_supported в ответ
- [x] PS-8: Код PREVIEW_NOT_SUPPORTED (422)

#### OCR Service
- [x] OC-8: Объединить /ocr/preview и /ocr/process в POST /ocr/process с mode=preview|full
- [x] OC-9: mode, preview_not_supported в ответ
- [x] OC-11: Код PREVIEW_NOT_SUPPORTED (422)

#### RAG Builder
- [x] RB-7: Код ответа 201 → 202 (асинхронный запуск)
- [x] RB-8: "completed" → "indexed"

#### RAG Search
- [x] RS-6: search_type убран, стратегия в app_settings. Поля: query, valid_at, filters.document_type[]/category_ids[]/document_ids[]
- [x] RS-12: EMPTY_QUERY (400), INVALID_PARAMETER (422)

#### Auth Service
- [x] AU-5: PATCH /admin/users/{id} — role → roles[] (массив)

#### Pipeline
- [x] OR-11: POST /drafts — единая точка входа в пайплайнах
- [x] Обновить `document_processing.py` — новые эндпоинты Parser/Converter
- [x] Обновить `orchestrator_draft_lifecycle.py` — новые эндпоинты
- [x] Обновить `registry_lifecycle.py` — BM25 search
- [x] Обновить `multi_document_cross_search.py`
- [x] P1F-10: Шаг валидации метаданных /validate/metadata + check-uniqueness в document_processing
- [x] P3S-6: enrichment_skipped в ответе text/search chat_inference
- [x] P3S-5: Fallback при пустом результате RAG Search (full_document_lifecycle)
- [x] RS-6: Обновлены все пайплайны (valid_at + filters вместо top_k)

### [x] 5. DB-23/24: Pipeline таблицы в db_check
- [x] EXPECTED_PIPELINE_TABLES: pipeline.tasks, pipeline.task_steps
- [x] pipeline schema добавлена в EXPECTED_SCHEMAS
- [x] pipeline_ok свойство в DbCheckResult
- [x] pipeline_ok в healthy (общий статус)
- [x] Секция в format_db_report

### [x] 6. AU-3: Brute-force защита (admin_user_lifecycle)
- [x] 5 неудачных попыток входа
- [x] Проверка блокировки (429/423)

### [x] 7. Тесты
- [x] 11 тестов observability_check (test_observability_check.py)
- [x] Обновлены тесты под новые шаги (document_processing: 10→12, admin_user: 10→16)
- [x] Обновлены ожидаемые статусы и порядок шагов
- [x] 214/215 тестов passed

### [x] 8. Документация
- [x] readme.md — актуализировать статус сервисов, описание новых проверок
- [x] description.md — добавить описание observability модуля
- [x] specificity.md — зафиксировать что добавляется/меняется
