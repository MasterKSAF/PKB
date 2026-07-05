# PKB NeuroAssistant — Backend

## Архитектура

Сервисы развёрнуты в Docker Compose, взаимодействуют через HTTP. Каждый сервис — отдельное FastAPI-приложение.

```
Gateway (прокси + мок) → Orchestrator (бизнес-логика) → Registry (CRUD)
                                                     → Parser
                                                     → Converter/Validator
                                                     → RAG Builder
```

## Основные сервисы

| Сервис | Папка | Порт | Назначение |
|--------|-------|------|------------|
| Gateway | `gateway_service/` | 18080 | Входная точка, прокси, моки для тестов |
| Orchestrator | `orchestrator_service/` | 18081 | Бизнес-логика: создание/превью/решение черновиков |
| Registry | `registry_service/` | 18082 | CRUD для документов, черновиков, классификаторов, терминологии |
| Auth | `auth_service/` | 18085 | Аутентификация, управление пользователями/ролями |
| Parser | `parser_service/` | — | Парсинг документов |
| Converter/Validator | `converter_validator_service/` | — | Конвертация, валидация |
| RAG Builder | `rag_builder_service/` | — | Построение RAG-индекса |

## Черновики (Drafts)

Жизненный цикл: `upload` → `previewing` → `ready_for_approve` → `approved` / `discarded`

### API endpoints (через Gateway)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/drafts` | Создать черновик (загрузить файл) |
| GET | `/api/v1/drafts/{id}` | Получить информацию о черновике |
| GET | `/api/v1/drafts/{id}/preview` | Получить preview-метаданные |
| POST | `/api/v1/drafts/{id}/preview` | Запустить preview |
| GET | `/api/v1/drafts/{id}/preview/status` | Статус preview |
| PATCH | `/api/v1/drafts/{id}/decide` | Принять решение (approve/reject) |
| PATCH | `/api/v1/drafts/{id}/metadata` | Обновить метаданные |
| DELETE | `/api/v1/drafts/{id}` | Удалить черновик |
| GET | `/api/v1/drafts/{id}/tasks` | Список задач черновика |
| **GET** | **`/api/v1/drafts/{id}/pages`** | **Список страниц из raw_data** |
| **GET** | **`/api/v1/drafts/{id}/pages/{n}`** | **Блоки страницы из raw_data** |

> Endpoints **`/pages`** были добавлены в рамках задачи "Drafts Pages Preview". Данные берутся из `raw_data` (JSONB) черновика. Фронтенд получает `image_key`, собирает полный URL: `${BASE_URL}/files/${image_key}`.

### Схема данных (raw_data)

```json
{
  "document": {
    "source": { "file_name": "...", "page_count": 3 },
    "pages": [{ "page": 1, "width": 595, "height": 842 }],
    "block": [
      { "number": 1, "type": "heading", "page": 1, "content": "...", "heading_level": 1 },
      { "number": 2, "type": "paragraph", "page": 1, "content": "..." },
      { "number": 3, "type": "image", "page": 2, "image_key": "<hash>.png" },
      { "number": 4, "type": "table", "page": 2, "rows": [...] },
      { "number": 5, "type": "list", "page": 2, "block": [...] }
    ]
  }
}
```

### Цепочка вызова pages

```
Frontend → Gateway /api/v1/drafts/{id}/pages
  → Orchestrator /drafts/{id}/pages (proxy)
    → Registry /registry/drafts/{id}/pages (достаёт из raw_data)
```

## Как запустить

```bash
# Полный стек
cd backend
docker compose up -d

# Только gateway в mock-режиме
docker compose up -d gateway
```

## Тестирование

```bash
# Gateway mocks
cd backend/gateway_service/mocks
pip install -r requirements.txt
pytest tests/
```
