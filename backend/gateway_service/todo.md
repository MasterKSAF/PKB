# Todo — Unified Gateway Refactoring ✅ DONE

## Задача
Переделать gateway: убрать разделение на сервисы, создать единую общую оболочку,
где вся логика взаимодействует напрямую, без необходимости синхронизации данных между сервисами.

## Выполненные шаги

### ✅ 1. Обновить `mocks/common.py`
- Собраны ВСЕ seed-данные и in-memory хранилища в одном файле
- Все хранилища теперь в едином namespace (никакого разделения)
- Функция `init_all_data()` инициализирует всё сразу

### ✅ 2. Создать `mocks/handlers/` — единая папка с хендлерами
- `handlers/__init__.py` — объединяет все роутеры
- `handlers/auth_routes.py` — auth/admin/internal handlers
- `handlers/orch_routes.py` — documents/drafts/tasks/monitor handlers
- `handlers/query_routes.py` — chat/text/projects handlers
- `handlers/registry_routes.py` — classifiers/terminology/common/registry docs handlers
- ВСЕ хендлеры импортируют данные из `mocks.common` напрямую
- Никакой синхронизации не нужно — всё в одном namespace

### ✅ 3. Обновить `mocks/gateway.py`
- Импортирует единые роутеры из `handlers`
- Убраны импорты отдельных сервисов
- Использует `_access_token_map` из common.py напрямую (без патчинга _make_token)

### ✅ 4. Удалить директории сервисов
- `mocks/auth_service/` — удалена
- `mocks/orchestrator_service/` — удалена
- `mocks/query_service/` — удалена
- `mocks/registry_service/` — удалена

### ✅ 5. Обновить тесты
- `test_api.py` — импорт `_rate_limits` из `mocks.common`
- `test_extended.py` — импорт `_rate_limits` из `mocks.common`, фикс rate limit теста
- `test_tz_coverage.py` — переведён на gateway.app, фикс ошибок
- `test_checker_coverage.py` — импорт `_rate_limits` из `mocks.common`
- `test_registry_paths.py` — убран импорт `auth_app`

### ✅ 6. Результаты тестов
**396/396 тестов проходят** ✅
