# Session: Queue-based concurrent task limiting

## Статус: ✅ Выполнено

### Изменения в коде
- [x] **fsm.py** — `QUEUED = "queued"` в `TaskStatus`
- [x] **pipeline.py** — `get_next_queued_task()` с `SELECT ... FOR UPDATE SKIP LOCKED`
- [x] **orchestrator.py:**
  - `_check_concurrent_limit()` → `_has_free_slot()` (возвращает bool)
  - `_enqueue_celery_tasks()` — preview dispatch
  - `_enqueue_celery_full_tasks()` — full-phase dispatch (approve/confirm)
  - `_drain_queue()` — FIFO, определяет preview vs full по `pipeline_stage`
  - `start_pipeline()` — возвращает bool (True=active, False=queued)
  - `approve_draft()` — создаёт документ+шаги, затем проверяет слот
  - `confirm_draft()` — поддержка очереди
  - `_drain_queue()` вызывается в: `on_step_completed`, `on_step_failed`, `stop_duplicate_draft`, `reject_draft`
- [x] **drafts.py** — убран 429, добавлен `queued` в ответ; убран импорт `ConcurrentTaskLimitError`
- [x] **scheduler.py** — `drain_pipeline_queue` (Celery Beat, каждые 2 мин)
- [x] **celery_app.py** — зарегистрирована Beat задача
- [x] **schemas/drafts.py** — `queued: bool` в `DraftCreateResponse`
- [x] **schemas/tasks.py** — обновлена документация статусов
- [x] **models/pipeline.py** — обновлена документация статусов

### Тесты (21 тест)
- **TestCountActiveTasks** — `queued` исключается из active count
- **TestHasFreeSlot** — below/at/completed/queued-not-counted
- **TestGetNextQueuedTask** — empty, FIFO oldest, ignores active, ignores terminal
- **TestStartPipelineQueuing** — dispatches when slot free, queues when full, drain after free
- **TestApproveDraftQueuing** — approve returns queued when limit, stage=FULL
- **TestDrainQueue** — drain empty, FIFO, respects limit
- **test_fsm.py** — `queued` добавлен в all_values

### Итог
- Все unit-тесты: **177 passed**, 6 pre-existing failures
- saga/repository/lock/fsm тесты: **все проходят**
- `ConcurrentTaskLimitError` — класс оставлен (backward compat), не выбрасывается
- Celery Beat scheduler — страховочный drain каждые 2 мин
