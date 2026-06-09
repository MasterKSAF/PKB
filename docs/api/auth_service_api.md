# Auth Service API

Этот документ синхронизирован с текущей реализацией FastAPI в `backend/auth_service`.

Базовый URL:
- внутренний: `http://127.0.0.1:8082/api/v1`
- через gateway: `http://127.0.0.1:8080/api/v1`

## Сводка эндпоинтов

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/token` | Получить access/refresh токены |
| POST | `/auth/refresh` | Обновить access-токен |
| POST | `/auth/revoke` | Отозвать refresh-токен |
| GET | `/users/me` | Профиль текущего пользователя |
| GET | `/users` | Список пользователей (админ) |
| POST | `/users` | Создать пользователя (админ) |
| GET | `/users/{user_id}` | Информация о пользователе |
| PUT | `/users/{user_id}` | Обновить пользователя |
| DELETE | `/users/{user_id}` | Деактивировать пользователя |
| GET | `/roles` | Список ролей |
| POST | `/roles` | Создать роль |
| GET | `/audit` | Журнал аудита |
| POST | `/internal/auth/validate` | Проверить access-токен внутри сервиса |

## Общие правила

- Все ответы в формате JSON.
- Аутентификация для защищённых маршрутов выполняется через `Authorization: Bearer <access_token>`.
- Для обновления токенов и работы с пользователями используются реальные пути из текущего OpenAPI сервиса.
- Этот документ не описывает устаревшие маршруты и поля из предыдущих версий.

---

## POST /auth/token

Получить JWT-токены.

Запрос:

```json
{
  "username": "admin@example.com",
  "password": "Admin1234!"
}
```

Ответ `200`:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## POST /auth/refresh

Обновить access-токен по refresh-токену.

Запрос:

```json
{
  "refresh_token": "<refresh-token>"
}
```

Ответ `200` — тот же формат, что и у `/auth/token`.

---

## POST /auth/revoke

Отозвать refresh-токен.

Запрос:

```json
{
  "refresh_token": "<refresh-token>"
}
```

Ответ `200`:

```json
{
  "message": "Токен отозван",
  "revoked_at": "2026-06-09T12:00:00"
}
```

---

## GET /users/me

Вернуть текущего пользователя.

Требует `Authorization: Bearer <access_token>`.

Ответ `200`:

```json
{
  "user_id": "<uuid>",
  "email": "user@example.com",
  "full_name": "User Name",
  "roles": ["system_admin"],
  "permissions": ["users:manage", "roles:manage"],
  "is_active": true,
  "created_at": "2026-06-09T12:00:00",
  "updated_at": null
}
```

---

## GET /users

Список пользователей.

Параметры query:
- `role` — фильтр по роли
- `search` — поиск по email / full_name
- `limit` — размер страницы, по умолчанию 20
- `offset` — смещение, по умолчанию 0

Ответ `200`:

```json
{
  "users": [
    {
      "user_id": "<uuid>",
      "email": "user@example.com",
      "full_name": "User Name",
      "roles": ["engineer"],
      "is_active": true,
      "created_at": "2026-06-09T12:00:00"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

## POST /users

Создать пользователя.

Запрос:

```json
{
  "email": "new@example.com",
  "full_name": "New User",
  "password": "StrongPass123!",
  "roles": ["engineer"]
}
```

Ответ `201` — тот же формат, что и у `GET /users/me`.

---

## GET /users/{user_id}

Получить пользователя по ID.

Ответ `200` — тот же формат, что и у `GET /users/me`.

---

## PUT /users/{user_id}

Обновить пользователя.

Запрос:

```json
{
  "email": "updated@example.com",
  "full_name": "Updated User",
  "roles": ["engineer"],
  "is_active": true
}
```

Ответ `200` — тот же формат, что и у `GET /users/me`.

---

## DELETE /users/{user_id}

Деактивировать пользователя (soft delete).

Ответ `200`:

```json
{
  "user_id": "<uuid>",
  "is_active": false,
  "deactivated_at": "2026-06-09T12:00:00"
}
```

---

## GET /roles

Список ролей.

Ответ `200`:

```json
{
  "roles": [
    {
      "role_id": "<uuid>",
      "name": "system_admin",
      "permissions": ["users:manage", "roles:manage"],
      "created_at": "2026-06-09T12:00:00"
    }
  ]
}
```

---

## POST /roles

Создать роль.

Запрос:

```json
{
  "name": "knowledge_admin",
  "permissions": ["documents:read", "documents:write"]
}
```

Ответ `201` — объект роли из `GET /roles`.

---

## GET /audit

Журнал аудита.

Параметры query:
- `user_id`
- `action`
- `date_from`
- `date_to`
- `limit`
- `offset`

Ответ `200`:

```json
{
  "events": [
    {
      "event_id": "<uuid>",
      "user_id": "<uuid>",
      "action": "auth.login",
      "resource_type": "auth",
      "resource_id": "<uuid>",
      "details": null,
      "ip_address": "127.0.0.1",
      "timestamp": "2026-06-09T12:00:00"
    }
  ],
  "total": 1
}
```

---

## POST /internal/auth/validate

Проверить access-токен внутри сервиса.

Запрос:

```json
{
  "access_token": "<access-token>"
}
```

Ответ `200`:

```json
{
  "valid": true,
  "user_id": "<uuid>",
  "email": "user@example.com",
  "roles": ["system_admin"],
  "permissions": ["users:manage", "roles:manage"],
  "exp": 1718000000
}
```

---

## Примечание по сверке с текущим API

Если требуется полная генерация документации из кода, источник истины — OpenAPI FastAPI:

```bash
PYTHONPATH=backend/auth_service python -c "from app.main import app; import json; print(json.dumps(app.openapi(), indent=2))"
```

Этот файл следует обновлять при каждом изменении маршрутов, схем или статусов ответа в `backend/auth_service/app/`.
