# PKB Neuroassistant — Mock Services

Набор mock-сервисов для эмуляции бэкенда PKB Neuroassistant.  
Стек: **Python 3.12+**, **FastAPI**, **in-memory storage**.  
Все сервисы объединены в единый шлюз на порту **8081** (эмуляция nginx).

---

## 📦 Состав

| Сервис | Роль | Эндпоинты |
|--------|------|-----------|
| **Auth Service** | Аутентификация, пользователи, роли, аудит | `/api/v1/auth/*`, `/api/v1/admin/*` |
| **Orchestrator** | Документы, поиск, валидация, метрики | `/api/v1/documents/*`, `/api/v1/validate/*`, `/api/v1/monitor/*` |
| **Query Service** | Чат-сессии, Q&A, текстовый поиск | `/api/v1/chat/*`, `/api/v1/text/*` |
| **Registry** | Классификаторы, терминология, НСИ | `/api/v1/classifiers/*`, `/api/v1/terminology/*`, `/api/v1/common/*`, `/api/v1/registry/documents/*` |

---

## 🚀 Быстрый старт

```bash
# 1. Установить зависимости
pip install fastapi uvicorn pytest httpx python-multipart

# 2. Запустить единый шлюз (все сервисы на порту 8081)
python backend/gateway_service/mocks/gateway.py

# 3. Или запустить сервисы по отдельности
python backend/gateway_service/mocks/start_service.py all
python backend/gateway_service/mocks/start_service.py auth    # только Auth (порт 8082)
python backend/gateway_service/mocks/start_service.py orchestrator  # (порт 8081)
python backend/gateway_service/mocks/start_service.py query   # (порт 8083)
python backend/gateway_service/mocks/start_service.py registry  # (порт 8084)
```

---

## 🧪 Запуск тестов

```bash
# Все 173 теста
python -m pytest backend/gateway_service/mocks/tests/ -v

# Только базовые
python -m pytest backend/gateway_service/mocks/tests/test_api.py -v

# Только покрытие ТЗ
python -m pytest backend/gateway_service/mocks/tests/test_tz_coverage.py -v
```

---

## 🔑 Тестовые учётные данные

| Email | Пароль | Роль |
|-------|--------|------|
| `ivanov@example.com` | `secret123` | engineer |
| `petrova@example.com` | `secret456` | knowledge_admin |
| `admin@example.com` | `admin123` | system_admin |

---

## 📋 Структура проекта

```
backend/gateway_service/mocks/
├── common.py                     # Seed-данные, модели, утилиты
├── gateway.py                    # Единый шлюз (порт 8081)
├── requirements.txt              # Зависимости
├── start_service.py             # Утилита запуска
├── run_all.py                   # Запуск всех сервисов
├── README.md                    # Документация
│
├── auth_service/
│   └── main.py                  # Auth Service (router)
├── orchestrator_service/
│   └── main.py                  # Orchestrator (router)
├── query_service/
│   └── main.py                  # Query Service (router)
├── registry_service/
│   └── main.py                  # Registry Service (2 routers)
│
└── tests/
    ├── test_api.py              # 105 базовых тестов
    └── test_tz_coverage.py      # 68 тестов покрытия ТЗ
```

---

## 🔌 API Endpoints

### Auth Service (`/api/v1/auth/*`, `/api/v1/admin/*`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/token` | Получить JWT-токены (login) |
| POST | `/auth/refresh` | Обновить access-токен |
| POST | `/auth/revoke` | Отозвать refresh-токен |
| GET | `/auth/me` | Профиль текущего пользователя |
| GET | `/admin/users` | Список пользователей |
| POST | `/admin/users` | Создать пользователя |
| GET | `/admin/users/{id}` | Детали пользователя |
| PUT | `/admin/users/{id}` | Обновить пользователя |
| PATCH | `/admin/users/{id}` | Частичное обновление |
| DELETE | `/admin/users/{id}` | Деактивировать пользователя |
| GET | `/admin/roles` | Список ролей |
| POST | `/admin/roles` | Создать роль |
| GET | `/admin/audit` | Журнал аудита |
| POST | `/internal/auth/validate` | Проверить токен (внутренний) |

### Orchestrator (`/api/v1/documents/*`, `/api/v1/validate/*`, `/api/v1/monitor/*`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/documents` | Загрузить документ (асинхронно) |
| GET | `/documents` | Список документов |
| GET | `/documents/{id}` | Детали документа |
| GET | `/documents/{id}/status` | Статус обработки |
| GET | `/documents/{id}/file` | Информация о файле |
| GET | `/documents/{id}/pages` | Список страниц |
| GET | `/documents/{id}/pages/{num}` | Детали страницы |
| GET | `/documents/{id}/pages/{num}/preview` | Превью страницы |
| GET | `/documents/{id}/pages/{num}/text` | Текст страницы |
| GET | `/documents/{id}/parameters` | Извлечённые параметры |
| DELETE | `/documents/{id}` | Удалить документ |
| POST | `/documents/{id}/reprocess` | Повторная обработка |
| GET | `/documents/{id}/errors` | Ошибки обработки |
| GET | `/documents/queue` | Очередь обработки |
| POST/GET | `/documents/search` | Поиск по документам |
| POST | `/validate/compare` | Сравнение с эталоном |
| GET | `/validate/compare/{id}` | Результат сравнения |
| POST | `/validate/checks` | Массовая проверка |
| GET | `/validate/checks/{id}` | Статус проверки |
| GET | `/validate/checks/{id}/export` | Экспорт проверки |
| GET | `/monitor/metrics` | Метрики системы |

### Query Service (`/api/v1/chat/*`, `/api/v1/text/*`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/chat/sessions` | Создать сессию |
| GET | `/chat/sessions` | Список сессий |
| GET | `/chat/sessions/{id}` | Детали сессии |
| PUT | `/chat/sessions/{id}` | Обновить сессию |
| DELETE | `/chat/sessions/{id}` | Удалить сессию |
| POST | `/chat/sessions/{id}/messages` | Отправить сообщение |
| POST | `/chat/sessions/{id}/context` | Управление контекстом |
| POST | `/chat/sessions/{id}/export` | Экспорт сессии |
| POST | `/chat/feedback` | Обратная связь |
| GET | `/chat/history` | История вопросов |
| GET | `/chat/history/export` | Экспорт истории |
| POST | `/chat` | Вопрос вне сессии |
| POST | `/text/search` | Поиск по тексту |
| POST | `/text/ask` | Вопрос к тексту |

### Registry Service (`/api/v1/classifiers/*`, `/api/v1/terminology/*`, `/api/v1/common/*`, `/api/v1/registry/documents/*`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/classifiers` | Список классификаторов |
| GET | `/classifiers/tree` | Дерево классификаторов |
| GET | `/classifiers/{code}` | Узел классификатора |
| POST | `/classifiers` | Создать узел |
| PUT | `/classifiers/{code}` | Обновить узел |
| PATCH | `/classifiers/{code}` | Частичное обновление |
| DELETE | `/classifiers/{code}` | Удалить узел |
| POST | `/classifiers/import` | Импорт |
| GET | `/terminology` | Список терминов |
| GET | `/terminology/{id}` | Детали термина |
| POST | `/terminology` | Создать термин |
| PUT | `/terminology/{id}` | Обновить термин |
| DELETE | `/terminology/{id}` | Удалить термин |
| GET | `/terminology/normalize` | Нормализация термина |
| POST | `/terminology/import` | Импорт терминов |
| GET | `/registry/documents` | Список документов НСИ |
| GET | `/registry/documents/{id}` | Детали документа НСИ |
| POST | `/registry/documents` | Создать документ НСИ |
| PUT | `/registry/documents/{id}` | Обновить документ НСИ |
| PATCH | `/registry/documents/{id}/status` | Обновить статус |
| DELETE | `/registry/documents/{id}` | Удалить документ НСИ |
| GET | `/registry/documents/export` | Экспорт документов |
| POST | `/registry/documents/import` | Импорт документов |
| GET | `/common/stats` | Статистика реестра |
| GET | `/common/enums` | Допустимые значения |
| GET | `/system/health` | Health check |

---

## 📊 Seed-данные

| Сущность | Количество |
|----------|-----------|
| Пользователи | 5 (3 активных, 1 неактивный) |
| Роли | 3 (engineer, knowledge_admin, system_admin) |
| Документы (файловые) | 5 (specification, drawing, archival_scan, normative, failed) |
| Очередь обработки | 1 документ в processing |
| Ошибки документов | 3 |
| Проверки валидации | 1 (8 ok, 2 warning, 1 error) |
| Сравнения | 1 (match) |
| Сессии чата | 2 (с сообщениями) |
| История вопросов | 3 записи |
| Классификаторы | 6 (иерархия 2 уровня) |
| Терминология | 6 терминов |
| Документы НСИ | 5 (реестр) |

---

## 🛡️ Особенности gateway

- **CORS** — разрешены все origins
- **RBAC** — JWT-токены трекаются, user context доступен в `request.state.user`
- **Idempotency-Key** — POST `/documents` и `/chat` поддерживают идемпотентность
- **X-Process-Time** — каждый ответ содержит заголовок с временем обработки
- **Lifespan** — современный контекстный менеджер (без `@app.on_event`)

---

## ⚠️ Известные отличия от продакшена

- Данные **in-memory** (теряются при перезапуске)
- Нет реального OCR/RAG — результаты эмулируются
- RBAC не блокирует запросы (только логирует контекст)
- Idempotency-Key не влияет на тело ответа (только статус-код)