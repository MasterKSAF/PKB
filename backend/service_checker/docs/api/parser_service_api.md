## API Parser Service (parser-service:8087)

Сервис парсинга цифровых PDF/DOC-документов (без OCR). Соответствует этапу **«Parsing» Пайплайна 1 (Формирование документа)**.

*Внутренний сервис. Не предназначен для прямого вызова из frontend.*

**Особенность:** полная изоляция от базы данных — сервис не имеет доступа к БД.

> **Отличие от OCR-сервиса:** Parser-сервис работает только с цифровыми документами (PDF с текстовым слоем, DOC, DOCX). Не использует OCR-движок, а извлекает готовый текстовый слой и структуру документа. OCR-сервис, напротив, обрабатывает сканы и изображения через оптическое распознавание. Оба сервиса имеют **единый формат выходного JSON** (`raw_ocr_v4`), что позволяет Converter-validator работать с любым из них без изменений.

**Базовый URL (внутренний)**: `http://127.0.0.1:8087/api/v1`

---

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).

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

Поддерживает два режима через поле `mode`:
- **`full`** — полный парсинг всех страниц, сохранение изображений в MinIO
- **`preview`** — быстрый предпросмотр первых N страниц, **без** сохранения изображений в MinIO (`image_key` отсутствует)

Если движок не поддерживает постраничный парсинг, а запрошен `mode: "preview"`, сервис возвращает полный документ с отметкой `preview_not_supported: true` в метаданных результата. Далее Оркестратор передаёт данные в Converter-validator preview (`/converter/preview`), после чего пользователь принимает решение (approve/reject). Full-фаза OCR/Parser пропускается, так как JSON уже полный.

**Важно:** идентификатор задачи (`task_id`) генерирует Оркестратор и передаёт в запросе. Parser-сервис использует его для всех последующих операций (статус, результат).

**Вход:** ссылка на файл в MinIO.

**Запрос:**

```json
{
  "task_id": 420000,
  "draft_id": 12345,
  "file_key": "file-def456",
  "mode": "preview",
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
| `draft_id` | bigint | — | **Да (P12-1)** | Идентификатор черновика в Registry. **Обязателен** с 17.06 — без `draft_id` Parser не может записать `processing_status` / `quality` / `issues` обратно в черновик |
| `file_key` | string | — | Да | Ключ файла в MinIO |
| `mode` | enum | `"full"` | Нет | Режим обработки: `"preview"` / `"full"` |
| `max_pages` | int | `3` | Нет | Количество страниц для предпросмотра (только для `mode: "preview"`) |
| `options` | object | — | Нет | Параметры обработки |
| `options.extract_tables` | bool | `false` | Нет | Извлекать таблицы в структурированном виде |
| `options.extract_images` | bool | `false` | Нет | Извлекать изображения в MinIO (только для `mode: "full"`) |

**Ответ `202`** (всегда):

```json
{
  "task_id": 420000,
  "status": "accepted",
  "mode": "preview",
  "estimated_completion": "2026-05-15T10:02:00Z"
}
```

| Поле | Тип | Описание |
| ---- | --- | -------- |
| `task_id` | bigint | Идентификатор задачи |
| `status` | string | `"accepted"` |
| `mode` | enum | Проброшенный режим из запроса: `"preview"` / `"full"` |
| `estimated_completion` | datetime | Ориентировочное время завершения (ISO 8601) |

---

> **Ограничения режима `preview`:**
> - Поле `image_key` **отсутствует** у блоков (не сохраняется в MinIO)
> - Поле `font` (объект) может отсутствовать у text-блоков
> - Отсутствует детализация `quality.per_page`
> - Возвращаются только первые N страниц документа
> - Если движок не поддерживает постраничный парсинг — возвращается полный документ с флагом `preview_not_supported: true`. Full-фаза OCR/Parser пропускается, решение принимает пользователь

-----

### GET /parser/process/{task_id}/status — статус обработки (longpoll)

Оркестратор ожидает результат через longpoll.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
| -------- | --- | ------------ | -------- |
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при изменении статуса (прогресс / завершение) или по таймауту. |

**Ответ `200`**:

```json
{
  "task_id": 420000,
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
| `task_id`          | bigint | ID задачи                                               |
| `status`           | string | Статус: `accepted`, `processing`, `completed`, `failed` |
| `progress_percent` | int    | Процент выполнения (0–100)                              |
| `pages_processed`  | int    | Обработано страниц                                      |
| `pages_total`      | int    | Всего страниц                                           |
| `avg_confidence`   | float  | Средняя уверенность извлечения                          |
| `step`             | string | Текущий шаг обработки (см. таблицу ниже)                |
| `step_detail`      | string | Детализация шага (человекочитаемая)                     |
| `started_at`       | datetime | Время начала обработки                                  |
| `completed_at`     | datetime | Время завершения (null, если не завершён)               |

**Значения `step`:**

| `step`              | Описание                          |
| ------------------- | --------------------------------- |
| `downloading`       | Скачивание PDF/DOC из MinIO       |
| `splitting`         | Разбивка на страницы              |
| `parsing_pages`     | Парсинг цифровых страниц          |
| `extracting_tables` | Извлечение таблиц                 |
| `extracting_images` | Извлечение и загрузка изображений |
| `aggregating`       | Сборка итогового JSON             |

---

### GET /parser/process/{task_id}/result — итоговый JSON

Получение JSON-контейнера с результатом парсинга. Вызывается Оркестратором после `status: completed`.

> **Важно:** сервис **не пишет в БД** — отдаёт JSON тому, кто вызвал. JSON-формат известен только сервису Parser и downstream-сервисам (Validation, Registry). Изображения — только ссылки (сами файлы загружены в MinIO сервисом).

> ⚠️ **Полный формат данных:** [`docs/schema/schema_parser_result.json`](../schema/schema_parser_result.json) (схема `raw_ocr_v4`) — **обязательно** смотри этот файл, здесь приведён только сокращённый пример.

**Ответ `200`**:

```json
{
  "task_id": 420000,
  "metadata": {
    "schema": "raw_ocr_v4",
    "mode": "preview",
    "preview_not_supported": false,
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
| `metadata`                                   | object | Метаданные обработки                                                 |
| `metadata.schema`                            | string | Идентификатор схемы (напр. `"raw_ocr_v4"`)                          |
| `metadata.mode`                              | enum   | Режим обработки: `"preview"` / `"full"`                              |
| `metadata.preview_not_supported`             | bool   | `true`, если движок не поддерживает постраничный парсинг и вернул полный документ |
| `metadata.created_at`                        | datetime | Время создания результата (ISO 8601)                                 |
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
| `document.pages[].width`                     | float  | Ширина страницы в пикселях (сырые, px) — для нормирования bbox      |
| `document.pages[].height`                    | float  | Высота страницы в пикселях (сырые, px) — для нормирования bbox                                                 |
| `document.block`                             | array  | **Единый** массив всех элементов в reading order (сквозная нумерация)|
| `block[].number`                             | int    | Порядковый номер элемента в reading order                            |
| `block[].type`                               | string | Тип элемента: `headerFooter`, `heading`, `paragraph`, `text_block`, `list`, `table`, `image`, `caption`, `formula` |
| `block[].page`                               | int    | Номер страницы                                                       |
| `block[].bbox`                               | array  | Координаты `[left, bottom, right, top]` в пикселях (сырые, px)       |
| `block[].font`                               | object | Объект шрифта: `{ size: float, color: string, bold: bool, italic: bool, underline: bool }` |
| `quality`                                    | object | Общая оценка качества + `per_page` — детализация по страницам        |
| `quality.per_page[].status`                  | string | `ok`, `low_confidence`, `failed`                                     |
| `quality.per_page[].error`                   | string | Код ошибки страницы (только при `status: failed`)                    |
| `quality.notifications[]`                    | array  | **P12-3 / P3-5**: уведомления для оператора (см. ниже) — единый массив `{code, severity, category, message, location, suggested_action, db_fk_to_draft_notification}` |
| `errors`                                     | array  | Массив **системных** ошибок парсинга (не путать с `quality.notifications[]`) |
| `status`                                     | string | `completed`, `failed`                                                |

### P12-3 / P3-5 — quality.notifications[] (уведомления оператора)

Единый массив уведомлений для оператора. Содержит как security-предупреждения (P3-5), так и замечания по качеству (P12-3). Разделяются полем `category`.

| Поле | Тип | Описание |
|------|-----|----------|
| `code` | string | Код уведомления. Security: `EMBEDDED_JS`, `EMBEDDED_FILE`, `ENCRYPTED_PAYLOAD`, `OLE_OBJECT`, `MACRO`, `EXTERNAL_REFERENCE`, `LAMA_FALLBACK_USED`. Quality: `LOW_CONFIDENCE_PAGE`, `LANGUAGE_DETECTION_FAILED`, `TABLE_CORRUPTED`, `FORMULA_UNREADABLE`, `IMAGE_BLURRED`, `HEADER_FOOTER_OVERLAP` |
| `severity` | string | `info`, `warning`, `error`, `critical` |
| `category` | string | `security` — предупреждение безопасности; `quality` — замечание по качеству |
| `message` | string | Человекочитаемое описание |
| `location` | object | `{page, block}` — где в документе (опционально) |
| `suggested_action` | string | Что рекомендуется сделать: `reprocess`, `manual_edit`, `review`, `ignore` (опционально) |
| `db_fk_to_draft_notification` | bigint | После записи в БД — ID в `pipeline.draft_notifications` (см. `ddl_migrations_17_06.md`) |

**Особенности по category:**
- `category: security` — severity `info`, `warning`, `critical`. При `critical` — статус `low_confidence`, в лог пишется WARN (P11-3). UI отображает плашку «Документ содержит потенциально небезопасные элементы» и требует подтверждения оператора перед approve.
- `category: quality` — severity `info`, `warning`, `error`, `critical`. При `critical` черновик переводится в `review_required`.

**Запись в БД:** Parser/OCR вставляет уведомления в `pipeline.draft_notifications` через `INSERT ... RETURNING id`.

**Примечание:** Cписок кодов открытый — расширяется по мере добавления новых детекторов. Коды из разных `category` не пересекаются.

---

### GET /parser/processes

Список текущих (активных) процессов обработки документов.

**Ответ `200`**:

```json
{
  "processes": [
    {
          "task_id": 420000,
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
| `status`           | string | Статус: `accepted`, `processing` |
| `progress_percent` | int    | Процент выполнения               |
| `pages_processed`  | int    | Обработано страниц               |
| `pages_total`      | int    | Всего страниц                    |
| `started_at`       | datetime | Время начала обработки           |

---

### Коды ошибок Parser-сервиса

| `error.code`         | HTTP | Описание                         |
| -------------------- | ---- | -------------------------------- |
| `FILE_NOT_FOUND`     | 404  | Файл не найден в MinIO           |
| `FILE_TOO_LARGE`     | 413  | PDF/DOC > 500 MB / > 2000 страниц |
| `UNSUPPORTED_FORMAT` | 415  | Не PDF / не DOC                  |
| `PARSER_FAILED`      | 500  | Критическая ошибка парсинга      |
| `PREVIEW_NOT_SUPPORTED` | 422 | Движок не поддерживает постраничный парсинг (возвращается в metadata результата, не HTTP) |
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
| **Управляемость Оркестратором**        | 3 эндпоинта (`process`, `status`, `result`); режим `mode` управляет preview/full; JSON-контейнер как чёрный ящик  |
| **Большие документы**                  | Celery-воркер вне API-процесса, параллелизм страниц, потоковая загрузка из MinIO        |
| **Готовые ссылки на изображения**      | Parser сам выгружает в MinIO, отдаёт `image_key` в ответе                                |
| **Независимая разработка**             | Другая группа может писать и тестировать Parser-сервис, имея только контракт API        |
