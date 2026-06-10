# ✅ Выполнено: проверка инициализации БД сервисами

## Что сделано

### 1. Исправлена инициализация БД в Docker (service_checker)
- `entrypoint.sh` → шаг 5/6: `setup_db.py --docker`
- `setup_db.py` → читает env, ищет SQL-файл по маске, --docker режим
- `docker/.env` → создан с DEFAULT_ADMIN_* и всеми переменными
- `Dockerfile.base`/`.full` → добавлен postgresql-client

### 2. Проверка: какой сервис создаёт свои таблицы

| Сервис | Статус | Детали |
|--------|:------:|--------|
| Auth Service | ✅ | `on_event startup` → `init_db()` → create_all |
| Query Service | ✅ | `lifespan` → `init_db()` → create_all |
| Orchestrator | ✅ | `lifespan` → create_all |
| Integration | ✅ | create_all при импорте модуля |
| **Registry** | **❌** | **Нет create_all() в main.py** |
| **RAG Builder** | **❌** | **Нет create_all() в create_app()** |
| RAG Search | ✅ | Consumer, не должен создавать |

### 3. Документация
- `docs/database/db_init_requirements.md` — результаты проверки + таблица ответственных
- `specificity.md` (раздел 11) — зафиксировано
- `tests/test_db_setup.py` — 31 тест на SQL-генерацию

## Что остаётся (не checker)

| Сервис | Проблема |
|--------|----------|
| Registry | `registry_service/main.py` — нет create_all, ~18 таблиц схемы `registry` не создаются |
| RAG Builder | `rag_builder_service/src/rag_builder/api/app.py` — нет create_all, таблица `rag.document_chunks` не создаётся |
