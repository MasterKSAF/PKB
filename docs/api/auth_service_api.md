## API Auth Service

Сервис аутентификации и управления пользователями.

Базовый путь: `/api/v1`

### Группы

| Группа | Описание |
|--------|----------|
| `auth` | Аутентификация и профиль текущего пользователя |
| `admin` | Управление пользователями, ролями и аудит |

### Содержание

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/token` | username, password — получить JWT-токены доступа |
| POST | `/auth/refresh` | refresh_token — обновить access-токен |
| POST | `/auth/revoke` | refresh_token — отозвать refresh-токен |
| GET | `/auth/me` | Профиль текущего пользователя (UI-формат: camelCase) |
| GET | `/admin/users` | ?role, search, limit, offset — список пользователей |
| POST | `/admin/users` | email, full_name, password, roles — создать пользователя |
| GET | `/admin/users/{user_id}` | Информация о пользователе |
| PUT | `/admin/users/{user_id}` | обновляемые поля — обновить пользователя |
| PATCH | `/admin/users/{user_id}` | обновляемые поля — частичное обновление (например, только role) |
| DELETE | `/admin/users/{user_id}` | Деактивировать пользователя |
| GET | `/admin/roles` | Список ролей |
| POST | `/admin/roles` | name, permissions — создать роль |
| GET | `/admin/audit` | ?user_id, action, date_from, date_to, limit, offset — журнал действий (аудит) |

---

## Группа auth

### POST /auth/token

Получение пары JWT‑токенов (access + refresh).

**Запрос**:

```json
{
  "username": "ivanov",
  "password": "secret123"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `username` | string | Да | Имя пользователя |
| `password` | string | Да | Пароль |

**Ответ `200`**:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "dGhpcyBpcyB...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `access_token` | string | JWT access токен |
| `refresh_token` | string | JWT refresh токен |
| `token_type` | string | Тип токена (bearer) |
| `expires_in` | int | Время жизни токена в секундах |

**Ошибки**: `401` — неверные учётные данные, `400` — отсутствует тело.

#### POST /auth/refresh

Обновление access-токена по действующему refresh-токену.

**Запрос**:

```json
{
  "refresh_token": "dGhpcyBpcyB..."
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `refresh_token` | string | Да | Действующий refresh токен |

**Ответ `200`** — аналогичен `/auth/token`.

**Ошибки**: `401` — токен истёк / отозван.

#### POST /auth/revoke

Отзыв refresh-токена (выход).

**Запрос**:

```json
{
  "refresh_token": "..."
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `refresh_token` | string | Да | Refresh токен для отзыва |

**Ответ `200`**:

```json
{
  "message": "Токен отозван",
  "revoked_at": "2026-04-27T10:15:30Z"
}
```

#### GET /auth/me

Профиль текущего пользователя в формате, ожидаемом frontend. CamelCase-поля, `availableTabs` и `permissions` как объект boolean.

**Ответ `200`**:

```json
{
  "user_id": "u-001",
  "full_name": "Иванов Сергей Петрович",
  "position": "Инженер-конструктор",
  "role": "engineer",
  "role_title": "Инженер",
  "available_tabs": ["chat", "search", "checks", "history"],
  "permissions": {
    "can_upload_documents": false,
    "can_run_ocr": false,
    "can_manage_users": false,
    "can_manage_classifiers": false,
    "can_manage_terminology": false,
    "can_manage_registry": false
  },
  "last_login_at": "2026-05-01T08:20:00Z",
  "created_at": "2025-12-01T08:00:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | string | ID пользователя |
| `full_name` | string | Полное имя |
| `position` | string | Должность |
| `role` | string | Роль: `engineer`, `knowledge_admin`, `system_admin` |
| `role_title` | string | Отображаемое название роли |
| `available_tabs` | string[] | Доступные вкладки UI |
| `permissions` | object | Права доступа (boolean) |
| `last_login_at` | string | Дата последнего входа (ISO 8601) |
| `created_at` | string | Дата создания (ISO 8601) |

---

## Группа admin

### GET /admin/users

Список пользователей (только администратор).

**Параметры query**: `role`, `search` (по имени/email), `limit`, `offset`.

**Ответ `200`**:

```json
{
  "users": [
    {
      "user_id": "u-001",
      "email": "ivanov@example.com",
      "full_name": "Иванов И.И.",
      "position": "Инженер-конструктор",
      "roles": ["engineer"],
      "is_active": true,
      "last_login_at": "2026-05-01T08:20:00Z",
      "created_at": "2025-12-01T08:00:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### POST /admin/users

Создание пользователя (админ).

**Запрос**:

```json
{
  "email": "petrov@example.com",
  "full_name": "Петров П.П.",
  "password": "Temp1234!",
  "roles": ["engineer"]
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `email` | string | Да | Email пользователя |
| `full_name` | string | Да | Полное имя |
| `password` | string | Да | Пароль |
| `roles` | string[] | Да | Роли пользователя |

**Ответ `201`** — объект пользователя.

### GET /admin/users/{user_id}

Детали пользователя.

**Ответ `200`**:

```json
{
  "user_id": "u-001",
  "email": "ivanov@example.com",
  "full_name": "Иванов И.И.",
  "position": "Инженер-конструктор",
  "roles": ["engineer"],
  "permissions": ["documents:read", "search"],
  "is_active": true,
  "last_login_at": "2026-05-01T08:20:00Z",
  "created_at": "2025-12-01T08:00:00Z",
  "updated_at": "2026-04-27T10:00:00Z"
}
```

### PUT /admin/users/{user_id}

Обновление данных пользователя (админ). Поля в теле опциональны.

**Запрос**:

```json
{
  "email": "newemail@example.com",
  "full_name": "Иванов И.П.",
  "position": "Ведущий инженер",
  "roles": ["engineer", "admin"],
  "is_active": true
}
```

**Ответ `200`** — обновлённый объект пользователя.

### PATCH /admin/users/{user_id}

Частичное обновление пользователя (админ). Отличается от PUT тем, что обновляются только переданные поля.

**Запрос** (изменение только роли):

```json
{
  "role": "knowledge_admin"
}
```

`role` — единственное поле, строка (упрощённый формат для UI).

**Ответ `200`**:

```json
{
  "user_id": "u-001",
  "role": "knowledge_admin",
  "audit_log_id": "audit-001",
  "updated_at": "2026-04-27T11:00:00Z"
}
```

### DELETE /admin/users/{user_id}

Деактивация пользователя (админ).

**Ответ `200`**:

```json
{
  "user_id": "u-001",
  "is_active": false,
  "deactivated_at": "2026-04-27T11:00:00Z"
}
```

### GET /admin/roles

Список ролей.

**Ответ `200`**:

```json
{
  "roles": [
    {
      "role_id": "r-admin",
      "name": "Администратор",
      "permissions": ["users:manage", "audit:read"],
      "created_at": "2025-12-01T08:00:00Z"
    }
  ]
}
```

### POST /admin/roles

Создание роли (админ).

**Запрос**:

```json
{
  "name": "Инженер",
  "permissions": ["documents:read", "search"]
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `name` | string | Да | Название роли |
| `permissions` | string[] | Да | Список разрешений |

**Ответ `201`** — объект роли.

### GET /admin/audit

Журнал аудита (администратор/аудитор).

**Параметры query**: `user_id`, `action` (например, `document.upload`, `role.change`), `date_from`, `date_to`, `limit`, `offset`.

**Ответ `200`**:

```json
{
  "events": [
    {
      "event_id": "evt-123",
      "user_id": "u-001",
      "action": "document.upload",
      "resource_type": "document",
      "resource_id": "doc-456",
      "details": {"filename": "spec.pdf"},
      "ip_address": "192.168.1.25",
      "timestamp": "2026-04-27T09:30:00Z"
    }
  ],
  "total": 150
}
```

---

## Internal Auth Service (auth-service:8080)

### POST /internal/auth/validate

Проверка access‑токена (внутренний).

**Запрос**:

```json
{
  "access_token": "eyJhbGciOi..."
}
```

**Ответ `200`**:

```json
{
  "valid": true,
  "user_id": "u-001",
  "email": "ivanov@example.com",
  "roles": ["engineer"],
  "permissions": ["documents:read", "search"],
  "exp": 1714234567
}
```

**Ошибки**: `401` — токен недействителен.
