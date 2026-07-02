# Refactoring: Background Poller вместо блокирующего polling в Celery

- [x] **Шаг 1.** Модель `ExternalTask` + репозиторий + настройка таймаута
- [x] **Шаг 2.** Переписать `run_parser_full_step` — убрать цикл polling
- [x] **Шаг 3.** Переписать оба `run_rag_index_step` — убрать polling
- [x] **Шаг 4.** Переписать `run_reprocess_step` и `run_activate_document_step`
- [x] **Шаг 5.** Saga: убрать DISCARDED при ошибках времени (on_step_failed)
- [x] **Шаг 6.** Написать `BackgroundTaskPoller` + интеграция в lifespan
- [x] **Тесты:** 101 test pass (24 unit-tasks + 37 poller + saga + integration)

### Найденные и исправленные баги
- Redis lock не освобождался после успешной отправки в `run_rag_index_step` (indexation) — исправлено
- `process_parser_full_result` не вызывала `_notify_step_completed` после трансформации — исправлено
