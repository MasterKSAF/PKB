## API Orchestrator Service (orchestrator-service:8081)

Координатор пайплайнов 1 и 2. Оркестрирует конвейер обработки документов: загрузка → task → вызов Registry для создания черновика → OCR/Parser → Converter-validator → Registry.  
Ведение этапов задачи: запись входных/выходных данных каждого сервиса (OCR/Parser, Converter-validator) в `pipeline.task_steps`.  
Вызов Registry для CRUD операций с данными черновиков.

**Базовый URL (внутренний)**: `http://127.0.0.1:8081/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](../common_api.md#формат-ответа).

Для эндпоинтов с пагинацией используется формат `{ items: [...], meta: { total, page, page_size } }` — см. [common_api.md](../common_api.md#пагинация).

### Группы

| Группа      | Описание                                                            |
| ----------- | ------------------------------------------------------------------- |
| `monitor`   | Мониторинг, метрики и health                                        |
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
| `source_type`  | string | Да             | `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `OTHER` |
| `title`        | string | Нет            | Название документа                                                 |
| `doc_code`     | string | Нет            | Регистрационный номер (напр. `20868-81`)                           |
| `mks_oks_code` | string | Нет            | Код МКС/ОКС                                                        |
| `okstu_code`   | string | Нет            | Код ОКСТУ                                                          |
| `era`          | string | Нет            | `USSR`, `CIS`, `RF`, `CURRENT`                                     |
| `jurisdiction` | string | Нет            | `RU`, `EU`, `US`, `NO`, `INTL`                                     |
| `issuing_body` | string | Нет            | Организация-издатель                                               |
| `metadata`     | string | Нет            | JSON-строка с доп. данными                                         |

> **Примечание**: В запросе `metadata` передаётся как JSON-строка (string). Сервер парсит её в объект, который возвращается в ответе `GET /documents/{doc_id}` как структурированный JSON. Допустимые ключи: `year`, `udc`, `tags`, `notes`.

**Ответ `202`**:

```json
{
  "draft_id": 420000,
  "task_id": 420000,
  "version_id": 420001,
  "status": "uploaded",
  "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "file_size_bytes": 2048576,
  "is_duplicate_file": false,
  "is_duplicate_document": false,
  "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "created_at": "2026-05-15T10:00:00Z"
}
```

> **Примечание:** `draft_id` назначается Registry при создании записи черновика. `document_id` назначается Registry при завершении черновика. Первичный внешний идентификатор на этапе загрузки и preview — `draft_id`. `task_id` — внутренний сквозной ID задачи (`pipeline.tasks`), используется только для межсервисного взаимодействия и администрирования.

**Коды ошибок**:
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
  "document_id": null,
  "status": "previewing",
  "pipeline_stage": "preview",
  "progress_percent": 45,
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
| `status` | string | Текущий статус (`uploaded`, `previewing`, `ready_for_approve`, `processing`, `created`, `indexing`, `indexed`, `failed`) |
| `pipeline_stage` | string | Этап конвейера: `upload`, `preview`, `decision`, `full`, `registry`, `indexation` |
| `progress_percent` | int | Общий прогресс (0–100) |
| `steps` | array | Массив этапов задачи с промежуточными данными (`step_name`, `service_name`, `status`, `input_data`, `output_data`, `started_at`, `completed_at`) |
| `created_at` | string | Время создания задачи (ISO 8601) |
| `updated_at` | string | Время последнего обновления (ISO 8601) |

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
| `tasks` | array | Массив задач: `task_id`, `status`, `pipeline_stage`, `initiated_by`, `created_at`, `updated_at` |

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
      "uploaded_at": "2026-05-15T10:00:00Z",
      "uploaded_by": "Иванов И.И."
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
      "uploaded_by": "Иванов И.И.",
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
    "udc": "629.5.021",
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
  "uploaded_by": "Иванов И.И.",
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
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при изменении статуса или по таймауту. Подробнее — [Модель выполнения](../api/common_api.md#модель-выполнения-sync--async). |

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
  "chunk_summary": {"sections": 12, "chunks": 34, "embeddings": 34},
  "started_at": "2025-06-06T10:00:00Z",
  "completed_at": "2025-06-06T10:25:00Z"
}
```

**Статусы Formation (Формирование документа)**: `uploaded` → `previewing` → `ready_for_approve` → `processing` → `created` / `failed`.

> **Таймаут `uploaded`**: Если preview не запущен в течение 1 часа после загрузки, статус автоматически меняется на `failed` с кодом `PREVIEW_TRIGGER_TIMEOUT`.

**Статусы Indexation (Индексация)**: `pending` → `indexing` → `indexed` / `failed`. Подробнее — [статусная модель FSM](../pipelines/pipeline2-indexation.md#статусная-модель-fsm).

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

### POST /documents/{doc_id}/approve

Утверждение документа. Переводит черновик в статус `approved` и запускает запись в Registry (Пайплайн 1, Этап 3).

**Запрос**:

```json
{
  "force": false,
  "comment": "Все ошибки исправлены, контейнер валиден"
}
```

| Поле      | Тип    | Обязательность | Описание                            |
| --------- | ------ | -------------- | ----------------------------------- |
| `force`   | bool   | Нет (по умолч. false) | Если `true` — обойти блокирующие ошибки валидации и перевести документ в статус `approved`. Все ошибки валидации сохраняются в `GET /documents/{doc_id}/errors` с пометкой `forced: true`. |
| `comment` | string | Нет            | Комментарий                         |

**Ответ `202`**:

```json
{
  "document_id": 1,
  "status": "approved",
  "task_id": 420001,
  "approved_by": "ivanov_ai",
  "approved_at": "2026-05-15T12:00:00Z"
}
```

**Ошибки**: `409` — неверный статус для аппрува, `422` — контейнер не валиден (без `force`).

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

**Ошибки**: `404` — документ не найден, `409` — документ в обработке.

---

### DELETE /documents/{doc_id}

**Soft-delete:** документ помечается как удалённый (`deleted_at`), но запись в БД сохраняется. Связанные сущности (секции, версии, история, чанки) также помечаются как недоступные. Повторный вызов возвращает `404 NOT_FOUND`.

**Ответ `200`**:

```json
{
  "document_id": 1,
  "deleted_at": "2026-05-15T10:30:00Z"
}
```

**Коды ошибок**:
| HTTP | `error.code` | Когда возникает |
|------|-------------|----------------|
| 400 | VALIDATION_ERROR | Некорректный `doc_id` в пути |
| 401 | UNAUTHORIZED | Отсутствует или невалидный JWT |
| 403 | FORBIDDEN | Нет прав на удаление документа |
| 404 | DOCUMENT_NOT_FOUND | Документ не найден или уже удалён |
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
      "uploaded_by": "Иванов И.И.",
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
| `status` | string | Нет | Фильтр по статусу: `uploaded`, `previewing`, `ready_for_approve`, `approved`, `discarded` |
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
      "preview_metadata": {
        "doc_code": "ГОСТ 20868-81",
        "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ",
        "document_type": "normative",
        "year": "1981",
        "revision": null
      },
      "document_id": 1300,
      "created_at": "2026-06-05T10:00:00Z",
      "updated_at": "2026-06-05T10:05:00Z"
    },
    {
      "draft_id": 2,
      "task_id": 101,
      "file_key": "f-abc123",
      "document_key": "sha256:def456",
      "status": "discarded",
      "confidence": 0.45,
      "preview_metadata": {
        "doc_code": "ГОСТ 20868-81",
        "title": "СТОЙКИ УСТАНОВОЧНЫЕ",
        "document_type": "normative",
        "year": "1981",
        "revision": null
      },
      "error_code": "LOW_CONFIDENCE",
      "error_message": "Confidence below threshold (0.45 < 0.7)",
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

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Уникальный идентификатор черновика |
| `task_id` | bigint | Внутренний ID задачи (internal) |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256) |
| `status` | string | Статус черновика: `uploaded`, `previewing`, `ready_for_approve`, `approved`, `discarded` |
| `confidence` | float | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | Preview-метаданные: `doc_code`, `title`, `document_type`, `year`, `revision` |
| `document_id` | bigint \| null | ID документа в Registry (FK → `registry.documents`), созданный по результатам черновика |
| `error_code` | string \| null | Код ошибки при `discarded` |
| `error_message` | string \| null | Описание ошибки |
| `created_at` | string | Время создания (ISO 8601) |
| `updated_at` | string | Время последнего изменения (ISO 8601) |

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
  "preview_metadata": {
    "doc_code": "ГОСТ 20868-81",
    "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
    "document_type": "normative",
    "year": "1981",
    "revision": null
  },
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
  "error_code": null,
  "error_message": null,
  "created_by": "user_10",
  "created_at": "2026-06-05T10:00:00Z",
  "updated_at": "2026-06-05T10:02:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Уникальный идентификатор черновика |
| `task_id` | bigint | Внутренний ID задачи (internal) |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256) |
| `status` | string | Статус черновика |
| `confidence` | float | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | Извлечённые метаданные |
| `raw_data` | object | Сырые данные распознавания (`raw_ocr_v4`) — результат Parser или OCR |
| `document_id` | bigint \| null | ID документа в Registry, созданный по результатам черновика |
| `error_code` | string \| null | Код ошибки |
| `error_message` | string \| null | Описание ошибки |
| `created_by` | string | Кто создал черновик |
| `created_at` | string | Время создания (ISO 8601) |
| `updated_at` | string | Время последнего изменения (ISO 8601) |

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
  "preview_metadata": {
    "doc_code": "ГОСТ 20868-81",
    "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
    "document_type": "normative",
    "year": "1981",
    "revision": null
  },
  "created_at": "2026-06-05T10:00:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Уникальный идентификатор черновика |
| `task_id` | bigint | Внутренний ID задачи (internal) |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256) |
| `status` | string | Статус черновика |
| `confidence` | float | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | Извлечённые метаданные |
| `created_at` | string | Время создания (ISO 8601) |

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
| `estimated_completion` | string | Предполагаемое время завершения |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |
| 409 | `DRAFT_ALREADY_PREVIEWED` | Preview уже запущен или завершён |

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
  "preview": {
    "doc_code": "ГОСТ 20868-81",
    "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
    "document_type": "normative",
    "year": "1981",
    "revision": null
  },
  "duplicates": [],
  "decision_required": false
}
```

| Поле | Тип | Описание |
|---|---|---|
| `draft_id` | bigint | ID черновика |
| `status` | string | Статус превью (`pending`, `processing`, `completed`, `failed`) |
| `ocr_parser_status` | string | Статус выбранного сервиса распознавания |
| `converter_validator_status` | string | Статус converter-validator |
| `preview` | object | Метаданные превью |
| `duplicates` | array | Массив найденных дубликатов |
| `decision_required` | bool | Требуется ли решение пользователя |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |

---

### PATCH /drafts/{draft_id}/decide

**Основной эндпоинт для принятия решения по загруженному документу.** Доступно только для черновиков в статусе `ready_for_approve`. После решения черновик либо завершается с записью в Registry (`approve`), либо отклоняется (`reject`).

**Тело запроса:**

```json
{
  "action": "approve",
  "comment": "Метаданные корректны, уверенность 0.92"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| `action` | string | Да | Решение: `approve` — завершить черновик, записать документ в Registry; `reject` — отклонить (`discarded`) |
| `comment` | string | Нет | Комментарий оператора |

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
| `status` | string | Новый статус: `approved` или `discarded` |
| `action` | string | Выполненное действие: `approve` или `reject` |
| `document_id` | bigint \| null | ID документа в Registry (null при reject) |
| `message` | string | Описание результата |
| `decided_by` | string | Кто принял решение |
| `decided_at` | string | Время решения (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |
| 409 | `DRAFT_ALREADY_DECIDED` | Решение уже принято (статус не `ready_for_approve`) |
| 400 | `VALIDATION_ERROR` | Некорректный `action` (допустимы: `approve`, `reject`) |
| 400 | `EMPTY_DOCUMENT` | Нельзя аппрувнуть пустой черновик (0 страниц) |

> **Обработка пустого документа:** Если черновик содержит 0 страниц (пустой PDF/изображение), решение `approve` недоступно. Черновик переводится в статус `discarded` с кодом ошибки `EMPTY_DOCUMENT`. Такой черновик может быть только отклонён (`reject`) или удалён. Пустой документ не может покинуть черновики.

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
| `deleted_at` | string | Время удаления (ISO 8601) |

**Возможные ошибки:**

| HTTP | Код | Описание |
|------|-----|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не существует |

> **Примечание:** черновики со статусом `approved` также можно удалить — это не влияет на уже созданный документ в Registry.

---

## Группа monitor

### GET /monitor/health

> **Примечание**: Этот эндпоинт — для внутреннего мониторинга сервиса. Внешним системам следует использовать `/api/v1/system/health` (Gateway).

Агрегированная проверка состояния системы.

Orchestrator последовательно опрашивает `GET /health` каждого внутреннего сервиса
(см. [Мониторинг (Health Check)](common_api.md#мониторинг-health-check)) и возвращает сведённый результат.

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 234567,
  "services": {
    "auth": "ok",
    "rag_builder": "ok",
    "rag_search": "ok",
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
| `status` | string | Общий статус системы: `ok`, `degraded`, `error` |
| `version` | string | Версия Orchestrator |
| `uptime_seconds` | int | Время работы с момента запуска |
| `services` | object | Статусы внутренних сервисов (ключ — имя сервиса, значение — `ok`, `degraded`, `error`) |
| `database` | string | Статус подключения к БД |
| `search_index` | string | Состояние поискового индекса |
| `ocr_queue` | string | Состояние очереди OCR |
| `storage` | string | Статус файлового хранилища (MinIO) |

### GET /monitor/metrics

Метрики качества системы.

```json
{
  "control_metrics": { "ocr_quality": 0.984, "retrieval_quality": 0.91, "answers_with_sources": 0.96, "avg_latency_ms": 1420 },
  "answer_metrics": { "useful_rate": 0.84, "rated_answers": 43, "flagged_for_review": 5, "open_questions": 3 },
  "logs": [ { "time": "12:34:02", "type": "search", "text": "...", "level": "info" } ]
}
```

| Поле | Тип | Описание |
|---|---|---|
| `control_metrics` | object | Объект с метриками качества контроля |
| `control_metrics.ocr_quality` | number | Качество OCR (0–1) |
| `control_metrics.retrieval_quality` | number | Качество поиска (0–1) |
| `control_metrics.answers_with_sources` | number | Доля ответов с источниками (0–1) |
| `control_metrics.avg_latency_ms` | number | Средняя задержка, мс |
| `answer_metrics` | object | Объект с метриками качества ответов |
| `answer_metrics.useful_rate` | number | Доля полезных ответов (0–1) |
| `answer_metrics.rated_answers` | int | Количество оценённых ответов |
| `answer_metrics.flagged_for_review` | int | Количество отмеченных на ревью |
| `answer_metrics.open_questions` | int | Количество открытых вопросов |
| `logs` | array | Массив записей лога |
| `logs[].time` | string | Время события |
| `logs[].type` | string | Тип события |
| `logs[].text` | string | Текст события |
| `logs[].level` | string | Уровень логирования |
