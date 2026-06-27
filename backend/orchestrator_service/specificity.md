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

### 1.5. Все ID-колонки — BigInteger (64-bit)
Первичные ключи (`id`) и внешние ключи (`task_id`, `draft_id`, `document_id`,
`version_id`) во всех моделях (`Task`, `TaskStep`, `DraftNotification`) —
`BigInteger`. В PostgreSQL это `BIGINT` (int8), в SQLite — `INTEGER` (64-bit).

Для PK-колонок используется `_BIGINT_PK = BigInteger().with_variant(Integer, "sqlite")`,
потому что SQLite требует ровно `INTEGER` для `AUTOINCREMENT` — `BIGINT` не подходит.
FK-колонки (`task_id`, `draft_id`, `document_id`, `version_id`) — просто `BigInteger`,
автоинкремент им не нужен.

### 1.6. Валидация данных на границе service client
Все запросы к внешним сервисам проходят через `ServiceClient.call()`.
Там добавлены два уровня защиты:
1. **Pydantic request_model** — валидация структуры, если схема передана
2. **JSON serialization guard** — `json.dumps()` проверка для всех `json` kwargs

Ошибка выбрасывается как `TypeError` ДО ветвления mock/real, что
исключает «тихие» ошибки в мок-режиме и крахи при HTTP-сериализации.

### 1.6. partially_indexed статус (P2I-1)
При индексации через RAG Builder, если `indexed_count < expected_count`,
задача переводится в статус `partially_indexed`, а не `completed`.
Это позволяет мониторингу обнаружить частичную индексацию.

### 1.7. Таймауты pipeline (P3S-1/P3S-2)
Два уровня таймаутов:
- **Per-state timeout (30 с):** шаг, зависший в `pending` дольше 30 с,
  помечается как `failed` с кодом `PENDING_TIMEOUT`.
- **Absolute timeout (48 ч):** задача, активная дольше 48 ч,
  принудительно завершается с кодом `ABSOLUTE_TIMEOUT`.
Оба обрабатываются в `cleanup_stale_tasks()` scheduler'а (Celery Beat).

### 1.8. Валидация цитирований [source:N] (P3S-4)
LLM-ответы проверяются на корректность формата `[source:N]`.
При несоответствии: retry (2 попытки с авто-фиксом), затем fallback
(удаление невалидных цитирований).

### 1.9. enrichment_skipped в ответе поиска (P3S-6)
Ответ `POST /documents/search` содержит поле `enrichment_skipped: bool`.
Показывает, был ли пропущен этап LLM-обогащения результатов.
По умолчанию `false` — обогащение выполняется.

### 1.10. Integrity check после индексации (P2I-2)
После успешного вызова `index_document` в RAG Builder выполняется self-check:
- Вызов `check_index()` проверяет `integrity_ok` флаг со стороны RAG
- inline-проверка: если `expected_count > 0 && indexed_count == 0` — INTEGRITY_CHECK_FAILED
- При провале — шаг помечается `failed` с кодом `INTEGRITY_CHECK_FAILED`
- Фоновая задача `integrity_check` (scheduler) перепроверяет завершённые индексации раз в 6ч

### 1.11. Document status update (RG-1)
`PATCH /registry/documents/{id}/status` — internal-эндпоинт, доступный только Orchestrator.
Используется для обновления статуса документа после индексции.
Метод: `RegistryServiceClient.update_document_status()`.

### 1.12. RAG Builder API: sections-модель (RS-6/RS-7, уточнение 20.06)
- Эндпоинт: `POST /rag/build` (не `/rag/index`).
- Вход: `document_id` + `sections[]` (типизированная структура: `section_id`, `parent_id`, `clause`, `title`, `level`, `path`, `page` 1-based, `bbox` 0..1, `type`, `content`).
- `section_id` стабилен внутри документа, старый индекс удаляется перед переиндексацией.
- `chunk_id` — технический retrieval ID, цитирование НЕ по нему.
- Выход: `202 Accepted` + `indexing_txn_id`. Финальный ответ через longpoll: `indexed`/`failed` + `chunks_count`, `indexed_at`, `warnings[]`, `errors[]`.
- Оркестратор получает sections из Registry (`GET /registry/documents/{doc_id}/sections`) перед вызовом RAG Builder.

### 1.13. RAG Search API: только query/valid_at/filters (RS-6, уточнение 20.06)
- Запрос содержит только `query`, `valid_at`, `filters`.
- `search_type`, `top_k`, `rerank`, `version_id` **не передаются** — все параметры поиска только из `app_settings`.
- Ответ: `source{}` (document_id, section_id, clause, path, page, bbox, section_title, content, content_hash) + `retrieval{}` (chunk_id, score, mode) + `context[]`.

### 1.14. Query Service: плоская структура sources (RS-6, уточнение 20.06)
- Для UI источники возвращаются плоской структурой: `document_id`, `document_title`, `section_id`, `clause`, `path`, `page`, `excerpt`, `score`.
- Без `chunk_id`, `mode` и прочих retrieval-метаданных.
- Цитирование — только `document_id` + `section_id`.
- В историю чата сохраняется плоский `sources[]` без `chunk_id`/`mode`.

## 2. Расхождения со спецификациями

### 2.1. `docs/api/orchestrator_service_api.md` — устарела
Спецификация API описывает старую архитектуру:
- `POST /documents` как точка входа (сейчас `POST /drafts`)
- `POST /tasks/{task_id}/preview` (сейчас `POST /drafts/{draft_id}/preview`)
- `version_id` в ответе `POST /drafts` — нет версии на этапе черновика

**Статус:** Спецификация требует обновления, но это не блокирует разработку.
Код соответствует `docs/database/db_diagrams.md` и `docs/pipelines/*`.

### 2.2. `file_key` в `approve_draft` — исправлен `UnboundLocalError`
При `full_completed=True` переменная `file_key` была не определена вне блока `if not task.full_completed:`,
что вызывало `UnboundLocalError`. Исправлено: инициализация `file_key` вынесена до условного оператора.

### 2.3. Код не синхронизирован с новыми API-контрактами RAG (20.06)
Документация (`docs/api/rag_builder_service_api.md`, `rag_search_service_api.md`) обновлена под RS-6/RS-7, но код оркестратора ещё использует старые контракты:
- `requests.py`: `RagIndexRequest.chunks` вместо `sections`, `RagSearchRequest` содержит `top_k`/`search_type`.
- `rag_client.py`: эндпоинт `/rag/index` вместо `/rag/build`, старая структура ответа.
- `citation_validator.py`: проверяет `idx >= 1` (1-based), а спецификация требует 0-based `[0, len(sources))`.

### 2.4. Прокси drafts в оркестраторе для совместимости (23.06, обновлено)
Оркестратор добавляет прокси GET /drafts/{id} и PATCH /drafts/{id}/metadata.

**Причина:** чекер ожидает эти эндпоинты от оркестратора. Registry остаётся source of truth.

**Решение (23.06, обновлено):**
- `GET /api/v1/drafts/{id}` — прокси в Registry с трансформацией ответа (draft_id, document_id, version_id, is_new_document).
- `PATCH /api/v1/drafts/{id}/metadata` — прокси в Registry для обновления метаданных черновика.
- `GET /api/v1/drafts` (list) — не добавлен, остаётся в Registry.
- `GET /api/v1/documents/{id}/tasks` — endpoint в orchestrator для связи документа с задачами пайплайна.

### 2.5. GET /documents/* в оркестраторе — лишние эндпоинты (22.06)
В `app/api/v1/endpoints/documents.py` находилось ~700 LOC мок-эндпоинтов для чтения документов (list, get, status, file, history, errors, parameters, queue, pages/*, versions, approve, delete). Эти операции — зона `registry-service` (см. `docs/api/registry_service_api.md`, группа `documents`).

**Причина появления:** исторически оркестратор проектировался как прокси, но позже был перепроектирован на draft-first с Registry как источником правды. GET-эндпоинты остались как неиспользуемый код.

**Решение (22.06):**
- Все GET /documents/*, POST /documents/* полностью удалены из orchestrator.
- Исключение: `POST /documents/{doc_id}/reprocess` (P2I-9) **восстановлен** (22.06) — операция переиндексации, требующая управления Celery-задачей, остаётся в оркестраторе.
- `app/schemas/documents.py` пересоздан — только ReprocessMode/ReprocessRequest/ReprocessResponse.
- Тесты `tests/test_documents_api.py` удалены (reprocess покрывается интеграционными тестами пайплайнов).

## 3. Технические долги

### 3.1. Integration tests (✅ переписаны)
- `tests/integration/test_celery_tasks.py` — 5 тестов (Celery task functions with mocks)
- `tests/integration/test_pipeline_formation.py` — 8 тестов (PipelineOrchestrator + DB + mocks)
- `tests/integration/test_pipeline_preview.py` — 6 тестов (preview phase: API + orchestrator)

### 3.2. DATABASE_URL — обязательный параметр (без default)
`DATABASE_URL` не имеет значения по умолчанию. Запуск без него вызывает
`RuntimeError` с инструкцией. SQLite допустим только при явном указании
(локальная разработка / тесты). Production использует PostgreSQL.
`aiosqlite` вынесен в тестовые зависимости (requirements.txt).

### 3.3. Сериализация JSONB для SQLite
SQLite не поддерживает JSONB нативно. Текущая реализация использует `sqlalchemy.JSON`,
который корректно работает через SQLAlchemy. Для PostgreSQL заменить на
`sqlalchemy.dialects.postgresql.JSONB`.

### 3.4. Celery задачи используют `_run_async`
В `app/tasks/pipeline_formation.py` используется `_run_async` для запуска async-кода
из синхронных Celery-задач. Это временное решение — в production Celery-задачи
должны быть полностью async (Celery 6+ поддерживает async задачи).

**Проблема (26.06):** async engine с `pool_size=10` создаёт пул соединений asyncpg
при загрузке модуля. При вызове `_run_async()` в новом event loop соединения из
пула привязаны к старому loop → `RuntimeError: Future attached to a different loop`.

**Фикс:** `poolclass=NullPool` — каждое подключение создаётся в текущем event loop.
Дополнительно: `--pool=threads` в celery worker (все I/O bound, тредов достаточно).

### 3.5. Исправлен `UnboundLocalError` в `approve_draft`
В `app/core/pipeline/orchestrator.py` метод `approve_draft`:
- При `task.full_completed=True` переменная `file_key` была не инициализирована,
  но использовалась при создании full_converter/registry_creation шагов.
- **Исправление:** инициализация `file_key` вынесена до условного блока.

### 3.6. Тесты test_tasks.py (2 теста) — detail wrapper FastAPI
`test_get_task_status_not_found` — проверяет `"error" in data`, но FastAPI
оборачивает HTTPException.detail в `{"detail": ...}`.
`test_get_task_status_without_auth` — в mock-режиме auth не блокирует, но
эндпоинт возвращает 404, а не 200.

### 3.7. metadata_overrides вливается в doc_payload через update
`approve_draft` получает `metadata_overrides` и делает
`doc_payload.update(metadata_overrides)`, а не передаёт их как
вложенный объект. Поля (`title`, `doc_code` и др.) становятся
частью payload напрямую.

### 3.8. Longpoll в тестах — дефолт 15с
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

### 3.8. entrypoint.sh с CRLF вызывает restart loop контейнера

**Проблема:** после `git clone` на Windows файл
`backend/service_checker/docker/entrypoint.sh` получает CRLF-окончания.
Контейнер не может выполнить `#!/bin/bash\r` — ядро Linux ищет
интерпретатор `/bin/bash\r` и выдаёт `no such file or directory`.
Docker перезапускает контейнер (`restart: unless-stopped`), возникает restart loop.

**Исправление:** `sed -i 's/\r$//' backend/service_checker/docker/entrypoint.sh`
или `git config core.autocrlf input` перед клонированием.

### 3.9. Функции Document API документированы в `docs/api/orchestrator_service_api.md`

### 3.10. MinIO upload — требуется mock в conftest (26.06)
Тесты API (`test_drafts.py`) используют `TestClient`, который вызывает `upload_file`
из `app.storage`. Поскольку MinIO нет в тестовом окружении, требуется
`patch("app.api.v1.endpoints.drafts.upload_file", new=AsyncMock())` в conftest.
Без патча тест ждёт ~40с таймаута соединения.

### 3.11. pipeline_indexation — отсутствовал import settings (26.06, ИСПРАВЛЕНО)
В `app/tasks/pipeline_indexation.py` не было `from app.core.config import settings`,
хотя использовался `settings.REDIS_URL`. Баг найден при написании unit-тестов.
Все тесты Celery-задач вызывают `.run()` напрямую, что и выявило ошибку.

### 3.12. Empty file validation в POST /drafts (27.06, ДОБАВЛЕНО)
Ранее пустой файл (0 байт) проходил все проверки и создавал черновик.
Добавлена явная проверка `file_size == 0 → 422 EMPTY_FILE`.
Найдено тестом `test_create_draft_with_empty_file_returns_422`.

### 3.13. `data.get("id") or data.get("draft_id")` — 0 is falsy (27.06, НАЙДЕНО)
В `get_draft` эндпоинте (drafts.py, ~строка 509) используется:
```python
doc_id = data.get("id") or data.get("draft_id")
# и
draft_id = data.get("id") or data.get("draft_id")
```
Проблема: если `"id"` = 0 (число), Python считает его falsy и падает
на `"draft_id"`. Если `"draft_id"` тоже нет (Registry ответил без поля) —
в ответе будет `None`.

**Fix:** `data.get("id") if data.get("id") is not None else data.get("draft_id")`
или `data.get("id", data.get("draft_id"))`.
Тест `test_get_draft_with_id_zero_in_storage` документирует баг (xfail).

### 3.14. approve_draft не синхронизирует document_id с Registry (27.06, НАЙДЕНО)
`approve_draft` (orchestrator.py, ~строка 568-594) создаёт документ через
`registry.create_document`, но **никогда не вызывает**
`registry.update_draft_status(document_id=...)`. В результате:
- `GET /drafts/{id}` после approve возвращает `document_id=None`
- `is_new_document` остаётся `True` (хотя документ уже создан)

**Fix:** после `create_document` вызвать:
```python
await registry.update_draft_status(draft_id=draft_id, document_id=document_id)
```
Тест `test_approve_sets_document_id_in_registry` документирует баг (xfail).

### 3.15. POST /drafts Idempotency-Key (27.06, РЕАЛИЗОВАНО)
Добавлена обработка Idempotency-Key для POST /drafts.
In-memory кэш `_IDEMPOTENCY_CACHE` с TTL 1ч.
Повторный запрос с тем же ключом → 200 + существующий draft_id.
В production требуется замена на Redis.

## 4. Проблемы при запуске (ошибки в Python-сервисах)

При `docker compose up -d` контейнер `pkb-neuro` запускает 10 Python-процессов под supervisord.
6 работают, 4 падают с ошибками (см. ниже).

> ⛔ **service_checker не вмешивается в код других сервисов.**
> Проблемы ниже — ошибки в коде соответствующих сервисов.
> service_checker их диагностирует, но **не исправляет**.
> Ответственные разработчики — владельцы сервисов.

---

### 4.1. Auth Service (8082) — `email-validator` (ИСПРАВЛЕНО)

**Ошибка:**
```
ImportError: email-validator is not installed
```

**Причина:** `email-validator` был только в `auth_service/requirements.txt`, но Docker
устанавливает общий `service_checker/docker/requirements.txt`, где его не было.

**Исправление:** добавлен `email-validator>=2.0.0` в `service_checker/docker/requirements.txt`.

**Статус: ✅ ИСПРАВЛЕНО.** После исправления выявилась следующая ошибка, см. 4.1a.

---

### 4.1a. Auth Service (8082) — `MissingGreenlet` при подключении к БД

**Ошибка:** сервер стартует, но падает на этапе lifespan:
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here.
```

**Причина:** код `auth_service` использует `sqlalchemy[asyncio]`, но при создании
подключения к БД синхронный код вызывает асинхронную операцию без правильной
обёртки (greenlet). Проблема в коде сервиса, а не в зависимостях.

**Статус: 🔴 открыто — зона ответственности разработчика Auth Service.**

---

### 4.2. Gateway Mock (8081) — ошибка импорта `router`

**Ошибка:**
```
ImportError: cannot import name 'router' from 'mocks.auth_service.main'
```

**Причина:** `gateway_service/mocks/gateway.py:33`:
```python
from mocks.auth_service.main import router as auth_router
```
В файле `mocks/auth_service/main.py` нет объекта `router`.

**Исправление:** добавить `router` в `mocks/auth_service/main.py`
или исправить импорт в `gateway.py`.

---

### 4.3. Registry Service (8084) — нет модуля `env` (ИСПРАВЛЕНО)

**Ошибка:**
```
ModuleNotFoundError: No module named 'env'
```

**Причина:** `registry_service/main.py:17`:
```python
import env
```
Файл `env.py` отсутствовал в `registry_service/`.

**Исправление:** разработчик создал `registry_service/env.py`.

**Статус: ✅ ИСПРАВЛЕНО**

---

### 4.4. CRLF в entrypoint.sh — restart loop контейнера (ИСПРАВЛЕНО)

**Ошибка:** `exec entrypoint.sh: no such file or directory` — контейнер в restart loop.

**Причина:** на Windows `entrypoint.sh` получает CRLF, `#!/bin/bash\r` не находится.

**Исправление:** `sed -i 's/\r$//' backend/service_checker/docker/entrypoint.sh`
или `git config core.autocrlf input`.

**Статус: ✅ ИСПРАВЛЕНО**

---

### 4.5. Orchestrator (8000) — `extra_forbidden` в Settings (ИСПРАВЛЕНО)

**Ошибка:** pydantic `extra_forbidden` для `auth_service_url`, `auth_service_mock` и др.

**Причина:** pydantic-settings 2.x по умолчанию `extra="forbid"`, а плоские ENV-переменные
из `docker-compose.yml` не описаны в `Settings`.

**Исправление:** в `app/core/config.py` добавлено `extra="ignore"` в `model_config`.

**Статус: ✅ ИСПРАВЛЕНО**

---

### 4.6. `autorestart=true` — бесконечные перезапуски упавших сервисов (ИСПРАВЛЕНО)

**Проблема:** supervisor настроен с `autorestart=true` и `startretries=5`.
Падающие сервисы (auth, gateway, registry) перезапускаются бесконечно,
лог `.err` раздувается до 13+ МБ за несколько минут.

**Исправление:** в `service_checker/docker/supervisord.conf` выставлено:
```
autorestart=false
startretries=0
```
— одна попытка запуска, упал — значит упал, логи не плодятся.

**Статус: ✅ ИСПРАВЛЕНО**

---

### 4.7. Stale volume `app_logs` — логи с прошлых запусков не очищаются (ИСПРАВЛЕНО)

**Проблема:** при `docker compose rm -f app` volume `app_logs` **не удаляется**.
Новый контейнер монтирует старый volume с логами за 18 МБ.
Отчёт errors_*.md весит 17-18 МБ вместо 26 КБ.

**Исправление:** перед чистым запуском удалять volume:
```bash
docker compose -f service_checker/docker/docker-compose.yml down -v
```
Или точечно для app:
```bash
docker compose -f service_checker/docker/docker-compose.yml stop app
docker compose -f service_checker/docker/docker-compose.yml rm -f app
docker volume rm docker_app_logs
```

**Статус: ✅ ИСПРАВЛЕНО**

---

### 4.8. Ожидание инициализации — достаточно 10 секунд

После старта контейнера все 10 Python-процессов запускаются за ~10 с.
Проверка health раньше — connection refused.

```bash
sleep 10
python backend/service_checker/service_checker.py docker --action health
```

---

### 4.9. Автоматизация: entrypoint сам доустанавливает зависимости

В `entrypoint.sh` добавлен шаг 3:
```bash
pip install --no-cache-dir -r /app/backend/service_checker/docker/requirements.txt
```
При каждом старте контейнера зависимости автоматически доустанавливаются.
Это значит: изменил `requirements.txt` → `restart app` → пакеты подтянутся.

**Никаких ручных `pip install` в контейнере больше не нужно.**

Порядок работы после изменений:
```bash
# 1. Изменить код или requirements.txt
# 2. Перезапустить контейнер (он сам доустановит зависимости)
docker compose -f service_checker/docker/docker-compose.yml restart app
sleep 10
# 3. Проверить
python backend/service_checker/service_checker.py docker --action health
```

---

## 5. Функции Document API документированы в `docs/api/orchestrator_service_api.md`
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
		| **Versions** | `POST/GET /documents/{id}/versions` | documents |
		| **History** | `GET /documents/{id}/history` | documents |

		### 3.9. `created_by` в `create_draft` получал объект `CurrentUser` вместо строки

		В эндпоинте `POST /api/v1/drafts/` параметр `created_by` ожидает строку,
		но в коде передавался `current_user or MOCK_USER_ID`, где `current_user` —
		объект `CurrentUser` (из `app/api/deps/__init__.py`).
		Pydantic валидация падала с ошибкой типа.

		**Исправлено:** `created_by=current_user.user_id if current_user else MOCK_USER_ID`.

		### 3.10. Чекер шлёт JSON на multipart-эндпоинт POST /drafts

		Внешняя тестовая система (чекер) отправляет `POST /api/v1/drafts/`
		с JSON-телом `{"title": "...", "content": "..."}`, в то время как
		эндпоинт по спецификации и реализации принимает `multipart/form-data`
		с полями `file`, `document_key` и опциональным `title`.

		**Причина:** чекер использует собственную (устаревшую) спецификацию,
		не совпадающую с актуальным API оркестратора.

		**Статус:** не наша сторона. Если требуется прохождение чекера —
		нужно добавлять поддержку JSON-тела как альтернативного формата.

		---

		## 6. Аномалии, обнаруженные при анализе task assignment (19.06.2026)

		### 6.1. POST /drafts не передаёт mime_type в start_pipeline

		**Файл:** `app/api/v1/endpoints/drafts.py`

		В `create_draft()` есть `file.content_type`, но он не передаётся в `start_pipeline()`.
		`start_pipeline()` вызывается без mime_type (строки 233-238), что приводит к тому,
		что `start_pipeline()` определяет `is_scanned` без контекста — используется дефолт.

		**Нужно:** передавать `mime_type=file.content_type` в `start_pipeline()`.

		### 6.2. start_preview использует hardcoded "application/pdf"

		**Файл:** `app/api/v1/endpoints/drafts.py`, строка 482

		В `start_preview()` при вызове `start_pipeline()` всегда передаётся
		`mime_type="application/pdf"`. Если файл — изображение (PNG/JPEG/TIFF),
		это приведёт к неверному ветвлению OCR vs Parser.

		**Нужно:** хранить mime_type в Task или получать из Registry.

		### 6.3. _check_auto_approve всегда возвращает True

		**Файл:** `app/core/pipeline/orchestrator.py`, строки 288-293

		Метод `_check_auto_approve` всегда возвращает True, что означает auto-approve
		после каждого preview. Это может быть нежелательно для production, где
		требуется ручное подтверждение от пользователя.

		**Нужно:** реализовать реальную проверку (наличие дубликатов, качество метаданных).

		### 6.4. approve_draft не вызывает Registry.create_document()

		**Файл:** `app/core/pipeline/orchestrator.py`, метод `approve_draft()`

		При approve создаются TaskSteps и запускается full_phase, но document_id
		не запрашивается из Registry до registry_creation шага. По заданию (OR-13),
		document_id должен назначаться Registry при approve, а не Converter-validator.

		**Нужно:** при approve вызывать `Registry.create_document()` и
		возвращать document_id в ответе DecideResponse.

		### 6.5. Ветвление OCR vs Parser некорректно для PDF

		**Файл:** `app/core/pipeline/orchestrator.py`, строки 71-73

		Логика `is_scanned`:
		```python
		is_scanned = mime_type in ("image/png", "image/jpeg", "image/tiff") or (
		    mime_type == "application/pdf"  # would need deeper check
		)
		```

		Все PDF считаются scanned → идут в OCR Service. Но digital PDF (с текстовым слоем)
		должны идти в Parser Service. Нужна более глубокая проверка или явное указание
		типа документа при загрузке.

		**Нужно:** добавить параметр `document_type` (digital/scanned) в POST /drafts,
		либо выполнять MIME-детекцию по содержимому (magic bytes).

		### 6.6. Нет разделения внешних и внутренних действий в decide

		**Файл:** `app/api/v1/endpoints/drafts.py`, `decide_draft()`

		Сейчас поддерживаются только `approve` и `reject`. По заданию (OR-12):
		- Внешние (UI): approve, reject
		- Внутренние: proceed, stop_duplicate, force_new_version

		**Нужно:** добавить внутренние экшены с проверкой RBAC.

		### 6.7. Нет проверки идемпотентности preview

		**Файл:** `app/api/v1/endpoints/drafts.py`, `start_preview()`

		При повторном вызове `POST /drafts/{draft_id}/preview` не возвращается 409.
		Запускается новый pipeline, создаётся дублирующая задача.

		**Нужно:** проверять статус draft/task и возвращать 409 если preview уже запущен.

		### 6.8. PreviewMetadata содержит только 5 полей из требуемых 8+

		**Файл:** `app/schemas/drafts.py`, класс `PreviewMetadata`

		Сейчас:
		- doc_code
		- title
		- document_type
		- year
		- revision

		По заданию (OR-9) требуется минимум 8 полей:
		- source_type, era, jurisdiction, mks_oks_code, okstu_code, issuing_body, udk_code

		### 6.9. Нет OTEL SDK

		**Файл:** `app/main.py`

		OpenTelemetry SDK не подключён. Нет инициализации tracer, meter, exporter.
		По заданию (OR-8, CM-6) требуется OTEL интеграция с SigNoz.

		### 6.10. Нет модели DraftNotification

		По заданию (OR-6) требуется таблица `pipeline.draft_notifications`
		для хранения quality.notifications[] от Parser/OCR.
		Сейчас качество не отслеживается.

	### 6.11. Двойное создание document_id (ИСПРАВЛЕНО)

	**Проблема:** approve_draft вызывал Registry.create_document(), и затем
	run_registry_step (Celery задача) снова вызывал create_document().
	Документ создавался дважды.

	**Исправлено:** run_registry_step теперь вызывает update_draft_status()
	вместо create_document(), так как документ уже создан в approve_draft.

	### 6.12. approve_draft не проверял ответ Registry (ИСПРАВЛЕНО)

	**Проблема:** при ошибке Registry.create_document() без исключения,
	document_id = doc_data.get("document_id", draft_id) давал fallback = draft_id,
	и pipeline продолжался с некорректным ID.

	**Исправлено:** добавлена явная проверка `if not document_id: raise ValueError`.

	### 6.13. full_completed не запускал full_converter (ИСПРАВЛЕНО)

	**Файл:** `app/core/pipeline/orchestrator.py`, approve_draft()

	**Проблема:** при full_completed=True (preview вернул полный документ),
	создавались full_converter и registry_creation шаги, но full_converter
	не стартовался (не было start_task_step). Pipeline зависал.

	**Исправлено:** добавлен запуск full_converter step при full_completed=True.

	### 6.14. PDF всегда шёл в OCR (ИСПРАВЛЕНО)

	**Файл:** `app/core/pipeline/orchestrator.py`, строки 71-73

	**Проблема:** `is_scanned = ... or (mime_type == "application/pdf")` —
	все PDF считались сканами и шли в OCR Service. Digital PDF должны
	обрабатываться Parser Service.

	**Исправлено:** логика разделена: image/* + scanned_pdf -> OCR,
	application/pdf (digital) -> Parser.


## Типичные ошибки при разработке

Реальные проблемы, которые возникали в этом проекте. Проверяй перед комитом.

### 1. Старая test_pipeline.db не удалена

**Симптом:** `sqlite3.OperationalError: no such column: tasks.version_id`
**Причина:** SQLAlchemy `create_all()` не добавляет колонки в существующую таблицу.
**Лечение:** `rm -f test_pipeline.db && pytest -q`
**Правило:** Если меняешь `models/pipeline.py` — сразу удаляй test БД.

### 2. Метод переименован, а тесты/вызовы — нет

**Симптом:** `AttributeError: 'OCRServiceClient' object has no attribute 'process_document'`
**Причина:** renamed `process_document` → `process`, но grep не делали.
**Поиск:** `grep -rn "process_preview\|process_full\|process_document" app/ tests/`
**Правило:** После переименования метода — grep по всему проекту.

### 3. Изменён response, старые тесты проверяют старые поля

**Симптом:** `AssertionError: assert 'document_id' in {'data': {...}}'`
**Причина:** ответ OCR изменился с `{"document_id": ..., "pages": [...]}`
  на `{"data": {"task_id": ...}}`, а тесты проверяют старый формат.
**Правило:** После смены структуры ответа — обнови все тесты, которые её проверяют.

### 4. Новая валидация сломала существующие тесты

**Симптом:** `assert response.status_code == 200 → 409`
**Причина:** добавили проверку `pipeline_stage == "decision"` в decide,
  а тесты вызывали approve сразу после create_draft (stage=upload).
**Фикс:** Тест должен симулировать полный pipeline, а не резать углы.
  Либо — поднять stage вручную через `db_session` перед вызовом.
**Правило:** Новая валидация ломает тесты, которые ходили в обход логики.
  Это нормально. Исправляй тесты, не ослабляй валидацию.

### 5. Разные сессии БД в фикстуре и в endpoint'е

**Симптом:** фикстура изменила task в БД, endpoint не видит изменений → 409.
**Причина:** фикстура использует `db_session`, endpoint — `AsyncSessionLocal()`.
  Изменения не видны пока не сделан `commit()`.
**Фикс:** после `flush()` делать `await db_session.commit()`.
**Правило:** Если фикстура меняет БД для endpoint'а — commit обязательно.

### 6. Потерянная запятая в аргументах

**Симптом:** `SyntaxError` при запуске.
**Причина:** было `version_id=task.version_id` без запятой, следом `status=...`
**Фикс:** всегда проверяй trailing comma после добавления/удаления параметров.

### 7. orphan-assertions после рефакторинга тестов

**Симптом:** `NameError: name 'data' is not defined`
**Причина:** после переписывания теста остались assert'ы от старой версии,
  которые ссылаются на переменные из удалённого контекста.
**Правило:** после рефакторинга теста — удаляй все assert'ы, которые не
  относятся к новому телу функции.

### 8. Модель изменилась, а ответ API — нет

**Симптом:** новое поле есть в БД, но не возвращается из endpoint'а.
**Пример:** `version_id` добавили в модель Task, а `get_task_by_id`
  возвращал `version_id=None` (хардкод).
**Правило:** После добавления колонки — проверь что endpoint её читает.

### 9. Двойной вызов create_document

**Симптом:** Документ создаётся дважды.
**Причина:** approve_draft вызвал `Registry.create_document()`, и потом
  run_registry_step (Celery) снова вызвал `create_document()`.
**Правило:** Если один слой уже создал ресурс — другой слой должен
  обновлять, а не создавать заново.

### 10. Кэш перед read_file

Перед `read_file` проверь, загружен ли файл в кэш текущей сессии.
Повторное чтение уже загруженных файлов — потеря токенов.
Исключение: если файл гарантированно изменился между сессиями.