# PKB NeuroAssistant

Система семантического поиска и анализа нормативно-технической документации (НТД) для проектно-конструкторского бюро.

## Структура проекта

```
PKB_neuroassistant_docs/
├── README.md                    # ← Точка входа (этот файл)
├── docs/                        # Основная документация (API, схемы, пайплайны)
│   ├── README.md                #   Навигация по документации
│   ├── glossary.md              #   Глоссарий терминов
│   ├── specificity.md           #   Журнал аномалий и расхождений
│   ├── api/                     #   API-спецификации микросервисов
│   ├── database/                #   Модели БД
│   ├── pipelines/               #   Пайплайны обработки
│   ├── schema/                  #   JSON-схемы контрактов
│   ├── plans/                   #   Планы спринтов и дорожные карты
│   ├── rules/                   #   Правила и чек-листы
│   └── specifications/          #   Технические спецификации
│
├── docs_discussions/            # Обсуждения и черновики
│   ├── plans/                   #   Планы встреч
│   ├── features/                #   Feature-спеки (RAG, метрики)
│   └── *.md                     #   Протоколы встреч
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
├── UI-UX/
└── .gitignore
```

## Быстрый старт

- **Начать здесь**: [`docs/README.md`](docs/README.md) — навигация по всей документации
- **Глоссарий**: [`docs/glossary.md`](docs/glossary.md)
- **План спринта**: [`docs/plans/sprint1_04_06_10_06.md`](docs/plans/sprint1_04_06_10_06.md)
- **Сводный план реализации**: [`docs/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md`](docs/plans/СВОДНЫЙ_ПЛАН_РЕАЛИЗАЦИИ.md)

## Docker (All-in-One контейнер)

Всё в одном контейнере: **PostgreSQL 16 + pgvector, Redis, MinIO** и **все 8 backend-сервисов**.
Управление процессами — supervisord. Единая установка, одна команда.

```bash
# Сборка и запуск
docker compose up -d --build

# Проверка статуса
docker compose ps
```

Подробнее: [`backend/README.Docker.md`](backend/README.Docker.md)

