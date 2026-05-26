## API Auth Service (auth-service:8082)

Сервис аутентификации и управления пользователями.

**Базовый URL (внутренний)**: `http://127.0.0.1:8082/api/v1`
**Базовый URL (публичный через Orchestrator)**: `https://{host}/api/v1`

### Группы

| Группа | Описание |
|--------|----------|
| `auth` | Аутентификация и профиль текущего пользователя |
| `admin` | Управление пользователями, ролями и аудит |

### Формат ответа

Успех — данные возвращаются напрямую (поле `data` опционально).

При ошибке:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "Пользователь не найден",
    "details": {}
  }
}
```

Для списковых ответов `meta` содержит пагинацию на верхнем уровне.

### Коды ошибок

| HTTP-код | Код ошибки (`error.code`) | Описание |
|----------|--------------------------|----------|
| 400 | `VALIDATION_ERROR` | Некорректные входные данные |
| 401 | `UNAUTHORIZED` | Неверные учётные данные |
| 401 | `INVALID_TOKEN` | Токен недействителен или истёк |
| 403 | `FORBIDDEN` | Нет доступа |
| 404 | `USER_NOT_FOUND` | Пользователь не найден |
| 409 | `DUPLICATE_EMAIL` | Email уже используется |
| 500 | `INTERNAL_ERROR` | Внутренняя ошибка сервера |

### Содержание

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/token` | username, password — получить JWT-токены доступа |
| POST | `/auth/refresh` | refresh_token — обновить access-токен |
| POST | `/auth/revoke` | refresh_token — отозвать refresh-токен |
| GET | `/auth/me` | Профиль текущего пользователя (формат: snake_case) |
| GET | `/admin/users` | ?role, search, page, page_size — список пользователей |
| POST | `/admin/users` | email, full_name, password, roles — создать пользователя |
| GET | `/admin/users/{user_id}` | Информация о пользователе |
| PUT | `/admin/users/{user_id}` | обновляемые поля — обновить пользователя |
| PATCH | `/admin/users/{user_id}` | обновляемые поля — частичное обновление (например, только role) |
| DELETE | `/admin/users/{user_id}` | Деактивировать пользователя |
| GET | `/admin/roles` | Список ролей |
| POST | `/admin/roles` | name, permissions — создать роль |
| GET | `/admin/audit` | ?user_id, action, date_from, date_to, page, page_size — журнал действий (аудит) |

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

#### Жизненный цикл токенов

- **Access token**: живёт 1 час (значение `expires_in` в ответе `/auth/token`).
- **Refresh token**: живёт 30 дней, можно отозвать через `POST /auth/revoke`.
- При смене пароля все refresh-токены пользователя отзываются.
Rate limit: не более 10 запросов в минуту на `/auth/token` с одного IP (согласно глобальной политике Rate Limiting).
- Blacklist: отозванные refresh-токены хранятся в blacklist до истечения их исходного срока жизни.

#### GET /auth/me

Профиль текущего пользователя в формате frontend. Поля `available_tabs` и `permissions` как объект boolean.

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

**Параметры query**: `role`, `search` (по имени/email), `page`, `page_size`.

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
  "meta": { "total": 42, "page": 1, "page_size": 20 }
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
  "permissions": {
    "can_upload_documents": false,
    "can_run_ocr": false,
    "can_manage_users": false,
    "can_manage_classifiers": false,
    "can_manage_terminology": false,
    "can_manage_registry": false
  },
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

`role` — строка (упрощённый формат для UI). Принимается как shorthand для `["role"]`.
Рекомендуется использовать массив `roles` для согласованности с `POST /admin/users` и `PUT /admin/users/{user_id}`.

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

**Параметры query**: `user_id`, `action` (например, `document.upload`, `role.change`), `date_from`, `date_to`, `page`, `page_size`.

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
  "meta": { "total": 150, "page": 1, "page_size": 50 }
}
```

---

## Internal Auth Service 
### POST /internal/auth/validate

Проверка access‑токена (внутренний).

**Запрос**:

```json
{
  "access_token": "eyJhbGciOi..."
}
```

**Ответ `200`** (токен действителен):

```json
{
  "valid": true,
  "user_id": "u-001",
  "email": "ivanov@example.com",
  "roles": ["engineer"],
  "permissions": {
    "can_upload_documents": false,
    "can_run_ocr": false,
    "can_manage_users": false,
    "can_manage_classifiers": false,
    "can_manage_terminology": false,
    "can_manage_registry": false
  },
  "exp": 1714234567
}
```

**Ответ `401`** (токен недействителен):

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Токен недействителен или истёк",
    "details": {}
  }
}
```

---

## Политика безопасности паролей

### Хранение

- Пароли хранятся только в хэшированном виде (bcrypt, cost factor ≥ 12).
- Пароли **никогда** не возвращаются в ответах API.
- Refresh-токены хранятся в БД в хэшированном виде.
- Поле `password` исключено из логирования на всех уровнях (см. `common_api.md`).

### Передача

- Пароль передаётся только при создании пользователя (`POST /admin/users`) и получении токена (`POST /auth/token`).
- Все эндпоинты, принимающие пароль, доступны только через **HTTPS** (публичный API).
- Внутренние вызовы между сервисами (Orchestrator → Auth Service) не содержат пароль в теле после первичного обмена — используется JWT-токен.

### Жизненный цикл

| Событие | Действие |
|---------|----------|
| Создание пользователя | Пароль хэшируется, сохраняется в БД, plaintext отбрасывается |
| Вход (`/auth/token`) | Пароль проверяется против хэша, при успехе выдаются JWT |
| Смена пароля (админ) | Выдаётся новый refresh-токен, старые refresh-токены пользователя отзываются |
| Отзыв токена (`/auth/revoke`) | Refresh-токен помещается в blacklist до истечения срока |

---

## Планы развития

### 1. Отдельный эндпоинт смены пароля

Вместо включения `password` в `PUT /admin/users/{user_id}` планируется выделенный endpoint:

```
POST /admin/users/{user_id}/reset-password
```

```json
{
  "password": "NewStr0ng!Pass"
}
```

**Преимущества:**
- Явная семантика — смена пароля, а не «обновление пользователя с полем password»
- Обязательная аудит-запись с типом `password.change`
- Возможность добавить подтверждение (второй администратор) без изменения основного API
- Пароль не появляется в общем теле обновления пользователя

### 2. Переход на Authorization Code + PKCE

Текущий flow (`POST /auth/token` с `username` + `password`) является упрощённым (OAuth2 Resource Owner Password Credentials Grant).
В следующих релизах планируется переход на **Authorization Code + PKCE**, где пароль вводится только на стороне клиента и не передаётся API:

```
Фронтенд                          Бэкенд
    |                                |
    |  GET /auth/authorize           |
    |  <-- code_challenge, state     |
    |                                |
    |  (ввод логина/пароля           |
    |   локально на клиенте)         |
    |                                |
    |  POST /auth/token              |
    |  { code, code_verifier }       |
    |  --> access_token,             |
    |       refresh_token            |
```

**Преимущества:**
- Пароль не покидает браузер пользователя
- API не видит и не может скомпрометировать пароль
- Одноразовый code бесполезен без code_verifier (даже при перехвате)