# PKB Neuroassistant — Gateway Service & Mock Services

Production Gateway — reverse-proxy для внутренних микросервисов PKB Neuroassistant.  
Набор mock-сервисов для эмуляции бэкенда PKB Neuroassistant.  

Стек: **Python 3.13+**, **FastAPI**, **httpx** (gateway).

> 📖 **Полная спецификация API** — в папке [`docs/`](docs/).

---

## 📦 Состав

| Сервис | Порт | Роль |
|--------|:----:|------|
| **Gateway** | `8080` | Reverse-proxy, JWT, RBAC, логирование |
| **Auth Service** | `8082` | Аутентификация, пользователи, роли, аудит |
| **Orchestrator** | `8081` | Координация пайплайна, FSM, задачи |
| **Query Service** | `8083` | Чат-сессии, Q&A, текстовый поиск |
| **Registry** | `8084` | Данные реестра: документы, черновики, классификаторы, терминология |
| **Integration** | `8085` | Интеграция с Meridian, файлы, external API |
| **Converter-Validator** | `8086` | Конвертация и валидация документов |
| **Parser** | `8087` | Парсинг цифровых PDF/DOC |
| **OCR** | `8088` | OCR-распознавание сканов |
| **Analyse** | `8089` | Анализ, сравнение, расчёт |
| **RAG Builder** | `8090` | Чанкование и построение векторного индекса |
| **RAG Search** | `8091` | Гибридный поиск релевантных чанков |

---

## 🚀 Быстрый старт

### Production Gateway

```bash
pip install fastapi uvicorn httpx python-multipart
python -m gateway.main
```

### Mock-сервер (для разработки/тестирования)

```bash
python backend/gateway_service/mocks/gateway.py
python backend/gateway_service/mocks/run_all.py
python backend/gateway_service/mocks/start_service.py
```

---

## 🧪 Запуск тестов

### Mock-тесты (530+ тестов)

```bash
python -m pytest backend/gateway_service/mocks/tests/ -v
```

### Gateway Integration Tests (168 unit + 65 Docker)

```bash
# Unit-тесты (без Docker)
cd backend/gateway_service && python -m pytest tests/ -v -m "not docker"

# Все тесты (требуют Docker с Gateway на порту 18080)
cd backend/gateway_service && python -m pytest tests/ -v

# Через service_checker (recheck.bat)
python -m service_checker docker --action full-report
```

---

## 🔑 Тестовые учётные данные

| Email | Пароль | Роль |
|-------|--------|------|
| `ivanov@example.com` | `secret123` | engineer |
| `petrova@example.com` | `secret456` | knowledge_admin |
| `admin@example.com` | `admin123` | system_admin |
| `kuznetsov@example.com` | `secret789` | engineer |

---

## 🛡️ RBAC (Role-Based Access Control)

| Эндпоинт | engineer | knowledge_admin | system_admin | Аноним |
|----------|----------|----------------|-------------|--------|
| `/auth/*`, `/system/health`, `/health` | ✅ | ✅ | ✅ | ✅ |
| `GET /documents/*`, `/chat/*`, `/classifiers`, `/terminology`, `/registry/*` | ✅ | ✅ | ✅ | ❌ |
| `POST /drafts`, `POST /documents` | по `can_upload_documents` | ✅ | ✅ | ❌ |
| `DELETE /documents/{id}`, `/reprocess`, `/approve` | ❌ | ✅ | ✅ | ❌ |
| `POST/PUT/DELETE /classifiers`, `/terminology`, `/registry/*` | ❌ | ✅ | ✅ | ❌ |
| `/admin/*` | ❌ | ❌ | ✅ | ❌ |

---

## 📋 Структура проекта

```
backend/gateway_service/
├── docs/                           # Полная спецификация API
├── gateway/                        # Production reverse-proxy Gateway
│   ├── main.py                     # FastAPI app, middleware, endpoints
│   ├── client.py                   # HTTP-клиент для проксирования
│   ├── config.py                   # Конфигурация (env vars)
│   ├── routers.py                  # Catch-all router
│   ├── logging_config.py           # JSON-логирование (P11)
│   ├── rate_limiter.py             # Rate limiting + IDOR (CM-2, CM-3, GW-4, GW-6)
│   └── diagnostics.py              # Системная диагностика
├── mocks/                          # Mock-сервер для тестирования/разработки
│   ├── common.py                   # Seed-данные, in-memory хранилища
│   ├── gateway.py                  # Единый шлюз + middleware
│   ├── handlers/                   # Хендлеры мок-сервисов
│   ├── start_service.py            # Утилита запуска
│   └── tests/                      # 530+ тестов моков
├── tests/                          # Gateway Integration Tests
│   ├── conftest.py                 # Фикстуры (unit + Docker)
│   ├── helpers.py                  # Утилиты
│   ├── test_routing.py             # resolve_service / ROUTE_TABLE
│   ├── test_config.py              # GatewayConfig
│   ├── test_rate_limiter.py        # Rate limiting + IDOR
│   ├── test_middleware_*.py         # Middleware тесты
│   ├── test_rbac.py                # RBACMiddleware
│   ├── test_idempotency.py         # IdempotencyMiddleware
│   ├── test_proxy.py               # proxy_request
│   ├── test_health.py              # check_service_health
│   ├── test_client.py              # get_client / is_deprecated
│   ├── test_diagnostics.py         # build_summary
│   ├── test_main_handlers.py       # Собственные эндпоинты
│   └── test_logging.py             # JSONLogFormatter / PIIFilter
├── requirements.txt
├── guide.md                        # Архитектурные решения
├── specificity.md                  # Аномалии
└── README.md                       # Этот файл
```

---

## 🧠 Ключевые возможности Gateway (v1.2.0)

| Возможность | Описание |
|-------------|----------|
| **JWT-аутентификация** | Проверка Bearer-токена через Auth Service |
| **RBAC** | Матрица доступа на основе роли и permissions |
| **Path-pattern routing** | Маршрутизация по шаблону пути + HTTP-методу |
| **URL-трансформация Registry** | `/api/v1/documents/{id}` → `/api/v1/registry/documents/{id}` |
| **Структурированное логирование (P11-1)** | JSON с timestamp, level, service, request_id и т.д. |
| **X-Request-ID (P11-2)** | UUIDv4, проброс во все downstream |
| **PII-фильтрация** | password, access_token, refresh_token → *** |
| **Rate limiting + IDOR** | InMemory, 14 групп, 80% threshold, IDOR 30/мин |
| **Idempotency-Key** | Кеширование POST-ответов (TTL: 1 час) |
| **CORS** | Настраивается через `CORS_ALLOWED_ORIGINS` |
