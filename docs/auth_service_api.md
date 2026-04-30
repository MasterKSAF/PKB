**

#### 1.1 Аутентификация и управление пользователями

##### POST /auth/token

Получение пары JWT‑токенов (access + refresh).

Запрос (application/json):

json

{

  "username": "ivanov",

  "password": "secret123"

}

Ответ 200:

json

{

  "access_token": "eyJhbGciOi...",

  "refresh_token": "dGhpcyBpcyB...",

  "token_type": "bearer",

  "expires_in": 3600

}

Возможные ошибки: 401 – неверные учётные данные, 400 – отсутствует тело.

##### POST /auth/refresh

Обновление access-токена по действующему refresh-токену.

Запрос:

json

{

  "refresh_token": "dGhpcyBpcyB..."

}

Ответ 200 – аналогичен /auth/token.  
Ошибки: 401 – токен истёк / отозван.

##### POST /auth/revoke

Отзыв refresh-токена (выход).

Запрос:

json

{

  "refresh_token": "..."

}

Ответ 200:

json

{

  "message": "Токен отозван",

  "revoked_at": "2026-04-27T10:15:30Z"

}

##### GET /users/me

Профиль текущего пользователя.

Ответ 200:

json

{

  "user_id": "u-001",

  "email": "ivanov@example.com",

  "full_name": "Иванов И.И.",

  "roles": ["engineer"],

  "permissions": ["documents:read", "search"],

  "created_at": "2025-12-01T08:00:00Z"

}

##### GET /users

Список пользователей (только администратор).  
Параметры query: role (фильтр), search (по имени/email), limit, offset.

Ответ 200:

json

{

  "users": [

    {

      "user_id": "u-001",

      "email": "ivanov@...",

      "full_name": "Иванов И.И.",

      "roles": ["engineer"],

      "is_active": true,

      "created_at": "2025-12-01T08:00:00Z"

    }

  ],

  "total": 42,

  "limit": 20,

  "offset": 0

}

##### POST /users

Создание пользователя (админ).  
Запрос:

json

{

  "email": "petrov@example.com",

  "full_name": "Петров П.П.",

  "password": "Temp1234!",

  "roles": ["engineer"]

}

Ответ 201 – тело как в GET /users/{user_id}.

##### GET /users/{user_id}

Детали пользователя.  
Ответ 200:

json

{

  "user_id": "u-001",

  "email": "ivanov@...",

  "full_name": "Иванов И.И.",

  "roles": ["engineer"],

  "permissions": ["documents:read", "search"],

  "is_active": true,

  "created_at": "...",

  "updated_at": "..."

}

##### PUT /users/{user_id}

Обновление данных пользователя (админ). Поля в теле опциональны (email, full_name, roles, is_active).  
Ответ 200 – обновлённый объект пользователя.

##### DELETE /users/{user_id}

Деактивация пользователя (админ).  
Ответ 200:

json

{

  "user_id": "u-001",

  "is_active": false,

  "deactivated_at": "2026-04-27T11:00:00Z"

}

##### GET /roles

Список ролей.  
Ответ 200:

json

{

  "roles": [

    {

      "role_id": "r-admin",

      "name": "Администратор",

      "permissions": ["users:manage", "audit:read"],

      "created_at": "..."

    }

  ]

}

##### POST /roles

Создание роли (админ).  
Запрос:

json

{

  "name": "Инженер",

  "permissions": ["documents:read", "search"]

}

Ответ 201 – объект роли.

##### GET /audit

Журнал аудита (администратор/аудитор).  
Параметры query: user_id, action (например, document.upload), date_from, date_to, limit, offset.  
Ответ 200:

json

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

---

#### Internal Auth Service (auth-service:8080)

##### POST /internal/auth/validate

Проверка access‑токена.

Запрос:

json

{

  "access_token": "eyJhbGciOi..."

}

Ответ 200:

json

{

  "valid": true,

  "user_id": "u-001",

  "email": "ivanov@...",

  "roles": ["engineer"],

  "permissions": ["documents:read", "search"],

  "exp": 1714234567

}

Ошибки: 401 – токен недействителен.

**