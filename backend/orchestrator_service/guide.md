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

### 3. Двухфазный pipeline
- **Preview фаза:** быстрая обработка первых страниц (OCR/Parser → Converter-validator) → решение пользователя.
- **Full фаза:** полная обработка (OCR/Parser → Converter-validator → Registry → RAG Builder).
- Ветвление по MIME-типу: image/* → OCR, application/pdf → Parser.
- Preview_not_supported → пропуск full-фазы.

### 4. Task как агрегатор шагов
- Один Task = одна pipeline-задача (formation/indexation/reprocess).
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

### Что уже реализовано и соответствует заданию
- ✅ POST /drafts — единая точка входа (OR-11)
- ✅ POST /drafts/{draft_id}/preview — запуск preview (OR-2, частично)
- ✅ GET /drafts/{draft_id}/preview/status — статус с longpoll (OR-2)
- ✅ PATCH /drafts/{draft_id}/decide — approve/reject (OR-12, частично)
- ✅ GET /tasks/{task_id}/status — статус задачи (OR-1, частично)
- ✅ Ветвление OCR vs Parser по MIME (OR-14, частично)
- ✅ Trace ID middleware (CM-5, частично)
- ✅ Service clients с dual-mode (все 6 клиентов)
- ✅ Task + TaskStep модели (DB-23, DB-24)
- ✅ Saga компенсация
- ✅ Structured logging с trace_id

### Что нужно изменить
- ❌ POST /drafts не передаёт mime_type в start_pipeline (OR-14)
- ❌ POST /drafts/{id}/preview hardcoded "application/pdf" (OR-14)
- ❌ Нет проверки идемпотентности preview → 409 (OR-2)
- ❌ Нет metadata_overrides в decide (OR-3)
- ❌ Нет draft_id в вызовах Parser/OCR (OR-5)
- ❌ Нет draft_notifications модели (OR-6)
- ❌ Нет version_id, is_new_document в GET /drafts/{id} (OR-7)
- ❌ Нет OTEL SDK (OR-8, CM-6)
- ❌ PreviewMetadata — только 5 полей, нужно расширить (OR-9)
- ❌ Нет разделения approve/reject vs proceed/stop_duplicate/force_new_version (OR-12)
- ❌ approve не вызывает Registry.create_document() (OR-13)
- ❌ Нет GET /tasks (список) (OR-1)
- ❌ Нет Idempotency-Key в POST /drafts (OR-11/GW-11)
