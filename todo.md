# Celery worker для оркестратора

## Проблема
После загрузки черновика preview зависает в статусе "processing".
PipelineOrchestrator запускает Celery задачи (.delay()), но Celery worker не запущен в docker-compose.

## План
- [ ] Добавить сервис celery-worker в docker-compose.yml
- [ ] Пересобрать и перезапустить на сервере
