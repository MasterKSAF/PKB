# todo.md — Reliability fixes (выполнено)

## Сделано

### §5.1 — update_task_status с опциональным FOR UPDATE
- `update_task_status(for_update=True)` — row-lock ТОЛЬКО при статусных переходах
- `update_task_progress()` — новый метод, без FOR UPDATE
- `update_task_stage()` — новый метод, без FOR UPDATE
- В `orchestrator.py` заменены progress-only вызовы на `update_task_progress`
- **Эффект:** на каждый step-completion убраны 2-3 ненужных FOR UPDATE → меньше lock contention

### §3.1 — Атомарный slot-counter
- `count_active_tasks(for_update=True)` — с FOR UPDATE, сериализует конкурентные проверки слота
- `try_activate_next_queued_task()` — атомарно: count(FOR UPDATE) + pick(SKIP LOCKED) + activate
- `_drain_queue` переписан на `try_activate_next_queued_task` — без race window
- `start_pipeline` использует `count_active_tasks(for_update=True)` вместо `_has_free_slot`
- **Эффект:** race condition на превышение MAX_CONCURRENT_TASKS закрыт

### §5.3 — (уже исправлен через §4.1)
- Converter не нотифицирует на каждом Celery retry → retry_count не расходится
