# Исправления — ВЫПОЛНЕНО

## Критические замечания из audit.md (4/4)

| § | Проблема | Статус |
|---|---|---|
| §4.1 | Converter-tasks: `_notify_step_failed` на каждой Celery-retry | ✅ Исправлен код + тесты |
| §4.2 | `cleanup_stale_tasks` не вызывает `on_step_failed` → задачи «зависали» до 48h | ✅ Добавлены вызовы с try/except |
| §4.3 | Дубликат `get_stale_running_steps_for_hard_kill` | ✅ Удалено первое определение |
| §3.4 | `on_step_completed` передиспатчит downstream при дублированном callback | ✅ Добавлен `return` после already-completed |

## Исправления тестов (группы)

| Группа | Что исправлено | Результат |
|---|---|---|
| `test_celery_tasks_all.py` (8 тестов) | Guard для notify, mock registry, job_id int, версия конвертера | ✅ 28/28 pass |
| `test_celery_tasks_async.py` (2 теста) | Guard для notify converter preview | ✅ 3/3 pass |
| `test_concurrent_limit.py` (7 тестов) | Создание шагов для count_active_tasks | ✅ 21/21 pass |
| `test_pipeline_repository.py` (1 тест) | `create_task` создаёт `queued`, не `active` | ✅ pass |
| `test_drafts_consistency.py` (2 теста) | `MAX_FILE_SIZE_BYTES` перенесён в settings | ✅ pass |
| `test_file_hash_duplication.py` (2 теста) | `on_step_completed` с выходными данными вместо pre-complete | ✅ 4/4 pass |
| `test_idempotency_persistence.py` (1 тест) | `DUPLICATE_FILE` → `DUPLICATE_IN_PROGRESS` | ✅ pass |
| `test_idempotency_ttl.py` (1 тест) | `DUPLICATE_FILE` → `DUPLICATE_IN_PROGRESS` | ✅ pass |

## Предсуществующие падения (12, не мои)

- `test_base_client` (8) — настройки real-режима клиента
- `test_drafts` (3) — mock размера файла в draft API
