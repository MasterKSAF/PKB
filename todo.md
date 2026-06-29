# Fix: converter-validator contract alignment — tests

1. [x] Диагностика: найти причину падения тестов после мержа PR #75
2. [x] conftest.py — вернуть db_engine в сигнатуру clean_db (фикстура создаётся до async контекста)
3. [x] test_celery_tasks_all.py — обновить mock и проверки под v3-контракт (parameters → metadata/validation)
4. [x] test_celery_tasks.py — обновить mock preview под плоский PreviewMetadataResponse
5. [x] test_celery_tasks_async.py — обновить mock preview под плоский формат
6. [x] Проверка: 558 passed в orchestrator_service, все E2E в docker проходят
