## API OCR Service (ocr-service:8088)

Сервис OCR и распознавания структуры документов.

*Внутренний сервис. Не предназначен для прямого вызова из frontend.*

**Базовый URL (внутренний)**: `http://127.0.0.1:8088/api/v1`

### Формат ответа

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

### Группы

| Группа | Описание |
|--------|----------|
| `ocr` | Обработка и распознавание документов |

### POST /ocr/process

Асинхронная обработка PDF/DOCX: распознавание текста (OCR), выделение структуры, извлечение таблиц/изображений, чанкинг и классификация.

**Важно:** длительные операции (более 50 страниц) обрабатываются асинхронно (`202` + `task_id`). Оркестратор опрашивает статус и забирает готовый контейнер.

**Запрос**:

```json
{
  "version_id": "c4b9f2d3-...",
  "file_id": "file-abc123",
  "options": {
    "engine": "auto",
    "language": "ru",
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
| `options.engine` | string | Нет | OCR-движок (`auto`, `paddleocr`, `tesseract`, `docling`) |
| `options.language` | string | Нет | Язык (`ru`, `en`, `auto`) |
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

### GET /ocr/process/{task_id}/status

Статус асинхронной обработки. Оркестратор опрашивает до статуса `completed`.

**Ответ `200`**:

```json
{
  "task_id": "ocr-task-001",
  "status": "completed",
  "progress_percent": 100,
  "pages_processed": 12,
  "pages_total": 12,
  "avg_confidence": 0.94,
  "started_at": "2026-05-15T10:00:05Z",
  "completed_at": "2026-05-15T10:01:30Z"
}
```

**Статусы `status`**: `accepted`, `processing`, `completed`, `failed`.

### GET /ocr/process/{task_id}/container

Получение готового chunk container. Вызывается Оркестратором после `status: completed`. Контейнер содержит все чанки, изображения, классификацию. **OCR НЕ пишет контейнер в БД** — отдаёт JSON тому, кто вызвал.

**Ответ `200`**:

```json
{
  "container": {
    "container_id": "cnt-001",
    "document_id": "b3a8f1c2-...",
    "version_id": "c4b9f2d3-...",
    "version_hash": "sha256-of-payload",
    "chunks": [
      {
        "chunk_id": "chk-001",
        "sequence": 1,
        "ltree_path": "root.section1.subsection1_1",
        "heading": "1. Общие положения",
        "text": "Настоящий стандарт распространяется...",
        "page": 1,
        "chunk_type": "text",
        "token_count": 256,
        "has_embedding": false,
        "bbox": { "x": 120, "y": 350, "width": 400, "height": 60 },
        "references": ["ГОСТ 12345-77"]
      }
    ],
    "images": [
      {
        "image_id": "img-001",
        "chunk_id": "chk-020",
        "page": 8,
        "file_path": "b3a8f1c2/v1/img/fig1.png",
        "caption": "Рисунок 1 — Стойка установочная",
        "width": 800, "height": 600
      }
    ],
    "classification": {
      "mks_oks_code": "47.020",
      "mks_display_name": "Конструкция корпуса",
      "mks_status": "CONFIRMED",
      "okstu_code": null,
      "okstu_status": "NOT_USED",
      "udk_code": "629.5.021",
      "year": "1981",
      "confidence": 0.89
    }
  }
}
```

### GET /ocr/engines

Список доступных OCR‑движков.

**Ответ `200`**:

```json
{
  "engines": [
    {
      "engine_id": "paddleocr",
      "name": "PaddleOCR",
      "status": "available",
      "supported_languages": ["ru", "en"],
      "average_processing_time_ms": 1500,
      "default_for_types": ["normative", "specification"]
    },
    {
      "engine_id": "tesseract",
      "name": "Tesseract 5",
      "status": "available",
      "supported_languages": ["ru", "en"],
      "average_processing_time_ms": 2500,
      "default_for_types": ["archival_scan"]
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `engine_id` | string | ID движка |
| `name` | string | Название |
| `status` | string | Статус: `available`, `unavailable` |
| `supported_languages` | string[] | Поддерживаемые языки |
| `average_processing_time_ms` | int | Среднее время обработки |
| `default_for_types` | string[] | Типы документов по умолчанию |