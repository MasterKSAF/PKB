# PKB Neuroassistant — Service Checker

Утилита для проверки сервисов PKB Neuroassistant.

## Структура

```
service_checker/
├── setup.py                 # One-command setup: модель TEI + Docker Compose
├── Makefile                 # Альтернативный setup (Linux/macOS/Git Bash)
├── api_coverage_test.py     # API Coverage Test (real-режим, Docker)
├── service_checker.py       # Точка входа (делегирует в core/)
├── core/                    # Основные модули
│   ├── __init__.py
│   ├── config.py             # Конфигурация (пути, сервисы, credentials)
│   ├── models.py             # Модели данных (Report, ServiceProcess, HealthResult...)
│   ├── utils.py              # Утилиты (логирование, конвертация Markdown→HTML)
│   ├── services.py           # Запуск/остановка сервисов, health check, эмуляция UI
│   ├── docker.py             # Docker Compose управление
│   ├── reports.py            # Генерация full-отчёта (coverage + pipeline)
│   └── cli.py                # CLI-парсер и команды
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
- `setup_db.py`              # Инициализация БД (только база + расширения, схемы/таблицы — создают сами сервисы)
├── pipeline_test.py         # Pipeline Testing (сквозные сценарии)
├── pipelines/               # Модули пайплайнов
│   ├── __init__.py                      # Реестр пайплайнов
│   ├── base.py                          # Базовые классы (PipelineStep, PipelineRunner и др.)
│   ├── document_processing.py           # Пайплайн обработки документов (8 шагов)
│   ├── chat_inference.py                # Пайплайн чат-инференса (6 шагов)
│   └── registry_lifecycle.py            # Пайплайн жизненного цикла Registry (13 шагов)
├── docker/                  # Docker-конфигурация
│   ├── docker-compose.yml               # 5 контейнеров: postgres, redis, minio, tei, app
│   ├── supervisord.conf                 # Управление Python-сервисами
│   ├── Dockerfile.base / .full          # Образы
│   ├── entrypoint.sh                    # Точка входа
│   ├── prepare_tei_model.py             # Скачивание и подготовка модели TEI
│   ├── recheck.bat                      # Быстрый re-check: сброс БД + restat + full-report
│   └── requirements.txt                 # Python-зависимости всех сервисов
├── tests/
│   ├── conftest.py                        # Общие фикстуры
│   ├── test_success_determination.py      # Логика success/fail для статус-кодов
│   ├── test_override_logic.py             # Оверрайд all_404 и ping_ok
│   ├── test_report_generation.py          # Формирование отчёта
│   ├── test_pipeline_base.py              # Тесты базовых классов Pipeline Testing
│   └── test_pipeline_steps.py             # Тесты шагов пайплайнов
├── specificity.md           # Аномалии и архитектурные решения
└── readme.md                # Точка входа (этот файл)
```

## Текущий статус сервисов в Docker

После `recheck.bat` (2026-06-13):

| Сервис | Порт | HTTP | supervisorctl | Проблемы |
|--------|:----:|:----:|:-------------:|----------|
| PostgreSQL | 5432 | — | — | (здоров) |
| Redis | 6379 | — | — | (здоров) |
| MinIO | 9000 | — | — | (здоров) |
| TEI | 8092 | 200 | — | (здоров) |
| Gateway (Mock) | 8080 | 401 | RUNNING | 🟡 Логи в stderr (аном. №22) |
| Orchestrator | 8081 | 200 | RUNNING | ✅ Исправлен `DraftItem.created_by` |
| Auth | 8082 | 200 | RUNNING | 🟡 Ключ JWT короткий (предупреждение) |
| Query | 8083 | 200 | RUNNING | ❌ Двойная транзакция (аном. №21) |
| Registry | 8084 | 200 | RUNNING | ✅ `create_all()` есть в lifespan |
| Integration | 8085 | 200 | RUNNING | ✅ |
| Converter-Validator | 8086 | 200 | RUNNING | ✅ Исправлен trailing slash /validate |
| Parser | 8087 | 200 | RUNNING | ✅ |
| OCR | 8088 | — | RUNNING | ✅ |
| RAG Builder | 8090 | 200 | RUNNING | 🟡 Нет `create_all()` при старте |
| RAG Search | 8091 | 200 | RUNNING | 🟡 500 в pipeline |

**supervisorctl:** ✅ Все 11 процессов RUNNING (исправлен socket + symlink)
**.env файлы:** ✅ Создаются автоматически (исправлен entrypoint.sh)
**.err логи:** ✅ Health check проверяет ошибки, INFO/WARNING фильтруются

> **Важно:** `recheck.bat` уже запускает **все проверки**:
> 1. Health check (контейнеры + HTTP + supervisorctl + .err логи) ← теперь выводится
> 2. DB check
> 3. API Coverage Test
> 4. Pipeline Testing
> 5. Сводный отчёт + сбор логов
>
> Отдельный `docker --action health` после recheck **не нужен** — вся диагностика уже в начале `full-report`. Смотрите отчёты в `check_result/`.

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
Пересоздаёт контейнеры с чистой БД (kill + rm -v + up) и запускает полный отчёт
(coverage + pipelines + db-check). TEI контейнер не перезапускается.
Подходит для повторных проверок после изменений в сервисах.

> **Внимание:** удаляет volumes с БД — каждый запуск начинается с чистого состояния.

### Вариант D — вручную

```bash
# 1. Собрать образ (если нет)
docker build -f docker/Dockerfile.base -t ghcr.io/pkb/neuro-base:latest docker/

# 2. Запустить
python setup.py
```

## Запуск тестов

```bash
# Unit-тесты
python -m pytest tests/ -v

# По файлам
python -m pytest tests/test_success_determination.py -v
python -m pytest tests/test_override_logic.py -v
python -m pytest tests/test_report_generation.py -v
python -m pytest tests/test_pipeline_base.py -v
python -m pytest tests/test_pipeline_steps.py -v
python -m pytest tests/test_db_setup.py -v          # Статический анализ SQL (без Docker)

# Integration-тест (требует Docker)
python -m pytest tests/test_no_restarts.py -v         # Проверка restart-циклов

# ⚠️ Pipeline Testing — только через модуль (см. 15-ю аномалию в specificity.md):
#    прямой запуск python pipeline_test.py не работает из-за конфликта имён
python -m service_checker docker --action full-report  # Coverage + все пайплайны + сводка

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
| `document_processing` | Полный цикл обработки документа | Auth → MinIO → Parser → Converter → Registry → RAG Builder → RAG Search | 9 |
| `chat_inference` | Чат-сессия с поиском по документам | Auth → Query (Chat) → Query (Text Search) → RAG Search | 5 |
| `registry_lifecycle` | CRUD + импорт классификаторов и терминов | Auth → Registry | 11 |

## Ключевые решения

- **2xx/3xx** — success
- **4xx/5xx** — fail (любая ошибка сервиса)
- **all_404 оверрайд** — если >=2 не-health эндпоинтов вернули 404, сервис помечается мёртвым (ping_ok=False, success откатывается)
- **Статус-колонка отчёта** — ❌ если ping_ok=False или есть failed эндпоинты
- **Пайплайны** — сквозные сценарии в отдельных файлах `pipelines/*.py`, запуск через `pipeline_test.py`
- **Эмбеддинги через TEI** — локальный сервер эмбеддингов Hugging Face TEI с моделью `TrendHD/rubert-tiny2-int8` (312 dim, ONNX int8) на порту 8092
