Аутентификация и пользователи
================================

Базовый путь: ```/api/v1```

# Содержание

| Метод | Путь | Описание |
|------|------|----------|
| POST | ```/auth/token``` | username, password — получить JWT-токены доступа |
| POST | ```/auth/refresh``` | refresh_token — обновить access-токен |
| POST | ```/auth/revoke``` | refresh_token — отозвать refresh-токен |
| GET | ```/users/me``` | Профиль текущего пользователя |
| GET | ```/users``` | ?role, search, limit, offset — список пользователей (админ) |
| POST | ```/users``` | email, full_name, password, roles — создать пользователя (админ) |
| GET | ```/users/{user_id}``` | Информация о пользователе |
| PUT | ```/users/{user_id}``` | обновляемые поля — обновить пользователя |
| DELETE | ```/users/{user_id}``` | Деактивировать пользователя |
| GET | ```/roles``` | Список ролей |
| POST | ```/roles``` | name, permissions — создать роль |
| GET | ```/audit``` | ?user_id, action, date_from, date_to, limit, offset — журнал действий (аудит) |

