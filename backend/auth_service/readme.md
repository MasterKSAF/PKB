# Auth Service

Сервис аутентификации, управления пользователями, ролями, правами доступа и аудитом действий.

Сделано по ТЗ проекта "Нейро-координатор" и API описанию `auth_service_api.md`.

## Что реализовано

- FastAPI backend
- JWT access token
- JWT refresh token
- Отзыв refresh token
- Пользователи
- Роли
- Permissions
- Аудит действий
- Внутренний endpoint проверки токена
- PostgreSQL
- Docker Compose
- OpenAPI автоматически доступен в `/docs`

## Роли по умолчанию

| Роль | Назначение | Права |
|---|---|---|
| engineer | Инженер-конструктор | documents:read, search, history:read |
| knowledge_admin | Администратор знаний | documents:read, documents:write, search, history:read |
| system_admin | Администратор системы | users:manage, roles:manage, audit:read, documents:read, documents:write, search |

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## Данные администратора по умолчанию

```text
email: admin@example.com
password: Admin1234!
```

## Получить токен

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"Admin1234!"}'
```

## Проверить текущего пользователя

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## Структура проекта

```text
app/
  api/v1/          HTTP endpoints
  core/            настройки, безопасность, зависимости
  db/              база и стартовые данные
  models/          SQLAlchemy модели
  schemas/         Pydantic схемы
  services/        бизнес-логика
tests/             тесты
```

## Команды без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Переменные окружения

См. `.env.example`.

## Тесты

```bash
pytest
```

## Важные endpoints

| Метод | Путь |
|---|---|
| POST | /api/v1/auth/token |
| POST | /api/v1/auth/refresh |
| POST | /api/v1/auth/revoke |
| GET | /api/v1/users/me |
| GET | /api/v1/users |
| POST | /api/v1/users |
| GET | /api/v1/users/{user_id} |
| PUT | /api/v1/users/{user_id} |
| DELETE | /api/v1/users/{user_id} |
| GET | /api/v1/roles |
| POST | /api/v1/roles |
| GET | /api/v1/audit |
| POST | /internal/auth/validate |
