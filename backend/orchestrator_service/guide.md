# Guide — Архитектурные ориентиры Orchestrator Service

> Создан: 19.06.2026

## Ключевые принципы

### 1. Draft-first архитектура
- **Draft — единственная точка входа.** POST /drafts — первичный эндпоинт для загрузки файлов.
- POST /documents — deprecated, используется только для совместимости.
- Документ не может существовать без черновика.

### 2. Registry — единственный источник правды для drafts/documents
- Оркестратор не хранит данные документов — только pipeline tasks.
- Черновики и документы живут в Registry.
- Orchestrator обращается к Registry через RegistryServiceClient.

### 2.1. Scope эндпоинтов оркестратора (23.06.2026, обновлено)
Оркестратор **проксирует чтение и обновление черновиков** в Registry для обратной совместимости.
Прямое чтение документов (`GET /documents/{id}`, `/pages/*`, `/file`, `/history`, `/parameters`, `/versions`)
— зона Registry, доступная напрямую через Gateway.

В оркестраторе:
- `POST /drafts` — создание черновика (загрузка файла)
- `GET /drafts/{draft_id}` — прокси в Registry (для совместимости с чекером)
- `POST /drafts/{draft_id}/preview`, `GET /drafts/{draft_id}/preview*` — управление preview
- `PATCH /drafts/{draft_id}/decide` — решение по черновику
- `PATCH /drafts/{draft_id}/metadata` — прокси в Registry (для совместимости)
- `DELETE /drafts/{draft_id}` — удаление черновика
- `GET /drafts/{draft_id}/tasks` — задачи черновика
- `POST /documents/{doc_id}/reprocess` — переиндексация (P2I-9)
- `GET /documents/{doc_id}/tasks` — задачи документа
- `GET /tasks*` — мониторинг pipeline-задач
- `/system/health`, `/health/live`, `/health/ready` — health-check

### 3. Двухфазный pipeline
- **Preview фаза:** быстрая обработка первых страниц (Parser → OCR fallback → Converter-validator) → решение пользователя.
- **Full фаза:** полная обработка (Parser → OCR fallback → Converter-validator → Registry → RAG Builder).
- **Parser-first стратегия:** Parser пробуется первым для всех типов файлов (даже image/*).
- **OCR fallback:** при недоступности Parser или `preview_not_supported=true` — автоматический переход на OCR (если `PARSER_FALLBACK_TO_OCR=true` и `OCR_ENABLED=true`).
- `PARSER_ENABLED` / `OCR_ENABLED` — опции полного отключения сервисов.
- Preview_not_supported → fallback на OCR или пропуск full-фазы.

### 4. Task как агрегатор шагов
- Один Task = одна pipeline-задача (formation/indexation).
- TaskStep = шаг выполнения с input/output JSON-контейнерами.
- Шаги исполняются в Celery workers.

### 5. Service-to-service через Docker internal network
- Все внутренние вызовы — через Docker-сеть `internal`.
- Прямой доступ к internal-эндпоинтам только из разрешённых сервисов.
- API Gateway — единая точка входа для внешних запросов.

### 6. Service clients = dual-mode (mock/real)
- Каждый клиент наследует ServiceClient.
- Mock-режим по умолчанию для разработки.
- Валидация данных на границе клиента (JSON serialization guard + Pydantic request_model).

### 7. Трассировка через корреляционные заголовки
- X-Request-ID (UUIDv4) — генерируется Gateway.
- X-Trace-ID — пробрасывается во все downstream.
- X-User-ID — после JWT-валидации.
- X-Draft-ID, X-Document-ID — для контекста запроса.

### 8. Идемпотентность
- POST /drafts — Idempotency-Key (TTL 1ч).
- POST /drafts/{draft_id}/preview — 409 при повторном запуске.
- Task creation — UNIQUE(draft_id, pipeline_type).

### 9. Actions разделены
- **Внешние (UI):** approve, reject, confirm (для review_required).
- **Внутренние:** proceed (продолжить), stop_duplicate (дубликат), force_new_version (новая версия).

### 10. Компенсация через Saga
- При неисправимой ошибке → SagaCoordinator компенсирует выполненные шаги.
- Fallback: DELETE в Registry.

---

## Coverage тестов (27.06)

### Celery-задачи (unit, `tests/unit/test_celery_tasks_all.py`):
- Все 10 pipeline-задач + 2 scheduler + 2 compensation — happy & failure paths
- `run_rag_index_step`: также lock_held, invalid_document_id, integrity_check_fail, build_failed

### API статусов и результатов (integration, `tests/integration/test_tasks_api_extended.py`):
- `GET /tasks/{id}/status` — полная структура, step_data, alias, not_found
- `GET /tasks/{id}/steps` — output_data (результаты), running/converter/empty
- `GET /documents/{doc_id}/tasks` — formation+indexation, empty
- `GET /tasks/{id}` — document_id, version_id, notifications, error_info
- End-to-end: draft → celery → status/results через API

### CRUD черновиков (`tests/orchestrator/test_drafts_crud.py`):
- POST /drafts с пустым файлом → 422
- POST /drafts с некорректным JSON metadata → 422
- GET /drafts/{id} — существующий (seed + created) → 200
- GET /drafts/{id} — несуществующий → 404
- GET /drafts/abc — нечисловой id → 422

### Preview и decision (`tests/orchestrator/test_drafts_preview.py`):
- GET /preview/status — pending (шаги созданы, не завершены)
- GET /preview/status — completed с preview_metadata
- GET /preview/status — failed
- PATCH /decide — reject без comment
- PATCH /decide — невалидный action → 400

### Задачи черновиков (`tests/orchestrator/test_drafts_tasks.py`):
- GET /drafts/{id}/tasks — структура ответа
- GET /tasks/{id} — completed (100%), active (50%), failed
- GET /tasks/{id} — несуществующая → 404

### Pipeline документов (`tests/orchestrator/test_documents_pipeline.py`):
- POST /documents/{id}/reprocess — full mode response structure
- POST /documents/{id}/reprocess — partial (ocr_only)
- POST /documents/{id}/reprocess — несуществующий документ
- GET /documents/{id}/tasks — существующий, несуществующий, структура

### Статусы задач как proxy статусов документов (`tests/orchestrator/test_documents_status.py`):
- GET /tasks/{id} — completed, active (processing), failed — статусы
- GET /tasks/{id} — несуществующий → 404

### Интеграционный тест (`tests/integration/test_draft_to_document_flow.py`):
- Полный цикл: draft → preview → approve → document_id
- Reject flow: upload → reject → discarded

### State Machine Violations (`tests/orchestrator/test_drafts_state_machine.py`, NEW):
- Матрица 5 actions × 6 stages = 30 комбинаций (200 vs 409 INVALID_STAGE)
- 5 actions × 2 terminal статуса = 10 комбинаций (409 TASK_ALREADY_TERMINAL)

### Data consistency + Boundary + Idempotency (`tests/orchestrator/test_drafts_consistency.py`, NEW):
- Approve consistency: document_id, version_id, is_new_document
- Mock-real gap: draft_id=0, ключи id vs draft_id (xfail — найден баг)
- Boundary: file_size=MAX, metadata=null, title=""
- Idempotency: double POST /drafts (не реализована), double POST /preview (409)

### Saga compensation (`tests/unit/test_saga_compensation.py`, NEW):
- `SagaCoordinator.compensate` — registry_creation → delete_document
- Stateless steps not compensated, reverse order, retry before saga
- `_mock_delete_document` — runtime vs seed

### Mock-real gap (`tests/test_service_clients_registry.py::TestRegistryMockRealGap`, NEW):
- `data["id"]=0` is falsy → fallback на `draft_id`
- Расхождение ключей `id` vs `draft_id` в mock vs static response

### Pipeline Orchestrator Details (27.06, 9 файлов, 51 тест)
- `tests/orchestrator/test_drafts_boundaries.py` — MIME, empty, duplicate flags
- `tests/orchestrator/test_preview_state_validation.py` — state validation preview
- `tests/orchestrator/test_quality_auto_approve.py` — quality, auto-approve, review_required
- `tests/orchestrator/test_decide_edge_cases.py` — decide edge cases (terminal, stop_duplicate, proceed, force_new_version)
- `tests/orchestrator/test_race_conditions.py` — stop_duplicate flow, Registry errors
- `tests/orchestrator/test_metadata_patch.py` — PATCH /metadata
- `tests/orchestrator/test_delete_draft.py` — DELETE /drafts with various statuses
- `tests/orchestrator/test_full_phase_errors.py` — on_step_failed retry, OCR fallback
- `tests/orchestrator/test_pipeline2_orchestrator.py` — rag_index completion, reprocess modes, indexation tasks

### Инфраструктура
- MinIO `upload_file` замокан в conftest (timeout 40с → 0.2с)
- Все внешние сервисы замоканы (Registry, RAG, OCR, Parser, Converter)
- Celery `.delay()` — no-op, задачи тестируются через `.run()`
- **Итог: 543 passed, 3 failed (+51 новых, 0 сломанных)**
  - 3 failed — предсуществующая проблема в test_service_clients_rag.py (document_id=str vs int)

## Naming conventions

| Было | Стало | Где |
|------|-------|-----|
| uploaded_at | created_at | Все таблицы |
| uploaded_by | created_by | Все таблицы |
| udc | udk_code | Registry, Converter |
| review_required | manual | Converter-validator |
| completed | indexed | RAG Builder |

## Error codes (специфичные для Orchestrator)

| HTTP | code | Когда |
|------|------|-------|
| 400 | FILE_TOO_SMALL | Размер файла менее 1 КБ |
| 400 | EMPTY_DOCUMENT | 0 страниц при approve |
| 400 | INVALID_ACTION_FOR_STATUS | Несовместимое действие для статуса |
| 408 | DECISION_TIMEOUT | Истекло время на принятие решения |
| 408 | PREVIEW_TRIGGER_TIMEOUT | Таймаут preview |
| 409 | TASK_ALREADY_EXISTS | Задача уже существует для draft |
| 409 | PREVIEW_IN_PROGRESS | Preview уже запущен |
| 409 | DUPLICATE_FILE | Дубль по SHA-256 при создании черновика |
| 409 | DRAFT_ALREADY_DECIDED | decide для терминального черновика |
| 409 | DUPLICATE_FILE_AFTER_APPROVE | Race condition на full-фазе |
| 409 | BUSINESS_KEY_DRIFT | Бизнес-ключ изменился между preview и approve |
| 422 | UNSUPPORTED_FILE_TYPE | Неподдерживаемый MIME |
| 422 | VALIDATION_ERROR | Некорректные поля запроса |
| — | INTEGRITY_CHECK_FAILED | (шаг rag_index) — проверка целостности индекса не пройдена (P2I-2) |
| — | PENDING_TIMEOUT | Шаг завис в pending (P3S-1) |
| — | PIPELINE_TIMEOUT | Задача превысила время выполнения |
| — | ABSOLUTE_TIMEOUT | Задача превысила абсолютный таймаут 48ч (P3S-1) |

## Pipeline Task lifecycle

```
uploaded → previewing → ready_for_approve → approved → [formation completed]
                                                    → discarded
```

### FSM states

| State | Description |
|-------|-------------|
| uploaded | Файл загружен, задача создана |
| previewing | Выполняется preview фаза |
| ready_for_approve | Preview завершён, ожидает решения |
| approved | Черновик утверждён |
| discarded | Черновик отклонён |

### Task stages

| Stage | Description |
|-------|-------------|
| upload | Регистрация файла |
| preview | OCR/Parser preview |
| decision | Ожидание решения |
| full | Полная обработка |
| registry | Сохранение в Registry |
| indexation | Индексация в RAG |

---

## Анализ изменений по заданию от 19.06.2026

### Все OR-задачи выполнены
- ✅ OR-1 — GET /tasks, GET /tasks/stats, GET /tasks/{id}/steps
- ✅ OR-2 — Идемпотентность preview (409 PREVIEW_ALREADY_RUNNING)
- ✅ OR-3 — metadata_overrides в DecideRequest
- ✅ OR-4 — created_at вместо uploaded_at
- ✅ OR-5 — draft_id передаётся в Parser/OCR
- ✅ OR-6 — DraftNotification модель + has_notifications/critical_count
- ✅ OR-7 — document_id, version_id, is_new_document в ответах
- ✅ OR-8 — OTEL SDK в main.py
- ✅ OR-9 — PreviewMetadata расширен до 12 полей
- ✅ OR-11 — POST /drafts единая точка входа
- ✅ OR-12 — approve/reject + proceed/stop_duplicate/force_new_version
- ✅ OR-13 — approve → Registry.create_document()
- ✅ OR-14 — Ветвление OCR vs Parser по MIME

### Pipeline задачи
- ✅ P1F-1 — INSERT … ON CONFLICT
- ✅ P1F-2 — review_required → validation
- ✅ P1F-4 — preview_metadata → preview_snapshot
- ✅ P1F-5 — Draft-first
- ✅ P1F-6 — Пропуск full-фазы при preview_not_supported
- ✅ P1F-7 — Разделение external/internal actions
- ✅ P1F-8 — Ветвление OCR vs Parser по MIME
- ✅ P1F-9 — Два варианта full-фазы A/B
- ✅ P2I-1 — partially_indexed статус
- ✅ P2I-2 — Integrity check после индексации (self-check + background)
- ✅ P2I-3 — Компенсация через Saga
- ✅ P2I-7 — Advisory lock
- ✅ P3S-1/P3S-2 — Таймауты pending 30с + абсолютный 48ч
- ✅ P3S-4 — Валидация [source:N] (retry 2, fallback)
- ✅ P3S-5 — Fallback при пустом результате
- ✅ P3S-6 — enrichment_skipped в ответе

### Registry задачи
- ✅ RG-1 — PATCH /registry/documents/{id}/status (internal endpoint)

### Не входит в зону оркестратора
- P2I-5 (CPU/GPU timeouts) — конфигурация RAG Builder
- P2I-8 (транзакционность чанков) — логика RAG Builder
