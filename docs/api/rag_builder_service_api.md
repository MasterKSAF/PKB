## API RAG Builder Service (rag-builder:8090)

Сервис построения чанков, вычисления embeddings и создания векторного индекса.  
**Внутренний сервис.** Запускается после успешного завершения Пайплайна 1 (Формирование документа). На вход получает обогащённый JSON от Registry через Orchestrator (структура документа, секции, терминология, ссылки), на выходе — статус завершения индексации.

**Архитектурные принципы (RS-6/RS-7, уточнение 20.06):**

| Принцип | Описание |
|---------|----------|
| RAG хранит только актуальный индекс | Перед новой индексацией старый индекс по `doc_id` полностью удаляется |
| `chunk_id` — технический retrieval ID | **Не используется для цитирования.** Цитаты строятся по `doc_id + section_id` |
| `section_id` стабилен внутри документа | Не меняется при переиндексации |
| `page` — 1-based | Первая страница документа = 1 |
| `bbox` — нормализованный 0..1 | `[x1, y1, x2, y2]` относительно размеров страницы |
| `parent_id` | ID родительской секции в рамках документа |

**Базовый URL (внутренний)**: `http://127.0.0.1:8090/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](common_api.md#формат-ответа).

**Специфичные коды ошибок:**
| HTTP | `error.code` | Описание |
|------|-------------|----------|

### Группы

| Группа | Описание |
|--------|----------|
| `build` | Построение чанков, вычисление эмбеддингов и индексация документа |

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).

| HTTP | Описание |
|------|----------|
| 202 | Индексация запущена (асинхронно) |
| 200 | Статус/результат |
| 500 | `BUILD_FAILED` | Ошибка построения чанков или эмбеддингов |

---

### POST /rag/build

Построение чанков, вычисление embeddings и индексация документа.  
Вызывается Orchestrator после завершения Пайплайна 1.

**Proцесс внутри:**

| Шаг | Действие | Результат |
|---|---|---|
| 1 | Чтение структуры документа из входного JSON (обогащённый контейнер от Registry) | Документ, секции, таблицы, изображения |
| 2 | Построение чанков и иерархии | Разбиение на семантические фрагменты (не более 1024 токенов по умолчанию), построение иерархии секций (path) |
| 3 | Вычисление Embeddings | Векторные представления для каждого текстового чанка |
| 4 | Построение векторного индекса | Сохранение чанков, эмбеддингов и индексов в БД |

**Очистка старого индекса:** Перед началом индексации Builder **полностью удаляет** все существующие чанки для данного `document_id` из `rag.document_chunks`. Это гарантирует, что индекс содержит только актуальные данные. Если удаление не удалось — индексация отменяется с `BUILD_FAILED`.

**Конвенции:**
- `page` — **1-based** (первая страница документа = 1). См. также `common_api.md` § Координаты блоков.
- `bbox` — **нормализованный 0..1** в формате `[x1, y1, x2, y2]`. Нормирование выполняется Converter-validator. См. [common_api.md](common_api.md#координаты-блоков-bbox).
- `parent_id` — ID родительской секции.
- `section_id` — **стабилен** внутри документа: не меняется при переиндексации, обновлении метаданных или повторном чанкинге.
- `chunk_id` — **только технический retrieval ID**. Не用于 цитирования. Может меняться при переиндексации.

Orchestrator получает JSON из Registry (через `GET /registry/documents/{doc_id}/sections`) и передаёт его в RAG Builder. Формат — см. [`schema_registry_for_rag.json`](../schema/schema_registry_for_rag.json).

Каждая секция содержит объектный `content`, структура которого зависит от `type`:

| type | Как формируется чанк | Источник данных |
|------|---------------------|----------------|
| `text` | Разбивка `content.text` на чанки ≤1024 токенов | `content.text` |
| `textBlock` | Разбивка `content.text` на чанки ≤1024 токенов | `content.text` (font display details отброшены) |
| `headerFooter` | Всё содержимое → один чанк | `content.text` |
| `table` | Весь объект целиком → один чанк | `content.markdown` (если есть), иначе сборка из `columns`/`rows` |
| `list` | Весь объект целиком → один чанк | `content.markdown` (если есть), иначе сборка из `items[]` |
| `image` | Один чанк | `content.markdown` или `content.caption + content.description` |
| `formula` | Один чанк | `content.markdown` или `content.latex + content.meaning` |

**Защищённые span'ы (`protected_spans`):** участки текста внутри секций, которые нельзя разбивать при чанкинге (например, заголовки, важные термины). Задаются как массив `{section_id, start_offset, end_offset}`. Если не указаны — чанкинг выполняется без ограничений.

**Параметры индексации (`options`) — P13-1 (конфигурация по умолчанию, решение 17.06):**

| Параметр | Прод-значение | Описание |
|----------|---------------|----------|
| `options.strategy` | `semantic_1024` | Стратегия чанкинга. **Изменено с `semantic_512`** (17.06) — новый дефолт 1024 токена. Для экспериментов: `semantic_512`, `semantic_2048`, `fixed_256`, `fixed_512` |
| `options.embedding_model` | `qwen3-embedding-4b` | **P13-1**: модель эмбеддингов (Qwen3-Embedding-4B, **внешнее API**). Endpoint и API-key — `app_settings.rag.embedding_api.endpoint` / `.api_key` |
| `options.embedding_dim` | `2048` | **P13-1**: размерность эмбеддинга. Альтернативы (экспериментально): 1536, 2560, 4096 |
| `options.embedding_quantization` | `int8` | **P13-1**: квантизация для ускорения инференса (через Infinity — см. D67) |
| `options.rerank_model` | `bge-reranker-v2-m3-int8` | **P13-3**: модель rerank. URL TEI-сервера — `app_settings.rag.rerank_url` |
| `options.protected_spans` | `[]` | Защищённые span'ы (не разбивать при чанкинге) |

> **Не передавать `version_id` в RAG** (P12-6, уточнение 17.06): `rag_documents.doc_id` ссылается на **документ** (без версии), а сам чанк хранит `document_version_id` только для аудита. Убедитесь, что запрос к RAG Builder содержит `document_id`, но **не** `version_id`. См. `parser_service_api.md` — там `version_id` тоже не нужен.

> **P4-3 (Qwen3, int8, сетка 2560/2048/1536)**: см. `docs_plans/methodology/rag_experiments_methodology.md` §2.5 — обоснование выбора модели и сетки размерностей.

> **D67 (Infinity)**: для production-деплоя используется выделенный сервис эмбеддингов **Infinity** (OpenAI-совместимое API, локальный). Для тестирования и экспериментов — внешнее API Qwen3. Конфигурируется через `app_settings.rag.embedding_api.mode = "infinity" | "external"`.

**Запрос (передаётся от Orchestrator, обогащённый JSON из Registry):**

```json
{
  "document_id": 1,
  "sections": [
    {
      "section_id": 420001,
      "document_id": 1,
      "parent_id": null,
      "clause": "1",
      "title": null,
      "level": 1,
      "path": "1",
      "page": 1,
      "bbox": [0.05, 0.05, 0.95, 0.10],
      "type": "text",
      "content": {
        "text": "Настоящий стандарт распространяется...",
        "amendments": []
      }
    },
    {
      "section_id": 420005,
      "document_id": 1,
      "parent_id": 420001,
      "clause": "6.1",
      "title": "Допуск соосности при степени точности",
      "level": 2,
      "path": "6.1.table1",
      "page": 2,
      "bbox": [0.02, 0.15, 0.98, 0.65],
      "type": "table",
      "content": {
        "markdown": "| L, мм | нормальная |\n|-------|-----------|\n| От 6 до 50 | 0,1 |",
        "columns": [
          { "name": "L_range", "header": "L, мм" },
          { "name": "normal", "header": "нормальная" }
        ],
        "rows": [
          { "row_index": 0, "cells": { "L_range": { "label": "От 6 до 50" }, "normal": { "value": 0.1 } } }
        ]
      }
    }
  ],
  "protected_spans": [
    { "section_id": 420001, "start_offset": 0, "end_offset": 128 }
  ],
  "options": {
    "strategy": "semantic_1024"
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|---------------|----------|
| `document_id` | bigint | Да | ID документа в Registry |
| `sections` | array | Да | Массив секций для индексации |
| `sections[].section_id` | bigint | Да | ID секции (стабилен внутри документа) |
| `sections[].document_id` | bigint | Да | ID документа (дублируется для удобства) |
| `sections[].parent_id` | bigint \| null | Нет | ID родительской секции. `null` для корневых секций |
| `sections[].clause` | string | Нет | Номер пункта (напр. "6.1") |
| `sections[].title` | string | Нет | Заголовок секции |
| `sections[].level` | int | Нет | Уровень вложенности секции (1 — корневой) |
| `sections[].path` | string | Да | Путь секции (напр. "1.2.3") |
| `sections[].page` | int | Hет | Номер страницы (**1-based** — первая страница документа = 1) |
| `sections[].bbox` | array[float] | Нет | Координаты на странице: `[x1, y1, x2, y2]` (**нормализованные 0..1**). См. [common_api.md](common_api.md#координаты-блоков-bbox) |
| `sections[].type` | string | Да | Тип секции: `text`, `textBlock`, `table`, `image`, `list`, `formula`, `headerFooter` |
| `sections[].content` | object/jsonb | Да | Содержимое секции (JSONB, см. `registry_for_rag_v2`) |
| `protected_spans` | array | Нет | Массив защищённых span'ов: `{section_id, start_offset, end_offset}` — участки, которые нельзя разбивать при чанкинге |
| `options` | object | Нет | Дополнительные параметры индексации |
| `options.strategy` | string | Нет | Стратегия чанкинга: `semantic_1024` (по умолчанию) |

**Ответ `202` (асинхронный запуск):**
```json
{
  "document_id": 1,
  "task_id": 420000,
  "indexing_txn_id": "txn-abc123",
  "status": "indexing"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `task_id` | bigint | ID задачи для отслеживания прогресса |
| `indexing_txn_id` | string | Уникальный ID транзакции индексации (для отладки и компенсации) |
| `status` | string | Статус: `indexing` (индексация запущена) |

Оркестратор отслеживает прогресс через `GET /rag/build/{doc_id}/status?longpoll=15`.

**Финальный ответ** (возвращается через longpoll-статус):
```json
{
  "document_id": 1,
  "status": "indexed",
  "indexed_at": "2026-05-15T12:00:18Z",
  "chunks_count": 34,
  "indexing_txn_id": "txn-abc123",
  "index_stats": {
    "sections": 12,
    "chunks": 34,
    "embeddings": 31
  },
  "warnings": [
    {
      "code": "SECTION_SKIPPED",
      "message": "Секция 420010 пропущена: пустой content.text",
      "section_id": 420010
    }
  ],
  "errors": []
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `status` | string | Статус: `indexed`, `failed` |
| `indexed_at` | datetime | Время завершения индексации (ISO 8601) |
| `chunks_count` | int | Общее количество созданных чанков |
| `indexing_txn_id` | string \| null | ID транзакции индексации (повторяется из 202-ответа для связности) |
| `index_stats.sections` | int | Количество секций (структурных единиц) |
| `index_stats.chunks` | int | Количество чанков |
| `index_stats.embeddings` | int | Количество вычисленных эмбеддингов |
| `warnings` | array | Массив предупреждений (некритичные ошибки, пропуски секций) |
| `warnings[].code` | string | Код предупреждения |
| `warnings[].message` | string | Описание |
| `warnings[].section_id` | bigint \| null | ID секции, к которой относится предупреждение |
| `errors` | array | Массив критических ошибок (индексация не завершена) |
| `errors[].code` | string | Код ошибки |
| `errors[].message` | string | Описание |

---

### DELETE /rag/build/{doc_id}

Удаление всех чанков документа из векторного индекса.  
Вызывается Orchestrator в рамках reprocess (`POST /api/v1/documents/{doc_id}/reprocess`) при `mode: reindex`.

**Ответ `200`:**
```json
{
  "document_id": 1,
  "deleted_count": 128,
  "status": "completed"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `deleted_count` | int | Количество удалённых чанков |
| `status` | string | Статус: `completed`, `failed` |

---

### GET /rag/build/{doc_id}/status

Статус индексации документа.

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `longpoll` | int | `15` | Время ожидания в секундах. Сервер держит соединение, возвращая ответ при завершении индексации или по таймауту. |

**Ответ `200`:**
```json
{
  "document_id": 1,
  "status": "indexed",
  "chunks_count": 34,
  "has_embeddings": true,
  "indexed_at": "2026-05-15T12:00:18Z",
  "warnings": [],
  "errors": []
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `status` | string | Статус: `pending_index`, `indexing`, `indexed`, `failed` |
| `chunks_count` | int | Количество созданных чанков |
| `has_embeddings` | bool | Флаг наличия эмбеддингов |
| `indexed_at` | datetime \| null | Время завершения индексации |
| `warnings` | array | Предупреждения |
| `errors` | array | Критические ошибки |

---

### Содержание

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/rag/build` | Чанкинг + Embeddings + построение индекса |
| DELETE | `/rag/build/{doc_id}` | Удаление чанков документа из индекса |
| GET | `/rag/build/{doc_id}/status` | Статус индексации (longpoll) |

---

### Сводная информация о доступе к данным

| Аспект | Значение |
|---|---|
| Доступ к БД | **Пишет** (индексация), **Читает** (статус) |
| Пайплайн | 2 (Индексация документа) |
| Вход | Плоский JSON с секциями от Registry |
| Выход | Статус индексации |
