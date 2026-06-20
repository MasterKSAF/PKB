# Todo — План разработки Orchestrator Service

> Создан: 19.06.2026
> Режим: **real** (по умолчанию), **mock** только для тестов

## Условные обозначения

- ✅ — Выполнено
- 🔴 — Блокирующе
- 🟠 — Серьёзно
- 🟡 — Важно
- 🔵 — Средне
- ⚪ — Косметика

---

## 🔴 Блок 1. Pipeline Formation — доделать

### 1.1 Quality notifications из Parser/OCR (OR-6 / PS-4 / OC-5)
- [x] ✅ `TaskRepository.save_notifications()` — добавлен
- [x] ✅ `_on_preview_completed()` — читает quality, сохраняет нотификации
- [x] ✅ Critical нотификации блокируют auto-approve
- [x] ✅ Quality добавлен в output_data Parser/OCR задач
- [x] ✅ Mock-ответы Parser/OCR содержат quality

### 1.2 Preview snapshot при approve (P1F-4 / CV-5)
- [x] ✅ `RegistryServiceClient.create_draft_snapshot()` — добавлен
- [x] ✅ `approve_draft()` — отправляет snapshot в Registry

### 1.3 GET /tasks/{id}/steps (OR-1)
- [x] ✅ Эндпоинт `GET /tasks/{task_id}/steps` — реализован
- [x] ✅ Схема `TaskStepsListResponse` — добавлена

### 1.4 FSM: review_required → validation (P1F-2)
- [x] ✅ `_on_preview_completed()` — проверяет `validated` из Converter
- [x] ✅ Если `validated == false` → статус `review_required`, auto-approve блокируется

### 1.5 Явный выбор full-фазы A/B (P1F-9)
- [x] ✅ Параметр `FULL_PHASE_MODE: str = "auto"` в `PipelineConfig`
- [x] ✅ `approve_draft()` — использует full_mode: auto | partial | full

---

## 🟠 Блок 2. Observability

### 2.1 OTEL SDK в main.py (OR-8 / CM-6)
- [x] ✅ Модуль `app/core/otel.py` — инициализация TracerProvider + OTLP экспорт
- [x] ✅ Auto-instrumentation FastAPI + httpx (graceful degradation если нет пакетов)
- [x] ✅ Вызов `setup_otel()` в lifespan main.py
- [x] ✅ Зависимости в requirements.txt

### 2.2 Проброс X-User-ID, X-Draft-ID, X-Document-ID, X-Version-ID (CM-5)
- [x] ✅ Contextvars для всех 4 заголовков в `trace.py`
- [x] ✅ `build_correlation_headers()` — собирает все 6 заголовков
- [x] ✅ `base_client._build_correlation_headers()` — использует общую функцию
- [x] ✅ Middleware читает X-User-ID из запроса
- [x] ✅ X-Draft-ID устанавливается в create_draft
- [x] ✅ X-Document-ID / X-Version-ID устанавливаются в approve/proceed/force_new_version

### 2.3 Коды ошибок 408 (CM-7)
- [x] ✅ `408 DECISION_TIMEOUT` — добавлен
- [x] ✅ `408 PREVIEW_TRIGGER_TIMEOUT` — добавлен
- [x] ✅ `422 PREVIEW_NOT_SUPPORTED` — добавлен
- [x] ✅ Структура `STATUS_CODES` переделана в list для поддержки дублирующихся HTTP-кодов

---

## 🟠 Блок 3. Pipeline 2 — Indexation

### 3.1 Advisory lock для Scheduler (P2I-7)
- [x] ✅ Redis SETNX lock перед стартом indexation
- [x] ✅ Lock release на success и failure
- **Файлы:** `app/tasks/pipeline_indexation.py`

### 3.2 Компенсация fallback (P2I-3)
- [x] ✅ `delete_registry_document` — реальный вызов Registry API
- [x] ✅ `delete_from_vector_index` — реальный вызов RAG API
- **Файлы:** `app/tasks/compensation.py`, `app/services/registry_client.py`

### 3.3 partially_indexed статус (P2I-1)
- [x] ✅ Добавлен статус `partially_indexed` в FSM/TaskStatus
- [x] ✅ Индексация проверяет chunk_count_actual < expected
- [x] ✅ Search schemas обновлены (IndexationPipeline)
- **Файлы:** `app/core/fsm.py`, `app/tasks/pipeline_indexation.py`

### 3.4 POST /documents/{id}/reprocess (P2I-9)
- [x] ✅ Эндпоинт `/api/v1/documents/{document_id}/reprocess`
- [x] ✅ Celery задача `run_reprocess_step` в pipeline_indexation.py
- [x] ✅ Схема `ReprocessResponse`
- **Файлы:** `app/api/v1/endpoints/documents.py`, `app/tasks/pipeline_indexation.py`

---

## 🟡 Блок 4. Pipeline 3 — Search

### 4.1 Fallback при пустом результате (P3S-5)
- [x] ✅ Пустой результат RAG Search → ответ с `items=[]`, не ошибка
- [x] ✅ Реальный вызов RAGServiceClient в production, MOCK_RESULTS в mock-mode
- **Файлы:** `app/api/v1/endpoints/search.py`

### 4.2 enrichment_skipped в ответе (P3S-6)
- [x] ✅ Поле `enrichment_skipped: bool` в SearchResponse
- [x] ✅ Возвращается из search endpoint
- **Файлы:** `app/schemas/search.py`, `app/api/v1/endpoints/search.py`

### 4.3 Валидация [source:N] формата (P3S-4)
- [x] ✅ CitationValidator — проверка формата [source:N]
- [x] ✅ Retry-механизм (2 попытки, fallback)
- **Файлы:** `app/shared/citation_validator.py`

---

## 🟡 Блок 5. БД оркестратора

### 5.1 Soft-delete: deleted_at (DB-6)
- [x] ✅ `deleted_at` в Task + TaskStep модели
- [x] ✅ Фильтр `WHERE deleted_at IS NULL` в get_task, get_task_for_update, get_task_steps, get_stale_running_tasks
- **Файлы:** `app/models/pipeline.py`, `app/repositories/pipeline.py`

---

## 🟡 Блок 6. Таймауты и scheduler

### 6.1 Pending state timeout + absolute timeout (P3S-1 / P3S-2)
- [x] ✅ `PENDING_STATE_TIMEOUT: int = 30` в PipelineConfig
- [x] ✅ `ABSOLUTE_TASK_TIMEOUT_HOURS: int = 48` в PipelineConfig
- [x] ✅ Scheduler: cleanup_stale_tasks обнаруживает зависшие pending
- **Файлы:** `app/core/config.py`, `app/tasks/scheduler.py`, `app/repositories/pipeline.py`

---

## 🔴 Блок 7. Тесты

| # | Приор. | Тест | Файл | Статус |
|---|--------|------|------|--------|
| T-5 | 🔴 | draft_id в Parser/OCR (400/404/202) | `tests/orchestrator/test_draft_id_propagation.py` | ✅ |
| T-7 | 🟠 | Цепочка draft → document → version | `tests/integration/test_draft_to_version.py` | ✅ |
| T-11 | 🟠 | Корреляционные заголовки в downstream | `tests/integration/test_correlation.py` | ✅ |
| T-12 | 🟡 | health/live vs health/ready | `tests/integration/test_health.py` + `app/api/v1/endpoints/health.py` | ✅ |
| T-1 | 🔴 | assess_quality пороги (<0.6 / <0.85) | `tests/shared/test_quality.py` | ✅ |
| T-4 | 🟠 | Запись notifications в draft_notifications | `tests/orchestrator/test_issues_recording.py` | ✅ |
| | 🟠 | enrichment_skipped в SearchResponse | `tests/test_search.py` | ✅ |
| | 🟠 | citation_validator | `tests/shared/test_citation_validator.py` | ✅ |
| | 🟠 | reprocess endpoint | `tests/test_documents_api.py` | ✅ |
| | 🟠 | partially_indexed статус | `tests/test_pipelines.py` | ✅ |
| | 🟠 | timeout config + stale pending | `tests/unit/test_pipeline_repository.py` | ✅ |

## 🟠 Блок 9. Интеграционные задачи (добавлены 20.06)

### 9.1 RG-1 — PATCH /registry/documents/{id}/status
- [x] ✅ `UpdateDocumentStatusRequest` schema
- [x] ✅ `RegistryServiceClient.update_document_status()` + mock handler
- [x] ✅ 4 unit-теста в `tests/test_service_clients_registry.py`

### 9.2 P2I-2 — Integrity check (indexed → failed)
- [x] ✅ `RAGBuilderClient.check_index()` + mock handler
- [x] ✅ `RAGBuilderClient = RAGServiceClient` alias (fixes runtime import)
- [x] ✅ Self-check в `run_rag_index_step()` — проверка INTEGRITY_CHECK_FAILED
- [x] ✅ Background check `integrity_check()` в scheduler.py
- [x] ✅ `TaskRepository.get_recently_indexed_tasks()`
- [x] ✅ 11 unit-тестов в `tests/unit/test_integrity_check.py`
- [x] ✅ 3 unit-теста check_index в `tests/test_service_clients_rag.py`

---

## ⚪ Блок 8. Очистка и документация

- [x] ✅ Deprecate POST /documents (уже удалён, upload только через POST /drafts)
- [x] ✅ Monitor router — уже удалён
- [x] ✅ Актуализирован readme.md под real-режим
- [x] 📖 Актуализирован orchestrator_service_api.md (пользователь)
- [x] 📖 Зафиксированы архитектурные решения в specificity.md (пользователь)
- [ ] 📖 Обновить guide.md

---

## ✅ Выполнено (предыдущие этапы)

### Критические (🔴)
- [x] OR-5 — draft_id передаётся в Parser/OCR
- [x] OR-11 — POST /drafts единая точка входа (mime_type пробрасывается)
- [x] OR-12 — approve/reject + proceed/stop_duplicate/force_new_version
- [x] OR-13 — approve → Registry.create_document()
- [x] P1F-1 — защита дубликатов Task (409 + UNIQUE)
- [x] P1F-5 — draft-first
- [x] P1F-6 — пропуск full-фазы при preview_not_supported
- [x] P1F-7 — разделение external/internal actions
- [x] P1F-8 — ветвление OCR vs Parser по MIME
- [x] PS-3/OC-4 — draft_id в Parser/OCR (клиенты и Celery)
- [x] PS-5/OC-8 — unified mode=preview|full

### Серьёзные (🟠)
- [x] OR-1 — GET /tasks (список), GET /tasks/stats
- [x] OR-2 — Идемпотентность preview (409 PREVIEW_ALREADY_RUNNING)
- [x] OR-6 — Модель DraftNotification + has_notifications/critical_count
- [x] OR-7 — version_id, is_new_document в DraftDetailResponse
- [x] OR-14 — MIME-ветвление исправлено
- [x] CM-5 — X-Trace-ID, X-Request-ID middleware + structured logging

### Важные (🟡)
- [x] OR-3 — metadata_overrides в DecideRequest
- [x] OR-9 — PreviewMetadata расширен до 12 полей
- [x] DB-5 — ON DELETE CASCADE для FK

### Косметика (⚪)
- [x] OR-4 — created_at вместо uploaded_at в моделях

### Режим работы
- [x] Переключён default с mock → real (config.py)
- [x] Mock принудительно только для тестов (conftest.py)

### Тесты
- [x] 386 passed (все тесты)

---

## 🟢 Блок 10. Синхронизация кода со спецификацией (20.06)

### 10.1 GET /tasks — формат пагинации
- [x] `TaskListResponse` — `total/page/page_size` → `meta: PaginationMeta`
- [x] `list_tasks()` — сборка `meta` вместо плоских полей
- [x] Тесты обновлены под `data["meta"]["total"]`

### 10.2 GET /tasks/stats — структура ответа
- [x] `TaskStatsResponse` — `active/completed/failed/by_type` → `by_status` + `by_stage`
- [x] `get_task_stats()` — CASE-запрос с 8 статусами (uploaded, previewing, ready_for_approve, processing, created, indexing, indexed, failed) + 6 этапов
- [x] Тесты обновлены под `data["by_status"]` / `data["by_stage"]`

### 10.3 GET /drafts/{draft_id}/tasks — новый эндпоинт
- [x] `DraftTasksResponse` + `DraftTaskItem` схемы
- [x] `get_draft_tasks()` в drafts.py (фильтр по draft_id, сортировка)
- [x] `created_by` поле добавлено в модель Task

### 10.4 Инфраструктурные правки
- [x] `Task.deleted_at.is_(None)` — фильтрация soft-delete во всех эндпоинтах задач
- [x] `DraftNotification` import вынесен наверх (был внутри try)

### Результат
- [x] **435 passed** (все тесты)

---

## 🟢 Блок 11. Устранение недочётов (отчёт 20.06)

### 11.1 POST /drafts — добавить поля (🔴)
- [x] ✅ Добавлены Form-параметры: source_type, doc_code, mks_oks_code, okstu_code, era, jurisdiction, issuing_body, metadata
- [x] ✅ Проброс метаданных в Registry через create_draft() + title_key
- [x] ✅ Валидация source_type/era/jurisdiction
- [x] ✅ title_key вычисляется и возвращается в ответе
- [x] ✅ Метаданные сохраняются в upload step input_data

### 11.2 Saga compensation — реализовать (🟠)
- [x] ✅ `_execute_compensation()` реально вызывает Celery-задачи delete_registry_document / delete_from_vector_index
- [x] ✅ Добавлены компенсации для rag_index и reprocess

### 11.3 documents/search — удалить dead code (⚪)
- [x] ✅ Удалён `app/api/v1/endpoints/search.py`
- [x] ✅ Убран search из `app/api/v1/api.py`
- [x] ✅ Удалён `tests/test_search.py`
- [x] ✅ Удалены неиспользуемые схемы `app/schemas/search.py`
- [x] ✅ Убран `/api/v1/documents/search` из OpenAPI проверки в test_health.py
- [x] ✅ Убран test_search_top_k_exceeds_max_returns_422 из test_error_handling.py

### 11.4 ReprocessResponse.user_id — убрать (⚪)
- [x] ✅ Удалён user_id из ReprocessResponse схемы
- [x] ✅ Убран user_id из ответа reprocess_document()
- [x] ✅ Убраны проверки user_id из тестов

### Результат
- [x] **408 passed** (все тесты)
