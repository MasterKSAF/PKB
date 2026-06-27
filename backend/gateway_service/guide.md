# Guide — Архитектурные решения и ориентиры

## Ключевые архитектурные решения

### 1. Единый Gateway (reverse-proxy)
- Gateway (порт 8080) — единственная точка входа. Режим: `real` (reverse-proxy).
- Все запросы `/api/v1/*` проксируются к внутренним сервисам через `gateway/client.py`.
- Маршрутизация по шаблону пути + HTTP-методу (`ROUTE_TABLE` в `client.py` с `RouteEntry`).
- Учитывается не только путь, но и метод: `GET /api/v1/drafts` → Registry, `POST /api/v1/drafts` → Orchestrator.
- Registry-пути трансформируются: `/api/v1/documents/{id}` → `/api/v1/registry/documents/{id}`.
- Catch-all router (`gateway/routers.py`) обрабатывает все `/api/v1/{path:path}`.

### 2. Mock-сервер — унифицированный
- Единый mock-gateway (`mocks/gateway.py`) на порту 8099 эмулирует все 5 сервисов.
- Все данные — в едином пространстве имён `mocks.common`.
- Нет разделения на отдельные сервисы (старая архитектура удалена 2026-06-12).
- `start_service.py` — утилита для запуска отдельных хендлеров.

### 3. Rate Limiting + IDOR (CM-2, CM-3, GW-4, GW-6)
- InMemory-бэкенд (`gateway/rate_limiter.py`), достаточен для single-instance.
- 14 групп эндпоинтов с различными лимитами.
- IDOR protection: 30 запросов/мин к draft_id / document_id / session_id.
- 80% threshold → WARNING в лог.

### 4. Сетевая изоляция (CM-4, GW-1, GW-2, GW-5)
- L2 (dmz): Gateway + Auth validate.
- L3 (internal): все сервисы без доступа к internet (`internal: true`).
- L4 (data): PostgreSQL, Redis.
- Реализовано в `docker-compose.yml`.

### 5. Логирование (P11-1, P11-2, P11-3)
- Структурированное JSON-логирование с обязательными полями.
- PII-фильтрация (password, access_token, refresh_token → ***).
- X-Request-ID / X-User-ID проброс во все downstream.

### 6. CORS (GW-3)
- В development — разрешены все origins (`*`).
- В production — строго заданные домены, `*` запрещён.

### 7. Тестирование Gateway
- Unit-тесты в `tests/` (168 тестов) — не требуют Docker, импортируют модули gateway напрямую.
- Docker-интеграционные тесты в `tests/` (65 тестов) — требуют запущенного Gateway в Docker (порт 18080).
- Помечены `@pytest.mark.docker`, автоматически скипаются без Docker.
- Запускаются как часть `service_checker docker --action full-report`.
- `conftest.py` — фикстуры для обоих режимов (Docker-клиент, токены, мок-клиент).
- `helpers.py` — утилиты (auth_header, PII_PARAMS, credentials).

## Ориентиры для разработки
- **Тестируемость**: код разделён на модули с внедрением зависимостей.
- **Декомпозиция**: файлы > 500 строк разбиваются по назначению.
- **Изменение логики** обязательно сопровождается тестом.
- **Ошибки** сначала фиксируются воспроизводящим тестом, затем исправляются.
- **Документация**: readme.md — точка входа, specificity.md — аномалии, guide.md — архитектурные решения.
- **Checker**: обнаружив проблему на своей стороне (согласно документации) — исправляет сразу, не спрашивая.

## Структура тестирования Gateway

- `tests/` — unit-тесты самого Gateway (287 тестов). Запускаются без внешних сервисов.
- `mocks/tests/` — интеграционные тесты через mock-сервер (550+ тестов, порт 8099).
- Все `check_rate_limit`, `close_client`, `proxy_request` — async, помечены `@pytest.mark.asyncio`.
- Для RBAC-тестов используется mock `_validate_token_remotely` (монки-патч).
- Для proxy-тестов используется mock `get_client()` с возвратом AsyncMock.
- `conftest.py` включает фикстуры: mock_auth_validate, mock_httpx_client, seed-данные пользователей.
- `ALLOW_ANONYMOUS=True` принудительно (прямое присвоение, не `setdefault`)
  — RBAC middleware не блокирует неаутентифицированных.
- Все async-фикстуры и тесты используют `@pytest.mark.asyncio`,
  ручное `asyncio.get_event_loop()` не используется (предотвращает `Event loop is closed`).
