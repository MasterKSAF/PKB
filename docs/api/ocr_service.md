## API OCR Service (ocr-service:8083)

Сервис OCR и распознавания структуры документов.

### POST /ocr/process

Пакетная обработка многостраничного PDF.

**Запрос**:

```json
{
  "file_id": "file-abc123",
  "pages": "1-5,8",
  "options": {
    "engine": "paddleocr",
    "language": "ru"
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `file_id` | string | Да | ID файла в хранилище |
| `pages` | string | Нет | Диапазон страниц (например, `"1-5,8"`) |
| `options` | object | Нет | Параметры обработки |
| `options.engine` | string | Нет | OCR-движок |
| `options.language` | string | Нет | Язык (`ru`, `en`) |

**Ответ `200`**:

```json
{
  "document_id": "temp-doc-batch",
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "confidence": 0.95,
      "engine_used": "paddleocr",
      "page_type_detected": "text",
      "blocks": [],
      "status": "success",
      "errors": []
    }
  ],
  "total_pages": 5,
  "successful_pages": 4,
  "low_confidence_pages": 1,
  "failed_pages": 0
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