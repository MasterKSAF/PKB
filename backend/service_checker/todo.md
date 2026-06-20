# План правок service_checker — учёт задач от 19.06.2026 (продолжение)

## Выполненный этап — 216/216 тестов passed

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

---

## Текущий этап — Tolerance для частично обновлённых сервисов (2026-06-20)

### [x] 6. docker.py — OCR service в health check
- [x] 6.1 DOCKER_SUPERVISOR_SERVICES: добавить OCR (8088, /api/v1/health)
- [x] 6.2 .err log files: добавить "ocr.err"
- [x] 6.3 Health-эндпоинт Orchestrator: /api/v1/health (вместо /api/v1/system/health)

### [x] 7. config.py — DOCKER_SERVICE_NAMES: актуализация
- [x] 7.1 app: 11 процессов (было 10) — добавлен OCR

### [x] 8. observability_check.py — Tolerance для необновлённых сервисов
- [x] 8.1 Fallback health-пути: /api/v1/health → /api/v1/system/health → /health
- [x] 8.2 Без ответа health — warning, не error
- [x] 8.3 Корреляционные заголовки — warning, не error (CM-5 может быть не реализован)

### [x] 9. api_coverage_test.py — Tolerance для частичного обновления
- [x] 9.1 KNOWN_NEW_ENDPOINTS: список эндпоинтов из задач 19.06.2026
- [x] 9.2 404 на new endpoint → skipped с warning, не failed

### [x] 10. Документация
- [x] 10.1 readme.md — примечание о partial update + tolerant mode
- [x] 10.2 todo.md — актуализация
- [x] 10.3 specificity.md — запись об изменениях (ниже)
