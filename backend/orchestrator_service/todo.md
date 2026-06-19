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

## 🟠 Блок 3. Pipeline 2 — Indexation (реальные вызовы)

### 3.1 Advisory lock для Scheduler (P2I-7)
- [x] ✅ Redis SETNX lock перед стартом indexation
- [x] ✅ Lock release на success и failure
- **Файлы:** `app/tasks/pipeline_indexation.py`

### 3.2 Компенсация fallback (P2I-3)
- [x] ✅ `delete_registry_document` — реальный вызов Registry API
- [x] ✅ `delete_from_vector_index` — реальный вызов RAG API
- **Файлы:** `app/tasks/compensation.py`, `app/services/registry_client.py`

---

## 🟡 Блок 4. Pipeline 3 — Search (реальные вызовы)

### 4.1 Fallback при пустом результате (P3S-5)
- [x] ✅ Пустой результат RAG Search → ответ с `items=[]`, не ошибка
- [x] ✅ Реальный вызов RAGServiceClient в production, MOCK_RESULTS в mock-mode
- **Файлы:** `app/api/v1/endpoints/search.py`

---

## 🟡 Блок 5. БД оркестратора

### 5.1 Soft-delete: deleted_at (DB-6)
- [x] ✅ `deleted_at` в Task + TaskStep модели
- [x] ✅ Фильтр `WHERE deleted_at IS NULL` в get_task, get_task_for_update, get_task_steps, get_stale_running_tasks
- **Файлы:** `app/models/pipeline.py`, `app/repositories/pipeline.py`

---

## 🔴 Блок 6. Тесты

| # | Приор. | Тест | Файл | Статус |
|---|--------|------|------|--------|
| T-5 | 🔴 | draft_id в Parser/OCR (400/404/202) | `tests/orchestrator/test_draft_id_propagation.py` | ✅ |
| T-7 | 🟠 | Цепочка draft → document → version | `tests/integration/test_draft_to_version.py` | ✅ |
| T-11 | 🟠 | Корреляционные заголовки в downstream | `tests/integration/test_correlation.py` | ✅ |
| T-12 | 🟡 | health/live vs health/ready | `tests/integration/test_health.py` + `app/api/v1/endpoints/health.py` | ✅ |
| T-1 | 🔴 | assess_quality пороги (<0.6 / <0.85) | `tests/shared/test_quality.py` | ✅ |
| T-4 | 🟠 | Запись notifications в draft_notifications | `tests/orchestrator/test_issues_recording.py` | ✅ |

---

## ⚪ Блок 7. Очистка и документация

- [x] ✅ Deprecate POST /documents (уже удалён, upload только через POST /drafts)
- [x] ✅ Monitor router — уже удалён
- [x] ✅ Актуализирован readme.md под real-режим
- [ ] 📖 Актуализировать orchestrator_service_api.md (сейчас устарела)
- [ ] 📖 Зафиксировать архитектурные решения в specificity.md
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
