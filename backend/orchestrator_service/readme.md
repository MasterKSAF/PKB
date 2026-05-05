# Orchestrator Service

Единая точка входа для публичного API Нейроассистента ПКБ.

## Описание

Orchestrator Service реализует API, описанный в `docs/api/orchestrator_service_api.md`, и координирует взаимодействие с внешними микросервисами:

- **auth-service** — аутентификация и авторизация
- **query-service** — обработка произвольного текста и чаты
- **rag-service** — векторный поиск
- **ocr-service** — OCR распознавание
- **validation-service** — валидация и сопоставление
- **integration-service** — интеграция с внешними системами

## Режимы работы с внешними сервисами

Для каждого внешнего сервиса поддерживаются 2 режима:

### 1. Mock/Stub режим (по умолчанию)
- Сервис возвращает сгенерированные тестовые данные
- Не требует подключения к реальным сервисам
- Используется для разработки и тестирования

### 2. Режим реальных API вызовов
- Сервис выполняет HTTP-запросы к внешним сервисам
- Требует указания URL сервиса в конфигурации
- Активируется при установке `*_MOCK=false` и указании `*_SERVICE_URL`

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

Пример конфигурации для работы с реальными сервисами:

```env
AUTH_SERVICE_URL=http://auth-service:8080
AUTH_SERVICE_MOCK=false

RAG_SERVICE_URL=http://rag-service:8081
RAG_SERVICE_MOCK=false
```

Для работы в mock-режиме:

```env
AUTH_SERVICE_MOCK=true
RAG_SERVICE_MOCK=true
```

## Запуск

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or using the main script
python -m app.main
```

## API Endpoints

### Документы
- `POST /api/v1/documents` — загрузка документа
- `GET /api/v1/documents` — список документов
- `GET /api/v1/documents/{doc_id}` — информация о документе
- `GET /api/v1/documents/{doc_id}/status` — статус обработки
- `DELETE /api/v1/documents/{doc_id}` — удаление документа
- `POST /api/v1/documents/{doc_id}/reprocess` — повторная обработка
- `GET /api/v1/documents/{doc_id}/errors` — журнал ошибок
- `GET /api/v1/documents/{doc_id}/pages/{page_num}` — просмотр страницы
- `GET /api/v1/documents/{doc_id}/pages/{page_num}/text` — текст страницы
- `GET /api/v1/documents/{doc_id}/parameters` — извлечённые параметры

### Поиск и RAG
- `POST /api/v1/search` — семантический поиск
- `GET /api/v1/search?q=...` — быстрый поиск
- `POST /api/v1/ask` — генерация ответа с источниками

### Валидация
- `POST /api/v1/validate/compare` — запуск сопоставления
- `GET /api/v1/validate/compare/{comparison_id}` — результат сопоставления
- `POST /api/v1/validate/compare/batch` — массовое сопоставление

### Служебные
- `GET /api/v1/health` — проверка состояния системы

## Структура проекта

```
orchestrator_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API endpoints
│   │       │   ├── documents.py
│   │       │   ├── search.py
│   │       │   ├── validate.py
│   │       │   └── health.py
│   │       └── api.py          # Router configuration
│   ├── core/
│   │   └── config.py           # Configuration settings
│   ├── schemas/               # Pydantic models
│   │   ├── documents.py
│   │   ├── search.py
│   │   ├── validation.py
│   │   └── common.py
│   ├── services/              # External service clients
│   │   ├── base_client.py     # Base client with dual mode
│   │   ├── auth_client.py
│   │   ├── rag_client.py
│   │   ├── ocr_client.py
│   │   ├── query_client.py
│   │   ├── validate_client.py
│   │   └── integration_client.py
│   └── main.py                # FastAPI application
├── requirements.txt
├── .env.example
└── README.md
```

## Добавление нового сервиса

1. Создайте клиент в `app/services/{service}_client.py`, наследуясь от `ServiceClient`
2. Реализуйте метод `_generate_mock` для mock-ответов
3. Добавьте настройки в `app/core/config.py`
4. Используйте клиент в endpoint'ах

Пример клиента:

```python
from app.services.base_client import ServiceClient
from app.core.config import settings

class MyServiceClient(ServiceClient):
    def __init__(self):
        super().__init__(
            service_name="my_service",
            service_url=settings.services.MY_SERVICE_URL,
            mock_mode=settings.services.MY_SERVICE_MOCK
        )
    
    async def _generate_mock(self, method, endpoint, default_mock, **kwargs):
        if endpoint == "/api/endpoint":
            return {"mock": "data"}
        return default_mock
```
