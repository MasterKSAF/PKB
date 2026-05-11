orchestrator_service/PROJECT_DETAILS.md
# Orchestrator Service — Детальное описание проекта

## 1. Назначение

**Orchestrator Service** — это единая точка входа (API Gateway) для публичного API Нейроассистента ПКБ. Сервис принимает запросы от клиентских приложений, маршрутизирует их к соответствующим внутренним микросервисам и возвращает унифицированный ответ. Он также отвечает за аутентификацию и авторизацию запросов.

---

## 2. Ключевая архитектурная концепция: Dual-mode клиенты

Все внешние сервисы поддерживают два режима работы через базовый класс `ServiceClient`:

| Режим | Условие | Поведение |
|-------|---------|-----------|
| **Mock/Stub** | `*_MOCK=true` (по умолчанию) | Возвращает сгенерированные тестовые данные, не требует реальных сервисов |
| **Real API** | `*_MOCK=false` + `*_SERVICE_URL` указан | Выполняет HTTP-запросы к реальному микросервису |

Это позволяет разрабатывать и тестировать фронтенд без необходимости разворачивать всю инфраструктуру микросервисов.

---

## 3. Взаимодействие с микросервисами

### 3.1 Auth Service — порт 8082
- **Клиент**: `app/services/auth_client.py` → `AuthServiceClient`
- **Назначение**: Аутентификация и авторизация пользователей
- **Основные методы клиента**:
  - `validate_token(token)` — валидация Bearer JWT-токена
  - `get_me()` — профиль текущего пользователя
  - `list_users()`, `create_user()`, `get_user()`, `update_user()`, `patch_user()`, `deactivate_user()` — CRUD пользователей (админка)
  - `list_roles()`, `create_role()` — управление ролями
  - `get_audit_log()` — аудит действий
- **Mock-данные**:
  - Пользователь с полными правами: `u-mock-001`, инженер, доступны все вкладки
  - Токены: `mock_access_token_12345`, `mock_refresh_token_67890`

### 3.2 Query Service — порт 8083
- **Клиент**: `app/services/query_client.py` → `QueryServiceClient`
- **Назначение**: Обработка произвольного текста, управление чат-сессиями
- **Основные методы клиента**:
  - `text_search(text, ...)` — полнотекстовый поиск
  - `text_ask(text, ...)` — генерация ответа на вопрос
  - `create_session()`, `list_sessions()`, `get_session()`, `update_session()`, `delete_session()` — управление чат-сессиями
  - `send_message()` — отправка сообщения в сессию
  - `update_context()` — обновление контекста сессии
  - `submit_feedback()` — оценка ответа
  - `get_history()`, `export_history()` — история запросов
  - `quick_chat()` — быстрый чат без сессии

### 3.3 Registry Service — порт 8084
- **Клиент**: `app/services/registry_client.py` → `RegistryServiceClient`
- **Назначение**: Классификаторы, терминология, реестр документов
- **Основные методы клиента**:
  - **Классификаторы**: `list_classifiers()`, `get_classifier_tree()`, `get_classifier()`, `create/update/patch/delete_classifier()`, `import_classifiers()`
  - **Терминология**: `list_terminology()`, `get_term()`, `create/update/delete_term()`, `normalize_term()`, `import_terms()`
  - **Реестр документов**: `list_registry_documents()`, `get_registry_document()`, `create/update/update_status/delete_registry_document()`, `export/import_registry_documents()`
  - **Статистика**: `get_statistics()`
  - **Справочники**: `get_enums()`

### 3.4 Integration Service — порт 8085
- **Клиент**: `app/services/integration_client.py` → `IntegrationServiceClient`
- **Назначение**: Файловое хранилище и интеграция с внешними системами (Meridian)
- **Основные методы клиента**:
  - `upload_file()`, `get_file()`, `get_file_info()`, `delete_file()` — управление файлами
  - `export_to_meridian()` — экспорт в систему Meridian
  - `get_external_systems_status()` — статус внешних систем

### 3.5 Validation Service — порт 8086
- **Клиент**: `app/services/validate_client.py` → `ValidationServiceClient`
- **Назначение**: Валидация проектных параметров, сравнение с нормативными требованиями
- **Основные методы клиента**:
  - `extract_parameters()` — извлечение структурированных параметров из документа
  - `compare()` — сравнение нормативного и проектного текста
  - `get_comparison()` — получение результата сравнения
  - `compare_batch()` — массовое сравнение пар
  - `check()` — запуск проверки документа
  - `calculate()` — вычисление значения по выражению
  - `recommend()` — рекомендации по устранению несоответствий

### 3.6 RAG Service — порт 8087
- **Клиент**: `app/services/rag_client.py` → `RAGServiceClient`
- **Назначение**: Векторный поиск (RAG), индексация документов, генерация ответов LLM
- **Основные методы клиента**:
  - `index_document()` — индексация чанков документа
  - `delete_index()` — удаление документа из индекса
  - `search()` — поиск по векторному индексу (гибридный поиск)
  - `generate()` — генерация ответа с использованием LLM

### 3.7 OCR Service — порт 8088
- **Клиент**: `app/services/ocr_client.py` → `OCRServiceClient`
- **Назначение**: OCR-распознавание документов
- **Основные методы клиента**:
  - `process_document()` — запуск OCR-обработки документа
  - `get_engines()` — получение списка доступных OCR-движков

---

## 4. API Endpoints — полный перечень

Префикс всех endpoint'ов: `/api/v1`

### 4.1 Служебные

| Метод | Path | Auth | Описание |
|-------|------|------|----------|
| GET | `/` | Нет | Информация о сервисе (название, версия) |
| GET | `/system/health` | Нет | Проверка состояния системы |

### 4.2 Документы (`/documents`)

| Метод | Path | Описание |
|-------|------|----------|
| POST | `/documents` | Загрузка документа (multipart/form-data) |
| GET | `/documents` | Список документов (пагинация, статусы) |
| GET | `/documents/queue` | Очередь обработки документов |
| GET | `/documents/{doc_id}` | Детальная информация о документе |
| GET | `/documents/{doc_id}/file` | Скачивание файла документа |
| GET | `/documents/{doc_id}/status` | Статус обработки (processing/completed/failed) |
| GET | `/documents/{doc_id}/pages` | Список страниц документа |
| GET | `/documents/{doc_id}/pages/{page_num}` | Просмотр страницы с блоками |
| GET | `/documents/{doc_id}/pages/{page_num}/text` | Текст страницы |
| GET | `/documents/{doc_id}/pages/{page_num}/preview` | Превью страницы |
| GET | `/documents/{doc_id}/parameters` | Извлечённые параметры |
| GET | `/documents/{doc_id}/errors` | Журнал ошибок обработки |
| DELETE | `/documents/{doc_id}` | Удаление документа |
| POST | `/documents/{doc_id}/reprocess` | Повторная обработка |

### 4.3 Поиск и RAG

| Метод | Path | Описание |
|-------|------|----------|
| POST | `/documents/search` | Семантический поиск по фрагментам |
| GET | `/documents/search?q=...` | Быстрый поиск (GET-вариант) |
| POST | `/ask` | Генерация ответа с источниками (RAG) |

### 4.4 Валидация (`/validate`)

| Метод | Path | Описание |
|-------|------|----------|
| POST | `/validate/compare` | Запуск сопоставления (202 Accepted) |
| GET | `/validate/compare/{comparison_id}` | Результат сопоставления |
| POST | `/validate/compare/batch` | Массовое сопоставление пар |
| POST | `/validate/checks` | Запуск проверки проектных параметров |
| GET | `/validate/checks/{check_run_id}` | Статус проверки |
| GET | `/validate/checks/{check_run_id}/export` | Экспорт результатов |

### 4.5 Мониторинг (`/monitor`)

| Метод | Path | Auth | Описание |
|-------|------|------|----------|
| GET | `/monitor/metrics` | Да (admin) | Метрики качества системы |

---

## 5. Структура проекта — полное описание модулей

```
orchestrator_service/
│
├── main.py                           # Точка входа (uvicorn.run)
│
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI-приложение: create_application()
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps/
│   │   │   └── __init__.py           # Auth dependencies:
│   │   │       - get_current_user()  #   Извлекает и валидирует Bearer-токен
│   │   │       - CurrentUser         #   Модель аутентифицированного пользователя
│   │   │       - MOCK_USER           #   Тестовый пользователь для mock-режима
│   │   │       - PUBLIC_PATH_PREFIXES #   Пути без аутентификации
│   │   │
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                # Сборка роутера: объединяет все endpoint'ы
│   │       │                         # с Depends(get_current_user) по умолчанию
│   │       │
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── documents.py      # ~700 строк: все CRUD для документов
│   │           │                     # upload, list, get, status, pages, parameters
│   │           │                     # delete, reprocess, errors, queue, file
│   │           │
│   │           ├── search.py         # ~200 строк: POST/GET search, POST ask
│   │           │                     # Использует RAGServiceClient и QueryServiceClient
│   │           │
│   │           ├── validate.py       # ~200 строк: compare, batch, checks, export
│   │           │                     # Использует ValidationServiceClient
│   │           │
│   │           ├── health.py         # ~50 строк: /system/health
│   │           │                     # Считает uptime, проверяет статус сервисов
│   │           │
│   │           └── monitor.py        # ~120 строк: /monitor/metrics
│   │                                 # Возвращает метрики качества (mock)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                 # Pydantic Settings:
│   │       - Settings                #   APP_NAME, APP_VERSION, DEBUG, HOST, PORT
│   │       - ServiceConfig           #   URL и флаги MOCK для 7 внешних сервисов
│   │       - JWT_SECRET_KEY, JWT_ALGORITHM
│   │       - read .env файл
│   │
│   ├── models/
│   │   └── __init__.py               # Заготовка для моделей БД (не используются)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py                 # ErrorDetail, ErrorResponse, PaginationMeta,
│   │   │                             # ListResponse[T] (generic)
│   │   │
│   │   ├── documents.py              # ~500 строк: 20+ Pydantic-моделей
│   │   │     DocumentType, DocumentStatus, ReprocessMode, StepStatus (enum)
│   │   │     DocumentCreateResponse, DocumentSummary, DocumentListItem
│   │   │     DocumentListResponse, DocumentDetailResponse
│   │   │     DocumentStatusProcessing, DocumentStatusCompleted, DocumentStatusFailed
│   │   │     DocumentFileResponse, PagePreviewResponse
│   │   │     DocumentDeleteResponse, ReprocessRequest, ReprocessResponse
│   │   │     ProcessingError, DocumentErrorsResponse
│   │   │     QueueItem, QueueMeta, DocumentQueueResponse
│   │   │     PageInfo, DocumentPagesResponse
│   │   │     BlockCoordinates, PageBlock, PageViewResponse
│   │   │     PageBlockDetail, PageTextResponse
│   │   │     SpecificationItem, DocumentParameters, DocumentParametersResponse
│   │   │
│   │   ├── search.py                 # ~100 строк:
│   │   │     SearchRequest, SearchFilters, SearchResultFragment, SearchResponse
│   │   │     AskRequest, AskOptions, AskSource, AskResponse
│   │   │     SearchQueryParams
│   │   │
│   │   └── validation.py             # ~200 строк:
│   │         MatchStatus (enum)
│   │         CompareRequest, CompareInitResponse
│   │         NormativeBlock, ProjectBlock, SourceReference
│   │         CompareResultResponse, CompareBatchItem, CompareBatchResponse
│   │         CheckSource, CheckItem, CheckSummary
│   │         CheckRunResponse, CheckRunStatusResponse, CheckExportResponse
│   │         HealthStatus
│   │
│   └── services/
│       ├── __init__.py
│       ├── base_client.py            # ~140 строк:
│       │   - ServiceClient (ABC)     #   Базовый класс с dual-mode
│       │   - ServiceError            #   Кастомное исключение
│       │   Методы:
│       │     call(method, endpoint, mock_response, **kwargs)
│       │     _get_mock_response()
│       │     _generate_mock() (abstract)
│       │     _make_request()         #   реальный HTTP-вызов через httpx
│       │     _get_client()           #   ленивое создание httpx.AsyncClient
│       │     close()
│       │
│       ├── auth_client.py            # Auth Service
│       ├── query_client.py           # Query Service (~500 строк, 17 методов)
│       ├── registry_client.py        # Registry Service (~550 строк, 28 методов)
│       ├── integration_client.py     # Integration Service
│       ├── validate_client.py        # Validation Service
│       ├── rag_client.py             # RAG Service
│       └── ocr_client.py             # OCR Service
│
├── services/
│   ├── __init__.py
│   └── response.py                   # ~100 строк:
│       - get_status(code)            #   Маппинг HTTP-кодов в code_name и message
│       - APIException                #   HTTPException с единым форматом ошибки
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Фикстуры: app, client, auth_header
│   │                                 # Принудительно включает mock-режим для всех
│   │                                 # сервисов через os.environ
│   │
│   ├── test_documents.py             # ~700 строк: 55 тестов
│   │   TestUploadDocument            #   5 тестов
│   │   TestListDocuments             #   5 тестов
│   │   TestGetDocument               #   4 теста
│   │   TestDocumentStatus            #   3 теста
│   │   TestDeleteDocument            #   3 теста
│   │   TestReprocessDocument         #   4 теста
│   │   TestDocumentErrors            #   4 теста
│   │   TestDocumentPages             #   6 тестов
│   │   TestDocumentParameters        #   5 тестов
│   │   TestDocumentQueue             #   3 теста
│   │   TestDocumentFile              #   2 теста
│   │
│   ├── test_health.py                # ~200 строк: 13 тестов
│   │   TestRootEndpoint              #   2 теста
│   │   TestHealthEndpoint            #   7 тестов
│   │   TestOpenAPIEndpoints          #   4 теста
│   │
│   ├── test_monitor.py               # тесты метрик мониторинга
│   │
│   ├── test_search.py                # ~450 строк: 28 тестов
│   │   TestSearchPost                #   11 тестов
│   │   TestSearchGet                 #   9 тестов
│   │   TestAsk                       #   8 тестов
│   │
│   └── test_validate.py              # ~550 строк: 44 теста
│       TestStartComparison           #   6 тестов
│       TestGetComparisonResult       #   10 тестов
│       TestBatchCompare              #   7 тестов
│       TestCheckRun                  #   7 тестов
│       TestCheckRunStatus            #   5 тестов
│       TestCheckRunExport            #   3 теста
│
├── requirements.txt                  # fastapi, uvicorn, pydantic, httpx, pytest и др.
├── .env.example
├── README.md                         # Актуальная документация
└── PROJECT_DETAILS.md                # Данный файл
```

---

## 6. Аутентификация и авторизация

### 6.1 Публичные пути (без аутентификации)
- `GET /` — информация о сервисе
- `GET /system/health` — health check
- `GET /docs`, `/redoc`, `/openapi.json` — документация

### 6.2 Аутентифицированные пути
Все остальные endpoint'ы требуют Bearer JWT-токена. Механизм реализован в `app/api/deps/__init__.py`:

1. FastAPI `HTTPBearer` (auto_error=False) извлекает токен из заголовка `Authorization`
2. `get_current_user()`:
   - Если путь публичный → возвращает None
   - Если `AUTH_SERVICE_MOCK=true` → возвращает `MOCK_USER`
   - Иначе → вызывает `AuthServiceClient.validate_token(token)`
3. Если токен недействителен → 401 UNAUTHORIZED
4. Если сервис аутентификации недоступен → 503 SERVICE_UNAVAILABLE

### 6.3 Модель пользователя
```python
CurrentUser:
  user_id: str       # "u-mock-001"
  email: str         # "user@example.com"
  full_name: str     # "Иванов И.И."
  roles: list[str]   # ["engineer"]
  permissions: list[str]  # ["documents:read", "documents:write", "search", ...]
```

---

## 7. Централизованная обработка ошибок

### 7.1 ServiceError
- Возникает в клиентах сервисов при ошибках HTTP или сетевых проблемах
- Содержит: `message`, `status_code`, `details`
- Преобразуется в единый формат через метод `to_dict()`

### 7.2 APIException (`services/response.py`)
- HTTPException с форматированным `detail`
- Использует маппинг HTTP-кодов в коды ошибок:
  `200→OK`, `400→BAD_REQUEST`, `401→UNAUTHORIZED`, `403→FORBIDDEN`,
  `404→NOT_FOUND`, `409→CONFLICT`, `422→VALIDATION_FAILED`,
  `500→INTERNAL_ERROR`, `503→SERVICE_UNAVAILABLE`, `504→GATEWAY_TIMEOUT`

### 7.3 Единый формат ответа с ошибкой
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

---

## 8. Pydantic-схемы (ключевые типы)

### 8.1 Common
- `ErrorDetail`, `ErrorResponse` — формат ошибок
- `PaginationMeta` — `{total, page, page_size}`
- `ListResponse[T]` — generic: `{items: T[], meta: PaginationMeta}`

### 8.2 Documents
- `DocumentType` enum: `normative | archival_scan | drawing | specification`
- `DocumentStatus` enum: `queued | processing | processed | completed | failed | error`
- `ReprocessMode` enum: `standard | enhanced_preprocess | fallback_ocr`
- `StepStatus` enum: `pending | in_progress | completed | error`
- Union-тип `DocumentStatusResponse`: `DocumentStatusProcessing | DocumentStatusCompleted | DocumentStatusFailed`

### 8.3 Search
- `SearchRequest` с полями: `query`, `document_ids`, `top_k`, `filters`
- `SearchResponse` с `items: SearchResultFragment[]`, `total_found`, `processing_time_ms`
- `AskRequest` с `question`, `document_ids`, `options`
- `AskResponse` с `answer`, `sources: AskSource[]`, `model_used`

### 8.4 Validation
- `MatchStatus` enum: `match | possible_discrepancy | not_found_in_project | not_found_in_norm | insufficient_data`
- `CompareResultResponse`: полноценный результат сравнения с блоками, источниками, дисклеймером
- `CheckRunResponse`: результат проверки с items и summary

---

## 9. Конфигурация (.env)

### Основные параметры

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| `APP_VERSION` | `1.0.0` | Версия сервиса |
| `DEBUG` | `false` | Режим отладки |
| `HOST` | `0.0.0.0` | Хост |
| `PORT` | `8000` | Порт |
| `API_V1_PREFIX` | `/api/v1` | Префикс API |
| `JWT_SECRET_KEY` | \* | Секретный ключ JWT |
| `JWT_ALGORITHM` | `HS256` | Алгоритм JWT |

### Параметры внешних сервисов

Для каждого сервиса `{NAME}`:
- `{NAME}_SERVICE_URL` — URL (опционально, по умолчанию None)
- `{NAME}_SERVICE_MOCK` — boolean (по умолчанию true)

Поддерживаемые сервисы: `AUTH`, `QUERY`, `REGISTRY`, `INTEGRATION`, `VALIDATE`, `RAG`, `OCR`.

---

## 10. Тестирование

### 10.1 Конфигурация
- `conftest.py` принудительно устанавливает `*_MOCK=true` для всех сервисов через `os.environ` до импорта приложения
- Используется `TestClient` из FastAPI
- Фикстура `auth_header` предоставляет `Authorization: Bearer mock_access_token_12345`

### 10.2 Покрытие тестами
- **test_documents.py** — 55 тестов: все CRUD-операции, статусы, страницы, параметры, очередь
- **test_health.py** — 13 тестов: корневой endpoint, health check, OpenAPI-документация, CORS
- **test_search.py** — 28 тестов: POST/GET search, Ask (структура ответа, скоринг, пустые запросы)
- **test_validate.py** — 44 теста: сравнение, batch, проверки, экспорт
- Всего: ~140 тестов

### 10.3 Запуск
```bash
pytest                                     # все тесты
pytest --cov=app --cov-report=term-missing  # с coverage
pytest tests/test_search.py -v             # конкретный файл verbose
pytest tests/test_search.py::TestSearchPost::test_search_basic -v  # конкретный тест
```

---

## 11. Добавление нового микросервиса

Пошаговая инструкция:

1. **Добавить конфигурацию** в `app/core/config.py`:
   - Добавить поля в `ServiceConfig`: `NEW_SERVICE_URL: Optional[str]` и `NEW_SERVICE_MOCK: bool = True`

2. **Создать клиент** в `app/services/{service}_client.py`:
   - Унаследоваться от `ServiceClient`
   - Вызвать `super().__init__(service_name, service_url, mock_mode)`
   - Реализовать `async def _generate_mock(method, endpoint, default_mock, **kwargs)`

3. **Добавить endpoint'ы** в `app/api/v1/endpoints/`:
   - Создать или дополнить файл endpoint'ов
   - Использовать клиент для вызовов с mock-ответами

4. **Добавить схемы** в `app/schemas/` при необходимости

5. **Зарегистрировать роутер** в `app/api/v1/api.py`

6. **Написать тесты** в `tests/`

---

## 12. Ключевые шаблоны проектирования

### 12.1 Стратегия (Strategy) для dual-mode
Базовый класс `ServiceClient` определяет интерфейс, а подклассы реализуют `_generate_mock()`. Метод `call()` автоматически выбирает между mock и реальным вызовом.

### 12.2 Адаптер (Adapter)
Каждый `*ServiceClient` адаптирует API внешнего микросервиса к единому интерфейсу `ServiceClient`.

### 12.3 Фабричный метод (Factory Method)
`create_application()` в `app/main.py` создаёт настроенный экземпляр FastAPI.

### 12.4 Внедрение зависимостей (DI) через FastAPI Depends
Аутентификация: `get_current_user` как `Depends`. Роутер API создаётся с `dependencies=[Depends(get_current_user)]`.

---

## 13. Зависимости (requirements.txt)

| Пакет | Версия | Назначение |
|-------|--------|------------|
| fastapi | 0.109.0 | Веб-фреймворк |
| uvicorn | 0.27.0 | ASGI-сервер |
| pydantic | 2.5.3 | Валидация данных |
| pydantic-settings | 2.1.0 | Настройки из .env |
| httpx | 0.26.0 | HTTP-клиент |
| python-multipart | 0.0.6 | Обработка multipart/form-data |
| python-jose | 3.3.0 | JWT-токены |
| passlib | 1.7.4 | Хэширование паролей |
| pytest | 8.0.0 | Тестирование |
| pytest-asyncio | 0.23.3 | Async-тесты |

---

## 14. Особенности реализации

### 14.1 Загрузка документов
- Endpoint `POST /documents` принимает multipart/form-data
- Использует `IntegrationServiceClient.upload_file()` для сохранения файла
- Возвращает `202 Accepted` с `document_id` и `task_id`

### 14.2 Поиск (POST /documents/search)
- Использует `RAGServiceClient.search()` для векторного поиска
- Конвертирует результат RAG-сервиса в формат `SearchResultFragment[]`
- Поддерживает гибридный режим поиска (hybrid search_type)

### 14.3 Ask (POST /ask)
- Использует `QueryServiceClient.text_ask()` для генерации ответа
- Конвертирует источники в формат `AskSource[]`
- Возвращает `model_used` — название модели LLM

### 14.4 Сравнение (POST /validate/compare)
- Возвращает `202 Accepted` с `comparison_id`
- Реальный результат получается через `GET /validate/compare/{comparison_id}`
- Использует `ValidationServiceClient` для вызова

### 14.5 Проверки (POST /validate/checks)
- Синхронный endpoint (в mock-режиме)
- Возвращает `CheckRunResponse` с детальными результатами по каждому параметру
- Поддерживает экспорт в XLSX через `GET /validate/checks/{check_run_id}/export`

### 14.6 Health check
- Публичный endpoint (без аутентификации)
- Возвращает статус всех внешних сервисов
- Считает uptime сервиса с момента старта
- Определяет общий статус: `ok` (все сервисы доступны) или `degraded`

### 14.7 Мониторинг
- Endpoint `/monitor/metrics` защищён аутентификацией
- Возвращает метрики качества: OCR quality, retrieval quality, latency, ответы с источниками
- Возвращает статистику по оценкам ответов
- Возвращает последние записи лога

---

## 15. Инструменты и среда разработки

- **Язык**: Python 3.11+
- **Фреймворк**: FastAPI 0.109
- **Тестирование**: Pytest 8.0 + pytest-asyncio
- **HTTP-клиент**: httpx (AsyncClient)
- **Валидация**: Pydantic v2
- **Типизация**: mypy совместимые аннотации, Generic типы
- **Кодировка**: все строки в UTF-8, русский язык в коде и документации