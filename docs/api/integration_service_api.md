## API Integration Service (integration-service:8084)

Сервис интеграции с внешними системами и управления файлами.

*Внутренний сервис. Не предназначен для прямого вызова из frontend. Публичный API — в Orchestrator Service.*

Базовый путь: `/api/v1`

### Группы

| Группа | Описание |
|--------|----------|
| `files` | Загрузка, получение и удаление файлов |
| `meridian` | Экспорт в ИС «Меридиан» |
| `external` | Статус внешних систем |

### POST /files/upload

Загрузка файла в общее хранилище.

**Запрос**: `multipart/form-data`

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `file` | File | Да | Бинарный файл |
| `related_document_id` | string | Нет | ID связанного документа |

**Ответ `201`**:

```json
{
  "file_id": "file-xyz",
  "filename": "page_5.png",
  "size": 1048576,
  "mime_type": "image/png",
  "url": "/files/file-xyz",
  "uploaded_at": "2026-04-27T10:01:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `file_id` | string | ID файла |
| `filename` | string | Имя файла |
| `size` | int | Размер в байтах |
| `mime_type` | string | MIME-тип |
| `url` | string | URL для доступа |
| `uploaded_at` | string | Дата загрузки |

### GET /files/{file_id}

Получение бинарного потока файла.

**Ответ `200`**: Бинарные данные файла с корректными заголовками `Content-Type` и `Content-Length`.

### DELETE /files/{file_id}

Удаление файла.

**Ответ `200`**:

```json
{
  "file_id": "file-xyz",
  "deleted_at": "2026-04-27T10:30:00Z"
}
```

### GET /files/{file_id}/info

Метаданные файла без скачивания.

**Ответ `200`**: Объект метаданных (аналогичен ответу загрузки).

### POST /meridian/export

Отправка структурированных данных в систему «Меридиан».

**Запрос**:

```json
{
  "document_id": "doc-8a3f2b",
  "data": {}
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `document_id` | string | Да | ID документа |
| `data` | object | Да | Данные для экспорта |

**Ответ `200`**:

```json
{
  "export_id": "exp-001",
  "external_id": "mer-12345",
  "status": "sent",
  "sent_at": "2026-04-27T12:00:00Z",
  "response_message": "Принято"
}
```

### GET /external/status

Проверка доступности внешних систем.

**Ответ `200`**:

```json
{
  "systems": [
    {
      "api_name": "meridian",
      "status": "available",
      "last_checked": "2026-04-27T12:05:00Z",
      "latency_ms": 230
    }
  ]
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `api_name` | string | Название API |
| `status` | string | Статус: `available`, `unavailable`, `degraded` |
| `last_checked` | string | Время последней проверки |
| `latency_ms` | int | Задержка в миллисекундах |