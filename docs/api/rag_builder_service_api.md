## API RAG Builder Service (rag-builder:8090)

Сервис построения чанков, вычисления embeddings и создания векторного индекса.  
**Внутренний сервис.** Запускается после успешного завершения Пайплайна 1 (Формирование документа). На вход получает обогащённый JSON от Registry через Orchestrator (структура документа, секции, терминология, ссылки), на выходе — статус завершения индексации.

**Базовый URL (внутренний)**: `http://127.0.0.1:8090/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](../common_api.md#формат-ответа).

**Специфичные коды ошибок:**
| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 202 | — | Индексация запущена (асинхронно) |
| 200 | — | Статус/результат |
| 500 | `BUILD_FAILED` | Ошибка построения чанков или эмбеддингов |

---

### POST /rag/build

Построение чанков, вычисление embeddings и индексация документа.  
Вызывается Orchestrator после завершения Пайплайна 1.

**Процесс внутри:**

| Шаг | Действие | Результат |
|---|---|---|
| 1 | Чтение структуры документа из входного JSON (обогащённый контейнер от Registry) | Документ, секции, таблицы, изображения |
| 2 | Построение чанков и иерархии | Разбиение на семантические фрагменты (не более 512 токенов), построение иерархии секций (path) |
| 3 | Вычисление Embeddings | Векторные представления для каждого текстового чанка |
| 4 | Построение векторного индекса | Сохранение чанков, эмбеддингов и индексов в БД |

Orchestrator получает JSON из Registry (через `GET /registry/documents/{doc_id}/sections`) и передаёт его в RAG Builder. Формат — см. [`schema_registry_for_rag.json`](../schema/schema_registry_for_rag.json).

Каждая секция содержит объектный `content`, структура которого зависит от `type`:

| type | Как формируется чанк | Источник данных |
|------|---------------------|----------------|
| `text` | Разбивка `content.text` на чанки ≤512 токенов | `content.text` |
| `textBlock` | Разбивка `content.text` на чанки ≤512 токенов | `content.text` (font display details отброшены) |
| `headerFooter` | Всё содержимое → один чанк | `content.text` |
| `table` | Весь объект целиком → один чанк | `content.markdown` (если есть), иначе сборка из `columns`/`rows` |
| `list` | Весь объект целиком → один чанк | `content.markdown` (если есть), иначе сборка из `items[]` |
| `image` | Один чанк | `content.markdown` или `content.caption + content.description` |
| `formula` | Один чанк | `content.markdown` или `content.latex + content.meaning` |

**Защищённые span'ы (`protected_spans`):** участки текста внутри секций, которые нельзя разбивать при чанкинге (например, заголовки, важные термины). Задаются как массив `{section_id, start_offset, end_offset}`. Если не указаны — чанкинг выполняется без ограничений.

**Параметры индексации (`options`):**
- `options.strategy` — стратегия чанкинга: `semantic_512` (по умолчанию) — семантическое разбиение с макс. 512 токенов на чанк.

**Запрос (передаётся от Orchestrator, обогащённый JSON из Registry):**

```json
{
  "document_id": 1,
  "sections": [
    {
      "section_id": 420001,
      "document_id": 1,
      "clause": "1",
      "title": null,
      "level": 1,
      "path": "1",
      "page": 1,
      "type": "text",
      "content": {
        "text": "Настоящий стандарт распространяется...",
        "amendments": []
      }
    },
    {
      "section_id": 420005,
      "document_id": 1,
      "clause": "6.1",
      "title": "Допуск соосности при степени точности",
      "level": 2,
      "path": "6.1.table1",
      "page": 2,
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
    "strategy": "semantic_512"
  }
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|---------------|----------|
| `document_id` | bigint | Да | ID документа в Registry |
| `sections` | array | Да | Массив секций для индексации |
| `sections[].section_id` | bigint | Да | ID секции |
| `sections[].document_id` | bigint | Да | ID документа (дублируется для удобства) |
| `sections[].clause` | string | Нет | Номер пункта (напр. "6.1") |
| `sections[].title` | string | Нет | Заголовок секции |
| `sections[].level` | int | Нет | Уровень вложенности секции |
| `sections[].path` | string | Да | Путь секции (напр. "1.2.3") |
| `sections[].page` | int | Нет | Номер страницы |
| `sections[].type` | string | Да | Тип секции: `text`, `textBlock`, `table`, `image`, `list`, `formula`, `headerFooter` |
| `sections[].content` | object/jsonb | Да | Содержимое секции (JSONB, см. `registry_for_rag_v2`) |
| `protected_spans` | array | Нет | Массив защищённых span'ов: `{section_id, start_offset, end_offset}` — участки, которые нельзя разбивать при чанкинге |
| `options` | object | Нет | Дополнительные параметры индексации |
| `options.strategy` | string | Нет | Стратегия чанкинга: `semantic_512` (по умолчанию)

**Ответ `202` (асинхронный запуск):**
```json
{
  "document_id": 1,
  "task_id": 420000,
  "status": "indexing"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `task_id` | bigint | ID задачи для отслеживания прогресса |
| `status` | string | Статус: `indexing` (индексация запущена) |

Оркестратор отслеживает прогресс через `GET /rag/build/{doc_id}/status?longpoll=15`.

**Финальный ответ** (возвращается через longpoll-статус):
```json
{
  "document_id": 1,
  "status": "indexed",
  "indexed_at": "2026-05-15T12:00:18Z",
  "chunks_count": 34,
  "index_stats": {
    "sections": 12,
    "chunks": 34,
    "embeddings": 31
  }
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа |
| `status` | string | Статус: `indexed`, `failed` |
| `indexed_at` | string | Время завершения индексации |
| `chunks_count` | int | Общее количество созданных чанков |
| `index_stats.sections` | int | Количество секций (структурных единиц) |
| `index_stats.chunks` | int | Количество чанков |
| `index_stats.embeddings` | int | Количество вычисленных эмбеддингов |

---

### DELETE /rag/build/{doc_id}

Удаление всех чанков документа из векторного индекса.

**Ответ `200`:**
```json
{
  "document_id": 1,
  "deleted_count": 128,
  "status": "completed"
}
```

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
  "indexed_at": "2026-05-15T12:00:18Z"
}
```

---

### Сводная таблица эндпоинтов

| Метод | Путь | Описание | Доступ к БД |
|---|---|---|---|
| `POST` | `/rag/build` | Чанкинг + Embeddings + построение индекса | **Пишет** |
| `DELETE` | `/rag/build/{doc_id}` | Удаление чанков документа из индекса | **Пишет** |
| `GET` | `/rag/build/{doc_id}/status` | Статус индексации (с longpoll) | **Читает** |

---

### Сводная информация о доступе к данным

| Аспект | Значение |
|---|---|
| Доступ к БД | **Пишет** (индексация), **Читает** (статус) |
| Пайплайн | 2 (Индексация документа) |
| Вход | Плоский JSON с секциями от Registry |
| Выход | Статус индексации |
