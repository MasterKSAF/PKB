## API Orchestrator Service (orchestrator-service:8081)

Координатор пайплайнов 1 и 2. Оркестрирует конвейер обработки документов: загрузка → task → вызов Registry для создания черновика → OCR/Parser → Converter-validator → Registry.

**Orchestrator НЕ занимается чтением данных Registry.** Чтение черновиков, документов, страниц, версий, истории — через Gateway напрямую в Registry Service (см. [Разграничение ответственности](../guide.md#разграничение-ответственности-orchestrator-vs-registry)).

Orchestrator отвечает только за:
- Управление жизненным циклом черновика (upload, preview, decide)
- Координацию пайплайнов (вызов OCR/Parser, Converter-validator, Registry internal API, RAG Builder)
- Ведение этапов задачи в `pipeline.task_steps`
- Связь данных Registry с задачами пайплайна (GET `/{drafts,documents}/{id}/tasks`)
- Статус обработки (GET `/documents/{id}/status`, `/documents/queue`, `/documents/{id}/errors`)

**Базовый URL (внутренний)**: `http://127.0.0.1:8081/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](common_api.md#формат-ответа).

Для эндпоинтов с пагинацией используется формат `{ items: [...], meta: { total, page, page_size } }` — см. [common_api.md](common_api.md#пагинация).

### Группы

| Группа      | Описание                                                            |
| ----------- | ------------------------------------------------------------------- |
| `documents` | Статус обработки, очередь, ошибки, версии, переобработка             |
| `drafts`    | Управление загрузкой, preview, решение (approve/reject), метаданные  |
| `tasks`     | Мониторинг задач и шагов пайплайна (read-only, admin)               |
| `health`    | Агрегированный health-check                                         |

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).

> **Примечание:** Группа `tasks` — внутренняя (internal). Эндпоинты `/tasks/{task_id}/...` используются только для межсервисного взаимодействия и админского анализа. `task` — агрегатор этапов пайплайна, каждый этап хранит входные/выходные JSON-контейнеры сервисов.

### Содержание

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/drafts` | Загрузка файла (создание черновика) |
| POST | `/drafts/{draft_id}/preview` | Запуск preview-обработки черновика |
| GET | `/drafts/{draft_id}/preview/status` | Статус preview черновика |
| PATCH | `/drafts/{draft_id}/decide` | Решение по черновику (approve/reject) |
| PATCH | `/drafts/{draft_id}/metadata` | Обновление метаданных черновика |
| DELETE | `/drafts/{draft_id}` | Удаление черновика |
| GET | `/drafts/{draft_id}/tasks` | Связь черновика с задачами |
| GET | `/documents/{doc_id}/tasks` | Связь документа с задачами |
| POST | `/documents/{doc_id}/versions` | Создание версии документа |
| POST | `/documents/{doc_id}/reprocess` | Переобработка документа |
| GET | `/documents/{doc_id}/status` | Статус обработки документа |
| GET | `/documents/{doc_id}/errors` | Ошибки обработки документа |
| GET | `/documents/queue` | Очередь обработки документов |
| GET | `/tasks` | Список всех задач |
| GET | `/tasks/stats` | Статистика задач |
| GET | `/tasks/{task_id}/status` | Статус задачи (longpoll) |
| GET | `/tasks/{task_id}/steps` | Шаги задачи |
| GET | `/health` | Health-check сервиса |

---

## Группа documents

Оркестратор отвечает за статус обработки, очередь, ошибки, версионирование и переобработку. Чтение карточки документа, страниц, файлов, истории — через Registry (см. [registry_service_api.md](registry_service_api.md#группа-documents)).

### POST /drafts — Загрузка файла (создание черновика)

Загрузка файла с **обязательным созданием черновика**. Без черновика загрузить документ невозможно.

Orchestrator вычисляет SHA-256 содержимого, определяет формат, создаёт задачу (`pipeline.tasks`) и запись черновика в Registry (`POST /registry/drafts`), помещает в очередь Celery. Двухфазный конвейер: **Preview** (OCR/Parser preview → Converter-validator preview → решение пользователя) → **Full** (OCR/Parser → Converter-validator → Registry → RAG Builder).

> **Бизнес-ключ не вычисляется на этом этапе.** `title_hash_sha256` и `title_key` будут вычислены Converter-validator на этапе preview (см. `POST /converter/preview`). Оркестратор не имеет собственного нормализатора и не вычисляет бизнес-ключ.

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
  "created_at": "2026-05-15T10:00:00Z"
}
```

> **Примечание:** `title_hash_sha256` и `title_key` не возвращаются на этом этапе. Бизнес-ключ будет вычислен Converter-validator при вызове `POST /drafts/{draft_id}/preview` (см. `pipeline1-formation.md` §Preview-фаза).

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

Список задач для черновика.

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

### GET /documents/{doc_id}/tasks

Список задач пайплайна для документа. Позволяет найти все задачи, связанные с документом (включая задачи по черновикам, создавшим данный документ, и задачи переобработки).

**Путь:** `/api/v1/documents/{doc_id}/tasks`
**Метод:** `GET`
**Доступ:** `system_admin`, `knowledge_admin`

**Ответ `200`:**

```json
{
  "document_id": 1,
  "tasks": [
    {
      "task_id": 420000,
      "draft_id": 420000,
      "status": "indexed",
      "pipeline_stage": "indexation",
      "initiated_by": "orchestrator",
      "created_at": "2026-06-05T10:00:00Z",
      "updated_at": "2026-06-05T10:25:00Z"
    }
  ]
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `tasks` | array | Массив задач: `task_id`, `draft_id`, `status`, `pipeline_stage`, `initiated_by`, `created_at`, `updated_at` |

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

### POST /documents/{doc_id}/reprocess

Асинхронная переобработка документа без создания нового черновика.
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
Orchestrator вызывает `DELETE /rag/build/{doc_id}` для очистки существующих чанков документа из векторного индекса. Только после успешного удаления запускается новый `POST /rag/build`. Если `DELETE` вернул ошибку, переиндексация отменяется с кодом `CLEANUP_FAILED`.

**Ошибки**: `404` — документ не найден, `409` — документ в обработке.

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

---

## Группа drafts

**Чтение черновиков — Registry.** `GET /drafts`, `GET /drafts/{id}`, `GET /drafts/{id}/preview` — через Gateway напрямую в Registry (см. [registry_service_api.md](registry_service_api.md#группа-drafts)).

Orchestrator координирует **запись и жизненный цикл черновиков**: загрузка, preview, решение, metadata, удаление. Все write-эндпоинты вызывают Registry internal API.

**Принцип работы:**
- `POST /drafts` → создание task + `POST /registry/drafts`
- `POST /drafts/{id}/preview` → запуск OCR/Parser → Converter
- `PATCH /drafts/{id}/decide` → `PATCH /registry/drafts/{id}/status` + при `approve` → `POST /registry/documents`
- `PATCH /drafts/{id}/metadata` → `POST /validate/metadata` (Converter) → `PATCH /registry/drafts/{id}/metadata`
- `DELETE /drafts/{id}` → `DELETE /registry/drafts/{id}` + каскад `pipeline.task_steps`


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
  - Если preview **завершён** (`status=ready_for_approve` или `review_required`) — `409 DRAFT_ALREADY_PREVIEWED`. Для запуска заново удалите черновик и загрузите файл повторно.
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
| `metadata_overrides` | object | Нет | **D13**: ручные правки метаданных оператора. Может быть передан при `action: confirm` или `approve`. Если метаданные уже сохранены через `PATCH /metadata`, это поле можно не передавать — Orchestrator использует ранее сохранённые значения. Если поле передано — перезаписывает сохранённые. Допустимые поля — см. таблицу ниже |

**Логика обработки при approve/confirm:**
1. Orchestrator собирает **финальный снимок метаданных** с приоритетом:
   - `metadata_fields` из `POST /drafts` (база)
   - OCR/Parser извлечённые метаданные (перезаписывают)
   - Converter-validator валидированные метаданные (перезаписывают)
   - `metadata_overrides` пользователя (перезаписывают)
2. Orchestrator отправляет финальный снимок в **единую точку** вычисления бизнес-ключа — `POST /validate/metadata` — для нормализации названия и пересчёта `title_hash_sha256`.
3. После пересчёта — **повторная проверка уникальности** через `POST /registry/documents/check-uniqueness` (защита от race condition: между preview и approve БД могла измениться).
4. Если найден конфликт — `409 DUPLICATE_DOCUMENT`, черновик не завершается.
5. Если уникальность подтверждена — черновик завершается, документ создаётся в Registry.

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
1. Оркестратор собирает все поля метаданных (текущие из черновика + переданные в запросе) и отправляет в Converter-validator — **единую точку** нормализации и вычисления бизнес-ключа: `POST /validate/metadata`.
2. Converter-validator нормализует название, приводит `source_type` и `era` к нижнему регистру, вычисляет `title_hash_sha256` и `title_key`, возвращает результат.
3. Orchestrator выполняет **проверку уникальности** через `POST /registry/documents/check-uniqueness` с полученным `title_hash_sha256`.
4. Если найден конфликт — возвращается ошибка `409 DUPLICATE_DOCUMENT`, правки не сохраняются.
5. Если уникальность подтверждена — новые значения `preview_metadata`, `title_hash_sha256`, `title_key` сохраняются в `registry.drafts`.
6. `valid_from` / `valid_until` при необходимости выводятся из `year`: если `year = 2023`, а `valid_from` не задан → `valid_from = 2023-01-01`.

**Ответ `200`:**

```json
{
  "draft_id": 1,
  "status": "ready_for_approve",
  "preview_metadata": { ... },
  "title_hash_sha256": "<новый-хеш>",
  "title_key": "<новая-строка>",
  "message": "Метаданные обновлены. Бизнес-ключ пересчитан через Converter-validator, уникальность подтверждена.",
  "updated_at": "2026-06-05T10:03:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | ID черновика |
| `status` | string | Текущий статус черновика (не меняется) |
| `preview_metadata` | object | Обновлённые метаданные |
| `title_hash_sha256` | string | Пересчитанный бизнес-ключ (SHA-256) — вычислен Converter-validator |
| `title_key` | string | Исходная строка конкатенации (аудит) — вычислена Converter-validator |
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

