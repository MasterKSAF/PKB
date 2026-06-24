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
- **Preview фаза:** быстрая обработка первых страниц (OCR/Parser → Converter-validator) → решение пользователя.
- **Full фаза:** полная обработка (OCR/Parser → Converter-validator → Registry → RAG Builder).
- Ветвление по MIME-типу: image/* → OCR, application/pdf → Parser.
- Preview_not_supported → пропуск full-фазы.

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
- **Внешние (UI):** approve, reject.
- **Внутренние:** proceed (продолжить), stop_duplicate (дубликат), force_new_version (новая версия).

### 10. Компенсация через Saga
- При неисправимой ошибке → SagaCoordinator компенсирует выполненные шаги.
- Fallback: DELETE в Registry.

---

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
| 408 | DECISION_TIMEOUT | Истекло время на принятие решения |
| 408 | PREVIEW_TRIGGER_TIMEOUT | Таймаут preview |
| 409 | TASK_ALREADY_EXISTS | Задача уже существует для draft |
| 409 | PREVIEW_ALREADY_RUNNING | Preview уже запущен |
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
