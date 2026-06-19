# Mock-режим Gateway: Архитектура

## Назначение

Mock-режим (`mocks/gateway.py`) — единый FastAPI-сервер на порту `8081`, эмулирующий все внутренние микросервисы PKB Neuroassistant в одном процессе. Предназначен для:

- **Разработки Web UI** — не требует поднятия 12 отдельных сервисов
- **Интеграционных тестов** — 500+ тестов проверяют контракты API
- **Демо/презентаций** — полностью рабочее in-memory приложение без внешних зависимостей

## Архитектура

```
Web UI → Mock Gateway (:8081)
           ├── Auth handlers      (mock JWT, users, roles)
           ├── Orchestrator       (mock documents, drafts, tasks)
           ├── Query              (mock chat, search, Q&A)
           └── Registry           (mock classifiers, terminology, documents)
```

### Ключевые отличия от production

| Аспект | Production Gateway | Mock Gateway |
|--------|-------------------|--------------|
| **Порт** | `8080` | `8081` |
| **Сервисы** | Reverse-proxy к 12 микросервисам | Всё в одном процессе |
| **Данные** | PostgreSQL, MinIO, Redis | In-memory (Python dict) |
| **JWT** | Валидация через Auth Service | Симуляция: `_access_token_map` |
| **OCR/Parser/RAG** | Реальные сервисы | Эмуляция (предопределённые ответы) |
| **Idempotency** | In-memory (на время жизни процесса) | In-memory |
| **Health check** | Агрегация статусов всех сервисов | `{"status": "ok"}` |
| **CORS** | Настраивается через `CORS_ALLOWED_ORIGINS` | Все origins (`*`) |

### Middleware stack (порядок применения)

```
CORS → PIIQueryValidator → RBAC → Idempotency → ProcessTime → StripTrailingSlash → Router
```

Совпадает с production Gateway, за исключением:
- В production есть `RequestTracingMiddleware` и `CorrelationHeadersMiddleware` (для сквозной трассировки)
- В mock эти middleware не нужны — всё работает в одном процессе

### RBAC в mock-режиме

Использует ту же матрицу доступа, что и production:
- `/api/v1/auth/*` — анонимный доступ
- `/api/v1/admin/*` — только `system_admin`
- `POST /api/v1/drafts` — требует `can_upload_documents`
- `POST/PUT/DELETE /api/v1/registry/*` — требует соответствующего permission
- `GET /api/v1/registry/search` — `knowledge_admin` / `system_admin`
- Остальные эндпоинты — любой аутентифицированный пользователь

### Формат ошибок

Единый формат, совместимый с production:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден",
    "details": {}
  }
}
```

## Запуск

```bash
# Единый шлюз (все сервисы на порту 8081)
python mocks/gateway.py

# Или сервисы по отдельности
python mocks/start_service.py all
python mocks/start_service.py auth
python mocks/start_service.py orchestrator
python mocks/start_service.py query
python mocks/start_service.py registry
```

## Тестирование

```bash
# Все 500+ тестов
python -m pytest mocks/tests/ -v

# По файлам
python -m pytest mocks/tests/test_api.py -v
python -m pytest mocks/tests/test_gateway_routing.py -v
python -m pytest mocks/tests/test_integration_gateway.py -v
```

### Тестовый режим

При `ALLOW_ANONYMOUS = True` (устанавливается в тестах) анонимные запросы пропускаются без JWT-валидации.

## Seed-данные

Mock-сервис использует `mocks/common.py` с предопределёнными данными:

- **Пользователи**: 4 тестовых пользователя (ivanov, petrova, admin, kuznetsov)
- **Документы**: 5 seed-документов с версиями
- **Черновики**: 2 seed-черновика (один uploaded, один previewing)
- **Чат**: 2 проекта, 2 сессии, сообщения
- **Классификаторы**: MKS, OKS, OKSTU, UDK
- **Терминология**: 5 предопределённых терминов

## Ограничения

1. **In-memory данные** — теряются при перезапуске
2. **Нет реального OCR/RAG** — результаты эмулируются
3. **Ответы чата** — из предопределённых шаблонов (нет LLM)
4. **Асинхронные операции** — сразу возвращают `202` без реальной обработки
5. **Idempotency-Key** — in-memory кеш на 1 час (теряется при перезапуске)
6. **Scale** — не рассчитан на высокую нагрузку (single-process)
7. **Данные Registry** — не синхронизируются с другими мок-сервисами (кроме общих seed)
