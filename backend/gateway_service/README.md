# PKB Neuroassistant — Mock Services

Набор mock-сервисов для эмуляции бэкенда PKB Neuroassistant.  
Стек: **Python 3.13+**, **FastAPI**, **in-memory storage**.  
Все сервисы объединены в единый шлюз на порту **8081** (эмуляция nginx).

> 📖 **Полная спецификация API** — в папке [`docs/`](docs/).  
> Там описаны форматы ответов, статусные модели, пайплайны, матрица доступа и коды ошибок.

---

## 📦 Состав

| Сервис | Роль | Эндпоинты |
|--------|------|-----------|
| **Auth Service** | Аутентификация, пользователи, роли, аудит | `/api/v1/auth/*`, `/api/v1/admin/*` |
| **Orchestrator** | Документы, поиск, валидация, метрики | `/api/v1/documents/*`, `/api/v1/monitor/*` |
| **Query Service** | Чат-сессии, Q&A, текстовый поиск | `/api/v1/chat/*`, `/api/v1/text/*` |
| **Registry** | Классификаторы, терминология, НСИ | `/api/v1/classifiers/*`, `/api/v1/terminology/*`, `/api/v1/common/*`, `/api/v1/registry/documents/*` |

Детальное описание каждого эндпоинта (параметры, тела запросов/ответов, примеры) — в `docs/`:

- [`docs/common.md`](docs/common.md) — общие положения, формат ошибок, пагинация, матрица RBAC
- [`docs/orchestrator_service_api.md`](docs/orchestrator_service_api.md) — документы, поиск, очередь
- [`docs/query_service_api.md`](docs/query_service_api.md) — чат, Q&A, текстовый поиск
- [`docs/registry_service_api.md`](docs/registry_service_api.md) — классификаторы, терминология, реестр НСИ
- [`docs/overview.md`](docs/overview.md) — пайплайны обработки, FSM, архитектура

---

## 🚀 Быстрый старт

```bash
# 1. Установить зависимости
pip install fastapi uvicorn pytest httpx python-multipart

# 2. Запустить единый шлюз (все сервисы на порту 8081)
python backend/gateway_service/mocks/gateway.py

# 3. Или запустить сервисы по отдельности
python backend/gateway_service/mocks/start_service.py all
python backend/gateway_service/mocks/start_service.py auth       # только Auth (порт 8082)
python backend/gateway_service/mocks/start_service.py orchestrator  # (порт 8081)
python backend/gateway_service/mocks/start_service.py query      # (порт 8083)
python backend/gateway_service/mocks/start_service.py registry   # (порт 8084)
```

После запуска откройте `http://127.0.0.1:8081/docs` — интерактивная Swagger-документация.

---

## 🧪 Запуск тестов

```bash
# Все 288 тестов
python -m pytest backend/gateway_service/mocks/tests/ -v

# По файлам
python -m pytest backend/gateway_service/mocks/tests/test_api.py        -v  # 151 базовых
python -m pytest backend/gateway_service/mocks/tests/test_extended.py   -v  # 61 расширенный
python -m pytest backend/gateway_service/mocks/tests/test_tz_coverage.py -v  # 76 покрытие ТЗ
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

Мок-сервис эмулирует полноценную матрицу доступа:

| Эндпоинт | engineer | knowledge_admin | system_admin | Аноним |
|----------|----------|----------------|-------------|--------|
| `/auth/*`, `/system/health` | ✅ | ✅ | ✅ | ✅ |
| `GET /documents/*`, `/chat/*`, `/classifiers`, `/terminology` | ✅ | ✅ | ✅ | ❌ **401** |
| `POST /documents` (загрузка) | по `can_upload_documents` | ✅ | ✅ | ❌ **401** |
| `DELETE /documents/{id}`, `/reprocess`, `/approve`, `/promote` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `POST/PUT/DELETE /classifiers`, `/terminology` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `POST/PUT/DELETE /registry/documents` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `GET /monitor/metrics` | ❌ **403** | ✅ | ✅ | ❌ **401** |
| `/admin/*` | ❌ **403** | ❌ **403** | ✅ | ❌ **401** |

> Полная матрица доступа — в [`docs/common.md`](docs/common.md#матрица-доступа-rbac).

---

## 📋 Структура проекта

```
backend/gateway_service/
├── docs/                           # Полная спецификация API
│   ├── common.md
│   ├── orchestrator_service_api.md
│   ├── query_service_api.md
│   ├── registry_service_api.md
│   └── overview.md
├── mocks/
│   ├── common.py                   # Seed-данные, модели, утилиты
│   ├── gateway.py                  # Единый шлюз (порт 8081)
│   ├── start_service.py            # Утилита запуска
│   ├── run_all.py                  # Запуск всех сервисов
│   ├── README.md                   # Этот файл
│   │
│   ├── auth_service/
│   │   └── main.py                 # Auth Service (router)
│   ├── orchestrator_service/
│   │   └── main.py                 # Orchestrator (router)
│   ├── query_service/
│   │   └── main.py                 # Query Service (router)
│   ├── registry_service/
│   │   └── main.py                 # Registry Service (2 routers)
│   │
│   └── tests/
│       ├── test_api.py             # 151 базовых теста
│       ├── test_extended.py        # 61 расширенный тест
│       └── test_tz_coverage.py     # 76 тестов покрытия ТЗ
└── README.md                       # Этот файл
```

---

## ⚠️ Известные отличия от продакшена

- Данные **in-memory** (теряются при перезапуске сервиса)
- Нет реального OCR/RAG — результаты эмулируются
- Ответы `POST /chat` и `/text/ask` генерируются из предопределённых шаблонов
- Асинхронные операции (`POST /documents`) сразу возвращают `202` без реальной обработки
- Idempotency-Key кеширует ответы в памяти (TTL: 1 час)