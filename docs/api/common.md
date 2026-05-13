# API Нейроассистента ПКБ (v1.0)

### Общие положения

- Базовый URL (оркестратор): `https://{host}/api/v1`

- Базовый URL для внутренних запросов: `http://127.0.0.1:{port}/api/v1`

- Формат данных: `application/json`, для загрузки файлов – `multipart/form-data`

- Аутентификация: все запросы, кроме `/auth/*` и `/system/health`, требуют заголовок
  `Authorization: Bearer <access_token>`. Токен получается через `/auth/token`.

---

### Формат ответа

#### 1. Публичные API (Orchestrator, Auth, Query, Integration, OCR, RAG, Validation)

Успех — данные возвращаются напрямую (без обёртки). Поле `data` опционально — используется для группировки с `meta` или когда ответ не является списком/объектом напрямую.

**Для списковых ответов** допускаются следующие ключи массива на верхнем уровне:

| Ключ массива | Где используется |
|---|---|
| `items` | Orchestrator (документы, поиск, страницы), Query (история) |
| `users` | Auth (список пользователей) |
| `sessions` | Query (список сессий чата) |
| `events` | Auth (аудит) |
| `queue` | Orchestrator (очередь документов) |
| `errors` | Orchestrator (журнал ошибок) |
| `roles` | Auth (список ролей) |

Поле `meta` на верхнем уровне содержит пагинацию:

```json
{
  "items": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "page_size": 50
  }
}
```

Допускается дополнительное поле `summary` перед `items` (например, `GET /documents`).

**Для одиночных объектов** — данные возвращаются напрямую, без `data`:

```json
{
  "document_id": "doc-8a3f2b",
  "status": "queued"
}
```

#### 2. Registry Service

Для Registry Service используется wrapped-формат с обязательным полем `data`:

```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "page_size": 50
  }
}
```

Для одиночных объектов:

```json
{
  "data": {
    "doc_id": 42,
    "title": "..."
  }
}
```

#### При ошибке (все сервисы)

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден",
    "details": {}
  }
}
```

---

### Пагинация

Параметры пагинации для всех list-эндпоинтов:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `page` | int | 1 | Номер страницы |
| `page_size` | int | 50 | Записей на странице (max 200) |

Поля `meta`:

| Поле | Тип | Описание |
|------|-----|----------|
| `total` | int | Общее количество записей |
| `page` | int | Текущая страница |
| `page_size` | int | Размер страницы |

---

### Модель выполнения (sync / async)

API поддерживает три модели выполнения:

| Модель | HTTP-код ответа | Описание | Примеры |
|--------|------------------|----------|---------|
| **Синхронная** | `200` / `201` | Результат готов в теле ответа | `GET /documents`, `POST /chat/ask`, `POST /auth/token` |
| **Асинхронная с polling** | `202` | Запрос принят, сервер возвращает `task_id` / `document_id`. Клиент опрашивает статус через `GET .../{id}/status` | `POST /documents`, `POST /documents/{doc_id}/reprocess` |
| **Синхронная с фоновой обработкой** | `200` | Ответ приходит сразу, но часть данных может дозаполняться (поле `status: "processing"`). Клиент повторяет запрос для финального результата | `POST /validate/compare` (до перехода на `202`) |

**Правила для клиентов:**

- При получении `202` — сохранить `task_id` / `document_id` и опрашивать соответствующий GET-статус endpoint.
- Интервал опроса: не чаще 1 раза в 2 секунды.
- Если `status` в ответе `"processing"` — повторить запрос позже; если `"completed"`/`"failed"` — обработка завершена.

---

### Коды ответов HTTP и ошибок

| HTTP-код | Код ошибки (`error.code`) | Описание | Сервис |
|----------|--------------------------|----------|--------|
| 200 | — | Успех | все |
| 201 | — | Создан ресурс | все |
| 202 | — | Запрос принят (асинхронная обработка) | Orchestrator |
| 400 | `BAD_REQUEST` | Неверные параметры запроса | все |
| 400 | `VALIDATION_ERROR` | Ошибка валидации полей | все |
| 401 | `UNAUTHORIZED` | Нет доступа — клиент не известен | все |
| 401 | `INVALID_TOKEN` | Токен недействителен или истёк | Auth |
| 403 | `FORBIDDEN` | Нет доступа — нет прав на ресурс | все |
| 404 | `NOT_FOUND` | Ресурс не найден | все |
| 404 | `USER_NOT_FOUND` | Пользователь не найден | Auth |
| 404 | `CLASSIFIER_NOT_FOUND` | Узел классификатора не найден | Registry |
| 404 | `TERM_NOT_FOUND` | Термин не найден | Registry |
| 404 | `DOCUMENT_NOT_FOUND` | Документ не найден (реестр НСИ или файловый) | Registry, Orchestrator |
| 404 | `SESSION_NOT_FOUND` | Сессия чата не найдена | Query |
| 404 | `FILE_NOT_FOUND` | Файл не найден | Integration |
| 409 | `HAS_CHILDREN` | Нельзя удалить узел с дочерними | Registry |
| 409 | `DUPLICATE_CODE` | Код классификатора уже существует | Registry |
| 409 | `DUPLICATE_TERM` | Термин уже существует | Registry |
| 422 | `VALIDATION_FAILED` | Ошибка семантической валидации | Validation |
| 500 | `INTERNAL_ERROR` | Внутренняя ошибка сервера | все |
| 500 | `INDEXING_FAILED` | Ошибка индексации документа | RAG |
| 500 | `OCR_FAILED` | Ошибка OCR-распознавания | OCR, Orchestrator |
| 501 | `NOT_IMPLEMENTED` | Метод не реализован | все |
| 504 | `GATEWAY_TIMEOUT` | Таймаут при вызове внутреннего сервиса | Orchestrator |

---

### Матрица доступа (RBAC)

| Группа / Эндпоинт | `engineer` | `knowledge_admin` | `system_admin` |
|---|---|---|---|
| `GET /auth/me`, `POST /auth/token`, `/refresh`, `/revoke` | ✓ | ✓ | ✓ |
| `POST /documents` | ✓ | ✓ | ✓ |
| `GET /documents` (+ `/{id}`, `/status`, `/file`, `/pages`) | ✓ | ✓ | ✓ |
| `DELETE /documents/{id}` | ✗ | ✓ | ✓ |
| `POST /documents/{id}/reprocess` | ✗ | ✓ | ✓ |
| `POST /documents/search`, `GET /documents/search` | ✓ | ✓ | ✓ |

| `POST /validate/compare`, `GET /validate/compare/{id}` | ✓ | ✓ | ✓ |
| `POST /validate/checks` (+ экспорт) | ✓ | ✓ | ✓ |
| `GET /admin/users`, `POST/PUT/PATCH/DELETE /admin/users` | ✗ | ✗ | ✓ |
| `GET /admin/roles`, `POST /admin/roles` | ✗ | ✗ | ✓ |
| `GET /admin/audit` | ✗ | ✗ | ✓ |
| `GET /registry/*` | ✓ | ✓ | ✓ |
| `POST /PUT /DELETE /registry/*` | ✗ | ✓ | ✓ |
| `GET /monitor/metrics` | ✗ | ✓ | ✓ |

> Роли: `engineer` — инженер-конструктор; `knowledge_admin` — администратор НСИ; `system_admin` — системный администратор.
> Матрица применяется ко всем эндпоинтам публичного API (Orchestrator). Внутренние сервисы могут иметь собственные политики доступа.

---

### Примечания по реализации

- **Типы документов** строго фиксированы: `normative`, `archival_scan`, `drawing`, `specification`. Именно эти значения ожидаются в полях `document_type`.

- **Обработка полным документом:** API не содержит методов для ручного выделения областей. Распознавание запускается для всего документа сразу после загрузки; пользователь не может отметить фрагмент для OCR. Просмотр страниц возможен только в режиме чтения.

- **Пороговые значения confidence:** система помечает страницы с низким качеством OCR и логирует их (UC-02, UC-09). Конкретные пороги настраиваются на уровне сервисов.

- **Трассируемость ответов:** все ответы поиска и вопросно-ответной системы обязательно содержат `document_id` и `page`. Прямая ссылка на страницу формируется согласно публичному API просмотра (`/documents/{doc_id}/pages/{page_num}`).

- **Дисклеймер** о необходимости инженерной верификации присутствует в ответах `/validate/compare`.

- **Именование полей источников** (единый стандарт для всех сервисов):

  | Концепция | Единое имя поля |
  |---|---|
  | ID документа | `document_id` |
  | Номер страницы | `page` |
  | ID фрагмента | `fragment_id` |
  | URL превью страницы | `page_preview_url` |
  | URL документа | `document_url` |
  | Оценка релевантности | `score` |

  Допускаются синонимы в ответах внутренних сервисов, но публичный API (Orchestrator) **обязан** маппить поля к единым именам.

- **Лимиты загрузки:** максимальный размер файла — 100 МБ. Поддерживаемые MIME-типы: `application/pdf`, `image/png`, `image/jpeg`, `image/tiff`. При превышении лимита возвращается `413 PAYLOAD_TOO_LARGE`.

- **Идемпотентность:** опциональный заголовок `Idempotency-Key` поддерживается для `POST /documents` и `POST /chat/ask`. При повторном запросе с тем же ключом в течение 24 часов возвращается сохранённый результат.

---

## Схема оркестрации конвейера Purgatory

Orchestrator координирует прохождение документа через внутренние сервисы (OCR, RAG, Validation) по цепочке этапов.

### 1. Этапы конвейера

```
POST /documents
     │
     ▼
┌──────────────┐
│ OCR Service  │  OCR + Layout + чанкинг + классификация
│ /ocr/process │  → container_id
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ RAG Service  │  1. /rag/embed — вычисление embeddings
│              │  2. /rag/validate-chunks — JSON Schema, ltree, полнота
│              │  3. /rag/validate-classify — коды МКС/ОКСТУ
└──────┬───────┘
       │  если valid
       ▼
┌──────────────┐
│ Orchestrator │  POST /documents/{id}/approve → запуск промотирования
│              │  POST /documents/{id}/promote → атомарная запись в Registry
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Registry     │  nsi schema: documents, chunks, images, tables...
│ (nsi schema) │
└──────────────┘

Validation Service — отдельно, для бизнес-сценариев:
  POST /validate/compare     — норма vs проект
  POST /validate/check       — проверка правил
  POST /validate/calculate   — арифметика
```

### 2. Детальная схема вызовов

#### Этап 1: OCR + Layout Parsing (OCR Service)

Orchestrator вызывает `POST /ocr/process` с `version_id` (ссылка на файл в MinIO).

OCR Service:
1. Скачивает файл из MinIO по `file_id`
2. Определяет формат через `format_registry`
3. Выполняет OCR/распознавание
4. Формирует **chunk container** — JSON с чанками, ltree-иерархией, таблицами, изображениями
5. Извлекает коды классификации (МКС/ОКС, ОКСТУ, УДК)

**Запрос** (Orchestrator → OCR):
```json
POST /ocr/process
{
  "version_id": "c4b9f2d3-...",
  "file_id": "file-abc123",
  "options": {
    "engine": "auto",
    "language": "ru",
    "extract_tables": true,
    "extract_images": true,
    "extract_classification": true
  }
}
```

**Ответ**:
```json
{
  "container_id": "cnt-001",
  "document_id": "b3a8f1c2-...",
  "version_id": "c4b9f2d3-...",
  "status": "completed",
  "chunk_summary": {
    "total_chunks": 34, "text_chunks": 28, "table_chunks": 3, "image_chunks": 3
  },
  "pages_total": 12, "pages_processed": 12, "avg_confidence": 0.94,
  "classification": {
    "mks_oks_code": "47.020", "okstu_code": null, "udk_code": "629.5.021",
    "year": "1981", "mks_status": "CONFIRMED", "okstu_status": "NOT_USED",
    "confidence": 0.89
  }
}
```

#### Этап 2: Embedding + Валидация (RAG Service)

**2a. Вычисление embeddings:**

Orchestrator → `POST /rag/embed`
```json
{
  "container": {
    "container_id": "cnt-001",
    "document_id": "b3a8f1c2-...",
    "chunks": [ { "chunk_id": "...", "text": "...", "has_embedding": false } ],
    "images": [ ... ],
    "classification": { ... }
  },
  "model": "default"
}
```

RAG Service — stateless-функция: получает контейнер в теле запроса, вычисляет embeddings, возвращает обновлённый контейнер. Не ходит в БД.

**2b. Валидация chunk container:**

Orchestrator → `POST /rag/validate-chunks`
```json
{
  "container": {
    "container_id": "cnt-001",
    "chunks": [ { "chunk_id": "...", "text": "...", "ltree_path": "...", "has_embedding": true } ],
    "classification": { ... }
  },
  "schema_version": "purgatory-v2.3"
}
```

Проверки:
- все чанки имеют `text`
- все чанки имеют `ltree_path`
- все текстовые чанки имеют `embedding`
- нет orphan-чанков (висящих без родителя)
- ltree-структура валидна

**Ответ (успех):**
```json
{
  "container_id": "cnt-001",
  "status": "valid",
  "checks_passed": 14,
  "checks_failed": 0
}
```

**Ответ (ошибки):**
```json
{
  "container_id": "cnt-001",
  "status": "invalid",
  "checks_passed": 12,
  "checks_failed": 2,
  "errors": [
    {
      "chunk_id": "chk-012",
      "code": "MISSING_EMBEDDING",
      "severity": "error",
      "message": "Чанк не содержит embedding"
    }
  ]
}
```

**2c. Валидация классификации:**

Orchestrator → `POST /rag/validate-classify`
```json
{
  "document_id": "b3a8f1c2-...",
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null
  }
}
```

RAG сверяет коды со справочником Registry и возвращает статус по каждому коду. **Не отправляет данные никуда** — чистая валидация. Решение о создании `classifier_pending` принимает Оркестратор, анализируя возвращённые статусы.

**Результат этапа 2:**
- Всё успешно → Orchestrator переводит статус в `ready_for_promotion`
- validation = `invalid` или есть `PENDING_REVIEW` → для каждого `PENDING_REVIEW` Orchestrator вызывает `POST /registry/classifiers/pending`, статус документа → `review_required`

#### Этап 3: Approve (опционально)

Если `review_required` — оператор проверяет ошибки через `GET /documents/{doc_id}/chunks` и вызывает `POST /documents/{doc_id}/approve`.

#### Этап 4: Promotion → Registry

Orchestrator вызывает `POST /documents/{doc_id}/promote`, атомарно записывает в Registry:

| Сущность | Таблица Registry | Источник |
|---|---|---|
| Документ | `documents` | Метаданные + классификация |
| Секции/иерархия | `document_sections` | ltree-пути из чанков |
| Чанки + embeddings | `chunks` | Текст + векторы |
| Изображения | `images` | Ссылки на MinIO |
| Таблицы | `extracted_tables` | JSONB-структуры |
| Связи | `chunk_relations` | Ссылки между чанками |

### 3. Полный цикл (sequence)

```
UI                Orchestrator            OCR Service       RAG Service         Validation Service      Registry
│                      │                      │                 │                      │                  │
│ POST /documents      │                      │                 │                      │                  │
│────────────────────▶││                      │                 │                      │                  │
│◀── 202 {uploaded} ──│                      │                 │                      │                  │
│                      │                      │                 │                      │                  │
│ GET /status          │ POST /ocr/process    │                 │                      │                  │
│────────────────────▶│────────────────────▶││                 │                      │                  │
│◀── "processing" ────│◀── {container_id} ───│                  │                      │                  │
│                      │                      │                 │                      │                  │
│                      │ POST /rag/embed      │                 │                      │                  │
│                      │──────────────────────────────────────▶││                      │                  │
│                      │◀── {embedded} ────────────────────────│                      │                  │
│                      │                      │                 │                      │                  │
│                      │ POST /rag/validate-chunks              │                      │                  │
│                      │──────────────────────────────────────▶│                      │                  │
│                      │◀── {valid} ────────────────────────────│                      │                  │
│                      │                      │                 │                      │                  │
│                      │ POST /rag/validate-classify            │                      │                  │
│                      │──────────────────────────────────────▶│                      │                  │
│                      │◀── {confirmed} ────────────────────────│                      │                  │
│                      │                      │                 │                      │                  │
│◀── "ready_for_promotion"                    │                 │                      │                  │
│                      │                      │                 │                      │                  │
│ POST /approve        │                      │                 │                      │                  │
│────────────────────▶│ POST /promote          │                 │                      │                  │
│                      │────────────────────────────────────────────────────────────────────────────▶│
│◀── "approved" ──────│◀─── {registry_doc_id} ──────────────────────────────────────────────────────│
│                      │                      │                 │                      │                  │
│ POST /validate/compare                       │                 │                      │                  │
│──────────────────────────────────────────────────────────────────────────────────▶││                  │
│◀── {match_status} ──────────────────────────────────────────────────────────────────│                  │
```

### 4. Матрица ответственности сервисов

| Операция | Сервис | Тип | Описание |
|---|---|---|---|
| Загрузка, дедупликация | Orchestrator | Sync→Async | SHA-256, logical doc + version |
| OCR + Layout + Чанкинг | **OCR Service** | Async | Распознавание, структура, таблицы, изображения |
| Извлечение классификации | **OCR Service** | Async | Коды МКС/ОКСТУ с первых страниц |
| Вычисление embeddings | **RAG Service** | Async | Векторизация текстовых чанков |
| Валидация chunk container | **RAG Service** | Sync | JSON Schema, ltree, полнота, embeddings |
| Проверка классификации | **RAG Service** | Sync | Сверка кодов со справочником |
| Аппрув (ручной) | Orchestrator | Sync | Оператор подтверждает готовность |
| Промотирование в Registry | **Orchestrator** | Async | Атомарная запись в nsi |
| Сопоставление норм и проекта | **Validation Service** | Async | Бизнес-валидация проектных решений |
| Проверка правил | **Validation Service** | Sync | Проверка текста на правила |

### 5. Новые/изменённые эндпоинты внутренних сервисов

#### OCR Service

| Метод | Путь | Изменение |
|---|---|---|
| `POST` | `/ocr/process` | Расширен: `version_id` + `file_id`. Асинхронный (`202`). Возвращает `container_id` + `classification` |
| `GET` | `/ocr/process/{task_id}/status` | 🆕 Статус асинхронной обработки |
| `GET` | `/ocr/container/{container_id}` | 🆕 Получение готового chunk container |
| `GET` | `/ocr/engines` | Без изменений |

#### RAG Service

| Метод | Путь | Изменение |
|---|---|---|
| `POST` | `/rag/embed` | 🆕 Вычисление embeddings для чанков контейнера |
| `POST` | `/rag/validate-chunks` | 🆕 Валидация chunk container (JSON Schema, ltree, полнота) |
| `POST` | `/rag/validate-classify` | 🆕 Проверка классификационных кодов по справочнику |
| `GET` | `/rag/embed/{task_id}/status` | 🆕 Статус вычисления embeddings |
| `POST` | `/rag/index` | Без изменений (production RAG) |
| `POST` | `/rag/search` | Без изменений |
| `POST` | `/rag/generate` | Без изменений |

#### Validation Service

| Метод | Путь | Изменение |
|---|---|---|
| `POST` | `/validate/extract/parameters` | Без изменений |
| `POST` | `/validate/check` | Без изменений |
| `POST` | `/validate/calculate` | Без изменений |
| `POST` | `/validate/compare` | Без изменений |
| `POST` | `/validate/compare/batch` | Без изменений |
| `POST` | `/validate/recommend` | Без изменений |
