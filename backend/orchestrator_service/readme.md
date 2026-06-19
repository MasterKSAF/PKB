# Orchestrator Service

Единая точка входа для публичного API Нейроассистента ПКБ. Сервис координирует обработку черновиков (drafts) через двухфазный pipeline (preview → decision → full), взаимодействие между микросервисами и предоставляет унифицированный REST API для клиентских приложений.

## Описание

Orchestrator Service реализует API, описанный в `docs/api/orchestrator_service_api.md`, и выступает в роли шлюза, маршрутизируя запросы к внутренним микросервисам:

| Сервис | Назначение | Порт |
|--------|-----------|------|
| **auth-service** | Аутентификация и авторизация пользователей | 8082 |
| **query-service** | Обработка произвольного текста, чаты и сессии | 8083 |
| **registry-service** | Классификаторы, терминология, реестр документов и черновиков | 8084 |
| **integration-service** | Интеграция с внешними системами (Meridian), файловое хранилище | 8085 |
| **validation-service** | Валидация, сравнение и сопоставление проектных/нормативных данных | 8086 |
| **rag-service** | Векторный поиск (RAG) и генерация ответов LLM | 8087 |
| **ocr-service** | OCR распознавание документов | 8088 |
| **parser-service** | Парсинг цифровых PDF (структура, текст без распознавания) | 8089 |
| **converter-validator** | Конвертация и валидация результатов OCR/Parser | 8090 |

## Архитектура

**Ключевое архитектурное решение:** Оркестратор больше не хранит документы.
- Черновики → `registry.drafts` (Registry)
- Документы → `registry.documents` (Registry)
- Оркестратор хранит только `pipeline.tasks` и `pipeline.task_steps` — задачи пайплайна и их шаги

### Двухфазный pipeline

1. **Preview-фаза** (сразу после загрузки):
   - Upload → OCR/Parser (3 страницы) → Converter-validator
   - Результат: метаданные документа, определение полноты preview
2. **Decision** (ожидание решения пользователя или auto-approve):
   - Если preview полный (preview_not_supported=true) — auto-approve при валидных метаданных
   - Если preview частичный — пользователь подтверждает или отклоняет
3. **Full-фаза** (после approve):
   - OCR/Parser (весь документ) → Converter-validator → Registry

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
- **SQLAlchemy (asyncio)** — ORM (SQLite / PostgreSQL)
- **Celery + Redis** — асинхронная очередь задач
- **Pydantic v2** — валидация схем и настроек
- **httpx** — HTTP-клиент для внешних сервисов
- **Uvicorn** — ASGI-сервер
- **Pytest** — тестирование
- **python-jose** — JWT-токены

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
REGISTRY_SERVICE_URL=http://registry-service:8084
REGISTRY_SERVICE_MOCK=false
# ... остальные сервисы
```

### Для работы в mock-режиме (по умолчанию):

```env
AUTH_SERVICE_MOCK=true
REGISTRY_SERVICE_MOCK=true
OCR_SERVICE_MOCK=true
PARSER_SERVICE_MOCK=true
CONVERTER_SERVICE_MOCK=true
INTEGRATION_SERVICE_MOCK=true
VALIDATE_SERVICE_MOCK=true
QUERY_SERVICE_MOCK=true
RAG_SERVICE_MOCK=true
```

Основные параметры:
- `APP_VERSION` — версия приложения (по умолчанию `1.0.0`)
- `DEBUG` — режим отладки
- `HOST` — хост (по умолчанию `0.0.0.0`)
- `PORT` — порт (по умолчанию `8081`)
- `DATABASE_URL` — URL БД (по умолчанию `sqlite+aiosqlite:///./orchestrator.db`)
- `CELERY_BROKER_URL` — Redis для Celery (по умолчанию `redis://localhost:6379/1`)
- `JWT_SECRET_KEY` — секретный ключ для JWT

## Запуск

```bash
# Development mode с hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8081

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8081

# Через entry point (также с reload)
python main.py
```

Swagger UI: `http://localhost:8081/docs`
ReDoc: `http://localhost:8081/redoc`

## API Endpoints

### Черновики (`/api/v1/drafts`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/drafts` | Загрузка файла и создание черновика (multipart/form-data) |
| GET | `/drafts` | Список черновиков с пагинацией |
| GET | `/drafts/{draft_id}` | Информация о черновике |
| GET | `/drafts/{draft_id}/preview` | Метаданные preview |
| POST | `/drafts/{draft_id}/preview` | Запуск preview-фазы |
| GET | `/drafts/{draft_id}/preview/status` | Статус preview (с longpoll) |
| PATCH | `/drafts/{draft_id}/decide` | Решение: approve / reject |
| DELETE | `/drafts/{draft_id}` | Удаление черновика |

### Задачи (`/api/v1/tasks`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/tasks/{task_id}/status` | Статус задачи с детализацией шагов |

### Документы (`/api/v1/documents`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/documents` | Загрузка версии документа |
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
│   ├── celery_app.py                  # Celery instance
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps/
│   │   │   └── __init__.py            # Auth dependencies (Bearer token)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                 # Конфигурация роутеров
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── documents.py       # CRUD документов, страницы, параметры, очередь
	│   │           ├── drafts.py          # Черновики: upload, preview, decide
	│   │           ├── tasks.py           # Статус задач пайплайна
	│   │           ├── search.py          # Поиск
	│   │           ├── health.py          # Health check
	│   │           └── monitor.py         # Метрики и мониторинг
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                  # Настройки (Pydantic Settings)
│   │   ├── fsm.py                     # DraftState/DraftFSM, TaskStatus/TaskStage
│   │   └── pipeline/
│   │       ├── __init__.py
│   │       ├── orchestrator.py        # PipelineOrchestrator — двухфазный pipeline
│   │       └── saga.py                # SagaCoordinator — компенсации
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                    # Engine, Session, Base, get_db()
│   │   └── session.py                 # get_db_context() для Celery
│   ├── models/
│   │   └── pipeline.py                # Task + TaskStep ORM модели
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py                  # Общие схемы (Error, Pagination)
	│   │   ├── documents.py               # Схемы документов
	│   │   ├── drafts.py                  # Схемы черновиков
	│   │   ├── tasks.py                   # Схемы задач пайплайна
	│   │   ├── search.py                  # Схемы поиска
	│   │   └── validation.py              # Схемы валидации
	│   ├── services/
	│   │   ├── __init__.py
	│   │   ├── base_client.py             # Базовый клиент с dual-mode (mock/real)
	│   │   ├── rag_client.py              # RAG Service (векторный поиск, генерация)
	│   │   ├── ocr_client.py              # OCR Service
	│   │   ├── parser_client.py           # Parser Service (цифровые PDF)
	│   │   ├── converter_client.py        # Converter-Validator Service
	│   │   └── registry_client.py         # Registry Service (drafts, документы)
	│   └── tasks/
│       ├── __init__.py
│       ├── pipeline_formation.py      # Celery задачи: preview + full фазы
│       ├── pipeline_indexation.py     # Celery задачи: RAG indexation
│       ├── compensation.py            # Saga компенсации
│       └── scheduler.py               # Планировщик задач
├── services/
│   ├── __init__.py
│   └── response.py                    # Формирование единых API-ответов
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Фикстуры (TestClient, mock-режим)
│   ├── test_drafts.py                 # Тесты черновиков
	│   ├── test_tasks.py                  # Тесты задач
	│   ├── test_health.py                 # Тесты health endpoint'ов
	│   ├── test_monitor.py                # Тесты метрик
	│   ├── test_search.py                 # Тесты поиска
	│   ├── test_service_clients_*.py      # Тесты сервис-клиентов
│   ├── unit/
│   └── integration/
│       ├── test_celery_tasks.py       # Интеграционные тесты Celery
│       └── test_pipeline_formation.py # Интеграционные тесты pipeline
├── main.py                            # Entry point
├── requirements.txt
├── .env.example
├── pytest.ini
├── todo.md
└── readme.md
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
pytest tests/test_drafts.py

# Запуск конкретного теста
pytest tests/test_drafts.py::TestCreateDraft::test_create_draft_success -v
```

- Все тесты запускаются в mock-режиме (устанавливается в `conftest.py`)
- Тесты используют `TestClient` из FastAPI
- Для аутентифицированных запросов используется фикстура `auth_header`
- **345 тестов** проходят (актуально на 19.06.2026)
- Основные группы: `test_drafts.py` (26), `test_tasks.py` (10), `test_search.py` (25), `test_health.py` (12), `tests/integration/` (27), `tests/unit/` (18)


---

## Архитектура клиентов сервисов

Базовый класс `ServiceClient` предоставляет:

- **Dual-mode**: автоматический выбор между mock и реальным HTTP-вызовом
- **Единая обработка ошибок**: `ServiceError` с кодом и деталями
- **Управление HTTP-клиентом**: пул соединений через `httpx.AsyncClient`
- **Retry + Circuit Breaker**: exponential backoff через tenacity, защита от каскадных сбоев

Каждый клиент наследуется от `ServiceClient` и реализует:
- `_generate_mock()` — генерация тестовых данных для конкретного сервиса
- Публичные методы-обёртки (`async def search(...)`, `async def upload(...)` и т.д.)

## Формат ошибок API

Все ошибки возвращаются в едином формате:

```json
{
  "error": {
    "code": "DRAFT_NOT_FOUND",
    "message": "Черновик не найден",
    "details": {
      "draft_id": 123
    }
  }
}
```

Коды ошибок: `BAD_REQUEST`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `VALIDATION_FAILED`, `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`.
