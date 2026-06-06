# Query Service

FastAPI-сервис для обработки запросов к базе знаний. Принимает вопросы от фронтенда, обращается к RAG-движку и возвращает ответы с источниками.

## Стек

- Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL
- Аутентификация: Bearer-токен (DEV_AUTH_MODE — любой токен, user_id = u-001)
- RAG: заглушка с ротацией ответов (answered / needs_clarification / source_conflict)

## Запуск локально

Нужен PostgreSQL. Проще всего поднять через docker compose только базу:

```bash
docker compose up postgres
```

Затем сервис:

```bash
cd backend/query_service
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://pkb:pkb@localhost:5432/pkb_query \
  uvicorn app.main:app --host 0.0.0.0 --port 8083 --reload
```

Swagger: http://localhost:8083/docs

## Тесты

Тесты используют SQLite in-memory, PostgreSQL не нужен:

```bash
pytest
```

22 теста — все проходят.

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | — | asyncpg URL к PostgreSQL |
| `APP_HOST` | `0.0.0.0` | Хост |
| `APP_PORT` | `8083` | Порт |
| `CORS_ORIGINS` | `*` | Разрешённые origins через запятую |
| `DEV_AUTH_MODE` | `false` | `true` — принять любой Bearer |
| `MOCK_RAG_ENABLED` | `true` | `true` — использовать заглушку RAG |

## Основные эндпоинты

- `POST /api/v1/chat` — задать вопрос
- `GET /api/v1/chat/history` — история запросов
- `POST /api/v1/chat/feedback` — оценить ответ
- `POST /api/v1/text/search` — семантический поиск фрагментов
- `GET /api/v1/health` — статус сервиса
