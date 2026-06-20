## API RAG Search Service (rag-search:8091)

Сервис поиска релевантных чанков по векторному индексу.  
**Внутренний сервис.** Отвечает только за поиск и выдачу source-локаторов с retrieval-метаданными. **Без генерации ответа LLM** — генерация выполняется в Query Service.

**Архитектурные принципы (RS-6, уточнение 20.06):**

| Принцип | Описание |
|---------|----------|
| RAG хранит только актуальный индекс | version_id в публичный response не передаётся |
| chunk_id — технический retrieval ID | Цитирование строится по document_id + section_id |
| Параметры поиска — только из app_settings | search_type, top_k, rerank не переопределяются в запросе |
| context expansion — внутренний этап | Не публичное поле запроса |
| sparse/BM25 не удаляется | Остаётся как переключаемый режим в app_settings |

**Базовый URL (внутренний)**: `http://127.0.0.1:8091/api/v1`

### Формат ответа

Формат ответа и ошибок — см. [common_api.md](common_api.md#формат-ответа).

**Специфичные коды ошибок:**
| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 400 | `EMPTY_QUERY` | Пустой поисковый запрос |
| 500 | `SEARCH_FAILED` | Ошибка поиска чанков |

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).

| HTTP | Описание |
|------|----------|
| 200 | Результаты поиска |
| 400 | `EMPTY_QUERY` |
| 500 | `SEARCH_FAILED` |

---

### POST /rag/search

Поиск релевантных чанков по запросу. Возвращает source-локаторы (для цитирования) и retrieval-метаданные. Без генерации LLM.

**RAG-конфигурация — только из app_settings (P13-1, уточнение 20.06):**

| Параметр | Прод-значение | Ключ app_settings | Примечание |
|----------|---------------|-------------------|------------|
| Embedding model | Qwen3-Embedding-4B | `rag.embedding_api.endpoint` | Внешнее API / Infinity |
| Размерность | 2048 | `rag.embedding_dim` | 1536 / 2560 / 4096 — экспериментально |
| Chunk size | 1024 токенов | `rag.chunk_size` | По умолчанию `semantic_1024` |
| **search_type / mode** | `dense_rerank` | `rag.search_strategy` | **Единственный источник.** S1–S9 |
| **top_k** | 10 | `rag.search_top_k` | Количество результатов пользователю |
| **rerank_top_n** | 50 | `rag.rerank_top_n` | Кандидатов до rerank |
| **context_expansion** | 2 | `rag.context_expansion` | Соседние чанки до/после |
| Rerank model | bge-reranker-v2-m3-int8 | `rag.rerank_url` | TEI, локальный |

> `search_type`, `top_k`, `rerank`, `context_expansion` **не передаются в запросе** — стратегия фиксирована конфигом сервиса. Динамическое переключение через API требует отдельной проработки (не поддерживается).

**Процесс внутри:**

| Шаг | Действие | Результат |
|---|---|---|
| 1 | Dense-поиск (Qwen3-Embedding-4B, VECTOR(2048), cosine) → top-N кандидатов | N = `app_settings.rag.rerank_top_n` (по умолч. 50) |
| 2 | Rerank (bge-reranker-v2-m3-int8) → top-k результатов | k = `app_settings.rag.search_top_k` (по умолч. 10) |
| 3 | Context expansion: для каждого top-k чанка добавить соседние чанки (если есть) | `context[]` — массив соседних чанков |
| 4 | Сборка ответа: source-локаторы (document_id + section_id) + retrieval-метаданные (chunk_id + score + mode) | Финальный JSON |

> **P13-2 (разделение ролей BM25)**: В этом эндпоинте (RAG Search) **используется только dense + rerank**. BM25 применяется **только** для Registry Search (поиск по `doc_code` / `title` / `classifier_links`) — см. `registry_service_api.md` §3.1a (`GET /registry/documents/search`). Реализация BM25 = `ts_rank` + `pg_trgm`.

> **P13-3 (TEI rerank)**: rerank выполняется через **TEI-сервер** (text-embeddings-inference, локальный) с int8-квантизацией. URL — `app_settings.rag.rerank_url`.

> **P13-4 (экспериментальные стратегии)**: поисковые стратегии S1–S9 (см. `docs_plans/methodology/rag_experiments_methodology.md`) задаются **только** в `app_settings.rag.search_strategy`.

**Запрос:**

```json
{
  "query": "допуск соосности",
  "valid_at": "2026-06-20",
  "filters": {
    "document_type": ["gost"],
    "category_ids": [1, 2],
    "document_ids": [420000]
  }
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `query` | string | Да | Поисковый запрос |
| `valid_at` | date | Да | Дата, на которую документы active |
| `filters` | object | Нет | Фильтры: `document_type[]` — типы документов, `category_ids[]` — ID категорий, `document_ids[]` — конкретные ID |

**Ответ `200`:** объект с массивом результатов.

```json
{
  "query": "допуск соосности",
  "results": [
    {
      "source": {
        "document_id": 420000,
        "section_id": 8,
        "clause": "6.1",
        "path": "6/6.1",
        "page": 2,
        "bbox": null,
        "section_title": "Допуск соосности при степени точности",
        "content": "Для ледового класса Arc4 толщина обшивки должна быть не менее 12 мм.",
        "content_hash": "sha256-abcdef..."
      },
      "retrieval": {
        "chunk_id": 119,
        "score": 0.87,
        "mode": "dense_rerank"
      },
      "context": [
        {
          "chunk_id": 118,
          "content": "Предшествующий контекст...",
          "score": 0.45,
          "page": 2
        },
        {
          "chunk_id": 120,
          "content": "Последующий контекст...",
          "score": 0.44,
          "page": 2
        }
      ]
    }
  ],
  "processing_time_ms": 120,
  "total_found": 15
}
```

#### Поля `source` (стабильный локатор для цитирования)

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | bigint | ID документа в Registry |
| `section_id` | bigint | ID секции (стабилен внутри документа, **не** chunk_id) |
| `clause` | string \| null | Номер пункта (напр. "6.1") |
| `path` | string | Путь секции (напр. "6/6.1") |
| `page` | int | Номер страницы (1-based) |
| `bbox` | array[float] \| null | Координаты на странице: `[x1, y1, x2, y2]`, нормализованные 0..1 |
| `section_title` | string \| null | Название раздела |
| `content` | string | Текст чанка (excerpt для ответа) |
| `content_hash` | string \| null | SHA-256 содержимого для дедупликации |

#### Поля `retrieval` (технические метаданные поиска)

| Поле | Тип | Описание |
|---|---|---|
| `chunk_id` | bigint | ID чанка в БД (технический, **не用于 цитирования**) |
| `score` | float | Итоговая оценка релевантности (0..1) |
| `mode` | string | Режим поиска: `dense_rerank`, `hybrid_rerank`, `hybrid_rrf` |

#### Поля `context[]` (context expansion — соседние чанки)

| Поле | Тип | Описание |
|---|---|---|
| `chunk_id` | bigint | ID соседнего чанка |
| `content` | string | Содержимое соседнего чанка |
| `score` | float | Оценка релевантности |
| `page` | int | Номер страницы |

#### Корневые поля ответа

| Поле | Тип | Описание |
|---|---|---|
| `query` | string | Исходный поисковый запрос |
| `results` | array | Массив результатов (каждый: source + retrieval + context) |
| `processing_time_ms` | int | Время обработки запроса |
| `total_found` | int | Общее количество найденных чанков (до фильтрации) |

---

### Сводная таблица эндпоинтов

| Метод | Путь | Описание | Доступ к БД |
|---|---|---|---|
| `POST` | `/rag/search` | Поиск чанков (без генерации LLM) | **Читает** |

---

### Сводная информация о доступе к данным

| Аспект | Значение |
|---|---|
| Доступ к БД | **Читает** (поиск) |
| Пайплайн | 3 (Поиск) |
| Вход | Поисковый запрос |
| Выход | Source-локаторы + retrieval-метаданные + context expansion |

