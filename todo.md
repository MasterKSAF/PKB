# Todo — запуск системы + исправление ошибок загрузки черновиков

## Исправлено

### 1. 307 redirect при POST /api/v1/drafts
- **Причина:** роут `@router.post("/")` → FastAPI редиректил `/drafts` → `/drafts/`
- **Файл:** `backend/orchestrator_service/app/api/v1/endpoints/drafts.py:83`
- **Фикс:** `"/"` → `""`
- **Тест:** `test_draft_creation_path_no_trailing_slash` — проверяет путь без слеша

### 2. Location с Docker-hostname утекал в браузер
- **Причина:** Gateway проксировал 3xx ответы как есть
- **Файл:** `backend/gateway_service/gateway/client.py:414-431`
- **Фикс:** перезапись Location с внутреннего URL на Gateway
- **Тест:** интеграционный `test_draft_upload_full_chain` — проверяет 202, не 307

### 3. Неверные пути к Registry в оркестраторе
- **Причина:** клиент Registry стучался `/registry/drafts` вместо `/api/v1/registry/drafts`
- **Файл:** `backend/orchestrator_service/app/services/registry_client.py`
- **Фикс:** все пути заменены на `/api/v1/registry/...`
- **Тест:** интеграционный — проверяет 202 (не 404)

### 4. trace_id varchar(32) не вмещал UUID (36 символов)
- **Причина:** `String(32)` в модели Task
- **Файл:** `backend/orchestrator_service/app/models/pipeline.py:103`
- **Фикс:** `String(32)` → `String(36)` + ALTER TABLE
- **Тест:** интеграционный — проверяет 202 (не 500)

### 5. Пайплайн `orchestrator_draft_lifecycle` переведён на Gateway
- **Файл:** `backend/service_checker/pipelines/orchestrator_draft_lifecycle.py`
- Все 11 шагов через `service="gateway"`, `port=8080`
- Пути создания черновиков без трейлинг-слеша
- MinIO не трогали (не идёт через Gateway)

### 6. Тесты
- `tests/test_integration_draft_upload.py` — 2 интеграционных теста
- `tests/test_pipeline_orchestrator_draft_lifecycle.py` — 9 юнит-тестов
- `tests/test_pipeline_service_consistency.py` — адаптированы под Gateway (2 фикса)

### 7. Gateway — защита от будущих утечек Location
- `backend/gateway_service/gateway/client.py` — перехват 3xx, замена Location

### 8. Infinity — CPU-версия (экономия ~3.2 ГБ)
- `docker-compose.yml` — `latest` → `latest-cpu`, `mem_limit: 8g` → `4g`

### 9. start_web_real.bat
- Новый батник для запуска production-стека из корневого docker-compose.yml

## Осталось (передано в задачу агенту)
- Перевести остальные 14 пайплайнов на Gateway
- См. `backend/service_checker/tasks/translate_pipelines_to_gateway.md`
