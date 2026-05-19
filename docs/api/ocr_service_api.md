## API OCR Service / Парсинг (ocr-service:8088)

Сервис распознавания и парсинга документов. Соответствует этапу **«Парсинг» Пайплайна 1 (Формирование документа)**.

*Внутренний сервис. Не предназначен для прямого вызова из frontend.*

**Особенность:** полная изоляция от базы данных — сервис не имеет доступа к БД.

**Базовый URL (внутренний)**: `http://127.0.0.1:8088/api/v1`

---

### Контракт API (финальный)

#### Формат ответа

Успех — данные возвращаются напрямую.

При ошибке:

```json
{
  "error": {
    "code": "OCR_FAILED",
    "message": "Описание ошибки",
    "details": {}
  }
}
```

---

### POST /ocr/process — запуск обработки

Асинхронная обработка PDF/изображений: распознавание текста (OCR), очистка, нормализация, выделение структуры, извлечение таблиц/изображений и классификация.

**Важно:** длительные операции (более 50 страниц) обрабатываются асинхронно (`202` + `task_id`). Оркестратор опрашивает статус и забирает JSON-контейнер с результатом.

**Вход:** ссылка на файл в MinIO.

**Запрос** (без изменений относительно предыдущей версии):

```json
{
  "version_id": "c4b9f2d3-...",
  "file_id": "file-abc123",
  "options": {
    "extract_tables": true,
    "extract_images": true,
    "extract_classification": true
  }
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `version_id` | string | Да | ID версии документа (ссылка на `document_versions`) |
| `file_id` | string | Да | ID файла в MinIO |
| `options` | object | Нет | Параметры обработки |
| `options.extract_tables` | bool | Нет | Извлекать таблицы в структурированном виде |
| `options.extract_images` | bool | Нет | Извлекать изображения в MinIO |
| `options.extract_classification` | bool | Нет | Извлекать коды классификации (МКС, ОКСТУ, УДК) |

**Ответ `202`**:

```json
{
  "task_id": "ocr-task-001",
  "status": "accepted",
  "version_id": "c4b9f2d3-...",
  "estimated_completion": "2026-05-15T10:02:00Z"
}
```

---

### GET /ocr/process/{task_id}/status — опрос статуса

Оркестратор опрашивает до статуса `completed`.

**Ответ `200`** (без изменений в основных полях):

```json
{
  "task_id": "ocr-task-001",
  "status": "processing",
  "progress_percent": 45,
  "pages_processed": 5,
  "pages_total": 12,
  "avg_confidence": 0.94,
  "step": "ocr_pages",
  "step_detail": "8 / 12 pages done",
  "started_at": "2026-05-15T10:00:05Z",
  "completed_at": null
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `task_id` | string | ID задачи |
| `status` | string | Статус: `accepted`, `processing`, `completed`, `failed` |
| `progress_percent` | int | Процент выполнения (0–100) |
| `pages_processed` | int | Обработано страниц |
| `pages_total` | int | Всего страниц |
| `avg_confidence` | float | Средняя уверенность распознавания |
| `step` | string | **Текущий шаг** обработки (см. таблицу ниже) |
| `step_detail` | string | Детализация шага (человекочитаемая) |
| `started_at` | string | Время начала обработки |
| `completed_at` | string | Время завершения (null, если не завершён) |

**Значения `step`:**

| `step` | Описание |
|---|---|
| `downloading` | Скачивание PDF из MinIO |
| `splitting` | Разбивка на страницы |
| `ocr_pages` | Распознавание страниц |
| `extracting_tables` | Извлечение таблиц |
| `extracting_images` | Извлечение и загрузка изображений |
| `classifying` | Классификация (МКС, ОКСТУ, УДК) |
| `aggregating` | Сборка итогового JSON |

---

### GET /ocr/process/{task_id}/result — итоговый JSON

Получение JSON-контейнера с результатом парсинга. Вызывается Оркестратором после `status: completed`.

> **Важно:** сервис **не пишет в БД** — отдаёт JSON тому, кто вызвал. JSON-формат известен только сервису Парсинга и downstream-сервисам (Валидация, Реестр). Изображения — только ссылки (сами файлы загружены в MinIO сервисом).

**Ответ `200`**:

```json
{
  "document_id": "b3a8f1c2-...",
  "version_id": "c4b9f2d3-...",
  "structure": {
    "type": "normative",
    "title": "ГОСТ Р 12345-77",
    "sections": [
      {
        "heading": "1. Общие положения",
        "content": "Настоящий стандарт...",
        "page": 1,
        "subsections": []
      }
    ],
    "tables": [
      {
        "page": 5,
        "caption": "Таблица 1 — Параметры",
        "headers": ["Параметр", "Значение"],
        "rows": [["Толщина", "12 мм"], ["Длина", "6000 мм"]]
      }
    ],
    "images": [
      {
        "image_id": "img-001",
        "page": 8,
        "file_path": "b3a8f1c2/v1/img/fig1.png",
        "caption": "Рисунок 1 — Стойка установочная",
        "width": 800,
        "height": 600
      }
    ]
  },
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021",
    "year": "1981"
  },
  "quality": {
    "confidence": 0.94,
    "pages_processed": 12,
    "pages_failed": 0,
    "per_page": [
      { "page": 1, "confidence": 0.97, "status": "ok" },
      { "page": 2, "confidence": 0.88, "status": "low_confidence" },
      { "page": 7, "confidence": 0.0,  "status": "failed", "error": "empty_page" }
    ]
  },
  "errors": [
    {
      "stage": "ocr",
      "page": 7,
      "code": "EMPTY_PAGE",
      "message": "Страница не содержит текста",
      "severity": "warning"
    }
  ],
  "status": "completed"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | string | UUID документа |
| `version_id` | string | UUID версии |
| `structure` | object | Распознанная структура: тип, заголовок, секции, таблицы, изображения |
| `classification` | object | Извлечённые коды классификации |
| `quality` | object | Общая оценка качества + `per_page` — детализация по страницам |
| `quality.per_page[].status` | string | `ok`, `low_confidence`, `failed` |
| `quality.per_page[].error` | string | Код ошибки страницы (только при `status: failed`) |
| `errors` | array | Массив некритичных ошибок и предупреждений |
| `status` | string | `completed`, `failed` |

---

### GET /ocr/processes

Список текущих (активных) процессов обработки документов.

**Ответ `200`**:

```json
{
  "processes": [
    {
      "task_id": "ocr-task-001",
      "version_id": "c4b9f2d3-...",
      "status": "processing",
      "progress_percent": 45,
      "pages_processed": 5,
      "pages_total": 12,
      "started_at": "2026-05-15T10:00:05Z"
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `task_id` | string | ID задачи |
| `version_id` | string | ID версии документа |
| `status` | string | Статус: `accepted`, `processing` |
| `progress_percent` | int | Процент выполнения |
| `pages_processed` | int | Обработано страниц |
| `pages_total` | int | Всего страниц |
| `started_at` | string | Время начала обработки |

---

### Коды ошибок OCR-сервиса

| `error.code` | HTTP | Описание |
|---|---|---|
| `FILE_NOT_FOUND` | 404 | Файл не найден в MinIO |
| `FILE_TOO_LARGE` | 413 | PDF > 500 MB / > 2000 страниц |
| `UNSUPPORTED_FORMAT` | 415 | Не PDF / не изображение |
| `OCR_FAILED` | 500 | Критическая ошибка распознавания |
| `STORAGE_ERROR` | 502 | Ошибка доступа к MinIO |
| `TASK_NOT_FOUND` | 404 | task_id не существует или протух |
| `TASK_EXPIRED` | 410 | Результат удалён (старше N дней) |

---

### Сводная информация о доступе к данным

| Аспект | Значение |
|---|---|
| Доступ к БД | **Нет** (полная изоляция) |
| Пайплайн | 1 (Формирование документа), Этап 1 |
| Вход | Ссылка на файл в MinIO |
| Выход | JSON-контейнер со структурой документа |

---

### Резюме: что даёт такая архитектура

| Свойство | Как достигнуто |
|---|---|
| **Автономность OCR-сервиса** | Сам ходит в MinIO, сам складывает изображения, сам управляет своим стейтом |
| **Тестируемость без инфраструктуры** | Storage, OCR, State — адаптеры. Тесты на фейках, без Redis/MinIO |
| **Управляемость Оркестратором** | 3 эндпоинта (`process`, `status`, `result`) + `engines`; JSON-контейнер как чёрный ящик |
| **Большие документы** | Celery-воркер вне API-процесса, параллелизм страниц, потоковая загрузка из MinIO |
| **Готовые ссылки на изображения** | OCR сам выгружает в MinIO, отдаёт `file_path` в ответе |
| **Независимая разработка** | Другая группа может писать и тестировать OCR-сервис, имея только контракт API |


