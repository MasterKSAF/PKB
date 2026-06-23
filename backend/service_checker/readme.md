# PKB Neuroassistant — Service Checker

Назначение — **запустить сервисы в Docker (recheck.bat) и проверить корректность их работы.**

Это не production-сервис. Используется для локальной разработки, отладки и интеграционного тестирования.

Что делает проверка:

| Этап | Действие |
|------|----------|
| Docker Compose up | Запуск инфраструктуры: PostgreSQL, Redis, MinIO, TEI, 10 Python-сервисов под supervisord |
| Health Check | Проверка `/health` каждого сервиса — жив ли, отвечает ли |
| API Coverage | Вызов каждого эндпоинта из API-документации (~150 шт.) — проверка HTTP-статуса и JSON-схемы |
| Pipeline Testing | Сквозные сценарии: загрузка → парсинг → индексация → поиск, чат-сессия, CRUD классификаторов |
| DB Check | Проверка БД: расширения, схемы, таблицы (registry, rag, pipeline, auth), индексы |
| Observability Check | SC-1: проверка OTEL SDK, OTLP-экспорт, correlation-id, structured logging, error codes |
| Сбор логов | Чтение supervisor-логов каждого сервиса, поиск ошибок |
| Генерация отчёта | Сводная таблица по всем сервисам (Markdown / HTML) |

> 🔹 service_checker НЕ изменяет код, конфиги или данные сервисов — **кроме `gateway_service` и `orchestrator_service`**, которые разрешено править для исправления багов, не влияющих на бизнес-логику. Остальные сервисы (`auth`, `registry`, `rag_builder` и др.) — **не трогать**, только диагностика.

## Структура

```
service_checker/
├── setup.py                 # One-command setup: модель TEI + Docker Compose
├── Makefile                 # Альтернативный setup (Linux/macOS/Git Bash)
├── core/                    # Основные модули
│   ├── __init__.py
│   ├── api_coverage_test.py  # API Coverage Test (real-режим, Docker)
│   ├── cli.py                # CLI-парсер и команды
│   ├── config.py             # Конфигурация (пути, сервисы, credentials)
│   ├── db_check.py           # Проверка состояния БД
│   ├── docker.py             # Docker Compose управление
│   ├── models.py             # Модели данных (Report, ServiceProcess, HealthResult...)
│   ├── observability_check.py # SC-1: проверка OTEL, OTLP, correlation-id, логов, кодов ошибок
│   ├── pipeline_test.py      # Pipeline Testing (сквозные сценарии)
│   ├── reports.py            # Генерация full-отчёта (coverage + pipeline)
│   ├── service_checker.py    # Точка входа (делегирует в cli.py)
│   ├── services.py           # Запуск/остановка сервисов, health check, эмуляция UI
│   ├── setup_db.py           # Инициализация БД (расширения, схемы, .env)
│   └── utils.py              # Утилиты (логирование, конвертация Markdown→HTML)
├── services/                # Описания API сервисов (эндпоинты + prepare-шаги)
│   ├── __init__.py           # Реестр SERVICE_REGISTRY, MODE_PORTS
│   ├── base.py               # ServiceDef, EndpointDef, константы
│   ├── auth.py               # Auth Service (16 endpoints + 2 prepare)
│   ├── registry.py           # Registry Service (32 endpoints + 3 prepare)
│   ├── orchestrator.py       # Orchestrator Service (23 endpoints + 1 prepare)
│   ├── query.py              # Query Service (18 endpoints + 2 prepare)
│   ├── parser.py             # Parser Service (5 endpoints + 1 prepare)
│   ├── ocr.py                # OCR Service (5 endpoints + 1 prepare)
│   ├── converter_validator.py# Converter-Validator (4 endpoints)
│   ├── rag_builder.py        # RAG Builder (4 endpoints + 1 prepare)
│   ├── rag_search.py         # RAG Search (2 endpoints)
│   ├── tei.py                # TEI Embeddings (2 endpoints)
│   └── gateway.py            # Gateway (агрегирует auth+orchestrator+query+registry)
├── __init__.py               # Пакетный файл
├── __main__.py               # Точка входа python -m service_checker
├── pipelines/               # Модули пайплайнов
│   ├── __init__.py                      # Реестр пайплайнов (8 шт.)
│   ├── base.py                          # Базовые классы (PipelineStep, PipelineRunner и др.)
│   ├── document_processing.py           # Пайплайн обработки документов (12 шагов)
│   ├── chat_inference.py                # Пайплайн чат-инференса (6 шагов, с enrichment_skipped)
│   ├── registry_lifecycle.py            # Пайплайн жизненного цикла Registry (11 шагов)
│   ├── full_document_lifecycle.py       # Полный цикл: создание → ошибка → восстановление (12 шагов)
│   ├── admin_user_lifecycle.py          # Admin управление пользователем (16 шагов, AU-3)
│   ├── registry_quarantine.py           # Карантин классификаторов (10 шагов)
│   ├── orchestrator_draft_lifecycle.py  # Черновик Orchestrator (11 шагов, OR-13/14)
│   └── multi_document_cross_search.py   # Мульти-документный поиск (19 шагов)
├── docker/                  # Docker-конфигурация
│   ├── docker-compose.yml               # 5 контейнеров: postgres, redis, minio, tei, app
│   ├── supervisord.conf                 # Управление Python-сервисами
│   ├── Dockerfile.base / .full          # Образы
│   ├── entrypoint.sh                    # Точка входа
│   ├── prepare_tei_model.py             # Скачивание и подготовка модели TEI
│   ├── recheck.bat                      # Быстрый re-check: сброс БД + restart + full-report
│   ├── recheck_spd.bat                  # Re-check для rag_builder_service_spd: сброс БД + restart + --spd
│   ├── docker-compose.spd.yml           # Override для SPD-компоновки (supervisord.spd.conf + entrypoint.spd.sh)
│   ├── supervisord.spd.conf             # supervisor.conf для SPD (rag-builder-spk вместо rag-builder + rag-search)
│   ├── entrypoint.spd.sh                # entrypoint для SPD (.env для rag_builder_service_spd)
│   └── requirements.txt                 # Python-зависимости всех сервисов
├── tests/
│   ├── conftest.py                        # Общие фикстуры
│   ├── test_success_determination.py      # Логика success/fail для статус-кодов
│   ├── test_override_logic.py             # Оверрайд all_404 и ping_ok
│   ├── test_report_generation.py          # Формирование отчёта
│   ├── test_pipeline_base.py              # Тесты базовых классов Pipeline Testing
│   ├── test_pipeline_steps.py             # Тесты шагов (document_processing, chat_inference, registry_lifecycle)
│   ├── test_pipeline_full_document_lifecycle.py   # Полный цикл документа (12 шагов, skip_if)
│   ├── test_pipeline_admin_user_lifecycle.py      # Admin управление пользователем (10 шагов)
│   ├── test_pipeline_registry_quarantine.py       # Карантин классификаторов (10 шагов)
│   ├── test_pipeline_orchestrator_draft_lifecycle.py # Черновик Orchestrator (8 шагов)
│   ├── test_pipeline_document_approval.py                        # Подтверждение документа (10 шагов)
│   ├── test_pipeline_orchestrator_document_reject.py              # Reject черновика Orchestrator (6 шагов)
│   ├── test_pipeline_orchestrator_metadata_update.py              # Обновление метаданных (6 шагов)
│   ├── test_pipeline_orchestrator_draft_delete.py                 # Удаление черновика (6 шагов)
│   ├── test_pipeline_orchestrator_document_reprocess.py           # Переиндексация (9 шагов)
│   ├── test_pipeline_orchestrator_document_versions.py            # Версионирование (9 шагов)
│   ├── test_pipeline_orchestrator_full_document_lifecycle.py      # Полный цикл через Orchestrator (12 шагов)
│   └── test_pipeline_multi_document_cross_search.py               # Мульти-документный поиск (19 шагов)
├── specificity.md           # Аномалии и архитектурные решения
└── readme.md                # Точка входа (этот файл)
```

## Текущий статус сервисов в Docker

После обновлений (19.06.2026):

| Сервис | Порт | HTTP | supervisorctl | Проблемы |
|--------|:----:|:----:|:-------------:|----------|
| PostgreSQL | 15432 | — | — | здоров |
| Redis | 16379 | — | — | здоров |
| MinIO | 19000 | — | — | здоров |
| TEI | 18092 | 200 | — | здоров |
| Gateway | 8080 | 200 | RUNNING | Новая маршрутизация (GW-12) |
| Orchestrator | 8081 | 200 | RUNNING | Draft-first (OR-11), action вместо decision (OR-12) |
| Auth | 8082 | 200 | RUNNING | roles[] (AU-5), ROLES таблица (AU-2) |
| Query | 8083 | 200 | RUNNING | QS-3/7/10/12 — document_ids, valid_at, rating:int, search |
| Registry | 8084 | 200 | RUNNING | RG-2/6/7/8/9/10 — current_version_id, BM25, valid_at |
| Integration | 8085 | 200 | RUNNING | |
| Converter-Validator | 8086 | 200 | RUNNING | CV-3/3a — /converter/preview, /validate/metadata |
| Parser | 8087 | 200 | RUNNING | PS-5 — единый /process с mode=preview|full, PS-3: draft_id |
| OCR | 8088 | — | RUNNING | OC-8 — единый /process с mode=preview|full, OC-4: draft_id |
| RAG Builder | 8090 | 200 | RUNNING | RB-7: 202 async, RB-8: indexed |
| RAG Search | 8091 | 200 | RUNNING | RS-6: без top_k/search_type, valid_at+filters |

**supervisorctl (обычный):** ✅ 11 процессов RUNNING
**supervisorctl (SPD):** ✅ 10 процессов (rag-builder-spk вместо rag-builder + rag-search)
**.env файлы:** ✅ Создаются автоматически
**.err логи:** ✅ Health check проверяет ошибки

> **⚠️ Частичное обновление сервисов.**
> Docker запущен, но некоторые сервисы могут быть не полностью обновлены
> до спецификации от 19.06.2026. Checker использует tolerant mode:
> - Новые эндпоинты (KNOWN_NEW_ENDPOINTS), возвращающие 404,
>   показываются как warning, а не error.
> - OTEL/корреляционные заголовки — warning, если не реализованы (CM-5).
> - Health check пробует fallback-пути (/api/v1/system/health, /health).
>
> Это нормальное поведение: сервисы обновляются постепенно.

> **Важно:** `recheck.bat` уже запускает **все проверки**:
> 1. Health check (контейнеры + HTTP + supervisorctl + .err логи)
> 2. DB check
> 3. API Coverage Test
> 4. Pipeline Testing
> 5. Observability Check (SC-1)
> 6. Сводный отчёт + сбор логов

> Подробности аномалий — в [`specificity.md`](specificity.md)

## Быстрый старт (с нуля)

### Вариант A — `setup.py` (рекомендуется)

```bash
# Полный setup: модель TEI + сборка образа (если нет) + Docker Compose
python setup.py

# Или по шагам:
python setup.py --build      # Принудительная пересборка base-образа
python setup.py --model      # Только подготовка модели TEI
python setup.py --up         # Только запуск Docker Compose
python setup.py --down       # Остановка Docker Compose
python setup.py --ps         # Статус контейнеров
python setup.py --prepare    # Полный цикл: build + down -v + up (как prepare.bat)
```

> **Важно:** `setup.py` автоматически собирает образ `ghcr.io/pkb/neuro-base:latest`
> из `Dockerfile.base`, если его нет локально. Принудительная пересборка:
> `python setup.py --build`.

### Вариант B — `prepare.bat` (Windows, полный цикл)

```bash
docker/prepare.bat
```
Сборка образа + очистка volumes + запуск + проверка coverage.

### Вариант C — `recheck.bat` (быстрый re-check без установки)

```bash
docker/recheck.bat
```
Автоматически создаёт `docker/.env` через `create_env.py` (если файла нет).
Пересоздаёт контейнеры с чистой БД (kill + rm -v + up) и запускает полный отчёт
(coverage + pipelines + db-check). TEI контейнер не перезапускается.
Подходит для повторных проверок после изменений в сервисах.

> **Внимание:** удаляет volumes с БД — каждый запуск начинается с чистого состояния.

### Вариант C (SPD) — `recheck_spd.bat`

```bash
docker/recheck_spd.bat
```
Отличается от `recheck.bat` только компоновкой Docker:
`rag_builder_service_spd` объединяет API rag_builder + rag_search на одном порту 8090.
Checker подменяет порт `rag_search` → 8090 — никакой отдельной логики не требуется.
Отчёты сохраняются с суффиксом `_spd`:
- `check_result/api_coverage_spd.md`
- `check_result/full_report_spd.md`

Docker-композиция: `docker compose -f docker-compose.yml -f docker-compose.spd.yml`
(с `supervisord.spd.conf` и `entrypoint.spd.sh`).

### Вариант D — вручную

```bash
# 1. Собрать образ (если нет)
docker build -f docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest docker/

# 2. Запустить
python setup.py
```

## Режимы тестирования: Real vs Mock

`ApiCoverageTester` и тесты gateway поддерживают два режима:

| Режим | Описание | Credentials | Применение |
|-------|----------|-------------|------------|
| `real` (по умолчанию) | Против Docker (реальные сервисы) | `Admin1234!` (DEFAULT_ADMIN_PASSWORD) | CI, Docker, продакшн-валидация |
| `mock` | Против Gateway Mock (локальные моки) | `admin123` (SEED_USERS) | Локальная разработка без Docker |

**Управление режимом:**

1. **Переменная окружения** `TEST_MODE`:
   ```bash
   # Real (по умолчанию)
   set TEST_MODE=real
   
   # Mock
   set TEST_MODE=mock
   ```

2. **CLI-флаг** `--mode` для `api_coverage_test.py`:
   ```bash
   python api_coverage_test.py --mode mock
   python api_coverage_test.py --mode real
   ```

3. **Pytest-флаг** `--test-mode`:
   ```bash
   python -m pytest tests/test_gateway_mode.py --test-mode=mock -v
   python -m pytest tests/test_gateway_mode.py --test-mode=real -v
   ```

4. **Программно** через конструктор `ApiCoverageTester(mode="mock")`

**Gateway-специфичные credentials:**
- **Real-режим**: `username: admin@example.com`, `password: Admin1234!` (читается из DEFAULT_ADMIN_PASSWORD env)
- **Mock-режим**: `username: admin@example.com`, `password: admin123` (хардкод SEED_USERS в Gateway Mock)

## Запуск тестов

```bash
# Все unit-тесты (560 тестов, ~5с)
python -m pytest tests/ -v

# По файлам — юнит-тесты (без Docker):
# API Coverage — логика выполнения эндпоинтов
python -m pytest tests/test_api_coverage_execute_endpoint.py -v
python -m pytest tests/test_api_coverage_test_service.py -v
python -m pytest tests/test_success_determination.py -v
python -m pytest tests/test_override_logic.py -v
python -m pytest tests/test_report_generation.py -v

# Pipeline Runner — логика выполнения шагов и пайплайнов
python -m pytest tests/test_pipeline_runner_run_step.py -v
python -m pytest tests/test_pipeline_runner_run.py -v
python -m pytest tests/test_pipeline_base.py -v
python -m pytest tests/test_pipeline_steps.py -v

# Прочее
python -m pytest tests/test_db_setup.py -v          # Статический анализ SQL (без Docker)
python -m pytest tests/test_md_parser.py -v          # Парсинг MD-документации API
python -m pytest tests/test_observability_check.py -v # Наблюдаемость

# ⚠️ Интеграционные тесты (требуют Docker):
python -m pytest tests/test_no_restarts.py -v         # Проверка restart-циклов

# ⚠️ Pipeline Testing — только через модуль (см. 15-ю аномалию в specificity.md):
#    прямой запуск python pipeline_test.py не работает из-за конфликта имён
python -m service_checker docker --action full-report  # Coverage + все пайплайны + сводка

# Фильтрация по сервисам (--services):
python -m service_checker docker --action full-report --services gateway          # Только Gateway
python -m service_checker docker --action full-report --services registry         # Только Registry
python -m service_checker docker --action full-report --services rag_builder,rag_search  # RAG Builder + RAG Search
python -m service_checker docker --action full-report --services auth,registry,query     # Несколько сервисов

# Фильтрация по пайплайнам (--pipelines):
python -m service_checker docker --action full-report --pipelines registry_lifecycle          # Только один пайплайн
python -m service_checker docker --action full-report --pipelines registry_lifecycle,registry_quarantine  # Несколько

# Пропустить coverage или pipelines:
python -m service_checker docker --action full-report --skip-coverage     # Только pipelines
python -m service_checker docker --action full-report --skip-pipelines    # Только coverage

# То же через recheck.bat:
recheck.bat --api gateway                      # Только Gateway
recheck.bat --api rag_builder,rag_search       # RAG Builder + RAG Search
recheck.bat --pipeline registry_lifecycle      # Только один пайплайн
recheck.bat --skip-coverage                    # Без coverage, только pipelines
recheck.bat --skip-pipelines                   # Без pipelines, только coverage

# Coverage test в Docker
python -m service_checker docker --action coverage     # Только coverage

# Database health check
python -m service_checker docker --action db-check     # Проверка БД: таблицы Registry и RAG

# Сохранение отчёта пайплайнов отдельно (если нужен только pipeline без coverage):
python -m service_checker docker --action full-report  # full-report включает всё
```



### TEI (Text Embeddings Inference)

- **Образ:** `ghcr.io/huggingface/text-embeddings-inference:cpu-latest`
- **Модель:** `TrendHD/rubert-tiny2-int8` (312 dim, ONNX int8, русскоязычная)
- **Порт:** 8092 (маппинг на внутренний 80)
- **Загрузка:** локальная из `docker/tei_model/`, подготовка через `prepare_tei_model.py`

## Pipeline Testing

Сквозные сценарии проверки бизнес-пайплайнов:

| Пайплайн | Описание | Сервисы | Шагов |
|----------|----------|---------|:-----:|
| `document_processing` | Полный цикл обработки документа | Auth → MinIO → Parser → Converter → Registry → RAG Builder → RAG Search | 10 |
| `chat_inference` | Чат-сессия с поиском по документам | Auth → Query (Chat) → Query (Text Search) → RAG Search | 5 |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | Auth → Registry | 11 |
| `full_document_lifecycle` | Полный цикл: создание → ошибка → восстановление → удаление → пересоздание | Auth → Registry → RAG Builder → RAG Search | 12 |
| `admin_user_lifecycle` | Admin создаёт пользователя → работа → аудит → деактивация → 401 | Auth → Query | 10 |
| `registry_quarantine` | Карантин классификаторов: accept/reject + валидация | Auth → Registry | 10 |
| `orchestrator_draft_lifecycle` | Черновик Orchestrator: создание → превью → решение → 404 | Auth → Orchestrator | 8 |
| `multi_document_cross_search` | 2 документа → индексация → кросс-поиск → удаление → фильтрация | Auth → MinIO → Parser → Converter → Registry → RAG Builder → RAG Search | 19 |
| `document_approval` | Подтверждение документа: черновик → preview → approve → full → индексация | Auth → Orchestrator → Registry → RAG Builder | 11 |
| `orchestrator_document_reject` | Reject черновика: создание → reject → проверка статуса | Auth → Orchestrator | 6 |
| `orchestrator_metadata_update` | Обновление метаданных черновика (PATCH /metadata) | Auth → Orchestrator | 6 |
| `orchestrator_draft_delete` | Удаление черновика: создание → удаление → 404 | Auth → Orchestrator | 6 |
| `orchestrator_document_reprocess` | Переиндексация: черновик → approve → reprocess | Auth → Orchestrator → Registry | 9 |
| `orchestrator_document_versions` | Версионирование: черновик → approve → новая версия | Auth → Orchestrator → Registry | 9 |
| `orchestrator_full_document_lifecycle` | Полный цикл через Orchestrator: создание → preview → approve → Registry → индексация → удаление | Auth → Orchestrator → Registry → RAG Builder → RAG Search | 12 |

## Ключевые решения

- **2xx/3xx** — success
- **4xx/5xx** — fail (любая ошибка сервиса)
- **all_404 оверрайд** — если >=2 не-health эндпоинтов вернули 404, сервис помечается мёртвым (ping_ok=False, success откатывается)
- **Статус-колонка отчёта** — ❌ если ping_ok=False или есть failed эндпоинты
- **Пайплайны** — сквозные сценарии в отдельных файлах `pipelines/*.py`, запуск через `pipeline_test.py`
- **Эмбеддинги через TEI** — локальный сервер эмбеддингов Hugging Face TEI с моделью `TrendHD/rubert-tiny2-int8` (312 dim, ONNX int8) на порту 18092
- **Observability Check** — новая команда `check` (SC-1): проверка OTEL SDK, OTLP-экспорта, span-атрибутов, структуры логов, корреляционных заголовков (X-Request-ID, X-Trace-ID, X-User-ID, X-Draft-ID, X-Document-ID, X-Version-ID)
- **Post-deploy (SC-2)** — `service_checker check <service> --post-deploy` с exit-code 0/1/2 для CI
- **Draft-first (OR-11)** — POST /drafts — единая точка входа вместо POST /documents

