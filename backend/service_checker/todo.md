# План правок service_checker — учёт задач от 19.06.2026

## Всё выполнено — 216/216 тестов passed

### [x] 1. db_check.py — новые таблицы, схемы, UNIQUE-индексы
- DB-19/20/21: registry.drafts, registry.classifier_registry, registry.categories, registry.document_categories
- DB-29: схема auth + auth.users
- OR-6: pipeline.draft_notifications
- DB-4/P1F-1: EXPECTED_UNIQUE_INDEXES (6 индексов) + SQL-проверка

### [x] 2. services/*.py — эндпоинты и поля
- PS-3: draft_id в Parser
- OC-4: draft_id в OCR
- OR-1: GET /tasks/, GET /health в Orchestrator
- OR-3b: PATCH /drafts/{id}/metadata
- OR-14: MIME-ветвление в POST /drafts/

### [x] 3. observability_check.py — усиление
- GW-9: X-User-ID, X-Trace-ID
- health_endpoint_exists
- PREVIEW_NOT_SUPPORTED, EMPTY_QUERY, INVALID_PARAMETER

### [x] 4. pipelines — новые шаги
- OR-13: document_id + Registry check после approve
- OR-14: image/png черновик (MIME-ветвление)
- QS-8: enrichment_skipped
- CV-4/P1F-4: preview_snapshot

### [x] 5. RAG Builder
- P2I-1: /{doc_id}/integrity (частичная индексация)
- P2I-9: /{doc_id}/reprocess (переиндексация)
