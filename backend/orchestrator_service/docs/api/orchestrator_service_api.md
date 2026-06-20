## API Orchestrator Service (orchestrator-service:8081)

Координатор пайплайнов 1 и 2. Оркестрирует конвейер обработки документов: загрузка → task → вызов Registry для создания черновика → OCR/Parser → Converter-validator → Registry.  
Ведение этапов задачи: запись входных/выходных данных каждого сервиса (OCR/Parser, Converter-validator) в `pipeline.task_steps`.  
Вызов Registry для CRUD операций с данными черновиков.

**Базовый URL (внутренний)**: `http://127.0.0.1:8081/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](common_api.md#формат-ответа).

Для эндпоинтов с пагинацией используется формат `{ items: [...], meta: { total, page, page_size } }` — см. [common_api.md](common_api.md#пагинация).

### Группы

| Группа      | Описание                                                            |
| ----------- | ------------------------------------------------------------------- |

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).

| `health`    | Агрегированный health-check                                         |
| `documents` | Документы: загрузка, список, статус, версии, аппрув, завершение обработки |
| `drafts`    | Черновики: управление загрузкой, preview, решение (approve/reject) — единая точка входа. Вызов Registry internal API для CRUD |
| `pages`     | Просмотр страниц и текстового слоя                                  |

> **Примечание:** Группа `tasks` — внутренняя (internal). Эндпоинты `/tasks/{task_id}/...` используются только для межсервисного взаимодействия и админского анализа. `task` — агрегатор этапов пайплайна, каждый этап хранит входные/выходные JSON-контейнеры сервисов. Внешние клиенты используют `/drafts/{draft_id}/...` и `/documents/{document_id}/...`.

---

## Группа documents

### POST /drafts — Загрузка файла (создание черновика)

Загрузка файла с **обязательным созданием черновика**. Без черновика загрузить документ невозможно.

Orchestrator вычисляет SHA-256 содержимого, определяет формат, создаёт задачу (`pipeline.tasks`) и запись черновика в Registry (`POST /registry/drafts`), помещает в очередь Celery. Двухфазный конвейер: **Preview** (OCR/Parser preview → Converter-validator preview → решение пользователя) → **Full** (OCR/Parser → Converter-validator → Registry → RAG Builder).

`user_id` определяется из контекста аутентификации.

> **Черновик — точка входа:** При загрузке всегда создаётся черновик в статусе `uploaded`. Все последующие операции (preview, решение, конвертация, завершение черновика) привязаны к черновику. Без черновика документ не может существовать в системе.

**Запрос**: `multipart/form-data`

| Поле           | Тип    | Обязательность | Описание                                                           |
| -------------- | ------ | -------------- | ------------------------------------------------------------------ |
| `file`         | File   | Да             | Бинарный файл (PDF, PNG, JPG, TIFF)                                |
| `source_type`  | string | Да             | `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `title`        | string | Нет            | Название документа                                                 |
| `doc_code`     | string | Нет            | Регистрационный номер (напр. `20868-81`)                           |
| `mks_oks_code` | string | Нет            | Код МКС/ОКС                                                        |
| `okstu_code`   | string | Нет            | Код ОКСТУ                                                          |
| `era`          | string | Нет            | `USSR`, `CIS`, `RF`, `CURRENT`                                     |
| `jurisdiction` | string | Нет            | `RU`, `EU`, `US`, `NO`, `INTL`                                     |
| `issuing_body` | string | Нет            | Организация-издатель                                               |
| `metadata`     | string | Нет            | JSON-строка с доп. данными                                         |

> **Примечание**: В запросе `metadata` передаётся как JSON-строка (string). Сервер парсит её в объект, который возвращается в ответе `GET /documents/{doc_id}` как структурированный JSON. Допустимые ключи: `year`, `udk_code` (D-51: переименовано из `udc`), `tags`, `notes`.

**Ответ `202`**:

```json
{
  "draft_id": 420000,
  "task_id": 420000,
  "status": "uploaded",
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "file_size_bytes": 2048576,
  "is_duplicate_file": false,
  "is_duplicate_document": false,
  "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "title_key": "USSR|gost|47.020||20868-81|стойки установочные...",
  "created_at": "2026-05-15T10:00:00Z"
}
```

> **Примечание:** `draft_id` назначается Registry при создании записи черновика. `document_id` назначается Registry при завершении черновика. Первичный внешний идентификатор на этапе загрузки и preview — `draft_id`. `task_id` — внутренний сквозной ID задачи (`pipeline.tasks`), используется только для межсервисного взаимодействия и администрирования.

### Коды ошибок

| HTTP | `error.code` | Когда возникает |
|------|-------------|----------------|
| 400 | VALIDATION_ERROR | Некорректные поля запроса |
| 400 | EMPTY_FILE | Загружен пустой файл (0 байт) |
| 400 | FILE_TOO_SMALL | Файл менее 1 КБ |
| 401 | UNAUTHORIZED | Отсутствует или невалидный JWT |
| 403 | FORBIDDEN | Нет прав на операцию |
| 409 | DUPLICATE_FILE | Файл с таким SHA-256 уже обрабатывается |
| 413 | FILE_TOO_LARGE | Файл превышает 100 МБ |
| 422 | UNSUPPORTED_FILE_TYPE | Неподдерживаемый тип файла |
| 422 | VALIDATION_FAILED | Семантическая ошибка валидации |
| 502 | BAD_GATEWAY | Ошибка вызова внутреннего сервиса |
| 503 | SERVICE_UNAVAILABLE | MinIO или БД недоступны |

> **📐 Доступ:** Эндпоинты `/tasks/{task_id}/...` — read-only для `system_admin` (и `knowledge_admin` для привязки к черновикам). Используются для мониторинга процессов и просмотра данных, передаваемых между сервисами. У задач нет preview и decide — эти функции доступны через `/drafts/{draft_id}/...`.

### GET /tasks/{task_id}/status

Статус задачи по `task_id` (сквозной ID). Агрегированная информация о состоянии обработки на всех этапах: preview, full-фаза, Registry, индексация.

**Путь:** `/api/v1/tasks/{task_id}/status`
**Метод:** `GET`

**Ответ `200`:**

```json
{
  "task_id": 420000,
  "draft_id": 420000,
  "document_id": 1,
  "version_id": 1,
  "status": "previewing",
  "pipeline_stage": "preview",
  "progress_percent": 45,
  "has_notifications": false,
  "critical_count": 0,
  "steps": [
    {
      "step_name": "upload",
      "service_name": "Orchestrator",
      "status": "completed",
      "input_data": {"file_key": "f-abc123"},
      "output_data": {"draft_id": 1, "task_id": 100},
      "started_at": "2026-06-05T10:00:00Z",
      "completed_at": "2026-06-05T10:00:05Z"
    },
    {
      "step_name": "preview_ocr",
      "service_name": "OCR Service",
      "status": "running",
      "input_data": {"file_key": "f-abc123", "mode": "preview", "max_pages": 3},
      "output_data": null,
      "started_at": "2026-06-05T10:00:05Z",
      "completed_at": null
    }
  ],
  "created_at": "2026-06-05T10:00:00Z",
  "updated_at": "2026-06-05T10:02:30Z"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `task_id` | bigint | Сквозной ID задачи |
| `draft_id` | bigint \| null | ID черновика в Registry |
| `document_id` | bigint \| null | ID документа в Registry (если создан) |
| `version_id` | bigint \| null | ID версии документа (если создана) |
| `status` | string | Текущий статус (`uploaded`, `previewing`, `ready_for_approve`, `processing`, `created`, `indexing`, `indexed`, `failed`) |
| `pipeline_stage` | string | Этап конвейера: `upload`, `preview`, `decision`, `full`, `registry`, `indexation` |
| `progress_percent` | int | Общий прогресс (0–100) |
| `has_notifications` | bool | Есть ли уведомления у черновика |
| `critical_count` | int | Количество critical-уведомлений |
| `steps` | array | Массив этапов задачи с промежуточными данными (`step_name`, `service_name`, `status`, `input_data`, `output_data`, `started_at`, `completed_at`) |
| `created_at` | datetime | Время создания задачи (ISO 8601) |
| `updated_at` | datetime | Время последнего обновления (ISO 8601) |

**Примечание:** `GET /tasks/{task_id}/status` — эндпоинт для сквозного отслеживания задачи админом. `task` — агрегатор этапов пайплайна, каждый этап хранит входные/выходные JSON-контейнеры сервисов. Внешним клиентам для статуса загрузки следует использовать `GET /drafts/{draft_id}/preview/status`, для статуса документа — `GET /documents/{document_id}/status`.

### GET /tasks/{task_id}/steps

Шаги задачи (без общей обёртки статуса). Возвращает только массив `steps[]`, аналогичный вложенному в `GET /tasks/{task_id}/status`.

**Путь:** `/api/v1/tasks/{task_id}/steps`
**Метод:** `GET`
**Доступ:** `system_admin`

**Ответ `200`:**

```json
{
  "task_id": 420000,
  "total": 2,
  "steps": [
    {
      "step_name": "upload",
      "service_name": "Orchestrator",
      "status": "completed",
      "input_data": {"file_key": "f-abc123"},
      "output_data": {"draft_id": 1, "task_id": 100},
      "started_at": "2026-06-05T10:00:00Z",
      "completed_at": "2026-06-05T10:00:05Z"
    },
    {
      "step_name": "preview_ocr",
      "service_name": "OCR Service",
      "status": "completed",
      "input_data": {"file_key": "f-abc123", "mode": "preview", "max_pages": 3},
      "output_data": {"task_id": 420000, "pages": 3, "confidence": 0.92},
      "started_at": "2026-06-05T10:00:05Z",
      "completed_at": "2026-06-05T10:01:30Z"
    }
  ]
}
```

| Поле | Тип | Описание |
|---|---|---|
| `task_id` | bigint | Сквозной ID задачи |
| `total` | int | Количество шагов |
| `steps` | array | Массив этапов задачи (схема — см. `GET /tasks/{task_id}/status`) |

### GET /drafts/{draft_id}/tasks

Список задач для черновика. У черновика может быть несколько задач при повторных обработках (reprocess).

**Путь:** `/api/v1/drafts/{draft_id}/tasks`
**Метод:** `GET`
**Доступ:** `system_admin`, `knowledge_admin`

**Ответ `200`:**

```json
{
  "draft_id": 420000,
  "tasks": [
    {
      "task_id": 420000,
      "status": "created",
      "pipeline_stage": "full",
      "initiated_by": "ivanov_ai",
      "created_at": "2026-06-05T10:00:00Z",
      "updated_at": "2026-06-05T12:30:00Z"
    }
  ]
}
```

| Поле | Тип | Описание |
|---|---|---|
| `draft_id` | bigint | ID черновика |
| `tasks` | array | Массив задач: `task_id`, `status`, `pipeline_stage`, `initiated_by` (субъект), `created_at`, `updated_at` |

### POST /documents/{doc_id}/versions

Загрузка дополнительной версии файла к существующему логическому документу (скан к цифре, чертёж к спецификации и т.д.).

**Запрос**: `multipart/form-data`

| Поле   | Тип  | Обязательность | Описание      |
| ------ | ---- | -------------- | ------------- |
| `file` | File | Да             | Бинарный файл |

**Ответ `202`**:

```json
{
  "document_id": 1,
  "version_id": 420001,
  "version_number": 2,
  "status": "uploaded",
  "task_id": 420001,
  "file_hash_sha256": "6ca13d52ca70c883e0f0bb101e425a89e8624de51db2d2392593af6a84118090",
  "is_duplicate_file": false,
  "created_at": "2026-05-15T11:00:00Z"
}
```

---

### GET /documents/{doc_id}/versions

Список всех версий файлов логического документа.

> **Примечание:** Поле `size_bytes` в ответе API соответствует полю `file_size_bytes` в таблице БД `registry.document_versions`.

**Query-параметры**:
| Параметр | Тип | Обязательность | По умолчанию | Описание |
|----------|-----|---------------|-------------|----------|
| `page` | int | Нет | 1 | Номер страницы |
| `page_size` | int | Нет | 50 | Размер страницы (макс. 100) |

**Ответ `200`**:

```json
{
  "document_id": 1,
  "versions": [
    {
      "version_id": 420001,
      "version_number": 1,
      "format_code": "pdf_digital",
      "format_label": "PDF (цифровой)",
      "file_key": "b3a8f1c2/v1/e3b0c442...855.pdf",
      "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size_bytes": 2048576,
      "created_at": "2026-05-15T10:00:00Z",
      "created_by": "Иванов И.И."
    }
  ],
  "meta": { "total": 2 }
}

> **Разница между `version_id` и `version_number`**: `version_id` — внутренний идентификатор версии (bigint, sequence), `version_number` — порядковый номер версии документа (начиная с 1), видимый пользователю.

---

### GET /documents

Список документов с фильтрацией.

**Query-параметры** (дополнительно к существующим):

| Параметр            | Тип    | Описание                                                   |
| ------------------- | ------ | ---------------------------------------------------------- |
| `source_type`       | string | Фильтр по типу источника                                   |
| `era`               | string | `USSR`, `CIS`, `RF`, `CURRENT`                             |
| `validity_status`   | string | `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `jurisdiction`      | string | `RU`, `EU`, `US`, `NO`, `INTL`                             |
| `mks_oks_code`      | string | Фильтр по коду МКС/ОКС                                     |
| `okstu_code`        | string | Фильтр по коду ОКСТУ                                       |
| `doc_code`          | string | Поиск по номеру документа                                  |
| `status`            | string | Фильтр по статусу FSM                                      |
| `search`            | string | Поиск по названию                                          |
| `sort_by`           | string | Поле сортировки: `title`, `doc_code`, `created_at`, `status` (по умолчанию `created_at`) |
| `order`             | string | Направление: `asc`, `desc` (по умолчанию `desc`)            |
| `page`, `page_size` | int    | Пагинация                                                  |

**Ответ `200`**:

```json
{
  "summary": {
    "total": 128,
    "created": 100,
    "pending_index": 5,
    "indexing": 3,
    "indexed": 17,
    "failed": 3
  },
  "items": [
    {
      "document_id": 1,
      "title": "Стойки установочные",
      "doc_code": "20868-81",
      "source_type": "GOST",
      "era": "USSR",
      "validity_status": "active",
      "jurisdiction": "RU",
      "issuing_body": "Госстандарт СССР",
      "mks_oks_code": "31.240",
      "okstu_code": null,
      "classification_status": {
        "mks": ["31.240"],
        "okstu": [],
        "udk": [],
        "subject_area": ["Электроника", "Монтажные изделия"]
      },
      "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "file_size_bytes": 2048576,
      "status": "created",
      "latest_version": 1,
      "total_versions": 2,
      "user_id": "u-001",
      "created_by": "Иванов И.И.",
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T14:00:00Z"
    }
  ],
  "meta": { "total": 128, "page": 1, "page_size": 20 }
}
```

---

### GET /documents/{doc_id}

Детальная информация о документе со всеми метаданными и версиями файлов.

**Ответ `200`**:

```json
{
  "document_id": 1,
  "title": "Стойки установочные",
  "doc_code": "20868-81",
  "source_type": "GOST",
  "document_type": "normative",
  "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "title_key": "USSR|gost|47.020||20868-81|стойки установочные...",
  "status": "created",
  "era": "USSR",
  "validity_status": "active",
  "jurisdiction": "RU",
  "issuing_body": "Госстандарт СССР",
  "enterprise_id": null,
  "mks_oks_code": "31.240",
  "okstu_code": null,
  "classification_status": {
    "mks": ["31.240"],
    "okstu": [],
    "udk": [],
    "subject_area": ["Электроника", "Монтажные изделия"]
  },
  "metadata": {
    "year": "1981",
    "udk_code": "629.5.021",
    "tags": ["судостроение", "стойки"]
  },
  "latest_version": {
    "version_id": 420001,
    "version_number": 1,
    "format_code": "pdf_digital",
    "file_hash_sha256": "e3b0c442...",
    "size_bytes": 2048576
  },
  "total_versions": 2,
  "user_id": "u-001",
  "created_by": "system_registry_sync",
  "updated_by": "ivanov_ai",
  "created_at": "2026-04-27T10:00:00Z",
  "updated_at": "2026-04-27T14:00:00Z"
}
```

**Коды ошибок**:
| HTTP | `error.code` | Когда возникает |
|------|-------------|----------------|
| 400 | VALIDATION_ERROR | Некорректный `doc_id` в пути |
| 401 | UNAUTHORIZED | Отсутствует или невалидный JWT |
| 403 | FORBIDDEN | Нет прав на просмотр документа |
| 404 | DOCUMENT_NOT_FOUND | Документ с указанным ID не найден |
| 502 | BAD_GATEWAY | Ошибка вызова Registry |
| 503 | SERVICE_UNAVAILABLE | БД недоступна |

---

### GET /documents/{doc_id}/status

Прогресс обработки документа. UI вызывает для отслеживания асинхронного конвейера после загрузки.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
| -------- | --- | ------------ | -------- |
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при изменении статуса или по таймауту. Подробнее — [Модель выполнения](../api/common_api.md#модель-выполнения-sync-async). |

#### Статус: `processing` (в процессе)

```json
{
  "document_id": 12345,
  "status": "processing",
  "progress_percent": 60,
  "steps": {
    "pipeline": {
      "formation": {
        "status": "processing",
        "preview": {
          "status": "completed",
          "ocr_parser": {"status": "completed", "pages_processed": 3},
          "converter_validator": {"status": "completed", "metadata_extracted": true}
        },
        "decision": {
          "status": "completed",
          "action": "approve"
        }
      },
      "indexation": {
        "status": "pending",
        "rag_indexing": {"status": "pending"}
      }
    }
  },
  "started_at": "2025-06-06T10:00:00Z",
  "estimated_completion": "2025-06-06T10:30:00Z"
}
```

#### Статус: `approval_required` (ждёт решения по черновику)

```json
{
  "document_id": 12345,
  "status": "approval_required",
  "progress_percent": 40,
  "steps": {
    "pipeline": {
      "formation": {
        "status": "ready_for_approve",
        "preview": {
          "status": "completed"
        }
      }
    }
  }
}
```

#### Статус: `completed` (готов)

```json
{
  "document_id": 12345,
  "status": "completed",
  "progress_percent": 100,
  "steps": {
    "pipeline": {
      "formation": {
        "status": "completed",
        "preview": {"status": "completed"},
        "decision": {"status": "completed", "action": "approve"}
      },
      "indexation": {
        "status": "completed",
        "rag_indexing": {
          "status": "completed",
          "chunks_generated": 34
        }
      }
    }
  },
  "chunk_summary": {"sections": 12, "chunks": 34, "embeddings": 31},
  "started_at": "2025-06-06T10:00:00Z",
  "completed_at": "2025-06-06T10:25:00Z"
}
```

**Статусы Formation (Формирование документа)**: `uploaded` → `previewing` → `ready_for_approve` → `processing` → `created` / `failed`.

> **Таймаут `uploaded`**: Если preview не запущен в течение 1 часа после загрузки, статус автоматически меняется на `failed` с кодом `PREVIEW_TRIGGER_TIMEOUT`.

**Статусы документов (FSM) для Indexation**: `pending_index` → `indexing` → `indexed` / `failed`. Подробнее — [статусная модель FSM](../pipelines/pipeline2-indexation.md#статусная-модель-fsm).

**Группировка `steps.pipeline`**: каждый пайплайн имеет свой ключ (`formation`, `indexation`) с полем `status` — агрегированный статус пайплайна, и вложенными этапами. Статусы пайплайна: `pending`, `in_progress`, `completed`, `failed`, `blocked`. Статусы этапов: `pending`, `in_progress`, `completed`, `error`, `blocked`.

После завершения Пайплайна 1 автоматически запускается **Пайплайн 2 (Индексация)**.

---

### GET /documents/{doc_id}/file

Получение полного файла документа (последняя версия).

**Query-параметры**:

| Параметр | Тип   | Обязательность | Значение по умолчанию | Описание                                     |
| -------- | ----- | -------------- | --------------------- | -------------------------------------------- |
| `format` | string| Нет            | `json`                | Формат ответа: `json` — JSON со ссылкой на файл; `binary` — бинарный поток файла |

---

#### format=json (по умолчанию)

Ответ возвращает JSON с метаданными и ссылкой для скачивания файла.

**Ответ `200`**:

```json
{
  "file_url": "/files/b3a8f1c2/full.pdf",
  "file_size": 1048576,
  "content_type": "application/pdf"
}
```

| Поле           | Тип    | Описание                                   |
| -------------- | ------ | ------------------------------------------ |
| `file_url`     | string | Относительный URL для скачивания файла     |
| `file_size`    | int    | Размер файла в байтах                      |
| `content_type` | string | MIME-тип файла (application/pdf, image/png, image/jpeg, image/tiff и т.д.) |

---

#### format=binary

Ответ возвращает бинарное содержимое файла напрямую.

**Ответ `200`**:

| Заголовок             | Значение                                           |
| --------------------- | -------------------------------------------------- |
| `Content-Type`        | Зависит от типа файла: `application/pdf`, `image/png`, `image/jpeg`, `image/tiff` и т.д. |
| `Content-Disposition` | `attachment; filename="<original_filename>"`       |
| `Content-Length`      | Размер файла в байтах                              |

Тело ответа — бинарный поток (сырые байты файла).

---



### GET /documents/{doc_id}/history

История переходов статусов документа (аудит).

**Query-параметры**:
| Параметр | Тип | Обязательность | По умолчанию | Описание |
|----------|-----|---------------|-------------|----------|
| `page` | int | Нет | 1 | Номер страницы |
| `page_size` | int | Нет | 50 | Размер страницы (макс. 100) |

**Ответ `200`**:

```json
{
  "document_id": 1,
  "history": [
    {
      "history_id": "h-001",
      "old_status": null,
      "new_status": "uploaded",
      "comment": { "reason": "initial_upload", "details": null },
      "changed_by": "ivanov_ai",
      "changed_at": "2026-05-15T10:00:00Z"
    },
    {
      "history_id": "h-002",
      "old_status": "created",
      "new_status": "indexed",
      "comment": { "reason": "manual_approve", "details": "Утверждено главным инженером" },
      "changed_by": "ivanov_ai",
      "changed_at": "2026-05-15T12:00:00Z"
    }
  ],
  "meta": { "total": 5 }
}
```

---

---

### POST /documents/{doc_id}/reprocess

Асинхронная переобработка документа без создания нового черновика. `user_id` из контекста аутентификации.
Перезапускает указанный этап обработки для существующего документа. Новый `draft_id` **не создаётся**.

**Запрос**:

```json
{
  "mode": "full",
  "options": { "ocr_engine": "paddleocr", "language": "ru", "pages": "1-5" }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `mode` | string | Режим переобработки: `full`, `ocr_only`, `chunking_only`, `validation_only`, `reindex` |
| `options` | object | Опциональные параметры обработки (см. таблицу ниже) |

**Поле `options`** (опционально):
| Поле | Тип | Описание | Допустимые значения |
|------|-----|----------|-------------------|
| `ocr_engine` | string | Движок OCR | `paddleocr`, `tesseract` |
| `parser_engine` | string | Движок парсинга | `docling` |
| `language` | string | Язык OCR | `rus` (по умолчанию), `eng` |
| `pages` | string | Диапазон страниц | `"1-5"`, `"1,3,5"`, `"all"` (по умолчанию) |

**Ответ `202`**:
```json
{
  "task_id": 420002,
  "document_id": 1,
  "mode": "full",
  "status": "processing",
  "message": "Переобработка запущена. Новый черновик не создаётся — используется существующий документ."
}
```

**Особенности переиндексации (`mode: reindex`):**
Перед повторным чанкингом Оркестратор вызывает `DELETE /rag/build/{doc_id}` для очистки существующих чанков документа из векторного индекса. Только после успешного удаления запускается новый `POST /rag/build`. Если `DELETE` вернул ошибку, переиндексация отменяется с кодом `CLEANUP_FAILED`.

**Ошибки**: `404` — документ не найден, `409` — документ в обработке.

---

### DELETE /documents/{doc_id}

**Soft-delete:** документ помечается как удалённый (`deleted_at`), но запись в БД сохраняется. Связанные сущности (секции, версии, история, чанки) также помечаются как недоступные. Повторный вызов возвращает `404 NOT_FOUND`.

**Ответ `200`**:

```json
{
  "document_id": 1,
  "deleted_at": "2026-06-05T10:05:00Z"
}
```

### Коды ошибок

| HTTP | `error.code` | Когда возникает |
|------|-------------|----------------|
| 401 | UNAUTHORIZED | Отсутствует или невалидный JWT |
| 403 | FORBIDDEN | Нет прав на удаление |
| 404 | DOCUMENT_NOT_FOUND | Документ не найден или уже удалён |
| 409 | DOCUMENT_IN_PROCESSING | Документ в обработке, удаление невозможно |
| 409 | HAS_CHILDREN | Нельзя удалить: есть дочерние версии/секции |
| 502 | BAD_GATEWAY | Ошибка вызова Registry |
| 503 | SERVICE_UNAVAILABLE | БД недоступна |

---

### GET /documents/{doc_id}/errors

Журнал ошибок обработки.

**Query-параметры**:
| Параметр | Тип | Обязательность | По умолчанию | Описание |
|----------|-----|---------------|-------------|----------|
| `stage` | string | Нет | — | Фильтр по этапу: `upload`, `ocr`, `parsing`, `indexing` |
| `severity` | string | Нет | — | Фильтр по серьёзности: `warning`, `error` |
| `page` | int | Нет | 1 | Номер страницы |
| `page_size` | int | Нет | 50 | Размер страницы (макс. 100) |

**Ответ `200`**:

```json
{
  "errors": [
    {
      "error_id": "err-001",
      "stage": "ocr",
      "page": 5,
      "error_code": "LOW_CONFIDENCE",
      "error_message": "Качество распознавания ниже порога (confidence=0.62)",
      "severity": "warning",
      "retry_attempt": 0,
      "timestamp": "2026-05-15T10:01:00Z"
    }
  ],
  "meta": { "total": 1, "page": 1, "page_size": 20 }
}
```

---

### GET /documents/queue

Очередь обработки документов (статусы `uploaded`, `previewing`, `ready_for_approve`, `processing`).

**Query-параметры**:
| Параметр | Тип | Обязательность | По умолчанию | Описание |
|----------|-----|---------------|-------------|----------|
| `page` | int | Нет | 1 | Номер страницы |
| `page_size` | int | Нет | 50 | Размер страницы (макс. 100) |

**Ответ `200`**:

```json
{
  "queue": [
    {
      "document_id": 1,
      "title": "Стойки установочные",
      "doc_code": "20868-81",
      "source_type": "GOST",
      "status": "processing",
      "progress_percent": 60.0,
      "current_step": "formation",
      "steps": {
        "pipeline": {
          "formation": {
            "status": "processing",
            "preview": "completed",
            "decision": "pending"
          },
          "indexation": {
            "status": "pending",
            "rag_indexing": "pending"
          }
        }
      },
      "user_id": "u-001",
      "created_by": "Иванов И.И.",
      "created_at": "2026-05-15T10:00:00Z",
      "started_at": "2026-05-15T10:00:05Z",
      "estimated_completion": "2026-05-15T10:02:00Z"
    }
  ],
  "meta": { "total": 5, "page": 1, "page_size": 20 }
}
```

> **Примечание**: Поле `total` — общее количество документов в очереди. Используется стандартный формат пагинации (см. common_api.md).

---

### GET /tasks

Список задач пайплайна. Возвращает задачи с фильтрацией по статусу, черновику и пагинацией.

**Path:** `/api/v1/tasks`
**Метод:** `GET`

**Query-параметры**:

| Параметр | Тип | Обязательность | По умолчанию | Описание |
|----------|-----|---------------|-------------|----------|
| `status` | string | Нет | — | Фильтр по статусу задачи: `uploaded`, `previewing`, `ready_for_approve`, `processing`, `created`, `indexing`, `indexed`, `failed` |
| `draft_id` | bigint | Нет | — | Фильтр по ID черновика |
| `pipeline_type` | string | Нет | — | Фильтр по типу пайплайна |
| `page` | int | Нет | 1 | Номер страницы |
| `page_size` | int | Нет | 50 | Размер страницы (макс. 100) |

**Ответ `200`**:

```json
{
  "items": [
    {
      "task_id": 420000,
      "draft_id": 420000,
      "document_id": null,
      "status": "previewing",
      "pipeline_stage": "preview",
      "progress_percent": 45,
      "created_at": "2026-06-05T10:00:00Z",
      "updated_at": "2026-06-05T10:02:30Z"
    }
  ],
  "meta": {
    "total": 12,
    "page": 1,
    "page_size": 50
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `items` | array | Массив задач |
| `items[].task_id` | bigint | ID задачи |
| `items[].draft_id` | bigint \| null | ID черновика |
| `items[].document_id` | bigint \| null | ID документа |
| `items[].status` | string | Статус задачи |
| `items[].pipeline_stage` | string | Этап конвейера |
| `items[].progress_percent` | int | Прогресс (0–100) |
| `items[].created_at` | datetime | Время создания |
| `items[].updated_at` | datetime | Время обновления |
| `meta.total` | int | Всего задач |
| `meta.page` | int | Текущая страница |
| `meta.page_size` | int | Размер страницы |

**Коды ошибок**: `401` — неавторизован, `403` — нет прав.

> **Доступ:** `system_admin`. Эндпоинт предназначен для мониторинга. Для получения статуса конкретного черновика используйте `GET /drafts/{draft_id}/preview/status`.

---

### GET /tasks/stats

Статистика по задачам пайплайна: количество задач в каждом статусе.

**Path:** `/api/v1/tasks/stats`
**Метод:** `GET`

**Ответ `200`**:

```json
{
  "total": 120,
  "by_status": {
    "uploaded": 0,
    "previewing": 3,
    "ready_for_approve": 5,
    "processing": 2,
    "created": 100,
    "indexing": 1,
    "indexed": 8,
    "failed": 1
  },
  "by_stage": {
    "upload": 0,
    "preview": 8,
    "decision": 5,
    "full": 2,
    "registry": 100,
    "indexation": 10
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `total` | int | Общее количество задач |
| `by_status` | object | Количество задач по статусам |
| `by_stage` | object | Количество задач по этапам конвейера |

**Коды ошибок**: `401` — неавторизован, `403` — нет прав.

> **Доступ:** `system_admin`.

---

## Группа pages

### GET /documents/{doc_id}/pages

Список страниц документа.

**Ответ `200`**:

```json
{
  "document_id": 1,
  "pages_total": 12,
  "pages": [
    {
      "page": 1,
      "width": 2480,
      "height": 3508,
      "ocr_status": "completed",
      "confidence": 0.95,
      "has_text_layer": true
    }
  ],
  "meta": { "total": 12, "page": 1, "page_size": 50 }
}

> **Примечание:** Поле `has_text_layer` указывает, содержит ли страница встроенный текстовый слой (цифровой PDF) или является сканированным изображением. Источник данных — OCR-сервис (этап распознавания).
```

### GET /documents/{doc_id}/pages/{page_num}

Изображение страницы с наложенными блоками (bbox). Используется для визуального просмотра страницы с подсветкой распознанных элементов.

**Параметры запроса (query):**

| Параметр | Тип | Обязательность | Описание |
|---|---|---|---|
| `highlight` | string | Нет | ID блока для подсветки (число из поля `block[].number` ответа `/text`). Если передан — соответствующий блок выделяется на изображении. |

**Ответ `200`:** Бинарные данные изображения страницы (PNG/JPEG) с заголовками:
- `Content-Type: image/png` (или `image/jpeg`)
- `Content-Length`

**Ошибки:**
| HTTP-код | Код ошибки | Описание |
|---|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | Документ не найден |
| `404` | `PAGE_NOT_FOUND` | Страница с указанным номером не существует |

### GET /documents/{doc_id}/pages/{page_num}/text

Текстовый слой и структура страницы: блоки, таблицы, изображения с координатами (bbox).

**Ответ `200`:**

```json
{
  "document_id": 1,
  "page": 1,
  "width": 2480,
  "height": 3508,
  "blocks": [
    {
      "number": 1,
      "type": "paragraph",
      "bbox": [0.05, 0.056, 1.0, 0.111],
      "content": "Настоящий стандарт распространяется...",
      "confidence": 0.95
    },
    {
      "number": 5,
      "type": "table",
      "bbox": [0.05, 0.417, 1.0, 0.694],
      "content": {
        "columns": ["L, мм", "нормальная", "повышенная"],
        "rows": [["От 6 до 50", "0,1", "0,05"]]
      },
      "confidence": 0.88
    }
  ]
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | string | ID документа |
| `page` | int | Номер страницы |
| `width` | int | Ширина страницы в пикселях |
| `height` | int | Высота страницы в пикселях |
| `blocks` | array | Массив блоков на странице в порядке чтения |
| `blocks[].number` | int | Порядковый номер блока |
| `blocks[].type` | string | Тип блока: `paragraph`, `heading`, `table`, `list`, `image`, `formula`, `headerFooter` |
| `blocks[].bbox` | array | Координаты блока: `[x1, y1, x2, y2]` в нормализованных единицах (0..1) |
| `blocks[].content` | string/object | Текстовое содержимое или структурированный объект (для таблиц) |
| `blocks[].confidence` | float | Уверенность распознавания (0..1) |

### GET /documents/{doc_id}/pages/{page_num}/preview

Агрегированный просмотр: изображение страницы + текстовый слой + подсветка блоков. 
Объединяет функциональность `/pages/{page_num}` и `/pages/{page_num}/text` в одном ответе.

**Параметры запроса (query):**

| Параметр | Тип | Обязательность | Описание |
|---|---|---|---|
| `highlight` | string | Нет | ID блока для подсветки |
| `format` | string | Нет | Формат ответа: `json` (по умолчанию) — структурированные данные, `html` — встроенный HTML с canvas |

**Ответ `200` (`format=json`):**

```json
{
  "document_id": 1,
  "page": 1,
  "image_url": "/documents/1/pages/1",
  "blocks": [
    {
      "number": 1,
      "type": "paragraph",
      "bbox": [0.05, 0.056, 1.0, 0.111],
      "content": "Настоящий стандарт распространяется..."
    }
  ],
  "text_layer": "Настоящий стандарт распространяется..."
}
```

**Ответ `200` (`format=html`):** HTML-документ с встроенным SVG/canvas-отображением страницы и наложенными блоками.

### GET /documents/{doc_id}/parameters

Извлечённые параметры документа — структурированные данные из спецификаций, таблиц и формул.

**Ответ `200`:**

```json
{
  "document_id": 1,
  "parameters": [
    {
      "symbol": "R_доп",
      "description": "Допустимый радиус",
      "unit": "мм",
      "value": 0.05,
      "source_clause": "6.1",
      "source_page": 1
    },
    {
      "symbol": "L",
      "description": "Длина стойки",
      "unit": "мм",
      "range": { "min": 6, "max": 80 },
      "source_clause": "6.1.table1",
      "source_page": 2
    }
  ],
  "total": 2
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | string | ID документа |
| `parameters` | array | Массив извлечённых параметров |
| `parameters[].symbol` | string | Обозначение параметра (например, `L`, `R_доп`) |
| `parameters[].description` | string | Описание параметра |
| `parameters[].unit` | string | Единица измерения |
| `parameters[].value` | number | Числовое значение (если применимо) |
| `parameters[].range` | object | Диапазон значений параметра:
  - `min`: number — минимальное значение
  - `max`: number — максимальное значение
  - `min_inclusive`: boolean (опционально) — включено ли минимальное значение
  - `max_inclusive`: boolean (опционально) — включено ли максимальное значение |
| `parameters[].source_clause` | string | Пункт документа-источника |
| `parameters[].source_page` | int | Страница документа-источника |
| `total` | int | Общее количество параметров |

> **Источник данных:** параметры извлекаются Converter-validator'ом на этапе полной обработки из таблиц, формул и спецификаций документа. Поле `parameters` присутствует в `registry.document_sections.content` для секций типа `formula` и `table`.

---

## Группа drafts

Orchestrator — **единая точка входа** для работы с черновиками. Все эндпоинты `/drafts` проксируют вызовы к Registry internal API (`/registry/drafts`), добавляя логику пайплайна (создание task, управление этапами).

Черновик (draft) — **обязательная точка входа** для загрузки документа. `POST /drafts` всегда создаёт задачу (`pipeline.tasks`) и черновик (`POST /registry/drafts`); загрузить документ без черновика невозможно.

**Принцип работы:**
- `POST /drafts` → создание task + вызов `POST /registry/drafts`
- `GET /drafts` / `GET /drafts/{id}` → прокси к `GET /registry/drafts`
- `PATCH /drafts/{id}/decide` → решение → `PATCH /registry/drafts/{id}/status` + при `approve` → `POST /registry/documents`
- `DELETE /drafts/{id}` → вызов `DELETE /registry/drafts/{id}`

Данные черновиков (raw_data, preview_metadata) хранятся в `registry.drafts` (БД Registry). Управление жизненным циклом — через Orchestrator. Этапы задачи с входными/выходными данными сервисов — в `pipeline.task_steps` (БД Orchestrator).  
Детальная схема БД — см. [db_diagrams.md](../database/db_diagrams.md).

### GET /drafts

Список черновиков с фильтрацией. Без параметров возвращает все черновики (доступно `system_admin` и `knowledge_admin`).
С одним из параметров — фильтрация по бизнес-ключу или конкретному черновику.

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `draft_id` | bigint | Нет | Фильтр по ID черновика |
| `document_key` | string | Нет | Бизнес-ключ документа (SHA-256). История попыток обработки одного документа |
| `status` | string | Нет | Фильтр по статусу: `uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation`, `approved`, `discarded` |
| `page` | int | Нет | Номер страницы (по умолчанию 1) |
| `page_size` | int | Нет | Записей на странице (по умолчанию 50, max 200) |

**Ответ `200`:**

```json
{
  "items": [
    {
      "draft_id": 1,
      "task_id": 100,
      "file_key": "f-abc123",
      "document_key": "sha256:def456",
      "status": "approved",
      "confidence": 0.92,
      "preview_metadata": { /* см. _schemas.md#PreviewMetadata */ },
      "document_id": 1300,
      "created_at": "2026-06-05T10:00:00Z",
      "updated_at": "2026-06-05T10:05:00Z"
    },
    {
      "draft_id": 2,
      "task_id": 101,
      "file_key": "f-abc123",
      "document_key": "sha256:def456",
      "status": "review_required",
      "confidence": 0.62,
      "preview_metadata": { /* см. _schemas.md#PreviewMetadata */ },
      "has_notifications": true,
      "critical_count": 1,
      "document_id": null,
      "created_at": "2026-06-05T10:10:00Z",
      "updated_at": "2026-06-05T10:12:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "page": 1,
    "page_size": 50
  }
}
```

> Схема полей `preview_metadata` — [_schemas.md](_schemas.md#PreviewMetadata).

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Уникальный идентификатор черновика |
| `task_id` | bigint | Внутренний ID задачи (internal) |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256) |
| `status` | string | Статус черновика: `uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation`, `approved`, `discarded` |
| `confidence` | float | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | Preview-метаданные — см. [_schemas.md](_schemas.md#PreviewMetadata) |
| `document_id` | bigint \| null | ID документа в Registry (FK → `registry.documents`), созданный по результатам черновика |
| `has_notifications` | bool | **P12-3**: есть ли у черновика уведомления (для индикатора в UI) |
| `critical_count` | int | **P12-3**: количество critical-уведомлений (для бейджа) |
| `error_code` | string \| null | Код ошибки при `discarded` |
| `error_message` | string \| null | Описание ошибки |
| `created_at` | datetime | Время создания (ISO 8601) |
| `updated_at` | datetime | Время последнего изменения (ISO 8601) |

**Терминальные и промежуточные статусы:**

| Тип | Статусы |
|-----|---------|
| **Промежуточные** (ждут операции) | `uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation` |
| **Терминальные** (финальные) | `approved`, `discarded` |

**Допустимые операции по статусам:**

| Статус | `approve` | `reject` | `delete` | `reprocess` |
|--------|:---------:|:--------:|:--------:|:-----------:|
| `uploaded` | ❌ | ❌ | ❌ | ❌ |
| `previewing` | ❌ | ❌ | ❌ | ❌ |
| `ready_for_approve` | ✅ | ✅ | ❌ | ❌ |
| `review_required` | ❌ | ✅ | ❌ | ❌ |
| `validation` | ❌ | ❌ | ❌ | ❌ |
| `approved` | ❌ | ❌ | ❌ | ❌ |
| `discarded` | ❌ | ❌ | ✅ | ✅ (через новую загрузку) |

> `reprocess` для `discarded` — оператор загружает файл заново (создаётся новый черновик). Прямого reprocess для discarded нет.

---

### GET /drafts/{draft_id}

Получить полную информацию о черновике, включая сырые данные распознавания (`raw_data`).

**Ответ `200`:**

```json
{
  "draft_id": 1,
  "task_id": 100,
  "file_key": "f-abc123",
  "document_key": "sha256:def456",
  "status": "ready_for_approve",
  "confidence": 0.92,
  "preview_metadata": { /* см. _schemas.md#PreviewMetadata */ },
  "raw_data": {
    "schema": "raw_ocr_v4",
    "pages": [
      {
        "page": 1,
        "width": 595.0,
        "height": 842.0,
        "blocks": [
          {
            "number": 1,
            "type": "text",
            "bbox": [56.7, 70.9, 481.9, 18.0],
            "content": "ГОСТ 20868-81",
            "confidence": 0.99
          }
        ]
      }
    ]
  },
  "document_id": null,
  "version_id": null,
  "is_new_document": true,
  "notifications": [],
  "error_code": null,
  "error_message": null,
  "created_by": "user_10",
  "created_at": "2026-06-05T10:00:00Z",
  "updated_at": "2026-06-05T10:02:00Z"
}
```

**P12-3 / P12-4 (новые поля в ответе черновика):**

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | bigint \| null | ID документа в Registry. `null` пока черновик не одобрен |
| `version_id` | bigint \| null | **P12-4**: ID версии документа (`document_versions.id`). `null` пока не создана |
| `is_new_document` | bool | **P12-4**: `true` — новый документ, `false` — новая версия существующего |
| `notifications` | array | **P12-3**: массив уведомлений для оператора. Заполняется при `status: review_required`. Структура — см. [parser_service_api.md](parser_service_api.md#p12-3--p3-5--qualitynotifications-уведомления-оператора). Orchestrator получает их от Parser/OCR и записывает в `pipeline.draft_notifications` |

> **`valid_from` / `valid_until`:** Эти поля появляются в ответе `GET /drafts/{id}` после того, как оператор передал их через `PATCH /drafts/{draft_id}/metadata`. На этапе черновика они хранятся во временном поле `metadata_overrides` в `registry.drafts`. При `approve` копируются в `registry.documents` как финальные даты действия. Если даты не заданы явно, `valid_from` может быть выведен из `year` (01-01-{year}).
> **Особенность `valid_until`:** В БД хранится `dateMax = '9999-12-31'` для бессрочных документов, но в API-ответах это значение **возвращается как `null`**. При передаче от UI: `null` → backend подставляет `dateMax`. Это внутренняя оптимизация — UI оперирует понятием «бессрочно», а не конкретной датой.

**P12-3 — поток уведомлений:**

1. Parser/OCR возвращает `quality.notifications[]` в ответе `/process/{task_id}/result`.
2. Orchestrator читает массив и вставляет записи в `pipeline.draft_notifications` (`INSERT ... RETURNING id`).
3. Если среди уведомлений есть `severity >= warning` (или по порогам `app_settings.parser.quality_thresholds`) — черновик переводится в `review_required`.
4. UI получает уведомления через `GET /drafts/{draft_id}` (поле `notifications`).
5. Оператор просматривает уведомления, принимает решение через `PATCH /drafts/{draft_id}/decide`.

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Уникальный идентификатор черновика |
| `task_id` | bigint | Внутренний ID задачи (internal) |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256) |
| `status` | string | Статус черновика |
| `confidence` | float | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | Preview-метаданные — см. [_schemas.md](_schemas.md#PreviewMetadata) |
| `raw_data` | object | Сырые данные распознавания (`raw_ocr_v4`) — результат Parser или OCR |
| `document_id` | bigint \| null | ID документа в Registry, созданный по результатам черновика |
| `error_code` | string \| null | Код ошибки |
| `error_message` | string \| null | Описание ошибки |
| `created_by` | string | Субъект (пользователь или сервис) |
| `created_at` | datetime | Время создания (ISO 8601) |
| `updated_at` | datetime | Время последнего изменения (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |

---

### GET /drafts/{draft_id}/preview

Получить preview-метаданные черновика (облегчённый ответ, без `raw_data`).

**Ответ `200`:**

```json
{
  "draft_id": 1,
  "task_id": 100,
  "file_key": "f-abc123",
  "document_key": "sha256:def456",
  "status": "ready_for_approve",
  "confidence": 0.92,
  "preview_metadata": { /* см. _schemas.md#PreviewMetadata */ },
  "created_at": "2026-06-18T10:00:00Z"
}
```

> Схема полей `preview_metadata` — [_schemas.md](_schemas.md#PreviewMetadata).

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Уникальный идентификатор черновика |
| `task_id` | bigint | Внутренний ID задачи (internal) |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256) |
| `status` | string | Статус черновика |
| `confidence` | float | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | Preview-метаданные — см. [_schemas.md](_schemas.md#PreviewMetadata) |
| `created_at` | datetime | Время создания (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |

---

### POST /drafts/{draft_id}/preview

Запуск фазы превью для черновика. Возвращает preview-данные (метаданные, кандидаты в дубликаты).

**Путь:** `/api/v1/drafts/{draft_id}/preview`
**Метод:** `POST`

**Ответ `202`:**

```json
{
  "draft_id": 420000,
  "status": "previewing",
  "estimated_completion": "2026-06-05T12:00:30Z"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `draft_id` | bigint | ID черновика |
| `status` | string | Статус: `previewing` |
| `estimated_completion` | datetime | Предполагаемое время завершения (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |
| 409 | `DRAFT_ALREADY_PREVIEWED` | Preview уже запущен или завершён |
| 409 | `PREVIEW_IN_PROGRESS` | (P1-19) Preview уже выполняется. Повторный POST с тем же `Idempotency-Key` (TTL 1 час) — вернётся кешированный ответ. Без `Idempotency-Key` — отказ. |
| 422 | `PREVIEW_NOT_SUPPORTED` | (P1-19) Файл не поддерживает постраничный preview; используйте `mode=full` или см. `parser_service_api.md` |

**Идемпотентность повторного запуска (P1-19, уточнение):**

- С заголовком `Idempotency-Key: <uuid>` — повторный POST в течение 1 часа возвращает кешированный ответ 202.
- Без `Idempotency-Key`:
  - Если preview **выполняется** (`status=previewing`) — `409 PREVIEW_IN_PROGRESS`.
  - Если preview **завершён** (`status=ready_for_approve` или `review_required`) — `409 DRAFT_ALREADY_PREVIEWED`. Для запуска заново используйте `POST /drafts/{draft_id}/reprocess` или `DELETE /drafts/{draft_id}` с повторной загрузкой.
  - Если preview **ошибся** (`status=discarded`) — `409 DRAFT_ALREADY_PREVIEWED` (черновик терминальный).

### GET /drafts/{draft_id}/preview/status

Статус превью черновика с longpoll-механизмом.

**Путь:** `/api/v1/drafts/{draft_id}/preview/status`
**Метод:** `GET`

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `longpoll` | int | 15 | Время ожидания в секундах |

**Ответ `200`:**

```json
{
  "draft_id": 420000,
  "status": "completed",
  "ocr_parser_status": "completed",
  "converter_validator_status": "completed",
  "preview": { /* см. _schemas.md#PreviewMetadata */ },
  "duplicates": [],
  "decision_required": false
}
```

> 📖 **Схема полей `preview`** — [_schemas.md](_schemas.md#PreviewMetadata).

| Поле | Тип | Описание |
|---|---|---|
| `draft_id` | bigint | ID черновика |
| `status` | string | Статус обработки: `pending`, `processing`, `completed`, `failed` |
| `ocr_parser_status` | string | Статус OCR/Parser: `pending`, `processing`, `completed`, `failed` |
| `converter_validator_status` | string | Статус Converter-validator: `pending`, `processing`, `completed`, `failed` |
| `preview` | object | Preview-метаданные — см. [_schemas.md](_schemas.md#PreviewMetadata) |
| `duplicates` | array | Массив кандидатов в дубликаты |
| `decision_required` | bool | Требуется ли решение пользователя |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |

---

### PATCH /drafts/{draft_id}/decide

**Основной эндпоинт для принятия решения по загруженному документу.** Доступно для черновиков в статусе `ready_for_approve` и `review_required`. Если черновик в статусе `review_required` — оператору перед принятием решения показываются `notifications` (см. P12-3).

**Допустимые действия по статусам (action):**

| Статус | `approve` | `reject` | `confirm` |
|--------|:---------:|:--------:|:---------:|
| `uploaded` | ❌ | ❌ | ❌ |
| `previewing` | ❌ | ❌ | ❌ |
| `ready_for_approve` | ✅ (→ `approved`) | ✅ (→ `discarded`) | ❌ |
| `review_required` | ❌ | ✅ (→ `discarded`) | ✅ (→ `validation`) |
| `validation` | ❌ | ❌ | ❌ |
| `approved` | ❌ | ❌ | ❌ |
| `discarded` | ❌ | ❌ | ❌ |

- `approve` — завершить черновик, записать документ в Registry. Доступно только для `ready_for_approve`.
- `reject` — отклонить черновик (→ `discarded`). `metadata_overrides` при `reject` игнорируются.
- `confirm` — подтвердить черновик после просмотра замечаний. Переводит `review_required → validation` для повторной валидации с `metadata_overrides`. Доступно только для `review_required`. После успешной валидации — `approved`.

**Механизм оповещения UI после `confirm`:** После `confirm` черновик переходит в `validation`. UI отслеживает завершение валидации через **polling `GET /drafts/{draft_id}`** (не `preview/status` — этот endpoint предназначен только для preview-фазы). Статус `approved` означает, что документ создан в Registry и доступен через `GET /documents/{document_id}`. Статус `discarded` — валидация не пройдена.

**Тело запроса:**

```json
{
  "action": "approve",
  "comment": "Метаданные корректны, уверенность 0.92",
  "metadata_overrides": {
    "doc_code": "311-05-1950ц-ИЗМ1",
    "title": "ЦИРКУЛЯРНОЕ ПИСЬМО № 311-05-1950ц (изм.1)",
    "mks_oks_code": "47.020.01",
    "okstu_code": null,
    "udk_code": "629.5.021",
    "validity_status": "active",
    "valid_from": "2026-01-01",
    "valid_until": null,
    "issuing_body": "РОССИЙСКИЙ МОРСКОЙ РЕГИСТР СУДОХОДСТВА",
    "source_type": "RMRS",
    "jurisdiction": "RU"
  }
}

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| `action` | string | Да | Решение: `approve` (→ `approved`), `reject` (→ `discarded`), `confirm` (→ `validation`, только для `review_required`) |
| `comment` | string | Нет | Комментарий оператора |
| `metadata_overrides` | object | Нет | **D13**: ручные правки метаданных оператора. Может быть передан при `action: confirm` или `approve`. Если метаданные уже сохранены через `PATCH /metadata`, это поле можно не передавать — Orchestrator использует ранее сохранённые значения. Если поле передано — перезаписывает сохранённые. Orchestrator использует эти значения при создании документа в Registry вместо автоматически извлечённых. Допустимые поля — см. таблицу ниже |

**Поля `metadata_overrides`:**

| Поле | Тип | Описание |
|------|-----|----------|
| `doc_code` | string \| null | Код документа. Переопределяет автоматически извлечённый |
| `title` | string \| null | Название документа |
| `mks_oks_code` | string \| null | Код МКС/ОКС |
| `okstu_code` | string \| null | Код ОКСТУ |
| `udk_code` | string \| null | Код УДК |
| `validity_status` | string \| null | Юридический статус: `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `valid_from` | string \| null | Дата начала действия (YYYY-MM-DD). По умолчанию `1000-01-01` |
| `valid_until` | string \| null | Дата окончания действия (YYYY-MM-DD). Для бессрочных — в БД хранится `9999-12-31`, но в API-ответах возвращается как `null`. При `null` от UI backend подставляет `dateMax` |
| `issuing_body` | string \| null | Издатель / утвердивший орган |
| `source_type` | string \| null | Тип источника: `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `jurisdiction` | string \| null | Юрисдикция: `RU`, `EU`, `US`, `NO`, `INTL` |

**Ответ `200` (approve):**

```json
{
  "draft_id": 1,
  "status": "approved",
  "action": "approve",
  "document_id": 1300,
  "message": "Черновик завершён, документ создан в Registry. Запущен Пайплайн 2 (индексация).",
  "decided_by": "user_10",
  "decided_at": "2026-06-05T10:05:00Z"
}
```

**Ответ `200` (confirm):**

```json
{
  "draft_id": 2,
  "status": "validation",
  "action": "confirm",
  "document_id": null,
  "message": "Черновик подтверждён. Запущена повторная валидация с учётом metadata_overrides.",
  "decided_by": "user_10",
  "decided_at": "2026-06-05T10:12:00Z"
}
```

**Ответ `200` (reject):**

```json
{
  "draft_id": 2,
  "status": "discarded",
  "action": "reject",
  "document_id": null,
  "message": "Черновик отклонён. Можно загрузить файл повторно для новой попытки.",
  "decided_by": "user_10",
  "decided_at": "2026-06-05T10:12:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Идентификатор черновика |
| `status` | string | Новый статус: `approved`, `validation` или `discarded` |
| `action` | string | Выполненное действие: `approve`, `confirm` или `reject` |
| `document_id` | bigint \| null | ID документа в Registry (null при reject) |
| `message` | string | Описание результата |
| `decided_by` | string | Субъект (пользователь или сервис) |
| `decided_at` | datetime | Время решения (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |
| 409 | `DRAFT_ALREADY_DECIDED` | Решение уже принято (статус не `ready_for_approve`/`review_required`) |
| 409 | `DUPLICATE_DOCUMENT` | **S8**: Конфликт уникальности — документ с таким `title_hash_sha256` уже существует в Registry. Возникает при `action: approve` или `confirm`, если после применения `metadata_overrides` бизнес-ключ совпал с существующим |
| 400 | `VALIDATION_ERROR` | Некорректный `action` (допустимы: `approve`, `confirm`, `reject`) |
| 400 | `EMPTY_DOCUMENT` | Нельзя аппрувнуть пустой черновик (0 страниц) |
| 400 | `INVALID_ACTION_FOR_STATUS` | Действие не применимо к текущему статусу (например, `confirm` для `ready_for_approve`) |

> **Обработка пустого документа:** Если черновик содержит 0 страниц (пустой PDF/изображение), решение `approve` недоступно. Черновик переводится в статус `discarded` с кодом ошибки `EMPTY_DOCUMENT`. Такой черновик может быть только отклонён (`reject`) или удалён. Пустой документ не может покинуть черновики.

---

### PATCH /drafts/{draft_id}/metadata

**Сохранение ручных правок метаданных черновика без принятия решения.** Позволяет оператору редактировать метаданные, переданные Converter-validator, до вызова `PATCH /decide`.

Доступно для черновиков в статусе `ready_for_approve` и `review_required`.

**Тело запроса:**

```json
{
  "doc_code": "311-05-1950ц-ИЗМ1",
  "title": "ЦИРКУЛЯРНОЕ ПИСЬМО № 311-05-1950ц (изм.1)",
  "mks_oks_code": "47.020.01",
  "okstu_code": null,
  "udk_code": "629.5.021",
  "validity_status": "active",
  "valid_from": "2026-01-01",
  "valid_until": null,
  "issuing_body": "РОССИЙСКИЙ МОРСКОЙ РЕГИСТР СУДОХОДСТВА",
  "source_type": "RMRS",
  "jurisdiction": "RU"
}
```

**Поля запроса (все опциональны — обновляются только переданные):**

| Поле | Тип | Описание |
|------|-----|----------|
| `doc_code` | string \| null | Код документа |
| `title` | string \| null | Название документа |
| `mks_oks_code` | string \| null | Код МКС/ОКС |
| `okstu_code` | string \| null | Код ОКСТУ |
| `udk_code` | string \| null | Код УДК |
| `validity_status` | string \| null | Юридический статус: `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `valid_from` | string \| null | Дата начала действия (YYYY-MM-DD). По умолчанию — `1000-01-01`. Если не указана, может быть выведена из `year` (01-01-{year}) |
| `valid_until` | string \| null | Дата окончания действия (YYYY-MM-DD). Для бессрочных — в БД хранится `9999-12-31`, но в API-ответах возвращается как `null`. При `null` от UI backend подставляет `dateMax` |
| `issuing_body` | string \| null | Издатель / утвердивший орган |
| `source_type` | string \| null | Тип источника: `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `jurisdiction` | string \| null | Юрисдикция: `RU`, `EU`, `US`, `NO`, `INTL` |

**Логика обработки (S5):**
1. При изменении любого из полей, участвующих в бизнес-ключе (`era`, `source_type`, `mks_oks_code`, `okstu_code`, `doc_code`, `title`) — Orchestrator **пересчитывает** `title_hash_sha256` и `title_key` по формуле нормализатора (см. `specifications/normalizer_specification.md` §2.1).
2. После пересчёта бизнес-ключа Orchestrator выполняет **проверку уникальности** через `POST /registry/documents/check-uniqueness`.
3. Если найден конфликт — возвращается ошибка `409 DUPLICATE_DOCUMENT`, правки не сохраняются.
4. Если уникальность подтверждена — новые значения `preview_metadata`, `title_hash_sha256`, `title_key` сохраняются в `registry.drafts`.
5. `valid_from` / `valid_until` при необходимости выводятся из `year`: если `year = 2023`, а `valid_from` не задан → `valid_from = 2023-01-01`.

**Ответ `200`:**

```json
{
  "draft_id": 1,
  "status": "ready_for_approve",
  "preview_metadata": { ... },
  "title_hash_sha256": "<новый-хеш>",
  "title_key": "<новая-строка>",
  "message": "Метаданные обновлены. Бизнес-ключ пересчитан, уникальность подтверждена.",
  "updated_at": "2026-06-05T10:03:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | ID черновика |
| `status` | string | Текущий статус черновика (не меняется) |
| `preview_metadata` | object | Обновлённые метаданные |
| `title_hash_sha256` | string | Пересчитанный бизнес-ключ (SHA-256) |
| `title_key` | string | Исходная строка конкатенации (аудит) |
| `message` | string | Описание результата |
| `updated_at` | datetime | Время обновления (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |
| 409 | `DUPLICATE_DOCUMENT` | После пересчёта бизнес-ключа найден конфликт с существующим документом в Registry |
| 400 | `VALIDATION_ERROR` | Некорректные значения полей |
| 400 | `INVALID_ACTION_FOR_STATUS` | Статус черновика не допускает редактирование метаданных (только `ready_for_approve` и `review_required`) |

---

### DELETE /drafts/{draft_id}

Удалить черновик вручную. Работает для любых статусов.

**Ответ `200`:**

```json
{
  "draft_id": 3,
  "deleted_at": "2026-06-05T10:15:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Идентификатор удалённого черновика |
| `deleted_at` | datetime | Время удаления (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |

> **Примечание:** черновики со статусом `approved` также можно удалить — это не влияет на уже созданный документ в Registry.

---

### GET /health

Агрегированная проверка состояния системы.

Orchestrator последовательно опрашивает `GET /health` каждого внутреннего сервиса
(см. [Мониторинг (Health Check)](common_api.md#мониторинг-health-check)) и возвращает сведённый результат.

> **Примечание**: Этот эндпоинт — для внутреннего мониторинга сервиса. Внешним системам следует использовать `/api/v1/system/health` (Gateway).

```json
{
  "status": "ok",
  "service": "orchestrator",
  "version": "1.0.0"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | Общий статус системы: `ok`, `degraded`, `error` |
| `service` | string | Идентификатор сервиса (`orchestrator`) |
| `version` | string | Версия Orchestrator |

Формат соответствует общему стандарту health для внутренних сервисов (см. `common_api.md`).

Агрегированные статусы зависимых сервисов, БД, индекса и очередей — не входят в health-ответ. Эти данные возвращаются через Gateway `/api/v1/system/health` (для внешнего мониторинга) и `/api/v1/monitor/metrics` (для метрик).

