# Orchestrator Service

Единая точка входа для публичного API Нейроассистента ПКБ. Сервис координирует взаимодействие между микросервисами и предоставляет унифицированный REST API для клиентских приложений.

## Описание

Orchestrator Service реализует API, описанный в `docs/api/orchestrator_service_api.md`, и выступает в роли шлюза, маршрутизируя запросы к внутренним микросервисам:

| Сервис | Назначение | Порт |
|--------|-----------|------|
| **auth-service** | Аутентификация и авторизация пользователей | 8082 |
| **query-service** | Обработка произвольного текста, чаты и сессии | 8083 |
| **registry-service** | Классификаторы, терминология и реестр документов | 8084 |
| **integration-service** | Интеграция с внешними системами (Meridian) | 8085 |
| **validation-service** | Валидация, сравнение и сопоставление проектных/нормативных данных | 8086 |
| **rag-service** | Векторный поиск (RAG) и генерация ответов LLM | 8087 |
| **ocr-service** | OCR распознавание документов | 8088 |

## Режимы работы с внешними сервисами

Для каждого внешнего сервиса поддерживаются 2 режима:

### 1. Mock/Stub режим (по умолчанию)
- Сервис возвращает сгенерированные тестовые данные
- Не требует подключения к реальным сервисам
- Используется для разработки и тестирования

### 2. Режим реальных API вызовов
- Сервис выполняет HTTP-запросы к внешним микросервисам
- Требует указания URL сервиса в конфигурации
- Активируется при установке `*_MOCK=false` и указании `*_SERVICE_URL`

## Технический стек

- **FastAPI** — веб-фреймворк
- **Pydantic v2** — валидация схем и настроек
- **httpx** — HTTP-клиент для внешних сервисов
- **Uvicorn** — ASGI-сервер
- **Pytest** — тестирование
- **python-jose** — JWT-токены
- **passlib** — хэширование паролей

## Установка

```bash
cd backend/orchestrator_service
pip install -r requirements.txt
```

## Конфигурация

Скопируйте `.env.example` в `.env` и настройте параметры:

```bash
cp .env.example .env
```

### Пример конфигурации для работы с реальными сервисами:

```env
AUTH_SERVICE_URL=http://auth-service:8080
AUTH_SERVICE_MOCK=false

RAG_SERVICE_URL=http://rag-service:8081
RAG_SERVICE_MOCK=false

QUERY_SERVICE_URL=http://query-service:8083
QUERY_SERVICE_MOCK=false
```

### Для работы в mock-режиме (по умолчанию):

```env
AUTH_SERVICE_MOCK=true
RAG_SERVICE_MOCK=true
QUERY_SERVICE_MOCK=true
OCR_SERVICE_MOCK=true
VALIDATE_SERVICE_MOCK=true
INTEGRATION_SERVICE_MOCK=true
REGISTRY_SERVICE_MOCK=true
```

Основные параметры:
- `APP_VERSION` — версия приложения (по умолчанию `1.0.0`)
- `DEBUG` — режим отладки
- `HOST` — хост (по умолчанию `0.0.0.0`)
- `PORT` — порт (по умолчанию `8000`)
- `JWT_SECRET_KEY` — секретный ключ для JWT
- `JWT_ALGORITHM` — алгоритм JWT (по умолчанию `HS256`)

## Запуск

```bash
# Development mode с hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Через entry point (также с reload)
python main.py
```

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Документы (`/api/v1/documents`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/documents` | Загрузка документа (multipart/form-data) |
| GET | `/documents` | Список документов с пагинацией |
| GET | `/documents/queue` | Очередь обработки документов |
| GET | `/documents/{doc_id}` | Информация о документе |
| GET | `/documents/{doc_id}/file` | Скачивание файла документа |
| GET | `/documents/{doc_id}/status` | Статус обработки |
| GET | `/documents/{doc_id}/pages` | Список страниц документа |
| GET | `/documents/{doc_id}/pages/{page_num}` | Просмотр страницы с блоками |
| GET | `/documents/{doc_id}/pages/{page_num}/text` | Текст страницы |
| GET | `/documents/{doc_id}/pages/{page_num}/preview` | Превью страницы |
| GET | `/documents/{doc_id}/parameters` | Извлечённые параметры |
| GET | `/documents/{doc_id}/errors` | Журнал ошибок обработки |
| DELETE | `/documents/{doc_id}` | Удаление документа |
| POST | `/documents/{doc_id}/reprocess` | Повторная обработка |

### Поиск и RAG (`/api/v1/documents/search`, `/api/v1/ask`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/documents/search` | Семантический поиск по фрагментам |
| GET | `/documents/search?q=...` | Быстрый поиск (GET-вариант) |
| POST | `/ask` | Генерация ответа с источниками (RAG) |

### Валидация и проверки (`/api/v1/validate`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/validate/compare` | Запуск сопоставления нормативных и проектных данных |
| GET | `/validate/compare/{comparison_id}` | Результат сопоставления |
| POST | `/validate/compare/batch` | Массовое сопоставление пар фрагментов |
| POST | `/validate/checks` | Запуск проверки проектных параметров |
| GET | `/validate/checks/{check_run_id}` | Статус проверки |
| GET | `/validate/checks/{check_run_id}/export` | Экспорт результатов проверки |

### Мониторинг (`/api/v1/monitor`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/monitor/metrics` | Метрики качества системы |

### Служебные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Информация о сервисе |
| GET | `/system/health` | Проверка состояния системы (публичный) |

## Аутентификация

- Публичные endpoint'ы: `/system/health`, `/docs`, `/redoc`, `/openapi.json` — не требуют аутентификации
- Остальные endpoint'ы защищены Bearer JWT-токеном
- В mock-режиме (`AUTH_SERVICE_MOCK=true`) аутентификация пропускается и возвращается тестовый пользователь
- В режиме реальных API токен валидируется через `auth-service`

## Структура проекта

```
orchestrator_service/
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI приложение
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps/
│   │   │   └── __init__.py            # Auth dependencies (Bearer token)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                 # Конфигурация роутеров
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── documents.py       # CRUD документов, страницы, параметры
│   │           ├── search.py          # Поиск и Ask endpoint'ы
│   │           ├── validate.py        # Сравнение, проверки, экспорт
│   │           ├── health.py          # Health check
│   │           └── monitor.py         # Метрики и мониторинг
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                  # Настройки (Pydantic Settings)
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py                  # Общие схемы (Error, Pagination, ListResponse)
│   │   ├── documents.py               # Схемы документов
│   │   ├── search.py                  # Схемы поиска и Ask
│   │   └── validation.py              # Схемы валидации (Compare, CheckRun, Health)
│   └── services/
│       ├── __init__.py
│       ├── base_client.py             # Базовый клиент с dual-mode (mock/real)
│       ├── auth_client.py             # Auth Service
│       ├── rag_client.py              # RAG Service (векторный поиск, генерация)
│       ├── query_client.py            # Query Service (текст, чаты, сессии)
│       ├── ocr_client.py              # OCR Service
│       ├── validate_client.py         # Validation Service
│       ├── integration_client.py      # Integration Service (файлы, Meridian)
│       └── registry_client.py         # Registry Service (классификаторы, термины)
├── services/
│   ├── __init__.py
│   └── response.py                    # Формирование единых API-ответов
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Фикстуры (TestClient, mock-режим)
│   ├── test_documents.py              # Тесты документов
│   ├── test_health.py                 # Тесты health и служебных endpoint'ов
│   ├── test_monitor.py                # Тесты метрик
│   ├── test_search.py                 # Тесты поиска и Ask
│   └── test_validate.py               # Тесты валидации
├── requirements.txt
├── .env.example
└── README.md
```

## Добавление нового сервиса

1. Создайте клиент в `app/services/{service}_client.py`, наследуясь от `ServiceClient`
2. Реализуйте метод `_generate_mock` для mock-ответов
3. Добавьте настройки URL и mock-режима в `app/core/config.py`
4. Используйте клиент в endpoint'ах

### Пример клиента:

```python
from app.services.base_client import ServiceClient
from app.core.config import settings

class MyServiceClient(ServiceClient):
    def __init__(self):
        super().__init__(
            service_name="my_service",
            service_url=settings.services.MY_SERVICE_URL,
            mock_mode=settings.services.MY_SERVICE_MOCK,
        )

    async def _generate_mock(self, method, endpoint, default_mock, **kwargs):
        if endpoint == "/api/endpoint":
            return {"mock": "data"}
        return default_mock
```

## Тестирование

```bash
# Запуск всех тестов
pytest

# С coverage отчётом
pytest --cov=app --cov-report=term-missing

# Запуск конкретного тестового файла
pytest tests/test_search.py

# Запуск конкретного теста
pytest tests/test_search.py::TestSearchPost::test_search_basic -v
```

- Все тесты запускаются в mock-режиме (устанавливается в `conftest.py`)
- Тесты используют `TestClient` из FastAPI
- Для аутентифицированных запросов используется фикстура `auth_header`

## Архитектура клиентов сервисов

Базовый класс `ServiceClient` предоставляет:

- **Dual-mode**: автоматический выбор между mock и реальным HTTP-вызовом
- **Единая обработка ошибок**: `ServiceError` с кодом и деталями
- **Управление HTTP-клиентом**: пул соединений через `httpx.AsyncClient`

Каждый клиент наследуется от `ServiceClient` и реализует:
- `_generate_mock()` — генерация тестовых данных для конкретного сервиса
- Публичные методы-обёртки (`async def search(...)`, `async def upload(...)` и т.д.)

## Формат ошибок API

Все ошибки возвращаются в едином формате:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден",
    "details": {
      "document_id": "doc-123"
    }
  }
}
```

Коды ошибок: `BAD_REQUEST`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `VALIDATION_FAILED`, `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`.