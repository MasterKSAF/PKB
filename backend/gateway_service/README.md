# PKB Neuroassistant — Gateway Service & Mock Services

Production Gateway — reverse-proxy для внутренних микросервисов PKB Neuroassistant.  
Набор mock-сервисов для эмуляции бэкенда PKB Neuroassistant.  

Стек: **Python 3.13+**, **FastAPI**, **httpx** (gateway).

> 📖 **Полная спецификация API** — в папке [`docs/`](docs/).  
> Там описаны форматы ответов, статусные модели, пайплайны, матрица доступа, коды ошибок,
> а также требования к логированию (P11) и трассировке (P11-2).

---

## 📦 Состав

| Сервис | Порт | Роль | Эндпоинты (через Gateway) |
|--------|:----:|------|---------------------------|
| **Gateway** | `8080` | Reverse-proxy, JWT, RBAC, логирование | `/api/v1/system/health`, `/api/v1/health`, `/api/v1/system/mode` |
| **Auth Service** | `8082` | Аутентификация, пользователи, роли, аудит | `/api/v1/auth/*`, `/api/v1/admin/*` |
| **Orchestrator** | `8081` | Документы, черновики, задачи, мониторинг | `/api/v1/documents/*`, `/api/v1/drafts/*`, `/api/v1/tasks/*`, `/api/v1/monitor/*` |
| **Query Service** | `8083` | Чат-сессии, Q&A, текстовый поиск | `/api/v1/chat/*`, `/api/v1/text/*` |
| **Registry** | `8084` | Классификаторы, терминология, реестр НСИ | `/api/v1/registry/*`, `/api/v1/registry/categories/*` |
| **Integration** | `8085` | Интеграция с Meridian, файлы, external API | `/api/v1/meridian/*`, `/api/v1/files/*`, `/api/v1/external/*` |
| **Converter-Validator** | `8086` | Конвертация и валидация документов | Внутренний (через Orchestrator) |
| **Parser** | `8087` | Парсинг цифровых PDF/DOC | Внутренний (через Orchestrator) |
| **OCR** | `8088` | OCR-распознавание сканов | Внутренний (через Orchestrator) |
| **Analyse** | `8089` | Анализ, сравнение, расчёт | `/api/v1/analyse/*` |
| **RAG Builder** | `8090` | Чанкование и построение векторного индекса | Внутренний (через Query) |
| **RAG Search** | `8091` | Гибридный поиск релевантных чанков | Внутренний (через Query) |

Детальное описание каждого эндпоинта — в `docs/`:

- [`docs/common_api.md`](docs/common_api.md) — общие положения, формат ошибок, пагинация, матрица RBAC, rate limiting, edge cases, стандарт логирования (P11)
- [`docs/gateway_service_api.md`](docs/gateway_service_api.md) — маршрутизация, middleware, собственные эндпоинты Gateway
- [`docs/orchestrator_service_api.md`](docs/orchestrator_service_api.md) — документы, черновики, задачи
- [`docs/query_service_api.md`](docs/query_service_api.md) — чат, Q&A, текстовый поиск
- [`docs/registry_service_api.md`](docs/registry_service_api.md) — классификаторы, терминология, реестр НСИ
- [`docs/converter_validator_service_api.md`](docs/converter_validator_service_api.md) — конвертация и валидация
- [`docs/parser_service_api.md`](docs/parser_service_api.md) — парсинг цифровых документов
- [`docs/ocr_service_api.md`](docs/ocr_service_api.md) — OCR-распознавание
- [`docs/overview.md`](docs/overview.md) — пайплайны обработки, FSM, архитектура
- [`docs/mock_architecture.md`](docs/mock_architecture.md) — архитектура mock-режима (GW-8)

---

## 🚀 Быстрый старт

### Production Gateway

```bash
# 1. Установить зависимости
pip install fastapi uvicorn httpx python-multipart

# 2. Запустить reverse-proxy Gateway (порт 8080)
python -m gateway.main
```

### Mock-сервер (для разработки/тестирования)

```bash
# Запустить единый шлюз (все сервисы на порту 8081)
python backend/gateway_service/mocks/gateway.py

# Или запустить сервисы по отдельности
python backend/gateway_service/mocks/start_service.py all
python backend/gateway_service/mocks/start_service.py auth         # только Auth (порт 8082)
python backend/gateway_service/mocks/start_service.py orchestrator # (порт 8081)
python backend/gateway_service/mocks/start_service.py query        # (порт 8083)
python backend/gateway_service/mocks/start_service.py registry     # (порт 8084)
```

После запуска откройте `http://127.0.0.1:8081/docs` — интерактивная Swagger-документация.

---

## 🧪 Запуск тестов

```bash
# Все 496 тестов
python -m pytest backend/gateway_service/mocks/tests/ -v

# По файлам
python -m pytest backend/gateway_service/mocks/tests/test_api.py        -v  # 158 базовых
python -m pytest backend/gateway_service/mocks/tests/test_extended.py   -v  # 68 расширенных
python -m pytest backend/gateway_service/mocks/tests/test_tz_coverage.py -v  # 115 покрытие ТЗ
python -m pytest backend/gateway_service/mocks/tests/test_checker_coverage.py -v  # checker coverage
python -m pytest backend/gateway_service/mocks/tests/test_gateway_fails.py -v  # gateway fails
```

---

## 🔑 Тестовые учётные данные

| Email | Пароль | Роль | Права на загрузку |
|-------|--------|------|-------------------|
| `ivanov@example.com` | `secret123` | engineer | ❌ нет |
| `petrova@example.com` | `secret456` | knowledge_admin | ✅ да |
| `admin@example.com` | `admin123` | system_admin | ✅ да |
| `kuznetsov@example.com` | `secret789` | engineer | ❌ нет |

---

## 🛡️ RBAC (Role-Based Access Control)

Производственный Gateway проверяет JWT через Auth Service и применяет матрицу доступа:

| Эндпоинт | engineer | knowledge_admin | system_admin | Аноним |
|----------|----------|----------------|-------------|--------|
| `/auth/*`, `/system/health`, `/health` | ✅ | ✅ | ✅ | ✅ |
| `GET /documents/*`, `/chat/*`, `/classifiers`, `/terminology`, `/registry/*` | ✅ | ✅ | ✅ | ❌ **401** |
| `POST /drafts`, `POST /documents` | по `can_upload_documents` | ✅ | ✅ | ❌ **401** |
| `DELETE /documents/{id}`, `/reprocess`, `/approve` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `POST/PUT/DELETE /classifiers`, `/terminology`, `/registry/*` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `GET /monitor/metrics` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `GET /tasks/*` (read-only) | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `/admin/*` | ❌ **403** | ❌ **403** | ✅ | ❌ **401** |

> Полная матрица доступа — в [`docs/common_api.md`](docs/common_api.md#матрица-доступа-rbac).

---

## 📋 Структура проекта

```
backend/gateway_service/
├── docs/                           # Полная спецификация API (12 файлов)
│   ├── common_api.md
│   ├── gateway_service_api.md
│   ├── auth_service_api.md
│   ├── orchestrator_service_api.md
│   ├── query_service_api.md
│   ├── registry_service_api.md
│   ├── converter_validator_service_api.md
│   ├── parser_service_api.md
│   ├── ocr_service_api.md
│   └── overview.md
├── gateway/                        # Production reverse-proxy Gateway
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, middleware, endpoints
│   ├── client.py                   # HTTP-клиент для проксирования запросов
│   ├── config.py                   # Конфигурация (env vars)
│   ├── routers.py                  # Catch-all router
│   ├── logging_config.py           # Структурированное JSON-логирование (P11)
│   └── rate_limiter.py             # Rate limiting + IDOR protection (CM-2, CM-3, GW-4, GW-6)
├── mocks/                          # Mock-сервер для тестирования/разработки
│   ├── common.py                   # Seed-данные, in-memory хранилища, модели
│   ├── gateway.py                  # Единый шлюз (порт 8081) + middleware
│   ├── handlers/                   # Хендлеры мок-сервисов
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── orch_routes.py
│   │   ├── query_routes.py
│   │   └── registry_routes.py
│   ├── start_service.py            # Утилита запуска
│   ├── run_all.py                  # Запуск всех сервисов
│   └── tests/                      # 496 тестов
│       ├── test_api.py
│       ├── test_extended.py
│       ├── test_tz_coverage.py
│       ├── test_checker_coverage.py
│       ├── test_gateway_fails.py
│       └── test_registry_paths.py
├── docker-compose.yml              # Production: сети L2–L4, все сервисы
├── requirements.txt
├── specificity.md                  # Аномалии и изменения
├── todo.md                         # Текущий план работ
└── README.md                       # Этот файл
```

---

## 🧠 Ключевые возможности Gateway (v1.2.0)

| Возможность | Описание |
|-------------|----------|
| **JWT-аутентификация** | Проверка Bearer-токена через Auth Service (`POST /internal/auth/validate`) |
| **RBAC** | Матрица доступа на основе роли и permissions пользователя |
| **Структурированное логирование (P11-1)** | JSON-логирование с обязательными полями (timestamp, level, service, request_id, user_id, path, method, status, latency_ms) |
| **X-Request-ID (P11-2)** | Автоматическая генерация UUIDv4 при отсутствии, проброс во все downstream сервисы |
| **X-User-ID (P11-2)** | Проброс ID аутентифицированного пользователя в downstream сервисы |
| **request_id в ошибках** | При ошибке `request_id` возвращается в `details.request_id` для быстрого поиска в логах |
| **PII-фильтрация** | Маскирование `password`, `access_token`, `refresh_token` в логах |
| **Health check** | Минимальный `{"status":"ok"}` для неаутентифицированных; полный ответ — только для system_admin |
| **Rate limiting + IDOR (CM-2, CM-3, GW-4, GW-6)** | InMemory rate limiter. 14 групп эндпоинтов. 80% threshold → WARNING. IDOR: 30 запросов/мин к draft_id / document_id / session_id. Настройка: `RATE_LIMIT_ENABLED`. |
| **Idempotency-Key** | Кеширование POST-ответов для `/drafts*` и `/chat*` (TTL: 1 час) |
| **CORS** | Настраивается через `CORS_ALLOWED_ORIGINS` |

---

## ⚠️ Известные отличия от продакшена

- Данные **in-memory** (теряются при перезапуске мок-сервиса)
- Нет реального OCR/RAG — результаты эмулируются
- Ответы `POST /chat` и `/text/ask` генерируются из предопределённых шаблонов
- Асинхронные операции (`POST /documents`) сразу возвращают `202` без реальной обработки
- Idempotency-Key кеширует ответы в памяти (TTL: 1 час)
- Импорт CSV/XLSX: для XLSX требуется `openpyxl`, для CSV используется встроенный `csv`
- `scope` терминологии приведён к `list[str]` (seed-данные и модель), обратная совместимость со строкой сохранена
- **POST /documents устарел** — единая точка входа `POST /drafts` (OR-11). POST /documents возвращает 410 Gone.
- **uploaded_by → created_by** (DB-11, OR-4) — во всех моделях и ответах
- **preview_metadata** содержит 11 полей (OR-9). `udc` → `udk_code` в metadata (DB-27)
- **GET /drafts/{id}** возвращает document_id, version_id, file_hash_sha256, is_new_document (OR-7)
- **Вкладка `checks` удалена** из `available_tabs` пользователей (GW-13)
- **Rate limiting** — InMemory по умолчанию, Redis для production (CM-2, GW-4)
- **IDOR protection** — rate limit по draft_id/document_id/session_id (CM-3, GW-6)
- **Сетевая изоляция** — docker-compose.yml с L2 (dmz), L3 (internal), L4 (data) сетями (CM-4, GW-1, GW-2, GW-5)
