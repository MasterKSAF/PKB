# todo_pipeline_impl.md — Реализация зафиксированных дефектов

План устранения 7 зафиксированных xfail-тестов из `todo_pipeline_coverage.md`.

## P0-блок (после 1-й итерации тестов)

- [x] Зафиксировано 7 дефектов через xfail (см. `todo_pipeline_coverage.md` §9, §14, §17, §1.2).

## План реализации (сверху вниз)

### 1. Lock watchdog в `cleanup_stale_tasks` (§14)
**Файл:** `app/core/pipeline/orchestrator.py:1652-1704`
**Действие:** добавить в конце метода цикл по задачам с устаревшим `locked_at`:
- если `locked_at < now - MAX_JOB_RUNNING_TIME` → `unlock_task()` + WARN-лог.
- не трогать task с активным `status='failed'` (защита от ложного unlock).
- Закрывает xfail-ы: `test_stale_lock_detected_by_cleanup`, `test_unlock_called_in_on_step_failed` (частично).

### 2. Реальный DB-чек в `/health/ready` (§9)
**Файл:** `app/api/v1/endpoints/health.py:72-86`
**Действие:**
- Импортировать `Depends(get_db)` и `AsyncSession` в сигнатуре.
- Внутри выполнить `SELECT 1` через существующую сессию.
- При успехе — 200 + `database="online"`.
- При исключении — 503 + `database="offline"`.
- Закрывает xfail: `test_health_ready_returns_offline_when_db_unreachable`.

### 3. Реальный опрос downstream в `/system/health` (§9)
**Файл:** `app/api/v1/endpoints/health.py:22-50`
**Действие:**
- В mock-mode — оставить "ok" для всех (как сейчас).
- В real-mode — параллельный `asyncio.gather` `client.get("/health")` для RAG Builder / Registry (быстрый timeout 2с).
- `services_status[svc] = "ok"` или `"degraded"` в зависимости от ответа.
- Общий `status` = `"ok"` если все ok, иначе `"degraded"`.
- Закрывает xfail-ы: `test_system_health_returns_degraded_when_rag_unavailable`, `test_system_health_aggregates_multiple_downstream_failures`.

### 4. Валидация `PARSER_ENABLED`/`OCR_ENABLED` в `on_step_failed` (§1.2)
**Файл:** `app/core/pipeline/orchestrator.py:1460-1650`
**Действие:** добавить проверку **перед** блоком retry (после установки `use_ocr_fallback`):
- если `step_name in ("preview_ocr", "full_ocr")` И `PARSER_ENABLED == False` И `OCR_ENABLED == False`:
  - `set_task_error(... "NO_AVAILABLE_ENGINES" ...)`;
  - `update_task_status(..., status="failed")`;
  - `return` (без retry).
- Закрывает xfail: `test_no_engines_raises_clear_error`.

## Тесты, которые должны перейти из xfail → passed

1. `tests/unit/test_pipeline_repository_lock.py::TestLockHolderCrashed::test_stale_lock_detected_by_cleanup` → после п.1.
2. `tests/unit/test_pipeline_repository_lock.py::TestLockReleasedOnTaskError::test_unlock_called_in_on_step_failed` → после п.1 + правка `on_step_failed`.
3. `tests/test_health_degraded.py::TestHealthReadyDbCheck::test_health_ready_returns_offline_when_db_unreachable` → после п.2.
4. `tests/test_health_degraded.py::TestSystemHealthAggregate::test_system_health_returns_degraded_when_rag_unavailable` → после п.3.
5. `tests/test_health_degraded.py::TestSystemHealthAggregate::test_system_health_aggregates_multiple_downstream_failures` → после п.3.
6. `tests/orchestrator/test_parser_ocr_fallback.py::TestAllServicesDisabled::test_no_engines_raises_clear_error` → после п.4.
7. `tests/unit/test_pipeline_repository_atomicity.py::TestAtomicTaskCreation::test_create_task_step_for_nonexistent_task_fails` — **НЕ реализуется** (особенность SQLite; тест уже корректно делает xfail). Остаётся xfail.

## Порядок реализации

1. Lock watchdog — минимальное изменение, без сетевых вызовов.
2. DB-чек в `/health/ready` — единичный SELECT 1, изолированно.
3. Опрос downstream в `/system/health` — самый сложный, требует HTTP-вызовов + timeout.
4. Валидация движков в `on_step_failed` — добавить ветку `NO_AVAILABLE_ENGINES`.

После каждого пункта — прогон xfail-теста, чтобы убедиться, что он переходит в passed.

## Что НЕ делаем

- Не реализуем: rate-limit, semaphore, Redis-замену для `_IDEMPOTENCY_CACHE` (P1).
- Не правим существующие тесты (кроме удаления `pytest.xfail` после успешной реализации).
- Не обновляем `specificity.md` / `guide.md` (опционально после всех правок).
