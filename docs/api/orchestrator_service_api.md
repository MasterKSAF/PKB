## API Orchestrator Service

Единая точка входа для публичного API Нейроассистента ПКБ.

**Базовый URL**: `https://{host}/api/v1`

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
  "status": "queued",
  "task_id": "task-ocr-001",
  "created_at": "2026-04-27T10:00:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | string | ID документа |
| `status` | string | Статус: `queued`, `processing`, `processed`, `error` |
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
  "documents": [
    {
      "document_id": "doc-8a3f2b",
      "filename": "21900M2_spec.pdf",
      "document_type": "specification",
      "status": "processing",
      "pages_total": 12,
      "pages_processed": 5,
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T10:02:00Z"
    }
  ],
  "total": 18,
  "limit": 20,
  "offset": 0
}
```

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
  "results": [
    {
      "fragment_id": "frg-123abc",
      "document_id": "doc-norm-001",
      "document_title": "Правила классификации и постройки морских судов. Часть I",
      "page_number": 42,
      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм...",
      "coordinates": {
        "x": 120, "y": 350, "width": 400, "height": 60
      },
      "score": 0.92,
      "document_type": "normative"
    }
  ],
  "total_found": 3,
  "processing_time_ms": 450
}
```

**Ошибки**: `400` — пустой запрос.

### GET /search

Быстрый GET-вариант поиска.

**Параметры query**: `q`, `document_id`, `page`, `limit`

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
      "score": 0.92
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

Запуск сопоставления нормы и проектного документа.

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
  }
}
```