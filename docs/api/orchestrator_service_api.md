## API Orchestrator Service

Единая точка входа для публичного API Нейроассистента ПКБ.

**Базовый URL**: `https://{host}/api/v1`

### Формат ответа

Все ответы Orchestrator Service оборачиваются в единую структуру:

```json
{
  "ok": true,
  "data": { ... },
  "error": null
}
```

При ошибке:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден"
  }
}
```

> Ниже в примерах ответов показано содержимое поля `data` (без внешней обёртки `ok`/`error`).

---

## 0. Пользователь и аутентификация

### GET /auth/me

Профиль текущего пользователя в формате UI (camelCase, с доступными вкладками и правами).

**Заголовки**: `Authorization: Bearer <access_token>`

**Ответ `200`**:

```json
{
  "user_id": "u-001",
  "full_name": "Иванов Сергей Петрович",
  "position": "Инженер-конструктор",
  "role": "engineer",
  "role_title": "Инженер",
  "available_tabs": ["chat", "search", "checks", "history"],
  "permissions": {
    "can_upload_documents": false,
    "can_run_ocr": false,
    "can_manage_users": false
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | string | ID пользователя |
| `full_name` | string | Полное имя |
| `position` | string | Должность |
| `role` | string | Роль: `engineer`, `knowledge_admin`, `system_admin` |
| `role_title` | string | Название роли для отображения |
| `available_tabs` | string[] | Доступные вкладки |
| `permissions` | object | Права как boolean-поля |

> Внутренняя реализация: проксирует `GET /users/me` из Auth Service, маппит поля в camelCase. `available_tabs` и `permissions` вычисляются из роли.

---

## 1. Документы

### POST /documents

Загрузка документа в очередь обработки.

**Запрос**: `multipart/form-data`

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `file` | File | Да | Бинарный файл (PDF, PNG, JPG, TIFF) |
| `document_type` | string | Да | Тип документа: `normative`, `archival_scan`, `drawing`, `specification` |
| `metadata` | string | Нет | JSON-строка с метаданными |

**Ответ `201`**:

```json
{
  "document_id": "doc-8a3f2b",
  "upload_status": "uploaded",
  "job_id": "job-ocr-554",
  "ocr_status": "queued",
  "index_status": "not_started",
  "status": "queued",
  "task_id": "task-ocr-001",
  "created_at": "2026-04-27T10:00:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | string | ID документа |
| `upload_status` | string | Статус загрузки: `uploaded`, `failed` |
| `job_id` | string | ID задачи загрузки |
| `ocr_status` | string | Статус OCR: `not_started`, `queued`, `processing`, `completed`, `error` |
| `index_status` | string | Статус индексации: `not_started`, `queued`, `completed`, `error` |
| `status` | string | Общий статус: `queued`, `processing`, `processed`, `error` |
| `task_id` | string | ID задачи обработки |
| `created_at` | string | Дата создания |

**Ошибки**: `400` — неподдерживаемый формат/размер, `422` — повреждённый файл.

### GET /documents

Список документов с фильтрацией.

**Параметры query**:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `status` | string | Фильтр по статусу: `queued`, `processing`, `processed`, `error` |
| `type` | string | Фильтр по типу документа |
| `date_from` | string | Дата начала (ISO 8601) |
| `date_to` | string | Дата окончания |
| `search` | string | Поиск по имени файла |
| `limit` | int | Лимит результатов |
| `offset` | int | Смещение |

**Ответ `200`**:

```json
{
  "summary": {
    "total": 128,
    "ocr_completed": 112,
    "indexed": 108,
    "need_attention": 4
  },
  "items": [
    {
      "document_id": "doc-8a3f2b",
      "title": "21900M2_spec.pdf",
      "type": "specification",
      "source": "РС",
      "version": "2026",
      "pages": 12,
      "ocr_status": "completed",
      "index_status": "ready",
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T10:02:00Z"
    }
  ],
  "total": 18,
  "limit": 20,
  "offset": 0
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `summary.total` | int | Общее количество документов |
| `summary.ocr_completed` | int | Количество с завершённым OCR |
| `summary.indexed` | int | Количество проиндексированных |
| `summary.need_attention` | int | Количество требующих внимания |
| `items[].document_id` | string | ID документа |
| `items[].title` | string | Название документа (отображаемое имя) |
| `items[].type` | string | Тип документа |
| `items[].source` | string | Источник |
| `items[].version` | string | Версия |
| `items[].pages` | int | Количество страниц |
| `items[].ocr_status` | string | Статус OCR: `not_started`, `queued`, `processing`, `completed`, `error` |
| `items[].index_status` | string | Статус индексации: `not_started`, `ready`, `error` |

### GET /documents/{doc_id}

Детальная информация о документе.

**Ответ `200`**:

```json
{
  "document_id": "doc-8a3f2b",
  "filename": "21900M2_spec.pdf",
  "document_type": "specification",
  "status": "processed",
  "file_size": 2048576,
  "pages_total": 12,
  "pages_processed": 12,
  "pages_failed": 0,
  "created_at": "2026-04-27T10:00:00Z",
  "updated_at": "2026-04-27T10:05:00Z",
  "metadata": {
    "project": "21900M2",
    "author": "Иванов"
  }
}
```

### GET /documents/{doc_id}/status

Прогресс обработки документа.

**Ответ `200`**:

```json
{
  "document_id": "doc-8a3f2b",
  "status": "processing",
  "progress_percent": 41.7,
  "steps": {
    "ocr": "in_progress",
    "layout_parsing": "pending",
    "indexing": "pending"
  },
  "started_at": "2026-04-27T10:00:30Z",
  "estimated_completion": "2026-04-27T10:06:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | Текущий статус |
| `progress_percent` | float | Процент выполнения |
| `steps` | object | Статус этапов: `pending`, `in_progress`, `completed`, `error` |

### GET /documents/{doc_id}/file

Получение полного файла документа.

**Ответ `200`**: Backend возвращает бинарный поток файла с корректным `Content-Type` или JSON со ссылкой:

```json
{
  "document_id": "doc-8a3f2b",
  "document_title": "21900M2_spec.pdf",
  "content_type": "application/pdf",
  "file_url": "/files/doc-8a3f2b/full.pdf"
}
```

### GET /documents/{doc_id}/pages/{page_num}/preview

Агрегированный просмотр страницы: изображение + текст + подсветка фрагмента.

**Параметры query**:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `highlight` | string | Текст для подсветки (опционально) |

**Ответ `200`**:

```json
{
  "document_id": "doc-8a3f2b",
  "document_title": "21900M2_spec.pdf",
  "page": 5,
  "content_type": "application/pdf",
  "preview_url": "/files/doc-8a3f2b/page-5.png",
  "text": "Спецификация...\nПоз. 1 Кница...",
  "highlight": "Кница"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | string | ID документа |
| `document_title` | string | Название документа |
| `page` | int | Номер страницы |
| `content_type` | string | MIME-тип |
| `preview_url` | string | URL изображения страницы |
| `text` | string | Распознанный текст страницы |
| `highlight` | string|null | Фрагмент для подсветки |

> Внутренняя реализация: агрегирует ответы от `/documents/{doc_id}/pages/{page_num}` (изображение) и `/documents/{doc_id}/pages/{page_num}/text` (текст).

### DELETE /documents/{doc_id}

Удаление документа и всех связанных данных.

**Ответ `200`**:

```json
{
  "document_id": "doc-8a3f2b",
  "deleted_at": "2026-04-27T10:30:00Z"
}
```

### POST /documents/{doc_id}/reprocess

Повторная обработка документа.

**Запрос**:

```json
{
  "mode": "enhanced_preprocess"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `mode` | string | Да | `standard`, `enhanced_preprocess`, `fallback_ocr` |

**Ответ `200`**:

```json
{
  "document_id": "doc-8a3f2b",
  "task_id": "task-ocr-002",
  "status": "reprocessing_queued",
  "mode": "enhanced_preprocess",
  "created_at": "2026-04-27T11:00:00Z"
}
```

### GET /documents/{doc_id}/errors

Журнал ошибок обработки.

**Параметры query**:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `stage` | string | Этап: `upload`, `ocr`, `parsing`, `indexing`, `generation` |
| `severity` | string | Уровень: `warning`, `error` |
| `limit` | int | Лимит |
| `offset` | int | Смещение |

**Ответ `200`**:

```json
{
  "errors": [
    {
      "error_id": "err-001",
      "document_id": "doc-8a3f2b",
      "page_number": 5,
      "stage": "ocr",
      "error_code": "LOW_CONFIDENCE",
      "error_message": "Качество распознавания страницы ниже порога (confidence=0.62)",
      "severity": "warning",
      "retry_attempt": 0,
      "timestamp": "2026-04-27T10:01:00Z"
    }
  ],
  "total": 1
}
```

---

## 2. Поиск и вопросно-ответная система

### POST /search

Семантический поиск фрагментов.

**Запрос**:

```json
{
  "query": "требования к ледовому классу Arc4",
  "document_ids": ["doc-norm-001", "doc-norm-002"],
  "top_k": 5,
  "filters": {
    "document_type": ["normative"],
    "date_from": "2020-01-01",
    "date_to": null
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `query` | string | Да | Поисковый запрос |
| `document_ids` | string[] | Нет | Ограничить поиск документами |
| `top_k` | int | Нет | Число результатов (по умолчанию 5) |
| `filters` | object | Нет | Фильтры по типу, дате |

**Ответ `200`**:

```json
{
  "query": "требования к ледовому классу Arc4",
  "items": [
    {
      "result_id": "sr-001",
      "document_id": "doc-norm-001",
      "document_title": "Правила классификации и постройки морских судов. Часть I",
      "document_type": "НСИ",
      "section": "Корпус",
      "page": 42,
      "fragment": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм...",
      "relevance": 0.92,
      "page_preview_url": "/documents/doc-norm-001/pages/42/preview",
      "document_url": "/documents/doc-norm-001/file"
    }
  ],
  "total_found": 3,
  "processing_time_ms": 450
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `items[].result_id` | string | ID результата |
| `items[].document_id` | string | ID документа |
| `items[].document_title` | string | Название документа |
| `items[].document_type` | string | Тип документа |
| `items[].section` | string | Раздел |
| `items[].page` | int | Номер страницы |
| `items[].fragment` | string | Текст фрагмента |
| `items[].relevance` | float | Релевантность (0–1) |
| `items[].page_preview_url` | string | URL preview страницы |
| `items[].document_url` | string | URL полного документа |

> `GET /search` возвращает аналогичный ответ. Параметры query: `q`, `document_id`, `page`, `limit`, `document_type`.

**Ошибки**: `400` — пустой запрос.

### GET /search

Быстрый GET-вариант поиска.

**Параметры query**: `q`, `document_id`, `page`, `limit`, `document_type`

**Ответ**: Аналогичен `POST /search`.

### POST /ask

Генерация ответа с источниками.

**Запрос**:

```json
{
  "question": "Какая должна быть толщина обшивки для ледового класса Arc4?",
  "document_ids": null,
  "options": {
    "temperature": 0.2
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `question` | string | Да | Вопрос |
| `document_ids` | string[] | Нет | Ограничение корпуса |
| `options` | object | Нет | Параметры генерации |
| `options.temperature` | float | Нет | Температура (0-1) |

**Ответ `200`**:

```json
{
  "question": "Какая должна быть толщина обшивки для ледового класса Arc4?",
  "answer": "Согласно Правилам классификации и постройки морских судов (Часть I, стр. 42), толщина обшивки для ледового класса Arc4 должна быть не менее 12 мм.",
  "sources": [
    {
      "document_id": "doc-norm-001",
      "document_title": "Правила классификации и постройки морских судов. Часть I",
      "page_number": 42,
      "fragment_id": "frg-123abc",
      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм...",
      "score": 0.92,
      "page_preview_url": "/documents/doc-norm-001/pages/42/preview",
      "document_url": "/documents/doc-norm-001/file"
    }
  ],
  "processing_time_ms": 3200,
  "model_used": "llama-3-70b"
}
```

---

## 3. Просмотр документа и фрагментов

### GET /documents/{doc_id}/pages/{page_num}

Изображение страницы с подсветкой блоков.

**Параметры query**:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `highlight` | string | ID блока для подсветки |

**Ответ `200`**:

```json
{
  "image_url": "/files/page-img/doc-8a3f2b_5.png",
  "page_number": 5,
  "width": 2480,
  "height": 3508,
  "blocks": [
    {
      "block_id": "blk-001",
      "type": "title_block",
      "coordinates": {"x": 200, "y": 100, "width": 800, "height": 50},
      "text": "Спецификация 21900M2.362135.0903",
      "highlighted": false
    },
    {
      "block_id": "blk-002",
      "type": "table",
      "coordinates": {"x": 150, "y": 200, "width": 1800, "height": 600},
      "text": "...",
      "highlighted": true
    }
  ]
}
```

### GET /documents/{doc_id}/pages/{page_num}/text

Текстовый слой и структура страницы.

**Ответ `200`**:

```json
{
  "page_number": 5,
  "full_text": "Спецификация...\nПоз. 1 Кница...",
  "blocks": [
    {
      "block_id": "blk-001",
      "type": "title_block",
      "coordinates": {"x": 200, "y": 100, "width": 800, "height": 50},
      "text": "Спецификация 21900M2.362135.0903",
      "confidence": 0.98
    },
    {
      "block_id": "blk-002",
      "type": "table",
      "coordinates": {"x": 150, "y": 200, "width": 1800, "height": 600},
      "text": "Поз.|Наименование|Кол.|Масса|Материал",
      "confidence": 0.92,
      "table_data": [
        ["Поз.", "Наименование", "Кол.", "Масса", "Материал"],
        ["1", "Кница", "2", "0.5", "сталь 09Г2С"]
      ]
    }
  ]
}
```

---

## 4. Извлечение параметров и сопоставление

### GET /documents/{doc_id}/parameters

Извлечённые структурированные параметры документа.

**Ответ `200`**:

```json
{
  "document_id": "doc-8a3f2b",
  "document_type": "specification",
  "parameters": {
    "designation": "21900M2.362135.0903",
    "title": "Секция 0903",
    "materials": ["сталь 09Г2С", "алюминий АМг5"],
    "dimensions": ["1200x800x6", "L=2500"],
    "references": ["21900M2.362135.0901СБ", "21900M2.362135.0902СБ"],
    "specification_items": [
      {
        "position": "1",
        "name": "Кница",
        "quantity": "2",
        "dimensions": "10x200x300",
        "weight": "0.5",
        "material": "сталь 09Г2С",
        "note": ""
      }
    ]
  },
  "extraction_confidence": 0.89,
  "unconfirmed_fields": ["dimensions позиции 3"],
  "updated_at": "2026-04-27T10:05:00Z"
}
```

### POST /validate/compare

Запуск сопоставления нормы и проектного документа (низкоуровневый, асинхронный).

> Для UI используется синхронный endpoint `POST /checks` (см. раздел 7), который внутри вызывает `POST /validate/compare` / `POST /compare/batch` и агрегирует результат.

**Запрос** (вариант 1 — по запросу):

```json
{
  "normative_query": "толщина обшивки ледового класса Arc4",
  "project_document_id": "doc-draw-001"
}
```

**Запрос** (вариант 2 — по фрагментам):

```json
{
  "normative_fragment_id": "frg-norm-42",
  "project_fragment_id": "frg-draw-5"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `normative_query` | string | Нет | Поисковый запрос к нормативным документам |
| `project_document_id` | string | Нет | ID проектного документа |
| `normative_fragment_id` | string | Нет | ID фрагмента нормы |
| `project_fragment_id` | string | Нет | ID фрагмента проекта |

**Ответ `200`**:

```json
{
  "comparison_id": "cmp-007",
  "status": "processing",
  "created_at": "2026-04-27T12:00:00Z"
}
```

### GET /validate/compare/{comparison_id}

Результат сопоставления.

**Ответ `200`**:

```json
{
  "comparison_id": "cmp-007",
  "status": "completed",
  "normative_block": {
    "document_id": "doc-norm-001",
    "document_title": "Правила РС часть I",
    "page_number": 42,
    "requirement_text": "Толщина обшивки в районе ледового пояса для класса Arc4 ≥ 12 мм"
  },
  "project_block": {
    "document_id": "doc-draw-001",
    "document_title": "21900M2.362135.0903СБ",
    "page_number": 1,
    "parameter_text": "Обшивка ледового пояса t=14 мм"
  },
  "match_status": "match",
  "details": "Требование выполнено: проектная толщина 14 мм превышает минимальные 12 мм.",
  "sources": [
    {"document_id": "doc-norm-001", "page": 42},
    {"document_id": "doc-draw-001", "page": 1}
  ],
  "disclaimer": "Результат носит информационный характер и подлежит обязательной инженерной проверке.",
  "processing_time_ms": 8700
}
```

**Статусы `match_status`**:

| Статус | Описание |
|--------|----------|
| `match` | Совпадает |
| `possible_discrepancy` | Возможное расхождение |
| `not_found_in_project` | Не найдено в проекте |
| `not_found_in_norm` | Не найдено в норме |
| `insufficient_data` | Недостаточно данных |

---

## 5. Служебные методы

### GET /health

Проверка состояния системы.

**Ответ `200`**:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 234567,
  "services": {
    "auth": "ok",
    "rag": "ok",
    "ocr": "degraded",
    "validation": "ok",
    "integration": "ok"
  },
  "database": "online",
  "search_index": "ready",
  "ocr_queue": "idle",
  "storage": "online"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `database` | string | Статус БД: `online`, `offline`, `degraded` |
| `search_index` | string | Статус индекса: `ready`, `building`, `error` |
| `ocr_queue` | string | Статус очереди OCR: `idle`, `processing`, `paused` |
| `storage` | string | Статус хранилища: `online`, `offline` |

---

## 6. Чат

### POST /chat

Единый endpoint для отправки вопроса и получения ответа в формате UI.

**Запрос**:

```json
{
  "question": "Какая минимальная толщина листа корпуса?",
  "session_id": "chat-001",
  "user_id": "u-001",
  "context": {
    "project_id": "project-17",
    "document_ids": ["doc-001", "doc-002"],
    "nsi_version": "2026"
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `question` | string | Да | Текст вопроса |
| `session_id` | string | Да | ID сессии чата |
| `user_id` | string | Да | ID пользователя |
| `context` | object | Нет | Контекст запроса |

**Ответ `200`** (успешный ответ):

```json
{
  "answer_id": "ans-001",
  "status": "answered",
  "message": null,
  "answer_items": [
    {
      "number": 1,
      "text": "Минимальная толщина листа не должна определяться отдельно от проекта. Ее нужно проверять по району корпуса, материалу и расчетной нагрузке.",
      "citations": [
        {
          "citation_id": "cit-001",
          "document_id": "doc-001",
          "document_title": "Правила классификации и постройки морских судов",
          "section": "Корпус",
          "page": 45,
          "fragment": "Фрагмент текста, на котором основан ответ.",
          "page_preview_url": "/documents/doc-001/pages/45/preview",
          "document_url": "/documents/doc-001/file"
        }
      ]
    }
  ],
  "latency_ms": 1420
}
```

**Ответ `200`** (недостаточно данных):

```json
{
  "answer_id": "ans-002",
  "status": "needs_clarification",
  "message": "Уточните проект, район корпуса и тип судна.",
  "missing_fields": ["project_id", "hull_area", "vessel_type"],
  "answer_items": []
}
```

**Ответ `200`** (конфликт источников):

```json
{
  "answer_id": "ans-003",
  "status": "source_conflict",
  "message": "Найдены разные требования в двух редакциях документа.",
  "conflicts": [
    {
      "document_id": "doc-001",
      "document_title": "НСИ, редакция 2024",
      "page": 45,
      "value": "8 мм"
    },
    {
      "document_id": "doc-002",
      "document_title": "НСИ, редакция 2026",
      "page": 47,
      "value": "10 мм"
    }
  ],
  "answer_items": []
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `answer_id` | string | ID ответа |
| `status` | string | `answered`, `needs_clarification`, `source_conflict` |
| `message` | string|null | Сообщение пользователю |
| `answer_items` | array | Список пунктов ответа (с citations) |
| `missing_fields` | string[]|null | Поля для уточнения |
| `conflicts` | object[]|null | Конфликтующие источники |
| `latency_ms` | int | Время обработки |

> Внутренняя реализация: создаёт сессию через Query Service (`POST /chat/sessions`) при первом запросе, отправляет сообщение (`POST /chat/sessions/{session_id}/messages`) и маппит ответ в UI-формат. Статусы `needs_clarification` и `source_conflict` проксируются из Query Service.

---

## 7. Проверка на соответствие требованиям НСИ

### POST /checks

Запуск проверки проектного решения на соответствие требованиям НСИ (синхронный вариант для UI).

**Запрос**:

```json
{
  "project_document_ids": ["doc-project-001"],
  "nsi_document_ids": ["doc-nsi-001", "doc-nsi-002"],
  "parameters": ["толщина листа", "марка стали"],
  "user_id": "u-001"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `project_document_ids` | string[] | Да | ID проектных документов |
| `nsi_document_ids` | string[] | Да | ID нормативных документов |
| `parameters` | string[] | Нет | Параметры для проверки |
| `user_id` | string | Да | ID пользователя |

**Ответ `200`**:

```json
{
  "check_run_id": "check-001",
  "status": "completed",
  "summary": {
    "ok": 8,
    "warning": 2,
    "error": 1
  },
  "items": [
    {
      "check_item_id": "chk-item-001",
      "project": "Проект 17",
      "section": "Корпус",
      "parameter": "Толщина листа",
      "project_value": "8 мм",
      "nsi_requirement": "Не менее 10 мм",
      "nsi_document": "Правила классификации и постройки морских судов",
      "status": "ERROR",
      "comment": "Значение в проекте ниже требования НСИ.",
      "project_source": {
        "document_id": "doc-project-001",
        "page": 12,
        "page_preview_url": "/documents/doc-project-001/pages/12/preview",
        "document_url": "/documents/doc-project-001/file"
      },
      "nsi_source": {
        "document_id": "doc-nsi-001",
        "page": 45,
        "page_preview_url": "/documents/doc-nsi-001/pages/45/preview",
        "document_url": "/documents/doc-nsi-001/file"
      }
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `check_run_id` | string | ID проверки |
| `status` | string | `completed`, `processing` |
| `summary.ok` | int | Количество совпадений |
| `summary.warning` | int | Количество предупреждений |
| `summary.error` | int | Количество ошибок |
| `items[].status` | string | `OK`, `WARNING`, `ERROR` |
| `items[].project_source` | object | Ссылка на источник проекта |
| `items[].nsi_source` | object | Ссылка на нормативный источник |

> Внутренняя реализация: разлагает запрос на пары нормативных и проектных фрагментов через Validation Service (`POST /compare/batch`), агрегирует результаты, маппит `match_status` → `OK`/`WARNING`/`ERROR`.

### GET /checks/{check_run_id}/export

Выгрузка результатов проверки в XLSX.

**Ответ `200`**: Backend возвращает XLSX-файл или JSON со ссылкой:

```json
{
  "check_run_id": "check-001",
  "export_url": "/files/exports/check-001.xlsx",
  "format": "xlsx",
  "created_at": "2026-04-27T12:05:00Z"
}
```

---

## 8. История запросов

### GET /history

Журнал запросов и ответов с фильтрацией.

**Параметры query**:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `user_id` | string | Фильтр по пользователю |
| `status` | string | `answered`, `needs_clarification`, `source_conflict` |
| `date_from` | string | Дата начала (ISO 8601) |
| `date_to` | string | Дата окончания |

**Ответ `200`**:

```json
{
  "items": [
    {
      "history_id": "hist-001",
      "created_at": "2026-04-27T14:01:04Z",
      "user_id": "u-001",
      "user_name": "Иванов Сергей Петрович",
      "question": "Какая минимальная толщина листа корпуса?",
      "answer_preview": "Минимальная толщина зависит от...",
      "status": "answered",
      "source_count": 2,
      "answer_id": "ans-001"
    }
  ],
  "total": 1
}
```

> Внутренняя реализация: агрегирует сессии из Query Service (`GET /chat/sessions`, `GET /chat/sessions/{session_id}`) в плоский список с фильтрацией.

### GET /history/export

Экспорт истории запросов с учётом текущих фильтров.

**Параметры query**: Аналогично `GET /history`.

**Ответ `200`**: Backend возвращает XLSX/CSV или JSON со ссылкой.

---

## 9. Оценка ответа (Feedback)

### POST /feedback

Оценка ответа ассистента инженером.

**Запрос**:

```json
{
  "answer_id": "ans-001",
  "user_id": "u-001",
  "useful": true,
  "comment": "Ответ точный, источник подходит",
  "opened_citation_ids": ["cit-001"]
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `answer_id` | string | Да | ID ответа |
| `user_id` | string | Да | ID пользователя |
| `useful` | bool | Да | Полезен ли ответ |
| `comment` | string | Нет | Комментарий |
| `opened_citation_ids` | string[] | Нет | Какие источники открывал |

**Ответ `200`**:

```json
{
  "feedback_id": "fb-001",
  "saved": true,
  "metrics_changed": {
    "rated_answers": 43,
    "useful_rate": 0.84,
    "flagged_for_review": 5
  }
}
```

> Внутренняя реализация: маппит UI-формат → Query Service (`POST /chat/feedback`): `useful: true` → `rating: "positive"`, `useful: false` → `rating: "negative"`. `answer_id` маппится в `session_id` + `message_id` через метаданные ответа.

---

## 10. QA Метрики

### GET /metrics

Метрики контроля качества системы.

**Ответ `200`**:

```json
{
  "control_metrics": {
    "ocr_quality": 0.984,
    "retrieval_quality": 0.91,
    "answers_with_sources": 0.96,
    "avg_latency_ms": 1420
  },
  "answer_metrics": {
    "useful_rate": 0.84,
    "rated_answers": 43,
    "flagged_for_review": 5,
    "open_questions": 3
  },
  "logs": [
    {
      "time": "12:34:02",
      "type": "search",
      "text": "По запросу найдено 5 релевантных документов",
      "level": "info"
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `control_metrics.ocr_quality` | float | Качество OCR (0–1) |
| `control_metrics.retrieval_quality` | float | Качество поиска (0–1) |
| `control_metrics.answers_with_sources` | float | Доля ответов с источниками (0–1) |
| `control_metrics.avg_latency_ms` | int | Среднее время ответа |
| `answer_metrics.useful_rate` | float | Доля полезных ответов (0–1) |
| `answer_metrics.rated_answers` | int | Количество оценённых ответов |
| `answer_metrics.flagged_for_review` | int | На проверке |
| `answer_metrics.open_questions` | int | Открытые вопросы |
| `logs[]` | array | Журнал событий |

> Внутренняя реализация: агрегирует данные из OCR Service (confidence), RAG Service (score), Query Service (feedback, latency), логов сервисов.

---

## 11. Администрирование

### GET /admin/users

Список пользователей в формате UI.

**Параметры query**: `role`, `search`, `limit`, `offset`.

**Ответ `200`**:

```json
{
  "items": [
    {
      "user_id": "u-001",
      "full_name": "Иванов Сергей Петрович",
      "position": "Инженер-конструктор",
      "login": "ivanov",
      "role": "engineer",
      "status": "active",
      "last_login_at": "2026-05-01T08:20:00Z"
    }
  ],
  "total": 1
}
```

### PATCH /admin/users/{user_id}

Изменение роли пользователя.

**Запрос**:

```json
{
  "role": "knowledge_admin"
}
```

**Ответ `200`**:

```json
{
  "user_id": "u-001",
  "role": "knowledge_admin",
  "audit_log_id": "audit-001"
}
```

### GET /admin/audit-log

Административный журнал.

**Параметры query**: `user_id`, `action`, `date_from`, `date_to`, `limit`, `offset`.

**Ответ `200`**:

```json
{
  "events": [
    {
      "event_id": "evt-123",
      "user_id": "u-001",
      "user_name": "Иванов И.И.",
      "action": "role.change",
      "resource_type": "user",
      "resource_id": "u-002",
      "details": {"old_role": "engineer", "new_role": "knowledge_admin"},
      "timestamp": "2026-04-27T11:00:00Z"
    }
  ],
  "total": 150
}
```

> Внутренняя реализация: `GET /admin/users` → прокси `GET /users` из Auth Service, маппинг полей. `PATCH /admin/users/{id}` → `PATCH /users/{id}` в Auth Service. `GET /admin/audit-log` → `GET /audit` из Auth Service.