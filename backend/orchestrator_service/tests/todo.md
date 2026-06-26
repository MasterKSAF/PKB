# План: тесты Celery-задач и статусов черновиков — ВЫПОЛНЕНО

## Результат
- **20 новых тестов Celery-задач** (unit): все pipeline_formation, pipeline_indexation, scheduler, compensation
- **18 новых интеграционных тестов API**: статусы, шаги с результатами, задачи документов
- **Исправлен production баг**: в `pipeline_indexation.py` отсутствовал `from app.core.config import settings`
- **Исправлена инфраструктура тестов**: добавлен патч MinIO upload в conftest (тесты вешались на 40с)
- **Исправлены существующие тесты**: mock assertions для `process()` — добавлен `task_id`
- **Исправлены 19 предсуществующих тестов**: добавлен `task_id` в вызовы `process()`
- **Итог**: 358 passed, 0 failed
