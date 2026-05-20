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

**Важно:** идентификатор задачи (`task_id`) генерирует Оркестратор и передаёт в запросе. OCR-сервис использует его для всех последующих операций (статус, результат).

**Вход:** ссылка на файл в MinIO.

**Запрос:**

```json
{
  "task_id": "task-8a3f2b",
  "version_id": "c4b9f2d3-...",
  "file_key": "file-abc123",
  "options": {
    "extract_tables": true,
    "extract_images": true,
    "extract_classification": true
  }
}
```

| Поле | Тип | Обязательность | Описание |
| ---- | --- | -------------- | -------- |
| `task_id` | string | Да | Идентификатор задачи (генерируется Оркестратором) |
| `version_id` | string | Да | ID версии документа (ссылка на `document_versions`) |
| `file_key` | string | Да | Ключ файла в MinIO |
| `options` | object | Нет | Параметры обработки |
| `options.extract_tables` | bool | Нет | Извлекать таблицы в структурированном виде |
| `options.extract_images` | bool | Нет | Извлекать изображения в MinIO |
| `options.extract_classification` | bool | Нет | Извлекать коды классификации (МКС, ОКСТУ, УДК) |

**Ответ `202`**:

```json
{
  "task_id": "task-8a3f2b",
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

| Поле               | Тип    | Описание                                                |
| ------------------ | ------ | ------------------------------------------------------- |
| `task_id`          | string | ID задачи                                               |
| `status`           | string | Статус: `accepted`, `processing`, `completed`, `failed` |
| `progress_percent` | int    | Процент выполнения (0–100)                              |
| `pages_processed`  | int    | Обработано страниц                                      |
| `pages_total`      | int    | Всего страниц                                           |
| `avg_confidence`   | float  | Средняя уверенность распознавания                       |
| `step`             | string | **Текущий шаг** обработки (см. таблицу ниже)            |
| `step_detail`      | string | Детализация шага (человекочитаемая)                     |
| `started_at`       | string | Время начала обработки                                  |
| `completed_at`     | string | Время завершения (null, если не завершён)               |

**Значения `step`:**

| `step`              | Описание                          |
| ------------------- | --------------------------------- |
| `downloading`       | Скачивание PDF из MinIO           |
| `splitting`         | Разбивка на страницы              |
| `ocr_pages`         | Распознавание страниц             |
| `extracting_tables` | Извлечение таблиц                 |
| `extracting_images` | Извлечение и загрузка изображений |
| `classifying`       | Классификация (МКС, ОКСТУ, УДК)   |
| `aggregating`       | Сборка итогового JSON             |

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
        "clause": "1",
        "title": "Общие положения",
        "level": 1,
        "type": "section",
        "content": {
          "text": "Настоящий стандарт..."
        },
        "page": 1,
        "bbox": "72,100,522,324",
        "subsections": []
      },
      {
        "title": "Таблица 1 — Параметры",
        "level": 2,
        "type": "table",
        "content": {
          "headers": ["Параметр", "Значение"],
          "rows": [["Толщина", "12 мм"], ["Длина", "6000 мм"]]
        },
        "page": 5,
        "bbox": "72,280,552,400",
        "subsections": []
      },
      {
        "title": "Рисунок 1 — Стойка установочная",
        "type": "image",
        "content": {
          "image_id": "img-001",
          "file_key": "b3a8f1c2/v1/img/fig1.png",
          "width": 800,
          "height": 600
        },
        "page": 8,
        "bbox": "100,90,500,390",
        "subsections": []
      }
    ]
  },
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021",
    "year": "1981"
  },
  "document_reference": [
    {
      "target_doc_code": "ГОСТ Р 54321-80",
      "reference_type": "normative",
      "context": "Раздел 3, пункт 3.2",
      "current_status": "действующий"
    }
  ],
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

| Поле                                   | Тип    | Описание                                                             |
| -------------------------------------- | ------ | -------------------------------------------------------------------- |
| `document_id`                          | string | UUID документа                                                       |
| `version_id`                           | string | UUID версии                                                          |
| `structure`                            | object | Распознанная структура: тип, заголовок, секции                       |
| `structure.type`                       | string | Тип документа: `normative`, `technical` и др.                        |
| `structure.title`                      | string | Заголовок документа                                                  |
| `structure.sections[]`                 | array  | Массив секций (заголовки, таблицы, изображения, формулы)             |
| `structure.sections[].clause`          | string | Номер пункта/раздела (напр. `"1"`, `"3.2"`)                         |
| `structure.sections[].title`           | string | Заголовок секции                                                     |
| `structure.sections[].level`           | int    | Уровень вложенности (1 — верхний)                                    |
| `structure.sections[].type`            | string | Тип элемента: `section`, `table`, `image`, `formula`                 |
| `structure.sections[].content` | JSONB | Содержимое (зависит от `type`: текст, строки таблицы, file_key и т.д.) |
| `structure.sections[].page`            | int    | Номер страницы                                                       |
| `structure.sections[].bbox`            | object | Координаты блока: `x`, `y`, `width`, `height`                        |
| `classification`                       | object | Извлечённые коды классификации                                       |
| `document_reference[]`                 | array  | Ссылки на другие нормативные/технические документы                   |
| `document_reference[].target_doc_code` | string | Код документа, на который ссылаются                                  |
| `document_reference[].reference_type`  | string | Тип ссылки: `normative`, `informative`, `replaces`                   |
| `document_reference[].context`         | string | Контекст ссылки (раздел/пункт)                                       |
| `document_reference[].current_status`  | string | Статус целевого документа (действующий, заменён и т.д.)              |
| `quality`                              | object | Общая оценка качества + `per_page` — детализация по страницам        |
| `quality.per_page[].status`            | string | `ok`, `low_confidence`, `failed`                                     |
| `quality.per_page[].error`             | string | Код ошибки страницы (только при `status: failed`)                    |
| `errors`                               | array  | Массив некритичных ошибок и предупреждений                           |
| `status`                               | string | `completed`, `failed`                                                |

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

| Поле               | Тип    | Описание                         |
| ------------------ | ------ | -------------------------------- |
| `task_id`          | string | ID задачи                        |
| `version_id`       | string | ID версии документа              |
| `status`           | string | Статус: `accepted`, `processing` |
| `progress_percent` | int    | Процент выполнения               |
| `pages_processed`  | int    | Обработано страниц               |
| `pages_total`      | int    | Всего страниц                    |
| `started_at`       | string | Время начала обработки           |

---

### Коды ошибок OCR-сервиса

| `error.code`         | HTTP | Описание                         |
| -------------------- | ---- | -------------------------------- |
| `FILE_NOT_FOUND`     | 404  | Файл не найден в MinIO           |
| `FILE_TOO_LARGE`     | 413  | PDF > 500 MB / > 2000 страниц    |
| `UNSUPPORTED_FORMAT` | 415  | Не PDF / не изображение          |
| `OCR_FAILED`         | 500  | Критическая ошибка распознавания |
| `STORAGE_ERROR`      | 502  | Ошибка доступа к MinIO           |
| `TASK_NOT_FOUND`     | 404  | task_id не существует или протух |
| `TASK_EXPIRED`       | 410  | Результат удалён (старше N дней) |

---

### Сводная информация о доступе к данным

| Аспект      | Значение                               |
| ----------- | -------------------------------------- |
| Доступ к БД | **Нет** (полная изоляция)              |
| Пайплайн    | 1 (Формирование документа), Этап 1     |
| Вход        | Ссылка на файл в MinIO                 |
| Выход       | JSON-контейнер со структурой документа |

---

### Резюме: что даёт такая архитектура

| Свойство                             | Как достигнуто                                                                          |
| ------------------------------------ | --------------------------------------------------------------------------------------- |
| **Автономность OCR-сервиса**         | Сам ходит в MinIO, сам складывает изображения, сам управляет своим стейтом              |
| **Тестируемость без инфраструктуры** | Storage, OCR, State — адаптеры. Тесты на фейках, без внешних зависимостей (MinIO, MemoryCache и т.д.) |
| **Управляемость Оркестратором**      | 3 эндпоинта (`process`, `status`, `result`) + `engines`; JSON-контейнер как чёрный ящик |
| **Большие документы**                | Celery-воркер вне API-процесса, параллелизм страниц, потоковая загрузка из MinIO        |
| **Готовые ссылки на изображения**    | OCR сам выгружает в MinIO, отдаёт `file_key` в ответе                                   |
| **Независимая разработка**           | Другая группа может писать и тестировать OCR-сервис, имея только контракт API           |
