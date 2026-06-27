# Gateway Service — тесты

**Директория:** `backend/gateway_service/tests/` (создать новую)

---

## 1. `tests/conftest.py` (~80 строк)

Фикстуры для всех тестов Gateway.

**Содержимое:**
- `TestClient(app)` — экземпляр FastAPI из `gateway.main`
- Мок-сервисы через `httpx_mock` или `mocks/gateway.py`
- Сид-данные: тестовый токен, пользователи, документы, черновики
- Конфигурация: `ALLOW_ANONYMOUS=True` по умолчанию
- Настройка логирования на `CRITICAL` для тестов

---

## 2. `tests/test_routing.py` (~200 строк)

`resolve_service()` — проверка таблицы маршрутов (ROUTE_TABLE).

**Сценарии:**

| # | Тест | Проверка |
|---|------|----------|
| 1 | GET `/api/v1/drafts` → registry c path transform | service="registry", target="/api/v1/registry/drafts" |
| 2 | GET `/api/v1/drafts/123` → orchestrator | numeric draft_id → orchestator (детали черновика) |
| 3 | GET `/api/v1/drafts/456` → orchestrator | другой numeric id |
| 4 | GET `/api/v1/drafts/5/preview` → 404 (не найдено) | нет GET-маршрута для preview, только POST |
| 5 | POST `/api/v1/drafts` → orchestrator | создание черновика |
| 6 | POST `/api/v1/drafts/123/preview` → orchestrator | запуск preview |
| 7 | GET `/api/v1/drafts/123/preview/status` → orchestrator | статус preview |
| 8 | PATCH `/api/v1/drafts/123/decide` → orchestrator | решение |
| 9 | PATCH `/api/v1/drafts/123/metadata` → orchestrator | обновление метаданных |
| 10 | DELETE `/api/v1/drafts/123` → orchestrator | удаление |
| 11 | GET `/api/v1/drafts/123/tasks` → orchestrator | задачи черновика |
| 12 | GET `/api/v1/documents` → registry | список документов |
| 13 | GET `/api/v1/documents/1` → registry | детали документа |
| 14 | PUT `/api/v1/documents/1` → registry | обновление документа |
| 15 | PATCH `/api/v1/documents/1` → registry | частичное обновление |
| 16 | DELETE `/api/v1/documents/1` → registry | удаление |
| 17 | GET `/api/v1/documents/1/sections` → registry | секции документа |
| 18 | GET `/api/v1/documents/1/pages` → registry | страницы |
| 19 | GET `/api/v1/documents/1/pages/1` → registry | конкретная страница |
| 20 | GET `/api/v1/documents/1/file` → registry | файл документа |
| 21 | GET `/api/v1/documents/1/history` → registry | история |
| 22 | GET `/api/v1/documents/1/parameters` → registry | параметры |
| 23 | GET `/api/v1/documents/1/versions` → registry | версии |
| 24 | GET `/api/v1/documents/1/succession` → registry | преемственность |
| 25 | POST `/api/v1/documents/search` → registry | поиск c path transform → /api/v1/registry/search |
| 26 | GET `/api/v1/documents/search` → registry | поиск GET |
| 27 | GET `/api/v1/documents/export` → registry | экспорт |
| 28 | POST `/api/v1/documents/import` → registry | импорт |
| 29 | POST `/api/v1/documents/check-uniqueness` → registry | проверка уникальности |
| 30 | POST `/api/v1/documents` → orchestrator | deprecated (OR-11) |
| 31 | GET `/api/v1/documents/1/status` → orchestrator | статус обработки |
| 32 | GET `/api/v1/documents/queue` → orchestrator | очередь |
| 33 | GET `/api/v1/documents/1/errors` → orchestrator | ошибки |
| 34 | POST `/api/v1/documents/1/versions` → orchestrator | новая версия |
| 35 | POST `/api/v1/documents/1/reprocess` → orchestrator | переобработка |
| 36 | GET `/api/v1/documents/1/tasks` → orchestrator | задачи документа |
| 37 | ALL_METHODS `/api/v1/registry/*` → registry | прямой доступ без изменений |
| 38 | ALL_METHODS `/api/v1/tasks/*` → orchestrator | задачи |
| 39 | ALL_METHODS `/api/v1/auth/*` → auth | аутентификация |
| 40 | ALL_METHODS `/api/v1/admin/*` → auth | администрирование |
| 41 | ALL_METHODS `/api/v1/chat/*` → query | чат |
| 42 | ALL_METHODS `/api/v1/text/*` → query | текст |
| 43 | ALL_METHODS `/api/v1/analyse/*` → analyse | анализ |
| 44 | ALL_METHODS `/api/v1/rag/*` → rag_search c path transform | RAG поиск, target="/api/v1/..." |
| 45 | GET `/api/v1/meridian/...` → None (410) | deprecated integration routes |
| 46 | GET `/api/v1/files/...` → None (410) | deprecated |
| 47 | GET `/api/v1/external/...` → None (410) | deprecated |
| 48 | GET `/api/v1/drafts/abc` → None (400 INVALID_DRAFT_ID) | нечисловой draft_id |
| 49 | GET `/api/v1/unknown/path` → None (404) | неизвестный путь |
| 50 | GET `/api/v1/drafts/` → registry (нормализованный) | trailing slash |
| 51 | Приоритет: специфичные правила перед общими | порядок ROUTE_TABLE |

---

## 3. `tests/test_config.py` (~80 строк)

`GatewayConfig` — валидация конфигурации.

**Сценарии:**
- `mode=real` — единственный поддерживаемый режим
- `mode=invalid` — `ValueError`
- `env=production` + `CORS_ALLOWED_ORIGINS=*` — `ValueError`
- `env=production` + `CORS_ALLOWED_ORIGINS=https://example.com` — OK
- `env=development` + `CORS_ALLOWED_ORIGINS=*` — OK
- `env=invalid` — `ValueError`
- `service_urls` по умолчанию — 11 сервисов
- Override через env: `AUTH_SERVICE_URL=http://custom:9090`

---

## 4. `tests/test_rate_limiter.py` (~150 строк)

Rate limiting (CM-2, CM-3, GW-4, GW-6).

**Сценарии:**
- `RateLimitRule` dataclass: limit, window, block
- `check_rate_limit()`: auth endpoint 10/min, chat 30/min, search 60/min, default 60/min
- Превышение лимита → `RateLimitResult.BLOCKED`
- Retry-After header в ответе
- `check_idor_rate_limit()`: превышение по конкретному resource
- Сброс после окна
- Разные правила для разных методов (POST /auth/token — строже)
- `RateLimitResult.THROTTLED` при приближении к лимиту

---

## 5. `tests/test_middleware_pii.py` (~80 строк)

`PIIQueryValidatorMiddleware` (GW-7).

**Сценарии (должны вернуть 400):**
- `?password=xxx`
- `?email=test@test.com`
- `?access_token=xxx`
- `?refresh_token=xxx`
- `?api_key=xxx`
- `?apikey=xxx`
- `?secret_key=xxx`
- `?phone=123`
- `?passport=123`
- `?inn=123`
- `?snils=123`
- `?ogrn=123`

**Сценарии (должны пройти):**
- `?document_key=xxx`
- `?file_key=xxx`
- `?search=xxx`
- `?q=xxx`
- `?page=1`

---

## 6. `tests/test_middleware_correlation.py` (~60 строк)

`CorrelationHeadersMiddleware` (P11-2/CM-5).

**Сценарии:**
- Входящий `X-Correlation-ID` пробрасывается в ответ
- Если клиент не передал — генерируется UUID
- Ответ содержит `X-Correlation-ID`
- Correlation-id передаётся в request.state

---

## 7. `tests/test_middleware_strip_slash.py` (~40 строк)

`StripTrailingSlashMiddleware`.

**Сценарии:**
- `/api/v1/drafts/` → путь нормализован до `/api/v1/drafts`
- `/api/v1/drafts` → без изменений
- `/` → без изменений (корень)
- `/api/v1/drafts/123/` → `/api/v1/drafts/123`

---

## 8. `tests/test_middleware_process_time.py` (~30 строк)

`ProcessTimeMiddleware`.

**Сценарии:**
- Ответ содержит `X-Process-Time`
- Значение — число с плавающей точкой (float)
- Время больше 0

---

## 9. `tests/test_rbac.py` (~250 строк)

`RBACMiddleware` — безопасность.

**Сценарии:**
- Без Authorization header → 401
- Bearer token не найден → 401
- GET `/api/v1/admin/*` для system_admin → 200
- GET `/api/v1/admin/*` для engineer → 403
- POST `/api/v1/admin/*` для engineer → 403
- POST `/api/v1/drafts` c `can_upload_documents=true` → 200
- POST `/api/v1/drafts` c `can_upload_documents=false` → 403
- POST/PUT/DELETE `/api/v1/registry/classifiers/*` c `can_manage_classifiers=true` → 200
- POST/PUT/DELETE `/api/v1/registry/classifiers/*` без права → 403
- POST/PUT/DELETE `/api/v1/registry/terminology/*` c `can_manage_terminology=true` → 200
- POST/PUT/DELETE `/api/v1/registry/terminology/*` без права → 403
- POST/PUT/PATCH/DELETE `/api/v1/registry/documents/*` c `can_manage_registry=true` → 200
- POST/PUT/PATCH/DELETE `/api/v1/registry/documents/*` без права → 403
- GET `/api/v1/registry/search` для knowledge_admin → 200
- GET `/api/v1/registry/search` для engineer → 403
- DELETE `/api/v1/documents/1` c правом → 200
- DELETE `/api/v1/documents/1` без права → 403
- DELETE `/api/v1/drafts/1` c правом → 200
- DELETE `/api/v1/drafts/1` без права → 403
- POST `/api/v1/documents/1/reprocess` c правом → 200
- POST `/api/v1/documents/1/reprocess` без права → 403
- GET `/api/v1/monitor/metrics` для system_admin → 200
- GET `/api/v1/monitor/metrics` для engineer → 403
- GET `/api/v1/health` без токена → 200 (публичный)
- POST `/api/v1/auth/token` без токена → 200 (публичный)

---

## 10. `tests/test_idempotency.py` (~100 строк)

`IdempotencyMiddleware`.

**Сценарии:**
- POST `/api/v1/drafts` с `Idempotency-Key: xxx` — первый запрос → 202
- POST `/api/v1/drafts` с тем же ключом — возвращает закешированный ответ (200/409)
- POST `/api/v1/chat/send` с `Idempotency-Key: xxx`
- POST без `Idempotency-Key` — обычный flow
- POST `/api/v1/documents/search` с ключом — игнорируется (не idempotency prefix)
- TTL истёк → повторный запрос создаёт новый ресурс
- Очистка устаревших записей при >1000

---

## 11. `tests/test_proxy.py` (~200 строк)

`proxy_request()` — проксирование к сервисам.

**Сценарии:**
- Успешное проксирование GET → 200, тело ответа передано
- Успешное проксирование POST с JSON телом
- Успешное проксирование POST с form-data (multipart)
- Прокси с `target_path=None` → используется `request.url.path`
- Прокси с `target_path` — path transform (Registry: /api/v1/documents → /api/v1/registry/documents)
- Пустой ответ (204 No Content) — тело не передаётся
- Сервис не настроен (нет в `service_urls`) → 502
- Сервис недоступен (`ConnectError`) → 502
- Таймаут сервиса (`TimeoutException`) → 504
- Hop-by-hop заголовки отфильтрованы (connection, keep-alive и др.)
- `X-User-ID` пробрасывается из request.state
- `X-Request-ID`, `X-Trace-ID` пробрасываются
- `X-Draft-ID`, `X-Document-ID`, `X-Version-ID` пробрасываются
- Location rewrite: 3xx ответ с внутренним Docker-хостом → переписан на Gateway
- Query string передаётся в target_url
- Request body: bytes читаются через `request.body()` и передаются в httpx
- Content-Type ответа сохранён
- Status code проксируется (200, 201, 204, 400, 404, 500)
- Redirect (3xx) c Location на Docker-хост → переписан на Gateway host

---

## 12. `tests/test_health.py` (~80 строк)

Health-check функции.

**Сценарии:**
- `check_service_health("auth")`: сервис отвечает 200 → "ok"
- `check_service_health("auth")`: сервис отвечает 503 → "degraded"
- `check_service_health("auth")`: ConnectError → "unavailable"
- `check_service_health("auth")`: Timeout → "unavailable"
- `check_service_health("unknown")`: нет в service_urls → "unavailable"
- `check_all_services_health()`: все ok → {"gateway":"ok", "auth":"ok", ...}
- `check_all_services_health()`: один не отвечает → "unavailable" в результатах
- `check_all_services_health()`: параллельный запуск (asyncio.gather)

---

## 13. `tests/test_client.py` (~60 строк)

`get_client()` / `close_client()` / `is_deprecated_integration_route()`.

**Сценарии:**
- `get_client()`: lazy initialization, возвращает `httpx.AsyncClient`
- `get_client()`: timeout равен `config.request_timeout`
- `get_client()`: follow_redirects=False
- `close_client()`: клиент закрыт, `_client = None`
- `is_deprecated_integration_route("/api/v1/meridian/test")` → True
- `is_deprecated_integration_route("/api/v1/files/123")` → True
- `is_deprecated_integration_route("/api/v1/external/sync")` → True
- `is_deprecated_integration_route("/api/v1/documents/1")` → False

---

## 14. `tests/test_diagnostics.py` (~80 строк)

Сбор диагностики.

**Сценарии:**
- `build_summary()`: формат вывода, содержит uptime
- `build_summary(verbose=True)`: расширенный вывод (диски, порты, Docker)
- `build_summary(log_lines=50)`: указанное число строк лога
- `build_service_diagnostics("gateway", 20)`: детали по сервису
- `build_service_diagnostics("unknown", 20)`: 404 + сообщение об ошибке
- `build_system_logs(100)`: системные логи
- `KNOWN_SERVICES`: содержит все ожидаемые сервисы

---

## 15. `tests/test_main_handlers.py` (~120 строк)

Собственные эндпоинты Gateway.

**Сценарии:**
- GET `/api/v1/health` без аутентификации → `{"status": "ok"}`
- GET `/api/v1/health` c system_admin → полный ответ со статусами сервисов
- GET `/api/v1/system/health/live` → `{"status":"ok"}`
- GET `/api/v1/system/health/ready` → `{"status":"ok"}`
- GET `/api/v1/system/mode` → mode, port, service_urls, allow_anonymous, request_timeout
- GET `/api/v1/monitor/metrics` → control_metrics + answer_metrics + logs
- HTTPException handler → `{"error": {"code": "...", "message": "..."}}`
- RequestValidationError → 422 c `details`
- ValidationError (Pydantic) → 422 c `errors`
- Internal error → 500
- NOT_FOUND → 404 c унифицированным форматом

---

## 16. `tests/test_logging.py` (~80 строк)

Логирование.

**Сценарии:**
- `JSONLogFormatter.format()`: JSON строка с полями timestamp, level, service, message
- PII-маскировка: `"password":"secret"` → `"password":"***"`
- PII-маскировка: `"access_token":"eyJ..."` → `"access_token":"***"`
- `mask_pii_in_text()`: единичное и множественное вхождение
- `PIIFilter.filter()`: не блокирует записи
- `setup_logging()`: уровень из `GATEWAY_LOG_LEVEL`
- `_parse_pii_fields()`: парсинг из env, значения по умолчанию
- `LOG_PII_FIELDS`: кастомный набор полей для маскировки
