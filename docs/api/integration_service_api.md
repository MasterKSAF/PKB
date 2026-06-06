## API Integration Service (integration-service:8085)

Сервис интеграции с внешними системами и управления файлами.

*Внутренний сервис. API — через Gateway Service.*

**Базовый URL (внутренний)**: `http://127.0.0.1:8085/api/v1`
**Базовый URL (через Gateway)**: `http://127.0.0.1:8080/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](../common_api.md#формат-ответа).

**Специфичные коды ошибок Integration-сервиса:**
| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 400 | `VALIDATION_ERROR` | Неверные параметры запроса |
| 404 | `FILE_NOT_FOUND` | Файл не найден |
| 413 | `FILE_TOO_LARGE` | Превышение лимита размера файла |

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
  "file_key": "file-xyz",
  "filename": "page_5.png",
  "size": 1048576,
  "mime_type": "image/png",
  "url": "/files/file-xyz",
  "uploaded_at": "2026-04-27T10:01:00Z"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `file_key` | string | Ключ файла |
| `filename` | string | Имя файла |
| `size` | int | Размер в байтах |
| `mime_type` | string | MIME-тип |
| `url` | string | URL для доступа |
| `uploaded_at` | string | Дата загрузки |

### GET /files/{file_key}

Получение бинарного потока файла.

**Ответ `200`**: Бинарные данные файла с корректными заголовками `Content-Type` и `Content-Length`.

### DELETE /files/{file_key}

Удаление файла.

**Ответ `200`**:

```json
{
  "file_key": "file-xyz",
  "deleted_at": "2026-04-27T10:30:00Z"
}
```

### GET /files/{file_key}/info

Метаданные файла без скачивания.

**Ответ `200`**: Объект метаданных (аналогичен ответу загрузки).

### POST /meridian/export

Отправка структурированных данных в систему «Меридиан».

**Запрос**:

```json
{
  "document_id": 1,
    "data": {
    "designation": "21900M2.362135.0903СБ",
    "title": "Сборочный чертёж корпуса",
    "materials": ["Сталь 09Г2С"],
    "dimensions": "1200x800x600",
    "specification_items": [
      {"position": 1, "name": "Кница", "quantity": 4}
    ]
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `document_id` | string | Да | ID документа |
| `data` | object | Да | Данные для экспорта. Структура определяется внешней системой «Меридиан». |
| `data.designation` | string | Нет | Обозначение документа |
| `data.title` | string | Нет | Наименование |
| `data.materials` | string[] | Нет | Материалы |
| `data.dimensions` | string | Нет | Габариты |
| `data.specification_items` | array | Нет | Позиции спецификации |

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