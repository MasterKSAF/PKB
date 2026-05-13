## API RAG Service (rag-service:8087)

Сервис векторного поиска, генерации ответов, вычисления embeddings и валидации chunk-контейнеров.  
**Внутренний сервис.** Используется в двух режимах:  
1. **Конвейер Purgatory** — вычисление embeddings + валидация контейнеров + проверка классификации  
2. **Production RAG** — поиск и генерация ответов

**Базовый URL (внутренний)**: `http://127.0.0.1:8087/api/v1`

### Формат ответа

Успех — данные возвращаются напрямую.  
При ошибке: `{ "error": { "code": "INDEXING_FAILED", "message": "...", "details": {} } }`

---

## Режим 1: Конвейер Purgatory

### POST /rag/embed

Вычисление векторных представлений (embeddings) для чанков в контейнере.  
Вызывается Orchestrator после OCR на этапе `processing`.

RAG Service — **stateless-функция**: получает контейнер в теле запроса, вычисляет embedding для каждого текстового чанка, возвращает обновлённый контейнер в теле ответа. **Не имеет доступа к БД.**

**Запрос**:
```json
{
  "container": {
    "container_id": "cnt-001",
    "document_id": "b3a8f1c2-...",
    "chunks": [
      { "chunk_id": "chk-001", "text": "Настоящий стандарт...", "has_embedding": false }
    ],
    "images": [ ... ],
    "classification": { ... }
  },
  "model": "default"
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `container` | object | Да | **Полный JSON контейнера** (opaque для Оркестратора) |
| `container.chunks` | array | Да | Массив чанков с текстом и метаданными |
| `container.images` | array | Нет | Извлечённые изображения |
| `container.classification` | object | Нет | Извлечённые коды классификации |
| `model` | string | Нет | Модель эмбеддинга |

**Ответ `200`**:
```json
{
  "container": {
    "container_id": "cnt-001",
    "document_id": "b3a8f1c2-...",
    "chunks": [
      { "chunk_id": "chk-001", "text": "Настоящий стандарт...",
        "has_embedding": true,
        "embedding": [0.123, -0.456, ...] }
    ],
    "images": [ ... ],
    "classification": { ... }
  },
  "embedded_chunks": 34,
  "failed_chunks": 0,
  "status": "completed"
}
```

### GET /rag/embed/{task_id}/status

Статус асинхронного вычисления embeddings.

**Ответ `200`**:
```json
{
  "task_id": "embed-task-001",
  "status": "completed",
  "container_id": "cnt-001",
  "embedded_chunks": 34,
  "failed_chunks": 0,
  "completed_at": "2026-05-15T10:01:00Z"
}
```

---

### POST /rag/validate-chunks

Валидация chunk container на соответствие JSON Schema Purgatory v2.3.  
**Read-only операция** — контейнер не изменяется. RAG не имеет доступа к БД.

**Запрос**:
```json
{
  "container": {
    "container_id": "cnt-001",
    "chunks": [
      { "chunk_id": "...", "text": "...", "ltree_path": "...",
        "has_embedding": true, "embedding": [...] }
    ],
    "images": [ ... ],
    "classification": { ... }
  },
  "schema_version": "purgatory-v2.3"
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `container` | object | Да | **Полный JSON контейнера** (read-only) |
| `schema_version` | string | Нет | Версия схемы валидации |

Проверки:
- все чанки имеют `text`
- все чанки имеют `ltree_path`
- все текстовые чанки имеют `embedding`
- нет orphan-чанков (висящих без родителя)
- ltree-структура валидна (нет двойных точек, циклов)
- `chunk_type` соответствует содержимому (text/table/image/formula)

**Ответ `200`** (успех):
```json
{
  "container_id": "cnt-001",
  "status": "valid",
  "checks_passed": 14,
  "checks_failed": 0,
  "validation_detail": {
    "schema": "purgatory-v2.3",
    "chunks_all_have_text": true,
    "chunks_all_have_ltree": true,
    "chunks_all_have_embedding": true,
    "no_orphan_chunks": true,
    "ltree_structure_valid": true
  }
}
```

**Ответ `200`** (ошибки):
```json
{
  "container_id": "cnt-001",
  "status": "invalid",
  "checks_passed": 12,
  "checks_failed": 2,
  "errors": [
    {
      "chunk_id": "chk-012",
      "code": "MISSING_EMBEDDING",
      "severity": "error",
      "message": "Чанк не содержит embedding"
    },
    {
      "chunk_id": "chk-025",
      "code": "INVALID_LTREE",
      "severity": "error",
      "message": "ltree-путь root.invalid..path содержит двойную точку"
    }
  ]
}
```

---

### POST /rag/validate-classify

Проверка и подтверждение извлечённых классификационных кодов (МКС/ОКС, ОКСТУ, УДК) по справочнику Registry.

**Запрос**:
```json
{
  "document_id": "b3a8f1c2-...",
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021"
  }
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `document_id` | string | Да | ID документа |
| `classification.mks_oks_code` | string | Нет | Код МКС/ОКС |
| `classification.okstu_code` | string | Нет | Код ОКСТУ |
| `classification.udk_code` | string | Нет | Код УДК |

**Ответ `200`**:
```json
{
  "mks_status": "CONFIRMED",
  "mks_display_name": "Конструкция корпуса",
  "okstu_status": "NOT_USED",
  "udk_valid": true,
  "overall_status": "valid"
}
```

**Статусы `*_status`**:

| Значение | Описание |
|---|---|
| `CONFIRMED` | Код найден в справочнике и верифицирован |
| `PENDING_REVIEW` | Извлечён автоматически, не найден в справочнике — запись в `classifier_pending` |
| `NOT_FOUND` | Парсер не обнаружил код на первых страницах |
| `NOT_USED` | Не применяется для данной эры/типа документа |
| `UNASSIGNED` | Классификация не назначалась |

RAG Service **только проверяет** — возвращает статус по каждому коду. Никаких outbound-вызовов к другим сервисам. Решение о создании `classifier_pending` принимает **Оркестратор**, анализируя возвращённые статусы.

---

## Режим 2: Production RAG (поиск и генерация)

### POST /rag/index

Добавление чанков документа в векторный индекс для поиска.  
При повторной индексации того же `document_id` старые чанки заменяются.

**Запрос**:
```json
{
  "document_id": "doc-8a3f2b",
  "chunks": [
    {
      "chunk_id": "chk-001",
      "text": "Для ледового класса Arc4...",
      "page": 42,
      "coordinates": { "x": 120, "y": 350, "width": 400, "height": 60 },
      "metadata": { "title": "Правила РС" }
    }
  ]
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `document_id` | string | Да | ID документа |
| `chunks[].chunk_id` | string | Да | ID чанка |
| `chunks[].text` | string | Да | Текст чанка |
| `chunks[].page` | int | Да | Номер страницы |
| `chunks[].coordinates` | object | Нет | Координаты на странице |
| `chunks[].metadata` | object | Нет | Метаданные |

**Ответ `201`**:
```json
{
  "document_id": "doc-8a3f2b",
  "indexed_count": 128,
  "status": "completed"
}
```

### DELETE /rag/index/{document_id}

Удаление всех чанков документа из индекса.

**Ответ `200`**:
```json
{
  "document_id": "doc-8a3f2b",
  "deleted_count": 128,
  "status": "completed"
}
```

### POST /rag/search

Гибридный поиск (dense + sparse + pg_trgm).

**Запрос**:
```json
{
  "query": "ледовый класс Arc4",
  "top_k": 10,
  "filters": { "document_type": ["normative"] },
  "search_type": "hybrid"
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `query` | string | Да | Поисковый запрос |
| `top_k` | int | Нет | Число результатов |
| `filters` | object | Нет | Фильтры: `document_type` (string[]) |
| `search_type` | string | Нет | `hybrid`, `sparse`, `dense` |

**Ответ `200`**:
```json
{
  "results": [
    {
      "chunk_id": "chk-001",
      "document_id": "doc-norm-001",
      "page": 42,
      "text": "Для ледового класса Arc4 толщина обшивки...",
      "score": 0.92,
      "metadata": { "title": "Правила РС" }
    }
  ],
  "search_type_used": "hybrid",
  "processing_time_ms": 120
}
```

### POST /rag/generate

Генерация ответа LLM с опорой на контекстные чанки.

**Запрос**:
```json
{
  "messages": [
    { "role": "system", "content": "Ты — ассистент инженера-судостроителя." },
    { "role": "user", "content": "Какая толщина обшивки для Arc4?" }
  ],
  "context_chunks": [
    {
      "chunk_id": "chk-001",
      "text": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм.",
      "document_id": "doc-norm-001",
      "page": 42
    }
  ],
  "model": "llama-3-70b",
  "temperature": 0.2
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `messages` | array | Да | Сообщения диалога |
| `context_chunks` | array | Да | Контекстные чанки |
| `model` | string | Нет | Модель LLM |
| `temperature` | float | Нет | Температура генерации |

**Ответ `200`**:
```json
{
  "content": "Согласно Правилам, толщина обшивки для Arc4 не менее 12 мм.",
  "model_used": "llama-3-70b",
  "usage": { "prompt_tokens": 150, "completion_tokens": 40 },
  "finish_reason": "stop"
}
```
