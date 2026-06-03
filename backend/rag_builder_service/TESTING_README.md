# Testing README

## Цель
Проверка корректности RAG Builder Service на уровнях unit/integration/e2e.

## Что покрыто
- Unit:
  - chunking (лимит токенов, таблицы)
  - embeddings (детерминизм, размерность)
  - API/OpenAPI контракт
- Integration:
  - запись/удаление чанков в PostgreSQL + pgvector
- E2E smoke:
  - build -> status -> delete через HTTP API

## Структура тестов
- `tests/unit`
- `tests/integration`
- `tests/e2e`
- `tests/conftest.py`

## Подготовка
1. Python 3.13 установлен.
2. PostgreSQL с pgvector поднят (контейнер `pkb-pg16` на `localhost:5433`).
3. Установлены зависимости:
```powershell
py -3.13 -m pip install -e .[dev]
```

## Базовый запуск (обязательный)

Windows:
```powershell
.\make.cmd test
```

Альтернатива:
```powershell
py -3.13 -m pytest
```

## Проверка качества
```powershell
py -3.13 -m ruff check .
py -3.13 -m mypy src tests
```

## Проверка покрытия
Покрытие считается автоматически через `pytest-cov`.
Текущий порог: `>= 80%`.

## Что делать при падениях
1. Сначала проверить доступность БД:
```powershell
docker ps
```
2. Проверить расширение vector:
```powershell
docker exec pkb-pg16 psql -U pkb_user -d pkb_db -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
```
3. Повторно запустить:
```powershell
py -3.13 -m pytest -x
```

## Smoke-проверка API вручную
Запуск сервиса:
```powershell
py -3.13 -m uvicorn rag_builder.main:app --host 0.0.0.0 --port 8090
```

OpenAPI:
```powershell
curl http://127.0.0.1:8090/openapi.json
```

## Логи во время тестов
- Локально: `./logs/rag_builder.log`
- В логах есть request id/correlation id/traceback.
