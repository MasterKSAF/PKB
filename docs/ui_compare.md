# Сопоставление API docs\api с требованиями UI

## Резюме

Выявлены **значительные расхождения** между документацией API в `docs\api` и требованиями UI из описания frontend. Многие endpoint'ы, которые UI ожидает найти в Orchestrator Service, отсутствуют или имеют другую структуру. **Ключевое фундаментальное расхождение** — разный формат ответа об ошибке/успехе (см. секцию 0).

---

## 0. Общий формат ответа (базовое расхождение)

**Все** endpoint'ы страдают от разного формата обёртки. Без согласования ни один запрос UI → API не сработает.

| Аспект | UI ожидает | API возвращает |
|--------|-----------|----------------|
| Обёртка успеха | `{"ok": true, "data": {…}, "error": null}` | Объект с данными напрямую (без `ok`/`data`/`error`) |
| Обёртка ошибки | `{"ok": false, "data": null, "error": {"code": "DOCUMENT_NOT_FOUND", "message": "…"}}` | `{"error": {"code": 422, "code_name": "INVALID_FORMAT", "message": "…", "details": {}}}` |
| HTTP-статус ошибки | Не оговорён | Числовой код дублируется в теле: `code: 422` |
| Поле `code` | Строковый код (`"DOCUMENT_NOT_FOUND"`) | Числовой код (`422`) + строковый `code_name` |

**Решение:** обернуть все ответы Orchestrator Service в единую структуру `{"ok": bool, "data": any, "error": {…}}`. Orchestrator — единственная точка входа для UI, поэтому обёртка добавляется именно в нём, а не во внутренних сервисах.

---

## Детальное сопоставление по разделам

### 1. Пользователь, роль и статус системы

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /auth/me` | ⚠️ Частично | `auth_service_api.md`: `GET /users/me` | **Несоответствие структуры**: UI ожидает `userId` (camelCase), `fullName`, `position`, `role`, `roleTitle`, `availableTabs`, `permissions` (объект с boolean). API возвращает `user_id` (snake_case), `email`, `full_name`, `roles` (массив), `permissions` (массив строк) |
| `GET /health` | ⚠️ Частично | `orchestrator_service_api.md`: `GET /health` | **Несоответствие структуры**: UI ожидает `database`, `searchIndex`, `ocrQueue`, `storage`. API возвращает `services` с полями `auth`, `rag`, `ocr`, `validation`, `integration` |

**Решения:**
- **Auth Service** — добавить эндпоинт `GET /auth/me` (camelCase, с полями `position`, `role`, `roleTitle`, `availableTabs`, `permissions` как объект boolean-полей). Либо **Orchestrator** проксирует `GET /users/me` из Auth Service и маппит поля в camelCase + добавляет `availableTabs` и `permissions` на основе роли.
- **Orchestrator** — расширить `GET /health`: добавить поля `database`, `searchIndex`, `ocrQueue`, `storage`, вычисляемые из существующего `services.*`.

---

### 2. Чат инженера

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `POST /chat` | ❌ Отсутствует | Нет прямого аналога | UI ожидает единый endpoint для отправки вопроса и получения ответа |
| Альтернатива 1 | ⚠️ Частично | `query_service_api.md`: `POST /chat/sessions/{session_id}/messages` | Query Service требует отдельного создания сессии (`POST /chat/sessions`) и потом отправки сообщения. UI ожидает одним запросом с `sessionId` в теле |
| Альтернатива 2 | ⚠️ Частично | `orchestrator_service_api.md`: `POST /ask` | Orchestrator имеет упрощённый вопрос-ответ без сессий и нумерации ответов |
| Статусы `needs_clarification` и `source_conflict` | ❌ Не поддерживаются | Ни одним сервисом | API не имеет аналогов `needs_clarification` (с `missingFields`) и `source_conflict` (с `conflicts[]`) |

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

Orchestrator `POST /ask` возвращает:
```json
{
  "question": "...",
  "answer": "...",
  "sources": [...],
  "processing_time_ms": 3200,
  "model_used": "llama-3-70b"
}
```

**Решения:**
- **Orchestrator** — добавить `POST /chat` как единый endpoint для UI. Внутри: либо создать сессию через Query Service + отправить сообщение, либо использовать RAG Service напрямую. Ответ маппить в формат UI (`answerItems` с нумерацией, `citations` с `citationId`, `pagePreviewUrl`, `documentUrl`).
- **Query Service** — добавить поддержку статусов `needs_clarification` (с полем `missingFields`) и `source_conflict` (с полем `conflicts[]`). Orchestrator проксирует эти статусы в UI-формат.

---

### 3. Открытие страницы и документа

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /documents/{documentId}/pages/{page}/preview` | ⚠️ Иное имя | `orchestrator_service_api.md`: `GET /documents/{doc_id}/pages/{page_num}` | Отличается путь (`preview` vs отсутствует суффикс). API разделяет image (`/pages/{page_num}`) и text (`/pages/{page_num}/text`), а UI ожидает единый комбинированный ответ с `previewUrl`, `text` и `highlight` |
| `GET /documents/{documentId}/file` | ❌ Отсутствует | Нет аналога | UI ожидает получение полного файла документа |

**Решения:**
- **Orchestrator** — добавить алиас `GET /documents/{doc_id}/pages/{page_num}/preview`, который агрегирует ответы от `/pages/{page_num}` (изображение) и `/pages/{page_num}/text` (текст) в единый объект с полями `previewUrl`, `text`, `highlight`, `contentType`, `documentTitle`.
- **Orchestrator** — добавить `GET /documents/{doc_id}/file`, который отдаёт бинарный поток файла через Integration Service (`GET /files/{file_id}`) или прямую ссылку на файл.

---

### 4. Поиск

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /search?q=...` | ⚠️ Частично | `orchestrator_service_api.md`: `GET /search?q=...` | **Endpoint существует**, но формат ответа отличается |
| Альтернатива | ⚠️ Частично | `query_service_api.md`: `POST /text/search` | Метод POST вместо GET, другая структура ответа (с `analysis`, `entities`) |

**Структурные расхождения между UI и Orchestrator `GET /search`:**

UI ожидает:
```json
{
  "items": [{ "resultId": "sr-001", "documentId": "...", "relevance": 0.92, "pagePreviewUrl": "...", "documentUrl": "..." }]
}
```

Orchestrator возвращает:
```json
{
  "results": [{ "fragment_id": "frg-123abc", "document_id": "...", "score": 0.92 }]
}
```
Различия: `results` → `items`, `fragment_id` → `resultId`, `score` → `relevance`, отсутствуют `pagePreviewUrl` и `documentUrl`.

**Решения:**
- **Orchestrator** — расширить `GET /search`: добавить в ответ поля `resultId`, `documentId`, `relevance`, `pagePreviewUrl`, `documentUrl`. Переименовать `results` → `items` (или маппить на уровне обёртки). Добавить query-параметр `documentType` для фильтрации.

---

### 5. Реестр документов

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /documents` | ⚠️ Частично | `orchestrator_service_api.md`: `GET /documents` | **Несоответствие структуры**: UI ожидает `summary` (total, ocrCompleted, indexed, needAttention) и `items` с полями `title`, `type`, `source`, `version`, `pages`, `ocrStatus`, `indexStatus`. API возвращает `documents` с полями `filename`, `document_type`, `pages_total`, `pages_processed`, `status` |
| `POST /documents` | ⚠️ Частично | `orchestrator_service_api.md`: `POST /documents` | **Несоответствие структуры ответа**: UI ожидает `uploadStatus`, `jobId`, `ocrStatus`, `indexStatus`. API возвращает `document_id`, `status`, `task_id` |

**Решения:**
- **Orchestrator** — в `GET /documents` добавить поле `summary` с вычисляемыми метриками (total, ocrCompleted — из `status=processed`, indexed — из RAG Service, needAttention — из страниц с низким confidence). Переименовать/добавить поля: `filename` → `title`, `document_type` → `type`, добавить `source`, `version`, `ocrStatus`, `indexStatus`.
- **Orchestrator** — в `POST /documents` добавить поля `uploadStatus`, `jobId` (алиас на `task_id`), `ocrStatus`, `indexStatus`.

---

### 6. Проверка на соответствие требованиям НСИ

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `POST /checks` | ⚠️ Иное имя | `orchestrator_service_api.md`: `POST /validate/compare` | Разные пути, структурные различия в запросе и ответе. **Ключевое: endpoint асинхронный** — возвращает `{"status": "processing"}` и требует polling `GET /validate/compare/{comparison_id}`. UI ожидает синхронный ответ |
| `GET /checks/{checkRunId}/export` | ❌ Отсутствует | Нет аналога | UI ожидает экспорт результата проверки в Excel |

**Структурные расхождения в запросе:**

UI ожидает:
```json
{
  "projectDocumentIds": ["..."],
  "nsiDocumentIds": ["..."],
  "parameters": ["..."],
  "userId": "u-001"
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

UI ожидает `summary` с `ok`, `warning`, `error` и `items` с полями `status` (OK/WARNING/ERROR), `projectValue`, `nsiRequirement`, `projectSource`, `nsiSource`.

API возвращает `match_status` (match/possible_discrepancy/not_found_in_project/not_found_in_norm/insufficient_data) — для одного сравнения, без группировки в items.

**Низкоуровневые endpoint'ы Validation Service (не закрывают UI-сценарий, но дают контекст):**
- `POST /extract/parameters` — извлечение параметров из документа
- `POST /check` — единичная проверка текста по правилам
- `POST /compare` / `POST /compare/batch` — низкоуровневое сопоставление пар фрагментов
- `POST /recommend` — рекомендации по исправлению
- `POST /calculate` — арифметический движок (потенциально для сценария 9 «Расчётный сценарий»)

**Решения:**
- **Orchestrator** — добавить `POST /checks` как синхронный (или с длинным таймаутом) endpoint для UI. Внутри: принять UI-формат, разложить на пары нормативных и проектных фрагментов через Validation Service `POST /compare/batch`, агрегировать результаты, смаппить `match_status` → OK/WARNING/ERROR.
- **Orchestrator** — добавить `GET /checks/{check_run_id}/export`, генерирующий XLSX на основе результатов проверки.
- **Validation Service** — не требует изменений (остаётся низкоуровневым движком).

---

### 7. История

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /history?userId=...` | ⚠️ Частично | `query_service_api.md`: `GET /chat/sessions` + `GET /chat/sessions/{session_id}` | **Частичное покрытие**: список сессий даёт историю диалогов с `last_message_preview`, `message_count`. Но UI ожидает плоский список записей с полями `historyId`, `userName`, `question`, `answerPreview`, `status`, `sourceCount`, с фильтрацией по `userId`, `status`, `dateFrom` |
| `GET /history/export?...` | ❌ Отсутствует | Ближайший аналог: `query_service_api.md`: `POST /chat/sessions/{session_id}/export` | Экспорт одной сессии есть, но не массовый экспорт с фильтрами |

**Решения:**
- **Orchestrator** — добавить `GET /history`. Внутри: агрегировать данные из Query Service (все сессии пользователя, сообщения в них) и представить в виде плоского списка с фильтрацией. Поля `status`, `sourceCount` вычислять из `feedback` и `sources` сообщений.
- **Orchestrator** — добавить `GET /history/export`: собрать отфильтрованные записи, сгенерировать XLSX/CSV.

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
  "userId": "u-001",
  "useful": true,
  "comment": "...",
  "openedCitationIds": ["cit-001"]
}
```

API принимает:
```json
{
  "session_id": "...",
  "message_id": "...",
  "rating": "positive|negative|neutral",
  "comment": "...",
  "aspects": [...]
}
```

**Решения:**
- **Orchestrator** — добавить `POST /feedback` с UI-форматом, внутри маппить `answerId` → `session_id` + `message_id` (из метаданных ответа), `useful: true` → `rating: "positive"`, `useful: false` → `rating: "negative"`. Проксировать в Query Service `POST /chat/feedback`.
- **Orchestrator** — в ответе `POST /feedback` вычислять и возвращать `metricsChanged` (агрегация метрик после сохранения оценки).

---

### 9. QA (Метрики)

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /metrics` | ❌ Отсутствует | Нет аналога | UI требует метрики: `ocrQuality`, `retrievalQuality`, `answersWithSources`, `avgLatencyMs`, `usefulRate`, `ratedAnswers`, `flaggedForReview`, `openQuestions`, `logs` |

**Решения:**
- **Orchestrator** — добавить `GET /metrics`. Внутри агрегировать данные из:
  - OCR Service (качество распознавания — средний confidence по страницам)
  - RAG Service (retrieval quality — средний score по поисковым запросам)
  - Query Service (доля ответов с источниками, средняя latency, оценки)
  - Логи из внутренних сервисов для `logs[]`.
- Альтернативно, создать **Metrics Service** как отдельный сервис-агрегатор.

---

### 10. Администрирование

| UI Endpoint | Статус | Существующий API | Расхождения |
|-------------|--------|------------------|-------------|
| `GET /admin/users` | ⚠️ Иное имя | `auth_service_api.md`: `GET /users` | Разные пути, UI ожидает поля `login`, `role`, `status`, `lastLoginAt`. API возвращает `email`, `roles`, `is_active` |
| `PATCH /admin/users/{userId}` | ⚠️ Иное имя/метод | `auth_service_api.md`: `PUT /users/{user_id}` | UI использует PATCH, API использует PUT. UI ожидает только `role`, API принимает множество полей |
| `GET /admin/audit-log` | ⚠️ Иное имя | `auth_service_api.md`: `GET /audit` | Разные пути, структура схожа |

**Решения:**
- **Orchestrator** — добавить алиасы: `GET /admin/users` → прокси `GET /users`, маппить поля (`email` → `login`, `roles[0]` → `role`, `is_active` → `status`, добавить `lastLoginAt`). `PATCH /admin/users/{userId}` → `PUT /users/{user_id}` с извлечением `role` из тела. `GET /admin/audit-log` → `GET /audit`.
- **Auth Service** — опционально: добавить поле `lastLoginAt` в ответ `GET /users` и `GET /users/me`, если требуется.

---

## 11. Дополнительные endpoint'ы API, не востребованные UI README

Ниже перечислены endpoint'ы из `docs/api`, которые **существуют**, но не описаны в UI README как требования. Часть из них покрывает сценарии, для которых UI ещё не оформил контракт.

### Orchestrator Service

| Endpoint | Потенциальное использование в UI |
|----------|----------------------------------|
| `POST /ask` | Упрощённый чат (без сессий) — альтернатива `POST /chat` |
| `POST /documents/{doc_id}/reprocess` | Кнопка «Переобработать OCR» в Реестре (UI упоминает эту функцию) |
| `DELETE /documents/{doc_id}` | Удаление документа из Реестра |
| `GET /documents/{doc_id}/status` | Прогресс-бар обработки документа |
| `GET /documents/{doc_id}/errors` | Журнал ошибок обработки (можно добавить в Реестр или QA) |
| `GET /documents/{doc_id}/parameters` | Извлечённые параметры — для предзаполнения формы Проверки |
| `GET /documents/{doc_id}/pages/{page_num}/text` | Текстовый слой страницы (для `/preview`) |

### Query Service

| Endpoint | Потенциальное использование |
|----------|----------------------------|
| `POST /text/search` | Поиск по произвольному тексту (с авто-декомпозицией) |
| `POST /text/ask` | Вопрос по произвольному тексту (с нормализацией) |
| `POST /chat/sessions/{id}/context` | Управление контекстом сессии (очистка, summarization) |
| `POST /chat/sessions/{id}/export` | Экспорт одного диалога (PDF/JSON/Markdown/HTML) |

### Validation Service

| Endpoint | Потенциальное использование |
|----------|----------------------------|
| `POST /extract/parameters` | Извлечение параметров из документа |
| `POST /check` | Единичная проверка текста по правилам |
| `POST /calculate` | Арифметический движок — **сценарий 9 «Расчётный сценарий»** из ТЗ |
| `POST /recommend` | Рекомендации по исправлению ошибок проверки |
| `POST /compare` / `POST /compare/batch` | Низкоуровневое сопоставление (используется внутри `POST /checks`) |

### Integration Service

| Endpoint | Потенциальное использование |
|----------|----------------------------|
| `POST /meridian/export` | Интеграция с ИС «Меридиан» — **сценарий 12** из ТЗ |
| `GET /external/status` | Статус внешних систем |

### OCR Service

| Endpoint | Потенциальное использование |
|----------|----------------------------|
| `POST /ocr/process` | Пакетная OCR-обработка (внутренний) |
| `GET /ocr/engines` | Список OCR-движков (для администрирования) |

---

## Что необходимо добавить в docs\api

### Orchestrator Service (приоритетно)

Добавить следующие endpoints:

1. **Обёртка ответов** — все ответы Orchestrator в формате `{"ok": bool, "data": …, "error": {…}}`
2. `GET /auth/me` — профиль текущего пользователя в UI-формате (camelCase, с `availableTabs`, `permissions` как объект boolean)
3. `POST /chat` — единый endpoint для чата с поддержкой статусов `needs_clarification` и `source_conflict`
4. `GET /search` — расширить существующий: добавить `pagePreviewUrl`, `documentUrl`, `relevance` вместо `score`
5. `GET /documents/{doc_id}/pages/{page_num}/preview` — агрегированный preview (image + text + highlight)
6. `GET /documents/{doc_id}/file` — получение файла документа
7. `POST /checks` — проверка на соответствие НСИ в UI-формате (синхронный или с длинным таймаутом)
8. `GET /checks/{check_run_id}/export` — экспорт результатов проверки в XLSX
9. `GET /history` — история запросов (агрегация из Query Service сессий)
10. `GET /history/export` — экспорт истории (XLSX/CSV)
11. `POST /feedback` — оценка ответа в UI-формате (прокси в Query Service)
12. `GET /metrics` — QA-метрики (агрегация из OCR, RAG, Query Service, логов)
13. `GET /admin/users` — список пользователей в UI-формате (прокси в Auth Service)
14. `PATCH /admin/users/{user_id}` — изменение роли (прокси в Auth Service)
15. `GET /admin/audit-log` — административный журнал (прокси в Auth Service)

### Auth Service

- Добавить поле `lastLoginAt` в профиль пользователя
- Добавить эндпоинт `GET /auth/me` (в дополнение к `GET /users/me`) с camelCase-полями

### Новые сервисы (опционально)

- **Metrics Service** — агрегатор QA-метрик (если не хочется нагружать Orchestrator)

---

## Что необходимо скорректировать в UI описании

### Если используем существующий API (вариант адаптации UI):

1. **Общий формат**: UI адаптировать к структуре ошибок API `{"error": {"code": …, "code_name": …, "message": …}}`
2. **Аутентификация**: Заменить `GET /auth/me` на `GET /users/me` с адаптацией полей (snake_case → camelCase, `roles` массив → `role` строка)
3. **Чат**: Разбить на два вызова: `POST /chat/sessions` + `POST /chat/sessions/{id}/messages`
4. **Поиск**: Адаптировать к существующему `GET /search` (переименовать поля в UI: `fragment_id` → `resultId`, `score` → `relevance`)
5. **Feedback**: Заменить `POST /feedback` на `POST /chat/feedback` с адаптацией полей (`useful` boolean → `rating` string, `answerId` → `message_id`)
6. **Проверка**: Заменить `POST /checks` на `POST /validate/compare` с адаптацией к асинхронной модели (polling)
7. **Администрирование**: Заменить пути на `/users`, `/audit`

### Рекомендуемый подход

**Вариант A (рекомендуется):** Создать в Orchestrator Service единые endpoint'ы для UI, которые:
- Принимают формат, ожидаемый UI
- Внутри маршрутизируют запросы к соответствующим сервисам (Auth, Query, RAG, Validation, OCR, Integration)
- Возвращают ответы в формате UI с обёрткой `{"ok": …, "data": …, "error": …}`

**Вариант B:** Адаптировать UI к существующему API (значительные изменения frontend, отказ от единого формата ответа).

---

## Приоритеты реализации

| Приоритет | Endpoint / Задача | Сервис | Обоснование |
|-----------|------------------|--------|-------------|
| **P0 (Критично)** | Обёртка `ok`/`data`/`error` | Orchestrator | Без неё ни один запрос не сработает |
| **P0** | `GET /auth/me` или `GET /users/me` | Orchestrator / Auth | Базовая аутентификация и роли |
| **P0** | `POST /chat` | Orchestrator | Основной сценарий использования |
| **P0** | `GET /documents`, `POST /documents` | Orchestrator | Управление документами |
| **P0** | `GET /documents/{id}/pages/{page}` и `/preview` | Orchestrator | Просмотр источников |
| **P1 (Высокий)** | `GET /search` (доработка ответа) | Orchestrator | Поиск по базе знаний |
| **P1** | `POST /checks` + асинхронный polling или синхронный | Orchestrator | Проверка проектных решений |
| **P1** | `GET /history` | Orchestrator | История запросов (агрегация сессий) |
| **P2 (Средний)** | `GET /metrics` | Orchestrator (или новый Metrics) | QA метрики |
| **P2** | `POST /feedback` | Orchestrator (прокси) | Оценка ответов |
| **P2** | `/admin/*` | Orchestrator (прокси Auth) | Администрирование |
| **P3 (Низкий)** | Экспорты (`/checks/export`, `/history/export`) | Orchestrator | Дополнительные функции |

---

## Сводка: какие изменения и в каком сервисе

### Orchestrator Service — основной объём изменений

| # | Что сделать | Почему |
|---|------------|--------|
| 1 | Добавить обёртку `{"ok": bool, "data": …, "error": {…}}` на все ответы | Фундаментальное расхождение формата |
| 2 | `GET /auth/me` — прокси `GET /users/me` из Auth Service, маппить поля (snake → camel), добавить `position`, `roleTitle`, `availableTabs`, `permissions` как boolean-object на основе роли | Аутентификация и роли в UI-формате |
| 3 | `GET /health` — добавить вычисляемые поля `database`, `searchIndex`, `ocrQueue`, `storage` на основе `services.*` | UI ожидает конкретные ключи |
| 4 | `POST /chat` — новый эндпоинт: принять UI-формат, внутри вызвать Query Service (создать сессию → отправить сообщение), смаппить ответ в `answerItems` с `citations` и `citationId`, сгенерировать `pagePreviewUrl` и `documentUrl` | Основной сценарий чата |
| 5 | `GET /documents/{doc_id}/pages/{page_num}/preview` — агрегировать `/pages/{page_num}` и `/pages/{page_num}/text` | UI ожидает единый preview |
| 6 | `GET /documents/{doc_id}/file` — отдать файл через Integration Service | Открытие полного документа |
| 7 | `GET /search` — расширить существующий ответ: `results` → `items`, `fragment_id` → `resultId`, `score` → `relevance`, добавить `pagePreviewUrl`, `documentUrl` | Формат ответа для UI |
| 8 | `GET /documents` — добавить `summary`, переименовать/добавить поля под UI | Реестр документов |
| 9 | `POST /documents` — добавить `uploadStatus`, `jobId`, `ocrStatus`, `indexStatus` в ответ | Загрузка документа |
| 10 | `POST /checks` — новый эндпоинт: принять UI-формат (`projectDocumentIds`, `nsiDocumentIds`, `parameters`), внутри разложить на пары фрагментов через Validation Service, агрегировать, смаппить `match_status` → OK/WARNING/ERROR. Сделать синхронным (с таймаутом ~30с) или асинхронным с моментальным возвратом `checkRunId` и последующим polling | Проверка НСИ |
| 11 | `GET /checks/{check_run_id}/export` — генерация XLSX по результатам проверки | Экспорт |
| 12 | `GET /history` — агрегировать сессии из Query Service в плоский список с фильтрацией | История |
| 13 | `GET /history/export` — XLSX/CSV по отфильтрованным записям | Экспорт истории |
| 14 | `POST /feedback` — маппить UI-формат → Query Service `POST /chat/feedback`, вернуть `metricsChanged` | Оценка ответов |
| 15 | `GET /metrics` — агрегировать метрики из OCR, RAG, Query Service | QA |
| 16 | `GET /admin/users`, `PATCH /admin/users/{id}`, `GET /admin/audit-log` — прокси в Auth Service с маппингом полей | Администрирование |

### Auth Service — минимальные доработки

| # | Что сделать | Почему |
|---|------------|--------|
| 1 | Добавить поле `lastLoginAt` в ответ `GET /users/me` и `GET /users` | Требуется UI |
| 2 | Опционально: поддержать PATCH на `/users/{user_id}` (сейчас только PUT) | UI использует PATCH |

### Query Service — минимальные доработки

| # | Что сделать | Почему |
|---|------------|--------|
| 1 | В ответе на сообщение ассистента добавить поддержку статуса `needs_clarification` (с `missingFields`) | Сценарий «уточнение» в UI |
| 2 | В ответе добавить поддержку статуса `source_conflict` (с `conflicts[]`) | Сценарий «конфликт источников» |

### Validation Service — без изменений

Используется как низкоуровневый движок через Orchestrator.

### OCR Service — без изменений

Используется как внутренний сервис.

### Integration Service — без изменений

Используется для отдачи файлов и интеграции с Меридиан.
