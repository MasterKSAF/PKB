# Проверка черновика через головной Docker — результаты

## Статус жизненного цикла черновика

```
POST /api/v1/drafts  →  202 ✓
  └─ upload          →  completed ✓
  └─ preview_ocr     →  completed ✓  (Parser: 2.12s)
  └─ preview_converter →  pending   ✗
```

## Исправлено ✅

### Celery инфраструктура
- [x] `celery-worker` слушает очередь `pipeline` (добавлено `-Q celery,pipeline,saga`)
- [x] `celery-worker` healthcheck отключён (наследовал от Dockerfile оркестратора)
- [x] Исправлен `_run_async` — event loop создаётся/закрывается внутри каждой async-операции

### Эндпоинты сервисов
- [x] Parser: `/parser/process` → `/api/v1/parser/process`
- [x] Converter: `/convert/preview` → `/api/v1/converter/preview`
- [x] Converter: `/convert/process` → `/api/v1/converter/convert`
- [x] OCR: `/ocr/process` → `/api/v1/ocr/process`

### Миграция схем
- [x] `task_id` добавлен в `ParserProcessRequest`, `OcrProcessRequest`
- [x] `task_id` передаётся в вызовы Parser/OCR

### MinIO
- [x] MinIO config добавлен в `config.py`
- [x] Создан `app/storage/__init__.py` — async upload через aiobotocore
- [x] `create_draft()` загружает файл в MinIO после чтения

### Converter-validator
- [x] `HTTP_422_UNPROCESSABLE_CONTENT` → `HTTP_422_UNPROCESSABLE_ENTITY`

## Осталось 🔴

### Protocol mismatch: Converter ожидает raw_json, а не file_key
Converter preview endpoint принимает `RawJsonRequest`:
- `task_id`, `version_id`, `document_id`, `raw_json` (результат парсера)
- А оркестратор шлёт `{file_key, draft_id}`

**Нужно:** переделать pipeline так, чтобы Converter получал результат Parser'а, а не сырой file_key. Либо изменить Converter endpoint на приём file_key.

## Затронутые файлы
| Файл | Изменения |
|------|-----------|
| `docker-compose.yml` | celery worker queue + healthcheck |
| `orchestrator_service/requirements.txt` | +aiobotocore, +botocore |
| `orchestrator_service/app/core/config.py` | +MinioConfig |
| `orchestrator_service/app/storage/__init__.py` | **новый** — MinIO upload |
| `orchestrator_service/app/api/v1/endpoints/drafts.py` | upload в MinIO в create_draft |
| `orchestrator_service/app/services/parser_client.py` | /api/v1 prefix, task_id |
| `orchestrator_service/app/services/ocr_client.py` | /api/v1 prefix, task_id |
| `orchestrator_service/app/services/converter_client.py` | /api/v1 prefix |
| `orchestrator_service/app/schemas/requests.py` | +task_id в схемах |
| `orchestrator_service/app/tasks/pipeline_formation.py` | _run_async fix, task_id передача |
| `converter_validator_service/app/api/v1/exception_handlers.py` | UNPROCESSABLE_CONTENT fix |
