# Диагностика и исправление проблем загрузки документов

## Выполнено ✅

- [x] Диагностика docker compose ps, логов gateway, orchestrator, celery-worker, parser
- [x] Проверка API вызовов через curl (все эндпоинты отвечают)
- [x] Создание настоящего PDF и тестовая загрузка
- [x] Выявлены и устранены все проблемы pipeline

## Исправлено

### 1. Баг в converter-validator (500 Internal Server Error)
- **Файл**: `backend/converter_validator_service/app/core/exceptions.py`
- **Проблема**: 3 класса ошибок использовали `status.HTTP_422_UNPROCESSABLE_CONTENT` (не существует)
- **Исправление**: заменил на `status.HTTP_422_UNPROCESSABLE_ENTITY`

### 2. Несоответствие формата ответа converter
- **Файл**: `backend/orchestrator_service/app/tasks/pipeline_formation.py`
- **Проблема**: orchestrator ожидал `{"data": {"metadata": {...}}}` от converter, но converter возвращает плоский PreviewMetadataResponse
- **Исправление**: добавлено определение формата ответа и корректное извлечение metadata

### 3. Orchestrator не сохранял preview_metadata в Registry
- **Файл**: `backend/orchestrator_service/app/core/pipeline/orchestrator.py`
- **Проблема**: после успешного preview converter'а metadata не записывались в Registry
- **Исправление**: добавлен вызов `registry.update_draft_metadata()` перед обновлением статуса

### 4. Orchestrator не передавал preview_metadata фронтенду
- **Файл**: `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`
- **Проблема**: GET /drafts/{id} не включал preview_metadata в ответ
- **Исправление**: добавлены поля `preview_metadata`, `created_at`, `updated_at` в ответ

### 5. Смена URL LLM API
- **Файл**: `docker-compose.yml`
- **Изменение**: `routerai.ru/api/v1` → `opencode.ai/zen/go/v1` для OPENAI_BASE_URL и LLM_API_URL

### 6. Очищены все невалидные черновики
- Удалены черновики 1-55 (созданные с test_draft.pdf или без metadata)

## Результат
- **Pipeline работает**: Parser preview → Converter preview → сохранение metadata в Registry
- **Реальный PDF** (123KB) успешно обработан: извлечены doc_code="10054-82", title, era, year и др.
- **Фронтенд получит корректные названия** черновиков через preview_metadata
