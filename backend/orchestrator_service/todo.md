# Сессия: 2026-07-06 — Правки по audit.md (High/Medium/Low)

## Результат

### 🔴 Critical (уже исправлено в f0f8a2b7)
- ~~§4.1 Converter: guard _notify_step_failed за retries >= max_retries~~
- ~~§4.2 cleanup_stale_tasks: вызов on_step_failed после hard-kill~~
- ~~§4.3 Удалён дубликат get_stale_running_steps_for_hard_kill~~
- ~~§3.4 on_step_completed: return после already-completed~~

### 🟠 High (сделано в этой сессии)
- [x] §4.5 — `integrity_check`: `client.close()` в `try/finally`
- [x] §4.10 — `_run_ocr_fallback`: UPDATE existing step row вместо CREATE (метод `reset_task_step_for_fallback`)
- [x] §3.3 — Прогресс по уникальным `step_name`, а не строкам
- [x] §5.4 — Worker restart: освобождать locks при старте (метод `release_locks_by_worker` + Celery сигнал)
- [x] §4.4 — Health-check: timeout 3s, fallback URLs только на 404

### 🟡 Medium
- [ ] §2.1 — `StepDispatcher` интерфейс для устранения циркулярной core←tasks зависимости
- [ ] §2.3 — Декомпозиция `orchestrator.py` (2000+ → dispatcher, health, cleanup, approver)
- [x] §4.6 — `_run_async`: единый event-loop на Celery-task (thread-local storage через `app/tasks/async_utils.py`)
- [ ] §6.3 — `cleanup_stale_tasks`: разбить на пачки с commit; health-check вынести из транзакции
- [ ] §6.1 — Outbox-таблица для external side-effects (Registry, RAG)
- [ ] §7 — Тесты: `_notify_step_*`, `BackgroundTaskPoller`, converter-retry-count

### 🟢 Low (сделано)
- [x] §8 — `"decision"` → `TaskStage.DECISION.value` (orchestrator.py + endpoints)

### 🟢 Low (осталось)
- [ ] §4.8/4.9 — Адаптивный poll-interval и distributed lock для poller
