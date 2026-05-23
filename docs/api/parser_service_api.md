## API Parser Service (parser-service:8087)

Сервис парсинга цифровых PDF/DOC-документов (без OCR). Соответствует этапу **«Parsing» Пайплайна 1 (Формирование документа)**.

*Внутренний сервис. Не предназначен для прямого вызова из frontend.*

**Особенность:** полная изоляция от базы данных — сервис не имеет доступа к БД.

**Базовый URL (внутренний)**: `http://127.0.0.1:8087/api/v1`

---

### Контракт API (финальный)

#### Формат ответа

Успех — данные возвращаются напрямую.

При ошибке:

```json
{
  "error": {
    "code": "PARSER_FAILED",
    "message": "Описание ошибки",
    "details": {}
  }
}
```

---

### POST /parser/process — запуск обработки

Асинхронный парсинг цифрового PDF/DOC: извлечение текста, структуры, таблиц, изображений и классификация.

**Важно:** идентификатор задачи (`task_id`) генерирует Оркестратор и передаёт в запросе. Parser-сервис использует его для всех последующих операций (статус, результат).

**Вход:** ссылка на файл в MinIO.

**Запрос:**

```json
{
  "task_id": "task-9b4c1d",
  "version_id": "d5e0f3a2-...",
  "file_key": "file-def456",
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
  "task_id": "task-9b4c1d",
  "status": "accepted",
  "version_id": "d5e0f3a2-...",
  "estimated_completion": "2026-05-15T10:02:00Z"
}
```

---

### POST /parser/preview — быстрый предпросмотр

Синхронный/полусинхронный предпросмотр первых N страниц документа. Бинарные объекты (изображения) **не сохраняются** в MinIO, `file_key` в ответе отсутствует.

**Запрос:**

```json
{
  "task_id": "task-9b4c1d",
  "version_id": "d5e0f3a2-...",
  "file_key": "file-def456",
  "max_pages": 3,
  "options": {
    "extract_tables": false,
    "extract_images": false,
    "extract_classification": false
  }
}
```

| Поле | Тип | По умолчанию | Обязательность | Описание |
| ---- | --- | ------------ | -------------- | -------- |
| `task_id` | string | — | Да | Идентификатор задачи (генерируется Оркестратором) |
| `version_id` | string | — | Да | ID версии документа |
| `file_key` | string | — | Да | Ключ файла в MinIO |
| `max_pages` | int | `3` | Нет | Количество страниц для предпросмотра |
| `options` | object | — | Нет | Параметры обработки |

**Ответ `200`** (предпросмотр):

```json
{
  "task_id": "task-9b4c1d",
  "version_id": "d5e0f3a2-...",
  "preview": true,
  "max_pages": 3,
  "blocks": [
    {
      "block_id": "block-001",
      "type": "section",
      "clause": "1",
      "title": "Общие положения",
      "level": 1,
      "content": {
        "text": "Настоящий стандарт..."
      },
      "page": 1,
      "bbox": "72,100,522,324"
    }
  ],
  "quality": {
    "confidence": 0.95,
    "pages_processed": 3,
    "pages_failed": 0,
    "per_page": []
  },
  "status": "completed"
}
```

> **Важно:** в режиме предпросмотра:
> - Поле `file_key` **отсутствует** у блоков с типом `image`
> - Бинарные объекты **не сохраняются** в MinIO
> - Поля `classification` и `document_reference` могут отсутствовать или быть неполными

---

### GET /parser/process/{task_id}/status — статус обработки (longpoll)

Оркестратор ожидает результат через longpoll.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
| -------- | --- | ------------ | -------- |
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при изменении статуса (прогресс / завершение) или по таймауту. |

**Ответ `200`**:

```json
{
  "task_id": "parser-task-001",
  "status": "processing",
  "progress_percent": 45,
  "pages_processed": 5,
  "pages_total": 12,
  "avg_confidence": 0.94,
  "step": "parsing_pages",
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
| `avg_confidence`   | float  | Средняя уверенность извлечения                          |
| `step`             | string | Текущий шаг обработки (см. таблицу ниже)                |
| `step_detail`      | string | Детализация шага (человекочитаемая)                     |
| `started_at`       | string | Время начала обработки                                  |
| `completed_at`     | string | Время завершения (null, если не завершён)               |

**Значения `step`:**

| `step`              | Описание                          |
| ------------------- | --------------------------------- |
| `downloading`       | Скачивание PDF/DOC из MinIO       |
| `splitting`         | Разбивка на страницы              |
| `parsing_pages`     | Парсинг цифровых страниц          |
| `extracting_tables` | Извлечение таблиц                 |
| `extracting_images` | Извлечение и загрузка изображений |
| `classifying`       | Классификация (МКС, ОКСТУ, УДК)   |
| `aggregating`       | Сборка итогового JSON             |

---

### GET /parser/process/{task_id}/result — итоговый JSON

Получение JSON-контейнера с результатом парсинга. Вызывается Оркестратором после `status: completed`.

> **Важно:** сервис **не пишет в БД** — отдаёт JSON тому, кто вызвал. JSON-формат известен только сервису Parser и downstream-сервисам (Validation, Registry). Изображения — только ссылки (сами файлы загружены в MinIO сервисом).

**Ответ `200`**:

```json
{
  "task_id": "task-9b4c1d",
  "version_id": "d5e0f3a2-...",
  "blocks": [
    {
      "block_id": "block-001",
      "type": "section",
      "clause": "1",
      "title": "Общие положения",
      "level": 1,
      "content": {
        "text": "Настоящий стандарт..."
      },
      "page": 1,
      "bbox": "72,100,522,324"
    },
    {
      "block_id": "block-002",
      "type": "table",
      "title": "Таблица 1 — Параметры",
      "level": 2,
      "content": {
        "headers": ["Параметр", "Значение"],
        "rows": [["Толщина", "12 мм"], ["Длина", "6000 мм"]]
      },
      "page": 5,
      "bbox": "72,280,552,400"
    },
    {
      "block_id": "block-003",
      "type": "image",
      "title": "Рисунок 1 — Стойка установочная",
      "content": {
        "image_id": "img-001",
        "file_key": "b3a8f1c2/v1/img/fig1.png",
        "width": 800,
        "height": 600
      },
      "page": 8,
      "bbox": "100,90,500,390"
    }
  ],
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
      "stage": "parsing",
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
| `task_id`                              | string | ID задачи оркестратора                                               |
| `version_id`                           | string | UUID версии                                                          |
| `blocks`                               | array  | **Плоский** массив блоков (без иерархии, без subsections/parent_id)  |
| `blocks[].block_id`                    | string | Уникальный идентификатор блока                                       |
| `blocks[].type`                        | string | Тип элемента: `section`, `table`, `image`, `formula`                 |
| `blocks[].clause`                      | string | Номер пункта/раздела (напр. `"1"`, `"3.2"`)                         |
| `blocks[].title`                       | string | Заголовок блока                                                      |
| `blocks[].level`                       | int    | Уровень вложенности (1 — верхний)                                    |
| `blocks[].content`                     | object | Содержимое (зависит от `type`: текст, строки таблицы, file_key и т.д.) |
| `blocks[].page`                        | int    | Номер страницы                                                       |
| `blocks[].bbox`                        | string | Координаты блока в формате `"x1,y1,x2,y2"`                          |
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

### GET /parser/processes

Список текущих (активных) процессов обработки документов.

**Ответ `200`**:

```json
{
  "processes": [
    {
      "task_id": "parser-task-001",
      "version_id": "d5e0f3a2-...",
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

### Коды ошибок Parser-сервиса

| `error.code`         | HTTP | Описание                         |
| -------------------- | ---- | -------------------------------- |
| `FILE_NOT_FOUND`     | 404  | Файл не найден в MinIO           |
| `FILE_TOO_LARGE`     | 413  | PDF/DOC > 500 MB / > 2000 страниц |
| `UNSUPPORTED_FORMAT` | 415  | Не PDF / не DOC                  |
| `PARSER_FAILED`      | 500  | Критическая ошибка парсинга      |
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

| Свойство                               | Как достигнуто                                                                          |
| -------------------------------------- | --------------------------------------------------------------------------------------- |
| **Автономность Parser-сервиса**        | Сам ходит в MinIO, сам складывает изображения, сам управляет своим стейтом              |
| **Тестируемость без инфраструктуры**   | Storage, Parser, State — адаптеры. Тесты на фейках, без внешних зависимостей (MinIO, MemoryCache и т.д.) |
| **Управляемость Оркестратором**        | 4 эндпоинта (`process`, `preview`, `status`, `result`); JSON-контейнер как чёрный ящик  |
| **Большие документы**                  | Celery-воркер вне API-процесса, параллелизм страниц, потоковая загрузка из MinIO        |
| **Готовые ссылки на изображения**      | Parser сам выгружает в MinIO, отдаёт `file_key` в ответе                                |
| **Независимая разработка**             | Другая группа может писать и тестировать Parser-сервис, имея только контракт API        |
