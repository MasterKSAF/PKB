# Сопоставление API docs\api с требованиями UI

## Резюме

Выявлены **значительные расхождения** между документацией API в `docs\api` и требованиями UI из описания frontend. Многие endpoint'ы, которые UI ожидает найти в Orchestrator Service, отсутствуют или имеют другую структуру.

---

## Детальное сопоставление по разделам

### 1. Пользователь, роль и статус системы

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /auth/me` | ⚠️ Частично | `auth_service_api.md`: `GET /users/me` | **Несоответствие структуры**: UI ожидает `userId` (camelCase), `fullName`, `position`, `role`, `roleTitle`, `availableTabs`, `permissions` (объект с boolean). API возвращает `user_id` (snake_case), `email`, `full_name`, `roles` (массив), `permissions` (массив строк) |
| `GET /health` | ⚠️ Частично | `orchestrator_service_api.md`: `GET /health` | **Несоответствие структуры**: UI ожидает `database`, `searchIndex`, `ocrQueue`, `storage`. API возвращает `services` с полями `auth`, `rag`, `ocr`, `validation`, `integration` |

**Рекомендации:**
- Добавить в Auth Service endpoint `GET /auth/me` с camelCase полями и `availableTabs`
- Или адаптировать UI к существующему `GET /users/me`
- Добавить в `GET /health` поля `database`, `searchIndex`, `ocrQueue`, `storage` или адаптировать UI

---

### 2. Чат инженера

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `POST /chat` | ❌ Отсутствует | Нет прямого аналога | UI ожидает единый endpoint для отправки вопроса и получения ответа |
| Альтернатива | ⚠️ Частично | `query_service_api.md`: `POST /chat/sessions/{session_id}/messages` | Query Service требует отдельного создания сессии (`POST /chat/sessions`) и потом отправки сообщения. UI ожидает одним запросом с `sessionId` в теле |

**Структурные расхождения в ответе:**

UI ожидает:
```json
{
  "ok": true,
  "data": {
    "answerId": "ans-001",
    "status": "answered|needs_clarification|source_conflict",
    "answerItems": [{ "number": 1, "text": "...", "citations": [...] }]
  }
}
```

Query Service возвращает:
```json
{
  "message_id": "msg-004",
  "role": "assistant",
  "content": "...",
  "sources": [...]
}
```

**Требуется:**
- Добавить в Orchestrator Service endpoint `POST /chat` с единым форматом запроса/ответа для UI
- Или UI адаптироваться к двухэтапному процессу (создание сессии → отправка сообщения)

---

### 3. Открытие страницы и документа

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /documents/{documentId}/pages/{page}/preview` | ⚠️ Иное имя | `orchestrator_service_api.md`: `GET /documents/{doc_id}/pages/{page_number}` | Отличается путь (`preview` vs отсутствует суффикс) |
| `GET /documents/{documentId}/file` | ❌ Отсутствует | Нет аналога | UI ожидает получение полного файла документа |

**Рекомендации:**
- Добавить в Orchestrator Service алиас `/documents/{doc_id}/pages/{page}/preview` → существующий `/documents/{doc_id}/pages/{page_number}`
- Добавить `GET /documents/{doc_id}/file` для получения файла документа

---

### 4. Поиск

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /search?q=...` | ❌ Отсутствует | `rag_service.md`: `POST /search` (внутренний) | UI ожидает GET с query-параметрами, API имеет POST с телом JSON |
| Альтернатива | ⚠️ Частично | `query_service_api.md`: `POST /text/search` | Метод POST вместо GET, другая структура ответа |

**Структурные расхождения:**

UI ожидает:
```json
{
  "items": [{ "resultId": "sr-001", "documentId": "...", "relevance": 0.92, "pagePreviewUrl": "..." }]
}
```

Query Service возвращает:
```json
{
  "results": [{ "fragment_id": "frg-042", "score": 0.94, ... }]
}
```

**Требуется:**
- Добавить в Orchestrator Service публичный endpoint `GET /search` с форматом UI

---

### 5. Реестр документов

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /documents` | ⚠️ Частично | `orchestrator_service_api.md`: `GET /documents` | **Несоответствие структуры**: UI ожидает `summary` (total, ocrCompleted, indexed, needAttention) и `items` с полями `title`, `type`, `source`, `version`, `pages`, `ocrStatus`, `indexStatus`. API возвращает `documents` с полями `filename`, `document_type`, `pages_total`, `pages_processed`, `status` |
| `POST /documents` | ⚠️ Частично | `orchestrator_service_api.md`: `POST /documents` | **Несоответствие структуры ответа**: UI ожидает `uploadStatus`, `jobId`, `ocrStatus`, `indexStatus`. API возвращает `document_id`, `status`, `task_id` |

**Рекомендации:**
- Добавить в `GET /documents` поле `summary` с метриками
- Добавить в ответ `POST /documents` поля `uploadStatus`, `jobId`, `ocrStatus`, `indexStatus`
- Или адаптировать UI к существующей структуре

---

### 6. Проверка на соответствие требованиям НСИ

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `POST /checks` | ⚠️ Иное имя | `orchestrator_service_api.md`: `POST /validate/compare` | Разные пути и значительные структурные различия |
| `GET /checks/{checkRunId}/export` | ❌ Отсутствует | Нет аналога | UI ожидает экспорт результата проверки в Excel |

**Структурные расхождения в запросе:**

UI ожидает:
```json
{
  "projectDocumentIds": ["..."],
  "nsiDocumentIds": ["..."],
  "parameters": ["..."]
}
```

API принимает:
```json
{
  "normative_query": "...",
  "project_document_id": "..."
}
```

**Структурные расхождения в ответе:**

UI ожидает `summary` с `ok`, `warning`, `error` и `items` с полями `status` (OK/WARNING/ERROR), `projectValue`, `nsiRequirement`.

API возвращает `match_status` (match/possible_discrepancy/not_found_in_project/not_found_in_norm/insufficient_data).

**Рекомендации:**
- Добавить в Orchestrator Service endpoint `POST /checks` с форматом UI
- Добавить `GET /checks/{checkRunId}/export` для экспорта

---

### 7. История

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /history?userId=...` | ❌ Отсутствует | Нет аналога | UI требует журнал запросов |
| `GET /history/export?...` | ❌ Отсутствует | Нет аналога | UI требует экспорт истории |

**Рекомендации:**
- Создать новый сервис или добавить в Orchestrator Service endpoints `/history` и `/history/export`

---

### 8. Оценка ответа инженером (Feedback)

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `POST /feedback` | ⚠️ Иное имя | `query_service_api.md`: `POST /chat/feedback` | Разные пути, структурные отличия |

**Структурные расхождения:**

UI ожидает:
```json
{
  "answerId": "ans-001",
  "useful": true,
  "openedCitationIds": ["cit-001"]
}
```

API принимает:
```json
{
  "session_id": "...",
  "message_id": "...",
  "rating": "positive|negative|neutral",
  "aspects": [...]
}
```

**Рекомендации:**
- Добавить в Orchestrator Service endpoint `POST /feedback` с форматом UI
- Или UI адаптироваться к существующей структуре с `session_id` и `message_id`

---

### 9. QA (Метрики)

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /metrics` | ❌ Отсутствует | Нет аналога | UI требует метрики: `ocrQuality`, `retrievalQuality`, `answersWithSources`, `avgLatencyMs`, `usefulRate`, `ratedAnswers`, `flaggedForReview` |

**Рекомендации:**
- Создать endpoint `GET /metrics` (возможно, новый Metrics Service или добавить в Orchestrator)

---

### 10. Администрирование

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /admin/users` | ⚠️ Иное имя | `auth_service_api.md`: `GET /users` | Разные пути, UI ожидает поля `login`, `role`, `status`, `lastLoginAt`. API возвращает `email`, `roles`, `is_active` |
| `PATCH /admin/users/{userId}` | ⚠️ Иное имя/метод | `auth_service_api.md`: `PUT /users/{user_id}` | UI использует PATCH, API использует PUT. UI ожидает только `role`, API принимает множество полей |
| `GET /admin/audit-log` | ⚠️ Иное имя | `auth_service_api.md`: `GET /audit` | Разные пути, структура схожа |

**Рекомендации:**
- Добавить в Orchestrator Service алиасы `/admin/users` → `/users`, `/admin/audit-log` → `/audit`
- Или адаптировать UI к существующим путям Auth Service

---

## Что необходимо добавить в docs\api

### Orchestrator Service

Добавить следующие endpoints:

1. `GET /auth/me` - профиль текущего пользователя (или алиас на Auth Service)
2. `GET /search` - публичный поиск для UI
3. `POST /chat` - единый endpoint для чата
4. `GET /documents/{doc_id}/file` - получение файла документа
5. `POST /checks` - проверка на соответствие НСИ
6. `GET /checks/{check_run_id}/export` - экспорт результатов проверки
7. `GET /history` - история запросов
8. `GET /history/export` - экспорт истории
9. `POST /feedback` - оценка ответа
10. `GET /metrics` - QA метрики
11. `GET /admin/users` - список пользователей (или алиас)
12. `PATCH /admin/users/{user_id}` - изменение роли
13. `GET /admin/audit-log` - административный журнал (или алиас)

### Новые сервисы (опционально)

- **History Service** - для работы с историей запросов
- **Metrics Service** - для QA метрик
- **Admin Service** - для административных функций (если не в Auth Service)

---

## Что необходимо скорректировать в UI описании

### Если используем существующий API:

1. **Аутентификация**: Заменить `GET /auth/me` на `GET /users/me` с адаптацией полей
2. **Чат**: Разбить на два вызова: `POST /chat/sessions` + `POST /chat/sessions/{id}/messages`
3. **Поиск**: Заменить `GET /search` на `POST /text/search`
4. **Feedback**: Заменить `POST /feedback` на `POST /chat/feedback` с адаптацией полей
5. **Проверка**: Заменить `POST /checks` на `POST /validate/compare` с адаптацией формата
6. **Администрирование**: Заменить пути на `/users`, `/audit`

### Рекомендуемый подход

**Вариант A (рекомендуется):** Создать в Orchestrator Service единые endpoint'ы для UI, которые:
- Принимают формат, ожидаемый UI
- Внутри маршрутизируют запросы к соответствующим сервисам
- Возвращают ответы в формате UI

**Вариант B:** Адаптировать UI к существующему API (значительные изменения frontend)

---

## Приоритеты реализации

| Приоритет | Endpoint | Обоснование |
|-----------|----------|-------------|
| **P0 (Критично)** | `GET /auth/me` или `GET /users/me` | Базовая аутентификация |
| **P0** | `POST /chat` или альтернатива | Основной сценарий использования |
| **P0** | `GET /documents`, `POST /documents` | Управление документами |
| **P0** | `GET /documents/{id}/pages/{page}` | Просмотр источников |
| **P1 (Высокий)** | `GET /search` | Поиск по базе знаний |
| **P1** | `POST /checks` | Проверка проектных решений |
| **P1** | `GET /history` | История запросов |
| **P2 (Средний)** | `GET /metrics` | QA метрики |
| **P2** | `POST /feedback` | Оценка ответов |
| **P2** | `/admin/*` | Администрирование |
| **P3 (Низкий)** | Экспорты (`/export`) | Дополнительные функции |
