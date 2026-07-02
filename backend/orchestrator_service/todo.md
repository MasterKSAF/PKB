# План изменений Orchestrator Service

На основе верифицированного анализа. Celery задачи fire-and-forget (BackgroundTaskPoller),
приоритеты скорректированы под актуальную архитектуру.

---

## ✅ Done

### [C1] Redis advisory lock — потеря блокировки при падении worker
**Файлы:** `app/tasks/pipeline_indexation.py`, `tests/unit/test_celery_tasks_all.py`
- `setnx` + `expire` (2 вызова) → атомарный `SET lock_key "1" NX EX 3600`
- Обновлены тесты: `setnx` → `set(... nx=True, ex=...)`

### [C2] RAG Index → Activation — документ зависает в "validating"
**Файлы:** `app/core/config.py`, `app/repositories/pipeline.py`, `app/core/pipeline/orchestrator.py`
- Добавлен `VALIDATING_STATE_TIMEOUT` (2ч) в PipelineConfig
- Добавлен `TaskRepository.get_stale_validation_tasks()` — находит indexation-задачи где rag_index completed, а activation не завершён
- Добавлена обработка в `cleanup_stale_tasks` — задачи с VALIDATING_TIMEOOT кодом ошибки

### [C3] Тесты на `_execute_compensation`
**Файлы:** `tests/unit/test_saga_compensation.py`
- 7 прямых тестов: delete_registry_document, delete_from_vector_index, fallback на task.document_id, fallback при task=None, проброс исключения, закрытие клиента при ошибке

### [H1] Full-фаза — watchdog для медленных, но живых сервисов
**Файлы:** `app/core/config.py`, `app/repositories/pipeline.py`, `app/core/pipeline/orchestrator.py`
- Добавлен `MAX_STEP_EXECUTION_TIME` (30 мин) в PipelineConfig
- Добавлен `TaskRepository.get_stale_running_steps_for_hard_kill()` — находит steps в running дольше лимита
- В `cleanup_stale_tasks` добавлен hard kill ДО health-check, с ошибкой STEP_HARD_TIMEOUT

### [H2] Тесты на uncovered компоненты
**Файлы:** `tests/unit/test_find_best_step.py`, `tests/unit/test_otel.py`
- `_find_best_step` — 6 unit-тестов (prefers completed > running > pending, no match, empty, etc.)
- `setup_otel` — тест graceful degradation (логирует warning, не крашится)
- `_execute_compensation` — см. C3

### [M4] Stale lock release — вынести в TaskRepository
**Файлы:** `app/repositories/pipeline.py`, `app/core/pipeline/orchestrator.py`
- Добавлен `TaskRepository.release_stale_locks(max_seconds)` — заменяет прямую SQL-запись
- `cleanup_stale_tasks` теперь использует repository вместо `self.db.execute(select(Task)...)`

### [M5] Scheduler — stale locks при падении Celery Beat
**Файлы:** `app/main.py`
- Добавлен cleanup stale locks при старте сервиса в `lifespan`
- Если Celery Beat был недоступен, locks освобождаются при следующем старте

---

## План на следующие сессии

- ~~**L1:** Hardcoded configs (MAX_FILE_SIZE_BYTES и др. → settings.validation.*)~~ ✅
- **L2:** In-memory idempotency cache → Redis *(отложено)*
- ~~**L3:** JSONB → postgresql.JSONB~~ ✅
- **M1:** Registry — прямой вызов без Saga-консистентности (4+ мест)
- **M2:** `_run_async` — убрать костыль (Celery 6 или AsyncTaskRunner)
- **M3:** Circuit Breaker — fallback `{}` вместо DataBase error
