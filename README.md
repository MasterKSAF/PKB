# PKB NeuroAssistant

Система семантического поиска и анализа нормативно-технической документации (НТД) для проектно-конструкторского бюро.

## Структура проекта

```
PKB_neuroassistant/
├── README.md                    # ← Точка входа (этот файл)
├── todo.md                      # Текущие задачи агента
├── opencode.json                # Конфигурация OpenCode
│
├── docs/                        # Основная документация системы
│   ├── README.md                #   Навигация по документации
│   ├── glossary.md              #   Глоссарий терминов
│   ├── specificity.md           #   Журнал аномалий и расхождений
│   ├── guide.md                 #   Архитектурные решения и стиль
│   ├── api/                     #   API-спецификации микросервисов (13 сервисов)
│   ├── architecture/            #   Архитектурные схемы и описание зависимостей
│   ├── checks/                  #   Проверки целостности документации
│   │   └── scripts/             #     Скрипты проверок (check_consistency.py)
│   ├── database/                #   Модели БД, диаграммы, DDL-миграции
│   ├── pipelines/               #   Пайплайны обработки документов (3 пайплайна)
│   ├── schema/                  #   JSON-схемы контрактов
│   └── specifications/          #   Технические спецификации (конвертер, парсинг, классификаторы и др.)
│
├── docs_plans/                  # Планы, обсуждения, исследования, методологии
│   ├── plans/                   #   Планы спринтов, дорожные карты, задачи разработчикам
│   ├── features/                #   Feature-спеки (RAG, хранение черновиков, спринты)
│   ├── methodology/             #   Методологии экспериментов (RAG evaluation, эксперименты)
│   ├── discussions/             #   Протоколы встреч и обсуждений
│   ├── research/                #   Исследования (Phase 2)
│   │   ├── notebooks/           #     Jupyter-ноутбуки
│   │   └── results/             #     Результаты экспериментов
│   ├── audit/                   #   Аудиты (API, БД, схемы, UI-Gateway синхронизация)
│   ├── errors/                  #   Журнал ошибок запуска сервисов
│   ├── docs_ui.md               #   UI-документация
│   ├── docs_ui_compare.md       #   Сравнение UI-решений
│   └── pipeline1-formation_discussion.md  #   Обсуждение pipeline 1
│
├── backend/                     # Микросервисы (в репозитории кода)
│   ├── <service_name>/          #   Каждый сервис в своей папке
│   └── ...
│
├── Abzalov_Igor/                # Личные папки участников
├── Benuni_George/               #   (перемещаются в backend/ по готовности)
├── Eugene_Rizov/
│   └── ingestion_mvp/           #   MVP ingestion app
├── Fakhrutdinov_Roman/
├── Osipenko_Dmitrii/
├── Vitalyy_Novozhilov/
├── start_web.bat                # Запуск backend + web UI одной командой
├── reset_web.bat                 # Сброс БД и Redis, перезапуск сервисов
├── UI-UX/                       # Актуальный UI Final и материалы UI/UX-команды
│
├── Documents_Pipeline/          # Наработки по пайплайну документов
└── .gitignore
```

## Быстрый старт

- **Начать здесь**: [`docs/README.md`](docs/README.md) — навигация по всей документации
- **Глоссарий**: [`docs/glossary.md`](docs/glossary.md)
- **Актуальный UI Final**: [`UI-UX/UI Final/README.md`](UI-UX/UI%20Final/README.md)
- **План спринта**: [`docs/plans/sprint1_04_06_10_06.md`](docs/plans/sprint1_04_06_10_06.md)
- **Сводный план реализации**: [`docs/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md`](docs/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md)

## Docker (All-in-One контейнер)

Всё в одном контейнере: **PostgreSQL 16 + pgvector, Redis, MinIO** и **все 8 backend-сервисов**.
Управление процессами — supervisord. Единая установка, одна команда.
- **Архитектурные решения**: [`docs/guide.md`](docs/guide.md)
- **План спринта 1**: [`docs_plans/features/sprint1_04_06_10_06.md`](docs_plans/features/sprint1_04_06_10_06.md)
- **План спринта 2**: [`docs_plans/features/sprint2_11_06_17_06.md`](docs_plans/features/sprint2_11_06_17_06.md)
- **Задачи разработчикам**: [`docs_plans/plans/6.dev_tasks_17_06.md`](docs_plans/plans/6.dev_tasks_17_06.md)
- **Сводный план реализации**: [`docs_plans/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md`](docs_plans/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md)
- **Аномалии**: [`docs/specificity.md`](docs/specificity.md)

```bash
# Сборка и запуск (backend + инфраструктура)
docker compose up -d --build

# Проверка статуса
docker compose ps
```

**Быстрый старт backend + web UI:**

```bash
start_web.bat
```

**Сброс данных и перезапуск сервисов (без пересборки образов):**

```bash
reset_web.bat
```

Откроется:
- Backend API: `http://localhost:8080`
- Web UI:     `http://localhost:3300`

Подробнее:
- [`backend/README.Docker.md`](backend/README.Docker.md) — Docker-сборка
- [`UI-UX/UI Final/README.md`](UI-UX/UI%20Final/README.md) — Web UI

## RAG Builder SPD

Сервис `backend/rag_builder_service_spd` отвечает за индексацию chunk-container документа в нормализованную схему `nsi`.

Текущий статус MVP:

* приём и валидация `BuildRequest`
* построение чанков
* разбиение длинного текста на subchunks с overlap
* batch generation embeddings
* подсчёт usage/cost для embeddings
* сохранение структуры документа в PostgreSQL
* поддержка `pgvector`
* поддержка `ltree`
* сохранение таблиц, изображений, формул и ссылок

Сервис записывает данные в таблицы:

```text
nsi.document_sections
nsi.chunks
nsi.cross_references
nsi.images
nsi.extracted_tables
nsi.formulas
nsi.formula_parameters
```

Проверка:

```text
18 passed
```

Подробнее: [`backend/rag_builder_service_spd/README.md`](backend/rag_builder_service_spd/README.md)



