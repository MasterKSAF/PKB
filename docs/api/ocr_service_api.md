## API OCR Service (ocr-service:8088)

Сервис OCR-распознавания отсканированных изображений и фотографий документов. Соответствует этапу **«Parsing» Пайплайна 1 (Формирование документа)**.

*Внутренний сервис. Не предназначен для прямого вызова из frontend.*

**Особенность:** полная изоляция от базы данных — сервис не имеет доступа к БД.

> **Отличие от Parser-сервиса:** OCR-сервис обрабатывает сканы, изображения (JPEG, PNG, TIFF) и PDF без текстового слоя. Использует движок оптического распознавания символов (Tesseract/внутренний). Parser-сервис, напротив, извлекает текстовый слой из цифровых PDF, DOC, DOCX. Оба сервиса имеют **единый формат выходного JSON** (`raw_ocr_v4`), что позволяет Converter-validator работать с любым из них без изменений.

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

Асинхронная обработка отсканированных изображений/фотографий: распознавание текста (OCR), очистка, нормализация, выделение структуры, извлечение таблиц/изображений и классификация.

**Важно:** идентификатор задачи (`task_id`) генерирует Оркестратор и передаёт в запросе. OCR-сервис использует его для всех последующих операций (статус, результат).

**Вход:** ссылка на файл в MinIO.

**Запрос:**

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "file_key": "file-abc123",
  "options": {
    "extract_tables": true,
    "extract_images": true
  }
}
```

| Поле | Тип | Обязательность | Описание |
| ---- | --- | -------------- | -------- |
| `task_id` | bigint | Да | Идентификатор задачи (генерируется Оркестратором) |
| `version_id` | bigint | Да | ID версии документа |
| `file_key` | string | Да | Ключ файла в MinIO |
| `options` | object | Нет | Параметры обработки |
| `options.extract_tables` | bool | Нет | Извлекать таблицы в структурированном виде |
| `options.extract_images` | bool | Нет | Извлекать изображения в MinIO |

**Ответ `202`**:

```json
{
  "task_id": 420000,
  "status": "accepted",
  "version_id": 420001,
  "estimated_completion": "2026-05-15T10:02:00Z"
}
```

---

### POST /ocr/preview — быстрый предпросмотр

Синхронный/полусинхронный предпросмотр первых N страниц документа. Бинарные объекты (изображения) **не сохраняются** в MinIO, `image_key` в ответе отсутствует.

**Запрос:**

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "file_key": "file-abc123",
  "max_pages": 3,
  "options": {
    "extract_tables": false,
    "extract_images": false
  }
}
```

| Поле | Тип | По умолчанию | Обязательность | Описание |
| ---- | --- | ------------ | -------------- | -------- |
| `task_id` | bigint | — | Да | Идентификатор задачи (генерируется Оркестратором) |
| `version_id` | bigint | — | Да | ID версии документа |
| `file_key` | string | — | Да | Ключ файла в MinIO |
| `max_pages` | int | `3` | Нет | Количество страниц для предпросмотра |
| `options` | object | — | Нет | Параметры обработки |

**Ответ `200`** (предпросмотр):

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "preview": true,
  "max_pages": 3,
  "metadata": {
    "schema": "raw_ocr_v4",
    "created_at": "2026-05-17T09:15:00Z"
  },
  "document": {
    "source": {
      "file_name": "GOST_20868-81_scan.pdf",
      "page_count": 2
    }
  }
}
```

> **Полный формат данных** (схема `raw_ocr_v4`) — см.  
> [`docs/schema/schema_parser_result.json`](../schema/schema_parser_result.json)

> **Важно:** в режиме предпросмотра:
> - Поле `image_key` **отсутствует** у блоков (не сохраняется в MinIO)
> - Поле `font` (объект) может отсутствовать у text-блоков
> - Отсутствует детализация `quality.per_page`
> - Возвращаются только первые N страниц документа

---

### GET /ocr/process/{task_id}/status — статус обработки (longpoll)

Оркестратор ожидает результат через longpoll.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
| -------- | --- | ------------ | -------- |
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при изменении статуса (прогресс / завершение) или по таймауту. |

**Ответ `200`** (без изменений в основных полях):

```json
{
  "task_id": 420000,
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
| `task_id`          | bigint | ID задачи                                               |
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
| `downloading`       | Скачивание изображения из MinIO           |
| `splitting`         | Разбивка на страницы              |
| `ocr_pages`         | Распознавание страниц             |
| `extracting_tables` | Извлечение таблиц                 |
| `extracting_images` | Извлечение и загрузка изображений |
| `aggregating`       | Сборка итогового JSON             |

---

### GET /ocr/process/{task_id}/result — итоговый JSON

Получение JSON-контейнера с результатом OCR-распознавания. Вызывается Оркестратором после `status: completed`.

> **Важно:** сервис **не пишет в БД** — отдаёт JSON тому, кто вызвал. JSON-формат известен только сервису OCR и downstream-сервисам (Validation, Registry). Изображения — только ссылки (сами файлы загружены в MinIO сервисом).

> ⚠️ **Полный формат данных:** [`docs/schema/schema_parser_result.json`](../schema/schema_parser_result.json) (схема `raw_ocr_v4`) — **обязательно** смотри этот файл, здесь приведён только сокращённый пример.

**Ответ `200`**:

```json
{
  "task_id": 420000,
  "version_id": 420001,
  "metadata": {
    "schema": "raw_ocr_v4",
    "created_at": "2026-05-17T09:15:00Z",
    "parser": { "name": "docling", "version": "2.1.0", "ocr_engine": "paddleocr", "ocr_fallback": false }
  },
  "document": {
    "source": { "file_name": "GOST_20868-81_scan.pdf", "file_hash_sha256": "...", "page_count": 2 },
    "block": [
      {
        "number": 1,
        "type": "heading",
        "heading_level": 1,
        "page": 1,
        "bbox": [10.0, 20.0, 200.0, 28.0],
        "content": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
        "font": { "size": 14.0, "color": "#000000", "bold": true, "italic": false, "underline": false }
      }
    ]
  },
  "quality": { "confidence": 0.94, "pages_processed": 12, "pages_failed": 0 },
  "errors": [],
  "status": "completed"
}

| Поле                                         | Тип    | Описание                                                             |
| -------------------------------------------- | ------ | -------------------------------------------------------------------- |
| `task_id`                                    | bigint | ID задачи оркестратора                                               |
| `version_id`                                 | bigint | ID версии                                                            |
| `metadata`                                   | object | Метаданные обработки                                                 |
| `metadata.schema`                            | string | Идентификатор схемы (напр. `"raw_ocr_v4"`)                          |
| `metadata.created_at`                        | string | Время создания результата (ISO 8601)                                 |
| `metadata.parser`                            | object | Информация о парсере                                                 |
| `metadata.parser.name`                       | string | Название парсера (напр. `"docling"`)                                 |
| `metadata.parser.version`                    | string | Версия парсера (напр. `"2.1.0"`)                                    |
| `metadata.parser.ocr_engine`                 | string | Используемый OCR-движок или `null`                                   |
| `metadata.parser.ocr_fallback`               | bool   | Флаг использования fallback-OCR                                      |
| `document`                                   | object | Контейнер документа с исходными данными и страницами                 |
| `document.source`                            | object | Информация об исходном файле                                         |
| `document.source.file_name`                  | string | Имя исходного файла                                                  |
| `document.source.file_hash_sha256`           | string | SHA256-хеш исходного файла                                           |
| `document.source.page_count`                 | int    | Общее количество страниц в документе                                 |
| `document.pages`                             | array  | Массив страниц документа (только геометрия)                          |
| `document.pages[].page`                      | int    | Номер страницы (начиная с 1)                                         |
| `document.pages[].width`                     | float  | Ширина страницы в мм                                                 |
| `document.pages[].height`                    | float  | Высота страницы в мм                                                 |
| `document.block`                             | array  | **Единый** массив всех элементов в reading order (сквозная нумерация)|
| `block[].number`                             | int    | Порядковый номер элемента в reading order                            |
| `block[].type`                               | string | Тип элемента: `headerFooter`, `heading`, `paragraph`, `text_block`, `list`, `table`, `image`, `caption`, `formula` |
| `block[].page`                               | int    | Номер страницы                                                       |
| `block[].bbox`                               | array  | Координаты `[left, bottom, right, top]` в пикселях (сырые, px)       |
| `block[].font`                               | object | Объект шрифта: `{ size: float, color: string, bold: bool, italic: bool, underline: bool }` |
| `quality`                                    | object | Общая оценка качества + `per_page` — детализация по страницам        |
| `quality.per_page[].status`                  | string | `ok`, `low_confidence`, `failed`                                     |
| `quality.per_page[].error`                   | string | Код ошибки страницы (только при `status: failed`)                    |
| `errors`                                     | array  | Массив некритичных ошибок и предупреждений                           |
| `status`                                     | string | `completed`, `failed`                                                |

---

### GET /ocr/processes

Список текущих (активных) процессов обработки документов.

**Ответ `200`**:

```json
{
  "processes": [
    {
          "task_id": 420000,
          "version_id": 420001,
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
| `task_id`          | bigint | ID задачи                        |
| `version_id`       | bigint | ID версии документа              |
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
| `FILE_TOO_LARGE`     | 413  | Изображение > 500 MB / > 2000 страниц |
| `UNSUPPORTED_FORMAT` | 415  | Не изображение (не scan/image)   |
| `ENGINE_UNAVAILABLE` | 503  | Запрошенный OCR-движок недоступен |
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
| **Управляемость Оркестратором**      | 4 эндпоинта (`process`, `preview`, `status`, `result`); JSON-контейнер как чёрный ящик |
| **Большие документы**                | Celery-воркер вне API-процесса, параллелизм страниц, потоковая загрузка из MinIO        |
| **Готовые ссылки на изображения**    | OCR сам выгружает в MinIO, отдаёт `image_key` в ответе                                   |
| **Независимая разработка**           | Другая группа может писать и тестировать OCR-сервис, имея только контракт API           |
