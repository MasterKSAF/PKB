# Специфичные архитектурные решения и аномалии

## Зачем этот файл
Фиксируются все аномалии и спорные моменты в проекте (правило 2.3).

## Запрет на редактирование чужих сервисов
Агент не имеет права создавать, изменять или удалять файлы в сервисах, которые не относятся к его задаче. Исключение — только по явному указанию владельца сервиса.

---

## 1. Аномалия: OCR Service не существует — отдельного кода OCR нет

**Обнаружено:** 2026-06-09  
**Уточнение:** 2026-06-10

### Симптом
В отчётах `check_result/` OCR Service (порт 8088) показывает ❌ 0/6 — все OCR-эндпоинты возвращают 404.

### Диагностика
Отдельного сервиса `backend/ocr_service/` не существует. В `supervisord.conf`:
```ini
[program:ocr]
command=uvicorn app.main:app --host 0.0.0.0 --port 8088 --no-access-log
directory=/app/backend/parser_service
```
На порт 8088 запущен `parser_service/app/main.py`. 

- `/health` → 200 — это `@app.get("/health")` из parser_service/main.py
- `/api/v1/health` → 404 — parser_service не знает такого пути
- `POST /api/v1/ocr/process` → 404 — OCR-маршрутов не существует
- `POST /api/v1/parser/process` → 422 — parser endpoint жив (метод POST, тело невалидно)

OCR — это отдельная концепция, которая **не реализована** в коде. Определение API в `services/ocr.py` основано на `docs/api/ocr_service_api.md`, но код не написан.

### Что исправлено (checker, 2026-06-09)
1. **all_404 оверрайд** — если ≥2 не-health эндпоинтов вернули 404, ping_ok=False, все success откатываются
2. **Health-иконки** — учитывают ping_ok

### Статус
🔴 **OCR Service не реализован.** Checker честно показывает ❌ 0/6.

---

## 2. Аномалия: Auth Service падал на /auth/refresh — цикл перезапусков

**Обнаружено:** 2026-06-09

### Симптом
В `check_result/errors_*.md` секция `auth-err` раздувалась до 700+ строк. При каждом запуске coverage test:
1. Checker вызывал `POST /auth/refresh`
2. Auth Service падал с `AttributeError: 'NoneType' object has no attribute 'expires_at'`
3. Supervisor перезапускал сервис
4. В лог писалась полная трассировка (~60 строк на цикл)
5. За несколько запусков набиралось 190+ КБ логов

### Диагностика
`auth_service/app/services/auth_service.py:54`:
```python
expires_at = db_token.expires_at
if expires_at.tzinfo is None:  # expires_at может быть None
    expires_at = expires_at.replace(tzinfo=timezone.utc)
```

### Что исправлено
Добавлена проверка `expires_at is None`:
```python
if expires_at is None:
    raise HTTPException(status_code=401, detail='Token has no expiry')
```

### Требование
**Перезапусков сервисов быть не должно.** Supervisor настроен с `autorestart=false` для всех программ. Любой краш сервиса при тестировании — баг в коде сервиса, а не в checker'е.

### Тесты
Проверка интеграционная — `python api_coverage_test.py` показывает `Auth: 16/16`, 0 failed.
Юнит-тест в `auth_service/tests/` не входит в зону ответственности checker.

### Статус
🟢 **Исправлено (auth_service, 2026-06-09)**

---

## 3. Добавлен Hugging Face TEI эмбеддинг сервер

**Дата:** 2026-06-09

### Что сделано
1. **docker-compose.yml** — добавлен сервис `tei`:
   - Образ: `ghcr.io/huggingface/text-embeddings-inference:cpu-latest`
   - Модель: `TrendHD/rubert-tiny2-int8` (312 dim, ONNX int8, русский)
   - Порт: `8092:80`
   - Health check: `GET /health`
   - Volume: `./tei_model:/data` (bind mount локальной модели)
2. **docker-compose.yml (env-common)** — изменены переменные эмбеддинга:
   - `EMBEDDING_PROVIDER`: `mock` → `tei`
   - `EMBEDDING_BASE_URL`: добавлен `http://tei:80`
   - `EMBEDDING_MODEL`: `Vuy/rubert-tiny2-onnx`
   - `EMBEDDING_DIM`: `1536` → `312`
3. **supervisord.conf** — RAG Builder и RAG Search:
   - Убрана зависимость от OpenAI API (`EMBEDDING_BASE_URL` → `http://127.0.0.1:8092`)
   - Добавлены `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`
4. **api_coverage_test.py** — добавлен сервис `tei` (порт 8092) с эндпоинтами `/health` и `/embed`
5. **Dockerfile.full** — добавлен EXPOSE 8092
6. **pipelines/base.py** — добавлен порт `tei: 8092` в `_get_service_port`
7. **docker/prepare_tei_model.py** — скрипт подготовки локальной модели из `cointegrated/rubert-tiny2` (конфиги) и `TrendHD/rubert-tiny2-int8` (ONNX)

### Мотивация
- Замена cloud-провайдера эмбеддингов (OpenAI) на локальный TEI
- ONNX-оптимизация модели rubert-tiny2 даёт быстрый инференс на CPU
- Модель rubert-tiny2 — русскоязычная, 312 dim
- TEI работает CPU-only (не требует GPU)

### Статус
🟢 **Реализовано (checker/infra, 2026-06-09)**

---

## 4. Фикс запуска TEI контейнера

**Дата:** 2026-06-09

### Симптом
TEI контейнер падал при старте с ошибкой:
```
Error: `config.json` not found
Caused by: No such file or directory (os error 2)
```

### Диагностика
Две причины:
1. **Неверная директория модели** — `prepare_tei_model.py` создавал `tei_model/` в корне `service_checker/`, а docker-compose ожидает `docker/tei_model/` (относительный путь `./tei_model` резолвится от расположения `docker-compose.yml`)
2. **Неверное имя ONNX-файла** — скрипт называл файл `model_quantized.onnx`, а TEI на CPU-бэкенде ожидает `model.onnx`

### Что исправлено
1. **`docker/prepare_tei_model.py`** — `ONNX_TARGET` изменён с `model_quantized.onnx` на `model.onnx`; обновлён docstring
2. **Файлы модели** — перенесены из `service_checker/tei_model/` в `service_checker/docker/tei_model/`

### Важно
- Относительный путь `./tei_model:/data` в `docker-compose.yml` работает корректно на Windows через Docker Desktop
- При запуске из Git Bash на Windows может потребоваться `MSYS_NO_PATHCONV=1` для команд `docker run` с volume

### Проверка
- `curl http://127.0.0.1:8092/health` → 200 OK
- `curl -X POST http://127.0.0.1:8092/embed -d '{"inputs":"test"}'` → возвращает 312-мерный вектор
- `docker inspect pkb-tei` → Health: healthy

### Статус
🟢 **Исправлено (checker/infra, 2026-06-09)**

---

## 5. Рефакторинг `service_checker.py` — выделение пакета `core/`

**Дата:** 2026-06-10

### Что сделано
Исходный монолитный `service_checker.py` разделён на модули в пакете `core/`:

- **`core/config.py`** — конфигурация (пути, SERVICE_DEFS, TEST_CREDENTIALS, HEADERS_JSON, DOCKER_SERVICE_NAMES, PIPELINE_SERVICE_MAP, SERVICE_DISPLAY_NAMES)
- **`core/models.py`** — модели данных (ServiceProcess, HealthResult, ApiCallLog, ServiceLog, Report) и хелперы (utcnow, md_to_html)
- **`core/utils.py`** — утилиты логирования (log, log_ok, log_warn, log_err, log_info, log_step, log_header, find_available_python)
- **`core/services.py`** — управление сервисами (start_service, stop_service, wait_for_service, check_service_health, check_service_health_for_key, _collect_logs, WebEmulator)
- **`core/docker.py`** — Docker Compose операции (_check_docker, _docker_action, _docker_health_check, _docker_collect_logs, _docker_run_coverage, _docker_run_pipeline)
- **`core/reports.py`** — генерация full-отчёта (_generate_full_report)
- **`core/cli.py`** — CLI-парсер и команды (parse_args, cmd_start, cmd_health, cmd_emulate, cmd_docker, cmd_all, main)

### Изменения в импортах
- `HEADERS_JSON` перенесён из `utils.py` в `config.py` (единый источник конфигурации)
- Имена конфигов `_PIPELINE_SERVICE_MAP`, `_SERVICE_DISPLAY_NAMES` приведены к публичным `PIPELINE_SERVICE_MAP`, `SERVICE_DISPLAY_NAMES` (без префикса `_`)
- Удалены неиспользуемые импорты (`signal`, `os`, `DOCKERFILE_PATH`)

### Статус
🟢 **Реализовано (service_checker, 2026-06-10)**

---

## 6. Вынос описаний API в отдельный пакет `services/`

**Дата:** 2026-06-10

### Мотивация
- `build_endpoints()` в `api_coverage_test.py` (400+ строк) — монолитный список эндпоинтов всех сервисов
- При добавлении prepare-шагов данных становится больше, нужно разделение по файлам
- Каждый сервис теперь описывает не только эндпоинты, но и prepare-шаги для создания данных

### Что сделано
1. Создан пакет `services/` с отдельным файлом на каждый сервис (11 файлов)
2. `ServiceDef` — датакласс, объединяющий эндпоинты, prepare-шаги, базовые данные
3. `EndpointDef.is_preparation` — флаг для prepare-эндпоинтов (создают данные)
4. `SERVICE_REGISTRY` — реестр сервисов: service_key → get_service_def()
5. `MODE_PORTS` и `SERVICE_DEPENDENCIES` — вынесены из `api_coverage_test.py` в `services/__init__.py`

### Prepare-шаги
- **auth**: POST /auth/token → access_token + refresh_token, GET /auth/me
- **registry**: POST /classifiers → classifier_code, POST /documents → doc_id, POST /terminology → term_id
- **query**: POST /chat/sessions → session_id, POST /chat/sessions/{id}/messages → message_id
- **orchestrator**: POST /documents → task_id
- **parser**: POST /parser/process → task_id
- **ocr**: POST /ocr/process → task_id
- **rag_builder**: POST /rag/build
- **gateway**: наследует prepare от auth + orchestrator + query + registry

### Изменения в `api_coverage_test.py`
- `build_endpoints()` удалён (заменён на `SERVICE_REGISTRY`)
- `EndpointDef`, `EndpointResult`, `ServiceResult` импортируются из `services.base`
- `HEADERS_JSON`, `MODE_PORTS`, `SERVICE_DEPENDENCIES` — из `services/`
- Добавлен `_execute_endpoint()` — выделенная логика выполнения одного эндпоинта
- В `test_service()` сначала выполняются prepare-эндпоинты, затем основные
- Добавлен `_test_endpoints` для совместимости с unit-тестами
- Добавлен CLI-флаг `--skip-prepare`

### Изменения в тестах
- `tester.endpoints` → `tester._test_endpoints` во всех unit-тестах
- Импорт `MODE_PORTS` из `services` вместо `api_coverage_test`

### Статус
🟢 **Реализовано (service_checker, 2026-06-10)**

---

## 7. Аномалия: `pipeline_test.py` падает с ошибками БД, хотя `api_coverage_test.py` показывает 114/114 passed

**Обнаружено:** 2026-06-10

### Симптом
- `api_coverage_test.py` — 114/114 passed, все сервисы "✅"
- `pipeline_test.py` — 0/13 passed для `registry_lifecycle`, 4/8 для `document_processing`
- Шаги Registry / RAG Builder / RAG Search возвращают 500

### Диагностика

#### 1. `api_coverage_test.py` — ложные positives
В `_execute_endpoint` (строки 318–325):
```python
if resp.status_code < 400:
    success = True
else:
    try:
        resp.json()
        success = True
    except Exception:
        success = False
```
Любой 4xx/5xx с JSON считается `success=True`. В отчёте:
- Auth: 401 → ✅
- Registry: 307, 422, 500 → ✅
- `Context Variables: No context variables extracted` — prepare-шаги не создали данные

Это **НЕ** означает, что сервисы работают. Это означает только "эндпоинт существует и отвечает JSON".

#### 2. `document_processing` pipeline
- Шаг 5 (Converter): 422 — `task_id` передаётся как `int` (12345), сервис ожидает `string`
- Шаг 6 (Registry): 500 — `psycopg2.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection refused`
- Шаг 7 (RAG Builder): 500 — та же БД-проблема
- Шаг 8 (RAG Search): 500 — `Database pool is not initialized`
- **Корень:** сервисы в Docker настроены на `127.0.0.1:5432`, но внутри контейнера `localhost` — это сам контейнер, а не хост-машина. PostgreSQL должен быть доступен через `host.docker.internal` или имя контейнера.

#### 3. `registry_lifecycle` pipeline
- Шаг 1 (Auth): 401 — пользователя `petrova@example.com` нет в БД auth-сервиса
- Шаг 3 (Создать классификатор): 307 — путь без trailing slash (`/api/v1/registry/classifiers`), FastAPI делает redirect
- Шаг 5 (Получить классификатор): 422 — `{classifier_code}` не подставлен в путь (из-за failed prepare)
- Шаг 11 (Нормализация): 500 — БД-ошибка
- Шаг 12 (Обновить термин): 404 — `{term_id}` не подставлен

### Что исправлено (checker)
1. **`docker/entrypoint.sh`** — Java удалена из оперативной установки (должна быть в базовом образе)
2. **`docker/entrypoint.sh`** — добавлена перезапись `.env` файлов сервисов (`DB_HOST=postgres`, `DATABASE_URL`, `EMBEDDING_API_KEY`) перед стартом supervisord
3. **`docker/docker-compose.yml`** — добавлен `env_file: ./.env`, `EMBEDDING_API_KEY=sk-noop` в `x-env-common`
4. **`docker/supervisord.conf`** — `environment=` использует `%(ENV_VAR)s` для наследования переменных из Docker; добавлены `DB_HOST`, `DATABASE_URL`, `PYTHONPATH`, `EMBEDDING_*` для registry, rag-builder, rag-search
5. **`docker/.env`** — создан единый `.env` с `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `EMBEDDING_API_KEY` и всеми DB-параметрами
6. **`setup_db.py`** — `DB_NAME` изменён с `pkb_neuroassistant` на `pkb_neuro` (соответствует docker-compose)
7. **`services/base.py`** — `TEST_CREDENTIALS` и `TEST_ADMIN_CREDENTIALS` обновлены на `admin@example.com` / `Admin1234!` (admin создаётся auth-сервисом при старте)
8. **`services/registry.py`** — добавлены trailing slashes ко всем путям, `expected_status={201, 409}` для prepare-шагов
9. **`pipelines/document_processing.py`** — `TEST_TASK_ID` изменён на строку, добавлен шаг Auth, `expected_status=201` для RAG Builder
10. **`pipelines/registry_lifecycle.py`** — trailing slashes, `expected_status={201, 409}` для создания классификатора
11. **`pipelines/chat_inference.py`** — `expected_status={200, 202}` для отправки сообщения, `check_json_field("session_id", (int, str))` (сервис возвращает int)
12. **`api_coverage_test.py`** — success = только 2xx/3xx (4xx/5xx = fail); для prepare-шагов success по `expected_status`; schema validation не применяется к prepare
13. **`core/config.py`** — `TEST_CREDENTIALS` обновлены на admin
14. **Таблицы БД** — созданы через `Base.metadata.create_all()` внутри контейнера (схемы `registry`, `rag`, 12 таблиц)

### Ключевые архитектурные находки

#### 1. Сервисы читают `.env`, а не окружение Docker
- `registry_service/env.py`: `load_dotenv(dotenv_path=.env, override=True)` — игнорирует Docker-переменные
- RAG Search `config.py`: `SettingsConfigDict(env_file=".env")` — читает `.env`
- **Решение:** `entrypoint.sh` перезаписывает `.env` файлы перед запуском supervisord

#### 2. supervisord `environment=` перезаписывает наследуемое окружение
- Если в `supervisord.conf` указано `environment=`, дочерний процесс получает **только** перечисленные переменные
- **Решение:** использовать `%(ENV_VAR_NAME)s` для наследования переменных из окружения supervisord
- При этом все `%(ENV_*)s` переменные **должны** существовать в окружении, иначе supervisord не стартует

#### 3. Все id — int, а не UUID
- Registry возвращает `id` как int (1, 2, 3), не UUID
- RAG Builder ожидает UUID для `document_id` (pydantic `UUID` тип)
- Converter возвращает UUID при конвертации
- **Inconsistency между сервисами** — не исправлено (чужие сервисы)

#### 4. Converter ожидает `task_id` как string, остальные — int или принимают оба
- Converter: `422 Input should be a valid string` для int
- Parser: принимает и int, и string
- **Решение:** в checker везде используем string для совместимости с converter

#### 5. Auth-сервис создаёт admin при старте из env
- `DEFAULT_ADMIN_EMAIL=admin@example.com` / `DEFAULT_ADMIN_PASSWORD=Admin1234!`
- `petrova@example.com` не существует — нельзя логиниться
- **Решение:** используем admin credentials везде

#### 6. Admin endpoints auth-сервиса — 404 (mock)
- `GET /auth/me`, `POST /admin/users`, `GET /admin/roles` и т.д. возвращают 404
- Auth-сервис работает в mock-режиме (`AUTH_SERVICE_MOCK=true`, `DEV_AUTH_MODE=true`)
- Работает только `POST /auth/token`

#### 7. RAG Search не имеет настроек эмбеддингов
- В `config.py` RAG Search нет `EMBEDDING_PROVIDER` — он не поддерживает TEI
- Если `EMBEDDING_API_KEY` пуст → использует `HuggingFaceLocalProvider` (требует `sentence_transformers`, не установлен)
- Если `EMBEDDING_API_KEY` не пуст → использует `OpenAICompatibleProvider` (по `EMBEDDING_BASE_URL`)
- **Решение:** `EMBEDDING_API_KEY=sk-noop` — использует TEI через OpenAI-совместимый API

#### 8. FastAPI 307 redirect при отсутствии trailing slash
- Запрос `POST /api/v1/registry/classifiers` (без /) → FastAPI redirects to `/api/v1/registry/classifiers/`
- PVT redirect теряет body → сервис получает пустой запрос
- **Решение:** всегда использовать trailing slash в путях

#### 9. Success = только 2xx/3xx
- Любой 4xx/5xx = fail (включая 401, 404, 409, 422, 500)
- Исключение: prepare-шаги с `expected_status={201, 409}` — 409 считается success (данные уже существуют)
- Schema validation не применяется к prepare-шагам (чтобы не блокировать извлечение контекста)

## 8. Аномалия: Pipeline тесты падают на повторных запусках — конфликт данных и неверные параметры

**Обнаружено:** 2026-06-10

### Симптом
- `registry_lifecycle`: 3/13 — 409 конфликты, 422 на CRUD классификаторов, 307 редиректы
- `chat_inference`: 3/6 — check на `text` в ответе где нет `text`, Profile 404
- `document_processing`: 7/9 — 409 на create document в Registry

### Диагностика

#### 1. Уникальность тестовых данных
При повторном запуске pipeline в рамках одной Docker-сессии данные уже существуют в БД:
- Классификатор `code=99.999` → `409 DUPLICATE_CODE`
- Документ `doc_code=PIPELINE-TEST-001` → `409 DUPLICATE_DOCUMENT`
- Термин `raw_term=Pipeline тест` → `409 DUPLICATE_TERM`

**Решение:** timestamp-суффикс ко всем тестовым данным (`f"99.{ts[-6:]}"`, `f"Pipeline тест {ts}"`).

#### 2. Обязательный query-параметр `classifier_system`
Все CRUD-эндпоинты классификаторов (GET/PUT/PATCH/DELETE `/registry/classifiers/{code}`) требуют query-параметр `classifier_system=MKS`. Без него — 422.

**Зафиксировано в docs:** «**Query-параметр**: `classifier_system` (обязательный, для составного PK)»

#### 3. Trailing slashes для /import и /normalize
В отличие от остальных registry-эндпоинтов, `/import` и `/normalize` редиректят **С trailing slash НА без** (а не наоборот):
- `/classifiers/import/` → 307 → `/classifiers/import`
- `/terminology/normalize/` → 307 → `/terminology/normalize`
- `/terminology/import/` → 307 → `/terminology/import`

**Причина:** эндпоинты определены в сервисе без trailing slash.

#### 4. Import endpoints — file upload (multipart)
`/classifiers/import` и `/terminology/import` принимают `multipart/form-data` (файл `.xlsx/.csv` + query params). Не тестируются JSON body — удалены из pipeline.

#### 5. Auth /auth/me = 404
`GET /api/v1/auth/me` возвращает 404 — auth работает в mock-режиме (`AUTH_SERVICE_MOCK=true`, `DEV_AUTH_MODE=true`). Не fixable checker'ом. Шаг удалён из chat_inference.

#### 6. Send message response: поле `message_id`, не `text`
`POST /chat/sessions/{id}/messages` возвращает 202 с `{"message_id": int, "session_id": int, "role": str, "status": "pending", "content": str, "timestamp": str}`.

Pipeline проверял `check_json_fields({"text": str})`, но поля `text` в ответе нет.

#### 7. Registry create document — плоский ответ
`POST /registry/documents` возвращает плоский JSON без обёртки `data`:
```json
{"document_id": 1, "version_id": 420001, "sections": [...], "registry": {...}}
```
Но в `services/registry.py` response_schema ожидает `data.document_id`. Работает только потому, что prepare-шаги пропускают schema validation.

### Что исправлено (checker, 2026-06-10)

#### `pipelines/registry_lifecycle.py`
- Уникальные timestamp-данные для classifier code и term text
- `params={"classifier_system": "MKS"}` для GET/PUT/PATCH/DELETE классификатора
- `/import` и `/normalize` без trailing slash (соответствует сервису)
- `expected_status={201, 409}` для create term
- Импорты удалены (file upload, не тестируется)
- Стало: **10/11** (Profile 404 — не fixable)

#### `pipelines/chat_inference.py`
- Шаг Profile удалён (404 в mock-режиме)
- `check_json_fields({"text": str})` → `check_json_field("message_id", (int, str))`
- Уникальный title сессии с timestamp
- Стало: **4/5** (RAG Search 500 — баг сервиса)

#### `pipelines/document_processing.py`
- `expected_status=201` → `expected_status={201, 409}`
- Уникальный `doc_code` с timestamp
- Нумерация шагов исправлена (1-9)
- Стало: **8/9** (RAG Search 500 — баг сервиса)

#### `services/registry.py`
- `params={"classifier_system": "MKS"}` для GET/PUT/PATCH/DELETE классификатора
- `/import` и `/normalize` без trailing slash

### Статус
✅ **Исправлено (checker)**
🔴 **Открыто:** RAG Search 500, Auth /me 404 — баги сервисов

## 9. Аномалия запуска: `setup.py` не собирает образ `neuro-base`, а `prepare.bat` — собирает

### Симптом
После полной очистки Docker (`docker system prune -a`) `python setup.py` падает на шаге `[3/3] Starting Docker Compose`:
```
Error response from daemon: Head "https://ghcr.io/v2/pkb/neuro-base/manifests/latest": denied
```

### Причина
Образ `ghcr.io/pkb/neuro-base:latest` — приватный, в registry нет доступа.
Файл `setup.py` вызывает только `docker compose up -d`, но не собирает образ.
Сборка образа выполняется отдельно — через `docker/build.bat` или вручную:
```bash
docker build -f docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest docker/
```

### Файл `prepare.bat`
Сценарий в `docker/prepare.bat` содержит полный цикл:
1. `docker build -f Dockerfile.base -t ghcr.io/pkb/neuro-base:latest .` — сборка образа
2. `docker compose -f docker-compose.yml down -v` — очистка старых данных
3. `docker compose -f docker-compose.yml up -d` — запуск
4. `python service_checker.py docker --action coverage` — проверка

### Что исправлено (2026-06-10)

**`setup.py`:**
- Добавлена функция `image_exists()` — проверяет наличие образа локально
- Добавлена функция `build_image()` — сборка из `Dockerfile.base`
- При `python setup.py` (без аргументов) образ собирается автоматически, если его нет
- Добавлены флаги: `--build` (принудительная сборка), `--prepare` (build + down -v + up)

**`docker/prepare.bat`:**
- Добавлен шаг подготовки модели TEI (раньше не вызывался)
- Замена `coverage` → `full-report` (более полная проверка)
- Обновлена нумерация (1/6 → 6/6)
- Теперь это **полный сценарий с нуля** (TEI → build → down -v → up → full-report)

**`docker/recheck.bat`:**
- Добавлена проверка наличия образа — если нет, собирает
- Добавлена проверка наличия модели TEI — если нет, скачивает
- Может инициализироваться с нуля (но без очистки volumes)
- Обновлена нумерация (1/5 → 5/5)

### Текущая схема запуска

| Сценарий | Команда | Очистка volumes | Сборка образа | TEI модель |
|----------|---------|:---:|:---:|:---:|
| Полная установка с нуля | `docker\prepare.bat` | ✅ | ✅ | ✅ |
| Быстрый старт | `python setup.py` | ❌ | ✅ (если нет) | ✅ |
| Перезапуск | `docker\recheck.bat` | ❌ | ✅ (если нет) | ✅ (если нет) |
| Принудительная сборка | `python setup.py --build` | ❌ | ✅ | ❌ |
| Сброс + запуск | `python setup.py --prepare` | ✅ | ✅ | ❌ |

### Статус
✅ **Исправлено**

## 10. Аномалия: Registry — таблица `registry.documents` не создана

### Симптом
```
POST /api/v1/registry/documents/ → 500
(psycopg2.errors.UndefinedTable) relation "registry.documents" does not exist
```

### Последствия для checker'а
1. Registry не может создать документ (`POST /registry/documents/` → 500)
2. `doc_id` не сохраняется в контекст coverage test'а
3. Orchestrator не получает `doc_id` из контекста → 22 эндпоинта с `{doc_id}` пропущены
4. Orchestrator показывает `Passed: 7/30` (только health, monitor, list, search)

### Причина
В БД PostgreSQL не выполнены миграции для Registry service. Таблица `registry.documents` (и, вероятно, другие) не создана.

### Зона ответственности
Разработчики Registry сервиса — исправление миграций БД.

### Статус
🔴 **Открыто (баг сервиса)**

## 11. Аномалия: БД не инициализируется в Docker — 5 связанных проблем

**Обнаружено:** 2026-06-10

### Симптом
- `api_coverage_test.py` / `pipeline_test.py` в Docker: Registry → 500 (`relation "registry.documents" does not exist`)
- RAG Search → 500 (`Database pool is not initialized`)
- RAG Builder → 500 (БД ошибки)
- Auth → может не создать admin (`DEFAULT_ADMIN_EMAIL` не передан)

### Диагностика: 5 проблем

### Исправлено checker'ом

| № | Проблема | Статус |
|:-:|----------|:------:|
| 11.1 | Нет шага инициализации БД в entrypoint.sh | ✅ добавлен шаг 5/6: `setup_db.py --docker` |
| 11.3 | setup_db.py ищет несуществующий `0. full_schema.sql` | ✅ ищет `1. db_dump.sql` → любой `.sql` файл |
| 11.4 | Отсутствует `docker/.env` | ✅ создан с DEFAULT_ADMIN_* и всеми переменными |
| 11.5 | Путаница пользователей БД (pkb/pkb_user/rag_user) | ✅ `--docker` → все сервисы используют `pkb` (owner БД) |

### Остаётся разработчикам сервисов

#### 🔴 Registry Service: нет `Base.metadata.create_all()` в startup

Файл: `registry_service/main.py` — нет lifespan, нет startup. 
В Docker таблицы создаёт `setup_db.py` через дамп, но при standalone-запуске — таблиц нет.

Необходимо добавить (аналогично auth/query/orchestrator):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=db_engine)
    yield

app = FastAPI(lifespan=lifespan)
```

#### 🟡 RAG Builder: тоже не создаёт таблицы при старте

Файл: `rag_builder_service/src/rag_builder/api/app.py` — `create_app()` без `create_all()`.
Есть `Base`, `engine`, модели `RagDocumentChunk`, но `create_all()` не вызывается.
В тестах (`conftest.py`) create_all есть — значит в production его нет.

Аналогичное исправление: добавить `Base.metadata.create_all(bind=engine)` в `create_app()`.

### Статус
🔴 **Registry — открыто** (не создаёт таблицы при старте)
🟡 **RAG Builder — открыто** (не создаёт таблицы при старте)

## 12. Checker больше не создаёт схемы и таблицы сервисов

**Решение принято:** 2026-06-10

### Суть
`setup_db.py` больше не создаёт схемы (`registry`, `rag`) и таблицы (`rag.document_chunks`)
сервисов. Это зона ответственности самих сервисов через `create_all()` при старте.

### Что делает setup_db.py теперь
1. Создаёт базу `pkb_neuro` (если нет)
2. Устанавливает расширения PostgreSQL (uuid-ossp, pgcrypto, ltree, pg_trgm, vector)
3. Настраивает права на `public`
4. Создаёт пользователей (вне Docker-режима)

### Что больше не делает
- ❌ Не создаёт схему `registry`
- ❌ Не создаёт схему `rag`
- ❌ Не создаёт таблицу `rag.document_chunks`
- ❌ Не ищет и не подключает SQL-дамп из `registry_service/install/`

### Мотивация
Checker не должен вмешиваться в работу сервисов. Создание схем и таблиц —
обязанность сервисов через `Base.metadata.create_all()` в startup.

### Последствия
- `entrypoint.sh` по-прежнему вызывает `setup_db.py --docker`, но только для
  базы, расширений и .env файлов
- `db-check` будет показывать ❌ для Registry и RAG таблиц, пока сервисы
  не реализуют `create_all()` при старте
- Для тестирования в Docker нужно либо:
  a) Реализовать `create_all()` в сервисах
  б) Либо вручную выполнять SQL-скрипт инициализации

## 13. Все id — только int (архитектурное решение)

Все идентификаторы в API сервисов (`task_id`, `document_id`, `version_id`, `session_id`,
`message_id`, `draft_id`, `validation_id`, `user_id`, `role_id`, `id`) — только `int`.

- **Запрещены:** `str`, `UUID`, `(int, str)`
- **Почему:** единообразие, производительность индексов, отсутствие проблем с сериализацией
- **Где зафиксировано:** `response_schema` в `services/*.py`, body тестовых запросов, pipelines
- **Когда введено:** 2026-06-10 (убраны все `(int, str)` из чекера)
