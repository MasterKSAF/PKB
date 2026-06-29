# Тест загрузки + фикс B1 + механизм stale running + тесты

- [x] 1. Изучить проект, Docker, существующие тесты
- [x] 2. Создать `data/tests/test_universal_pdf_loader.py`
- [x] 3. Добавить детальный вывод шагов + doc_id в поиске
- [x] 4. Запустить тест, проанализировать баги
- [x] 5. **B1**: `_run_ocr_fallback` — guard `has_existing_ocr` (+ `return`)
- [x] 6. **B2**: `RUNNING_STEP_TIMEOUT=600`, `get_stale_running_steps`, `_check_service_health`, `cleanup_stale_tasks` — stale running + health check
- [x] 7. **Config**: `PENDING_STATE_TIMEOUT=30→180`
- [x] 8. **Тесты**: 9 новых тестов (566 passed, 3 предсуществующих failed)
- [x] 9. **Пересобрать контейнеры** — `orchestrator` + `celery-worker`
- [x] 10. **E2E тест** — **PASSED**: pipeline completed, 8/8 фрагментов найдены
