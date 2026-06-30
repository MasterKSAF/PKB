# todo: /auth/me контракт — выполнено

## Диагностика
- [x] Проверить текущий код auth_service `/auth/me`
- [x] Проверить gateway mock
- [x] Проверить DEFAULT_ROLES, _PERMISSION_TO_TABS
- [x] Проверить init_db
- [x] Проверить тесты
- [x] Проверить документацию контракта

## Выполненные правки
1. **init_db — обновление permissions существующих ролей**
   - `auth_service/app/db/init_db.py`: добавлено обновление permissions у уже созданных ролей, если они отличаются от DEFAULT_ROLES
   - `auth_service/tests/conftest.py`: синхронизирован DEFAULT_ROLES

2. **knowledge_admin + audit:read**
   - `auth_service/app/db/init_db.py` (DEFAULT_ROLES): добавлен `"audit:read"` для knowledge_admin
   - `auth_service/tests/conftest.py` (DEFAULT_ROLES): добавлен `"audit:read"` для knowledge_admin
   - `gateway_service/mocks/common.py` (_ROLE_PERMISSIONS): добавлен `"audit:read"` для knowledge_admin
   - `auth_service/readme.md`: обновлена таблица ролей

3. **Поле `position`** — не добавлялось (нет в модели User, требует миграции БД)

4. **Тесты**: все 31 тест auth_service + 163 теста gateway mock проходят
