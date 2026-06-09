# Специфичные архитектурные решения и аномалии

## 1. Архитектурные решения

### 1.1. Оркестратор не хранит документы
Черновики → `registry.drafts` (Registry), документы → `registry.documents` (Registry).
Оркестратор хранит только `pipeline.tasks` и `pipeline.task_steps`.

### 1.2. Graceful fallback при вызове внешних сервисов
При `ConnectError` (сервис недоступен) `base_client.call()` не пробрасывает
исключение, а возвращает `mock_response` как fallback. Это осознанное решение
для обеспечения отказоустойчивости в development-окружении.
В production-режиме ожидается, что все сервисы доступны, и fallback будет
заменен на корректную обработку ошибок с ретраем через tenacity.

### 1.3. Двухфазный pipeline
- **Preview-фаза:** Upload → OCR/Parser (3 страницы) → Converter-validator
- **Decision:** auto-approve (если preview полный) или ожидание решения пользователя
- **Full-фаза:** OCR/Parser → Converter-validator → Registry

### 1.3. TaskStep.input_data / output_data — JSONB
Вместо `input_ref` / `output_ref` (строковые ссылки) используются JSON-контейнеры.
В SQLite хранятся как JSON, в PostgreSQL — как JSONB.

### 1.4. Longpoll — Database polling (Вариант B)
Выбран вариант B (опрос БД) вместо Redis Pub/Sub для простоты.
При появлении Redis в инфраструктуре можно перейти на Вариант A.

## 2. Расхождения со спецификациями

### 2.1. `docs/api/orchestrator_service_api.md` — устарела
Спецификация API описывает старую архитектуру:
- `POST /documents` как точка входа (сейчас `POST /drafts`)
- `POST /tasks/{task_id}/preview` (сейчас `POST /drafts/{draft_id}/preview`)
- `version_id` в ответе `POST /drafts` — нет версии на этапе черновика

**Статус:** Спецификация требует обновления, но это не блокирует разработку.
Код соответствует `docs/database/db_diagrams.md` и `docs/pipelines/*`.

### 2.2. `id` моделей — Integer, не BigInteger
В SQLite `Integer` и `BigInteger` эквивалентны (оба — INTEGER).
Для PostgreSQL в production нужно убедиться, что миграции создают BIGINT.

### 2.3. `file_key` в `approve_draft` — исправлен `UnboundLocalError`
При `full_completed=True` переменная `file_key` была не определена вне блока `if not task.full_completed:`,
что вызывало `UnboundLocalError`. Исправлено: инициализация `file_key` вынесена до условного оператора.

## 3. Технические долги

### 3.1. Integration tests (✅ переписаны)
- `tests/integration/test_celery_tasks.py` — 5 тестов (Celery task functions with mocks)
- `tests/integration/test_pipeline_formation.py` — 8 тестов (PipelineOrchestrator + DB + mocks)
- `tests/integration/test_pipeline_preview.py` — 6 тестов (preview phase: API + orchestrator)

### 3.2. Сериализация JSONB для SQLite
SQLite не поддерживает JSONB нативно. Текущая реализация использует `sqlalchemy.JSON`,
который корректно работает через SQLAlchemy. Для PostgreSQL заменить на
`sqlalchemy.dialects.postgresql.JSONB`.

### 3.3. Celery задачи используют `_run_async`
В `app/tasks/pipeline_formation.py` используется `_run_async` для запуска async-кода
из синхронных Celery-задач. Это временное решение — в production Celery-задачи
должны быть полностью async (Celery 6+ поддерживает async задачи).

### 3.4. Исправлен `UnboundLocalError` в `approve_draft`
В `app/core/pipeline/orchestrator.py` метод `approve_draft`:
- При `task.full_completed=True` переменная `file_key` была не инициализирована,
  но использовалась при создании full_converter/registry_creation шагов.
- **Исправление:** инициализация `file_key` вынесена до условного блока.

### 3.5. Тесты test_tasks.py (2 теста) — detail wrapper FastAPI
`test_get_task_status_not_found` — проверяет `"error" in data`, но FastAPI
оборачивает HTTPException.detail в `{"detail": ...}`.
`test_get_task_status_without_auth` — в mock-режиме auth не блокирует, но
эндпоинт возвращает 404, а не 200.

### 3.6. Longpoll в тестах — дефолт 15с
	В эндпоинте `GET /drafts/{id}/preview/status` параметр `longpoll` по
	умолчанию равен 15 секундам. Тесты без явного `longpoll=0` ждут таймаута.
	Исправлено в `test_drafts.py` через `params={"longpoll": 0}`.

### 3.7. nested BaseSettings не читали flat env vars

При использовании `env_nested_delimiter="__"` плоские env-переменные
(например `REGISTRY_SERVICE_URL`) не маппятся на вложенную модель и вызывали
`ValidationError: extra_forbidden` в Docker-окружении.

**Исправлено:**
- `services` и `pipeline` используют `default_factory=` вместо прямого вызова
  конструктора, чтобы дочерний `BaseSettings` перечитывал env-переменные
  при каждом создании `Settings()`
- В `Settings.model_config` добавлено `extra='ignore'`, чтобы плоские env-переменные
  не вызывали ошибок валидации (они игнорируются на уровне `Settings`,
  но читаются вложенным `ServiceConfig`)
- `AUTH_SERVICE_URL` / `AUTH_SERVICE_MOCK` не добавлены в `ServiceConfig` —
  оркестратор не взаимодействует с Auth Service напрямую
  (всегда mock-режим в `app/api/deps/__init__.py`)

### 3.8. Функции Document API документированы в `docs/api/orchestrator_service_api.md`
		Эндпоинты групп **documents** и **pages** (`/api/v1/documents/...`) описаны
		в `docs/api/orchestrator_service_api.md` и являются частью актуального API.
		Они не имеют аналогов в Draft/Task API, т.к. относятся к разным группам.

		| Функция | Эндпоинт(ы) | Группа в спецификации |
		|---------|------------|----------------------|
		| **Pages** | `GET /documents/{id}/pages`, `.../pages/{num}`, `.../text`, `.../preview` | pages |
		| **File** | `GET /documents/{id}/file` | documents |
		| **Errors** | `GET /documents/{id}/errors` | documents |
		| **Parameters** | `GET /documents/{id}/parameters` | pages |
		| **Queue** | `GET /documents/queue` | documents |
		| **Reprocess** | `POST /documents/{id}/reprocess` | documents |
		| **Versions** | `POST/GET /documents/{id}/versions` | documents |
		| **History** | `GET /documents/{id}/history` | documents |
