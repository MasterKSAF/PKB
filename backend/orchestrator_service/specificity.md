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
- **Preview-фаза:** Upload → Parser (3 страницы) → [OCR fallback] → Converter-validator
- **Decision:** auto-approve (если preview полный) или ожидание решения пользователя
- **Full-фаза:** Parser → [OCR fallback] → Converter-validator → Registry

### 1.3a. Parser-first стратегия (27.06)
- **Parser** пробуется первым для ВСЕХ типов файлов (включая image/*).
- **OCR fallback** при:
  1. `ConnectError` / ошибке Parser (через `on_step_failed`)
  2. `preview_not_supported` от Parser (через `_on_preview_completed`)
- Опции: `PARSER_ENABLED`, `OCR_ENABLED`, `PARSER_FALLBACK_TO_OCR`.
- Если оба disabled — `ValueError` при старте пайплайна.

### 1.3b. TaskStep.input_data / output_data — JSONB
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

### 2.3. Прокси drafts в оркестраторе для совместимости (23.06, обновлено)
Оркестратор добавляет прокси GET /drafts/{id} и PATCH /drafts/{id}/metadata.

**Причина:** чекер ожидает эти эндпоинты от оркестратора. Registry остаётся source of truth.

**Решение (23.06, обновлено):**
- `GET /api/v1/drafts/{id}` — прокси в Registry с трансформацией ответа (draft_id, document_id, version_id, is_new_document).
- `PATCH /api/v1/drafts/{id}/metadata` — прокси в Registry для обновления метаданных черновика.
- `GET /api/v1/drafts` (list) — не добавлен, остаётся в Registry.
- `GET /api/v1/documents/{id}/tasks` — endpoint в orchestrator для связи документа с задачами пайплайна.

## 3. Технические долги

### 3.1. Integration tests
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

### 3.5. Тесты test_tasks.py (2 теста) — detail wrapper FastAPI
`test_get_task_status_not_found` — проверяет `"error" in data`, но FastAPI
оборачивает HTTPException.detail в `{"detail": ...}`.
`test_get_task_status_without_auth` — в mock-режиме auth не блокирует, но
эндпоинт возвращает 404, а не 200.

### 3.6. Longpoll в тестах — дефолт 15с
	В эндпоинте `GET /drafts/{id}/preview/status` параметр `longpoll` по
	умолчанию равен 15 секундам. Тесты без явного `longpoll=0` ждут таймаута.
	Исправлено в `test_drafts.py` через `params={"longpoll": 0}`.

### 3.7. MinIO upload — требуется mock в conftest (26.06)
Тесты API (`test_drafts.py`) используют `TestClient`, который вызывает `upload_file`
из `app.storage`. Поскольку MinIO нет в тестовом окружении, требуется
`patch("app.api.v1.endpoints.drafts.upload_file", new=AsyncMock())` в conftest.
Без патча тест ждёт ~40с таймаута соединения.

### 3.8. Empty file validation в POST /drafts (27.06)
Ранее пустой файл (0 байт) проходил все проверки и создавал черновик.
Добавлена явная проверка `file_size == 0 → 422 EMPTY_FILE`.
Найдено тестом `test_create_draft_with_empty_file_returns_422`.

### 3.9. `data.get("id") or data.get("draft_id")` — 0 is falsy (27.06, ИСПРАВЛЕНО)
В `get_draft` эндпоинте (drafts.py) было:
```python
"draft_id": data.get("id") or data.get("draft_id")
```
Проблема: 0 числовой falsy в Python. Если id=0 — ответ draft_id=None.
**Исправление:** заменено на `data.get("id") if data.get("id") is not None else data.get("draft_id")`.
Аналогичный фикс для `doc_id` (registry_document_id) и `document_id` в `orchestrator.py:662`.

### 3.10. POST /drafts Idempotency-Key (27.06)
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

### 4.1. Auth Service (8082) — `MissingGreenlet` при подключении к БД

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

**Статус: 🔴 открыто.**

---

### 4.3. CRLF в entrypoint.sh — restart loop контейнера

**Симптом:** `exec entrypoint.sh: no such file or directory` — контейнер в restart loop.

**Причина:** на Windows `entrypoint.sh` получает CRLF, `#!/bin/bash\r` не находится.

**Решение при появлении:** `sed -i 's/\r$//' backend/service_checker/docker/entrypoint.sh`
или `git config core.autocrlf input` перед клонированием.

---

### 4.4. `autorestart=true` — бесконечные перезапуски упавших сервисов

**Проблема:** supervisor настроен с `autorestart=true` и `startretries=5`.
Падающие сервисы (auth, gateway, registry) перезапускаются бесконечно,
лог `.err` раздувается до 13+ МБ за несколько минут.

**Актуальная конфигурация** (`service_checker/docker/supervisord.conf`):
```
autorestart=false
startretries=0
```
— одна попытка запуска, упал — значит упал, логи не плодятся.

---

### 4.5. Stale volume `app_logs` — логи с прошлых запусков не очищаются

**Проблема:** при `docker compose rm -f app` volume `app_logs` **не удаляется**.
Новый контейнер монтирует старый volume с логами за 18 МБ.
Отчёт errors_*.md весит 17-18 МБ вместо 26 КБ.

**Актуальные команды для чистого запуска:**
```bash
docker compose -f service_checker/docker/docker-compose.yml down -v
```
Или точечно для app:
```bash
docker compose -f service_checker/docker/docker-compose.yml stop app
docker compose -f service_checker/docker/docker-compose.yml rm -f app
docker volume rm docker_app_logs
```

---

### 4.6. Ожидание инициализации — достаточно 10 секунд

После старта контейнера все 10 Python-процессов запускаются за ~10 с.
Проверка health раньше — connection refused.

```bash
sleep 10
python backend/service_checker/service_checker.py docker --action health
```

---

### 4.7. Автоматизация: entrypoint сам доустанавливает зависимости

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

### 11. TortoiseGit + sparse-checkout = скрытые конфликты

**Симптом:** `git pull` показал "All conflicts fixed", TortoiseGit
  не даёт закоммитить, после принудительного коммита в HEAD лежат
  маркеры `<<<<<<<` в файлах вне sparse-кассы.
**Причина:** TortoiseGit не показывает конфликты в файлах, исключённых
  sparse-checkout'ом. Git считает merge завершённым "по индексу",
  но реальные конфликты вне рабочей копии не разрешены.
**Правило:** При merge с sparse-checkout — временно расширяй кассу
  на `/*`, делай pull, разрешай **все** конфликты, коммить,
  потом сужай обратно. Проверять: `git grep -nE '^(<<<<<<<|=======|>>>>>>>)'`.

### 12. ИСПРАВЛЕНО (27.06): duplicate steps + registry 409

**Проблема**: Полный pipeline зависал на preview_ocr (pending) и registry_creation (pending).
- preview_ocr: дублирующийся шаг (один completed, второй pending) блокировал проверку `all()`
- start_pipeline создавал шаги без проверки существующих
- registry_creation: run_registry_step падал с 409 Conflict, т.к. approve_draft уже обновил статус draft

**Что исправлено**:
- `start_pipeline`: идемпотентное создание (skip if exists)
- `on_step_completed`: приоритет pending > completed при выборе шага
- `_wait_for_preview`: дедупликация с приоритетом статуса (failed > completed > running > pending)
- Добавлен `_find_best_step`: предпочитает completed для чтения output_data
- `run_registry_step`: 409 Conflict = idempotent success

**Проверено**: pipeline за ~15с, RAG Search 150 результатов.
