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

### Вариант C — вручную

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

# Pipeline Testing (требует Docker с реальными сервисами)
python pipeline_test.py list                        # Список пайплайнов
python pipeline_test.py run-all                     # Все пайплайны
python pipeline_test.py run document_processing     # Конкретный пайплайн
python pipeline_test.py run-all -o report.md        # С сохранением отчёта

# Coverage test в Docker
python api_coverage_test.py run-all

# Database health check
python service_checker.py docker --action db-check   # Проверка БД: таблицы Registry и RAG
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
