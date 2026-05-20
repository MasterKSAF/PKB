## API Registry Service / Реестр документов (registry-service:8084)

Базовый реестр НСИ (нормативно-справочной информации).  
Хранит классификаторы, документы и терминологию.  
Соответствует этапу **«Реестр документов» Пайплайна 1 (Формирование документа)** — **пишет** данные в БД.  
Также участвует в этапе **«Валидация»** — **читает** справочники классификаторов для проверки кодов.

**Внутренний сервис**. Публичный API — через Orchestrator.

**Базовый URL**: `http://127.0.0.1:8084/api/v1`

### Формат ответа

Все ответы обёрнуты в `{ data, meta }`:

```json
{
  "data": [ ... ],
  "meta": { "total": 150, "page": 1, "page_size": 50 }
}
```

Для одиночных объектов:

```json
{
  "data": { "id": "b3a8f1c2-...", "title": "..." }
}
```

При ошибке:

```json
{
  "error": { "code": "NOT_FOUND", "message": "Не найдено", "details": {} }
}
```

### Коды ошибок

| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 400 | `VALIDATION_ERROR` | Некорректные данные |
| 404 | `NOT_FOUND` | Ресурс не найден |
| 404 | `CLASSIFIER_NOT_FOUND` | Узел классификатора не найден |
| 404 | `TERM_NOT_FOUND` | Термин не найден |
| 404 | `DOCUMENT_NOT_FOUND` | Документ не найден |
| 409 | `DUPLICATE_CODE` | Код (в системе) уже существует |
| 409 | `DUPLICATE_DOCUMENT` | Документ с таким бизнес-ключом уже есть |
| 409 | `DUPLICATE_TERM` | Термин уже существует |
| 409 | `HAS_CHILDREN` | Нельзя удалить узел с дочерними |
| 409 | `HAS_DOCUMENTS` | Есть документы, ссылающиеся на код |
| 409 | `CROSS_SYSTEM_PARENT` | Родитель в другой системе классификации |
| 500 | `INTERNAL_ERROR` | Внутренняя ошибка |

---

### Содержание

| Группа | Описание |
|--------|----------|
| `classifiers` | Иерархический справочник классификаторов (МКС, ОКСТУ, УДК, внешние) |
| `terminology` | Реестр терминов, синонимов и правил нормализации |
| `documents` | Реестр логических документов НСИ |
| `common` | Статистика и справочные значения |

---

## Группа classifiers

### 1.1. Список (плоский)

```
GET /registry/classifiers
```

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `classifier_system` | string | `MKS`, `OKSTU`, `UDC`, `EXTERNAL` |
| `code` | string | Частичное совпадение по коду |
| `full_name` | string | Поиск по названию (ILIKE) |
| `status` | string | `active`, `deprecated`, `archived` |
| `parent_code` | string | Дочерние узлы (в рамках той же системы) |
| `page` | int | Номер страницы |
| `page_size` | int | Записей на странице (max 200) |

**Ответ `200`:**

```json
{
  "data": [
    {
      "classifier_system": "MKS",
      "code": "47.020",
      "parent_code": "47",
      "full_name": "Конструкция корпуса",
      "status": "active",
      "effective_date": "2020-01-01",
      "replaced_by": null,
      "created_at": "2025-11-15T10:30:00Z"
    },
    {
      "classifier_system": "OKSTU",
      "code": "05.010",
      "parent_code": "05",
      "full_name": "Документы конструкторские",
      "status": "active",
      "effective_date": "1980-01-01",
      "replaced_by": null,
      "created_at": "2025-11-15T10:30:00Z"
    }
  ],
  "meta": { "total": 2, "page": 1, "page_size": 50 }
}
```

> **v2.3:** Составной PK `(classifier_system, code)`. Поля `doc_type`, `jurisdiction`, `language`, `oks_code`, `is_thematic` удалены — это атрибуты документа, а не рубрики.

---

### 1.2. Дерево (иерархическое)

```
GET /registry/classifiers/tree
```

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `classifier_system` | string | Да | `MKS`, `OKSTU`, `UDC`, `EXTERNAL` |
| `root_code` | string | Нет | Если не указан — корень системы |
| `max_depth` | int | Нет (default 10) | Максимальная глубина |
| `search` | string | Нет | Поиск с раскрытием веток |
| `status` | string | Нет | `active`, `deprecated`, `archived` |

**Ответ `200`:**

```json
{
  "data": [
    {
      "classifier_system": "MKS",
      "code": "47",
      "parent_code": "MKS_ROOT",
      "full_name": "Судостроение и морские сооружения",
      "status": "active",
      "effective_date": "2020-01-01",
      "children": [
        {
          "classifier_system": "MKS",
          "code": "47.020",
          "parent_code": "47",
          "full_name": "Конструкция корпуса",
          "status": "active",
          "effective_date": "2020-01-01",
          "children": [
            {
              "classifier_system": "MKS",
              "code": "47.020.30",
              "parent_code": "47.020",
              "full_name": "Корпусные конструкции",
              "status": "active",
              "children": []
            }
          ]
        }
      ]
    }
  ],
  "meta": { "total": 1, "max_depth_reached": false }
}
```

---

### 1.3. Один узел

```
GET /registry/classifiers/{code}
```

**Query-параметр**: `classifier_system` (обязательный, для составного PK).  
**Ответ `200`**: объект узла + `children` первого уровня.

---

### 1.4. Создать

```
POST /registry/classifiers
```

**Тело запроса:**

```json
{
  "classifier_system": "MKS",
  "code": "47.020.99",
  "parent_code": "47.020",
  "full_name": "Прочие корпусные конструкции",
  "status": "active",
  "effective_date": "2026-06-01"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `classifier_system` | string | Да | `MKS`, `OKSTU`, `UDC`, `EXTERNAL` |
| `code` | string | Да | Код рубрики |
| `parent_code` | string | Нет | Код родителя (той же системы!) |
| `full_name` | string | Да | Наименование |
| `status` | string | Нет | `active` (default) |
| `effective_date` | date | Нет | Дата актуальности |

**Ответ `201`**: созданный объект.

**Ошибки**: `409` — `DUPLICATE_CODE`, `400` — `CROSS_SYSTEM_PARENT`, `404` — `PARENT_NOT_FOUND`.

---

### 1.5. Обновить

```
PUT /registry/classifiers/{code}
```

**Query-параметр**: `classifier_system` (обязательный).  
**Тело**: любые поля из 1.4.  

**Ответ `200`**: обновлённый объект.

---

### 1.6. Частичное обновление

```
PATCH /registry/classifiers/{code}
```

**Query-параметр**: `classifier_system`.  
**Тело**: подмножество полей.

---

### 1.7. Удалить

```
DELETE /registry/classifiers/{code}
```

**Query-параметр**: `classifier_system`.  
**Ошибки**: `409` — `HAS_CHILDREN` / `HAS_DOCUMENTS`.

---

### 1.8. Импорт

```
POST /registry/classifiers/import
```

**Запрос**: `multipart/form-data`

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `file` | File | Да | `.xlsx` или `.csv` |
| `classifier_system` | string | Да | `MKS`, `OKSTU`, `UDC`, `EXTERNAL` |
| `mapping` | string | Да | JSON-маппинг колонок |

**Ответ `200`:**

```json
{
  "data": {
    "classifier_system": "MKS",
    "inserted": 250,
    "updated": 15,
    "errors": [
      { "row": 12, "code": "47.020.XX", "message": "Parent not found" }
    ]
  }
}
```

---

### 1.9. Список карантина

```
GET /registry/classifiers/pending
```

Коды, найденные в документах, но отсутствующие в справочнике. Требуют административного разбора.

**Query-параметры**: `system` (`MKS`, `OKSTU`, `UDC`, `EXTERNAL`), `status` (`new`, `mapped`, `rejected`), `page`, `page_size`.

**Ответ `200`:**

```json
{
  "data": [
    {
      "id": "p-001",
      "system": "MKS",
      "code": "47.020.99",
      "found_in_document_id": "b3a8f1c2-...",
      "found_in_document_title": "Стойки установочные",
      "status": "new",
      "suggested_parent_code": "47.020",
      "suggested_parent_name": "Конструкция корпуса",
      "admin_comment": null,
      "created_at": "2026-05-15T10:01:00Z"
    }
  ],
  "meta": { "total": 7, "page": 1, "page_size": 50 }
}
```

---

### 1.10. Принять код из карантина

```
POST /registry/classifiers/pending/{pending_id}/accept
```

Переносит код в `classifier_registry`.

**Тело запроса:**

```json
{
  "parent_code": "47.020",
  "full_name": "Прочие корпусные конструкции",
  "admin_comment": "Подтверждено по МКС 2025"
}
```

**Ответ `200`:**

```json
{
  "data": {
    "pending_id": "p-001",
    "classifier_system": "MKS",
    "code": "47.020.99",
    "status": "mapped",
    "registry_created": true
  }
}
```

---

### 1.11. Отклонить код из карантина

```
POST /registry/classifiers/pending/{pending_id}/reject
```

**Тело запроса:**

```json
{
  "admin_comment": "Ошибка OCR — кода 47.020.99 не существует"
}
```

**Ответ `200`:**

```json
{
  "data": { "pending_id": "p-001", "status": "rejected" }
}
```

---

### 1.12. Валидация классификации

```
POST /registry/classifiers/validate
```

Проверка и подтверждение извлечённых классификационных кодов (МКС/ОКС, ОКСТУ, УДК) по справочнику Registry.  
**Синхронная операция.** Не имеет побочных эффектов.

**Запрос:**

```json
{
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021"
  }
}
```

| Поле | Тип | Обязательность | Описание |
|---|---|---|---|
| `classification.mks_oks_code` | string | Нет | Код МКС/ОКС |
| `classification.okstu_code` | string | Нет | Код ОКСТУ |
| `classification.udk_code` | string | Нет | Код УДК |

**Ответ `200`:**

```json
{
  "data": {
    "mks_status": "CONFIRMED",
    "mks_display_name": "Конструкция корпуса",
    "okstu_status": "NOT_USED",
    "udk_valid": true,
    "overall_status": "valid"
  }
}
```

**Статусы `*_status`:**

| Значение | Описание |
|---|---|
| `CONFIRMED` | Код найден в справочнике и верифицирован |
| `PENDING_REVIEW` | Извлечён автоматически, не найден в справочнике — требует ручного разбора |
| `NOT_FOUND` | Парсер не обнаружил код на первых страницах |
| `NOT_USED` | Не применяется для данной эры/типа документа |
| `UNASSIGNED` | Классификация не назначалась |

Registry Service — source of truth для классификаторов. Проверяет коды напрямую по `classifier_registry`.  
Решение о создании `classifier_pending` принимает **Оркестратор**, анализируя возвращённые статусы.

---

## Группа terminology

### 2.1. Список

```
GET /registry/terminology
```

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `raw_term` | string | Поиск по исходному термину (ILIKE) |
| `standard_term` | string | Поиск по эталонному написанию |
| `term_type` | string | `acronym`, `foreign_term`, `standard_code`, `avatar`, `symbol` |
| `is_blocked` | bool | Фильтр заблокированных |
| `scope` | string | Фильтр по области применения |
| `page` | int | Номер страницы |
| `page_size` | int | Записей на странице (max 200) |

**Ответ `200`:**

```json
{
  "data": [
    {
      "id": "t-001",
      "raw_term": "ГОСТ",
      "standard_term": "ГОСТ",
      "normalized_value": "гост",
      "term_type": "standard_code",
      "is_case_sensitive": false,
      "definition": "Государственный стандарт (СССР/РФ)",
      "synonyms": ["GOST", "gost"],
      "related_docs": ["ГОСТ 20868-81", "ГОСТ Р 1.0-2012"],
      "scope": ["Стандартизация", "Судостроение"],
      "is_blocked": false,
      "created_at": "2025-12-01T08:00:00Z",
      "updated_at": "2026-01-15T12:00:00Z"
    },
    {
      "id": "t-002",
      "raw_term": "DNV",
      "standard_term": "DNV",
      "normalized_value": "dnv",
      "term_type": "acronym",
      "is_case_sensitive": true,
      "definition": "Det Norske Veritas — норвежское классификационное общество",
      "synonyms": ["DNV GL"],
      "related_docs": ["DNV-RU-SHIP-Pt3"],
      "scope": ["Судостроение", "Классификация"],
      "is_blocked": false,
      "created_at": "2026-01-20T14:00:00Z",
      "updated_at": "2026-01-20T14:00:00Z"
    }
  ],
  "meta": { "total": 2, "page": 1, "page_size": 50 }
}
```

---

### 2.2. Один термин

```
GET /registry/terminology/{term_id}
```

**Ответ `200`**: объект термина.

---

### 2.3. Создать

```
POST /registry/terminology
```

**Тело запроса:**

```json
{
  "raw_term": "CAD",
  "standard_term": "CAD",
  "normalized_value": "cad",
  "term_type": "acronym",
  "is_case_sensitive": true,
  "definition": "Computer-Aided Design — система автоматизированного проектирования",
  "synonyms": ["САПР", "cad"],
  "scope": ["Проектирование", "Машиностроение"],
  "is_blocked": false
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `raw_term` | string | Да | Допустимое написание (UNIQUE) |
| `standard_term` | string | Да | Эталонное написание |
| `normalized_value` | string | Да | Для бизнес-ключа (нижний регистр) |
| `term_type` | string | Нет | `acronym`, `foreign_term`, `standard_code`, `avatar`, `symbol` |
| `is_case_sensitive` | bool | Нет | Учитывать регистр при поиске |
| `definition` | string | Нет | Определение для LLM |
| `synonyms` | string[] | Нет | Альтернативные написания |
| `related_docs` | string[] | Нет | Связанные документы |
| `scope` | string[] | Нет | Области применения |
| `is_blocked` | bool | Нет | Блокировка устаревшего термина |

**Ответ `201`**: созданный объект.

---

### 2.4. Обновить

```
PUT /registry/terminology/{term_id}
```

---

### 2.5. Удалить

```
DELETE /registry/terminology/{term_id}
```

---

### 2.6. Поиск нормализованной формы

```
GET /registry/terminology/normalize
```

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `term` | string | Да | Исходный термин |

**Ответ `200`**:

```json
{
  "raw_term": "гост р",
  "standard_term": "ГОСТ Р",
  "normalized_value": "гост р",
  "term_type": "standard_code",
  "is_blocked": false
}
```

Если не найден — возвращает исходный с `term_type: "unknown"`.

---

### 2.7. Импорт

```
POST /registry/terminology/import
```

**Запрос**: `multipart/form-data` (файл + mapping). Аналогично импорту классификаторов.

---

## Группа documents

### 3.1. Список

```
GET /registry/documents
```

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `title` | string | Поиск по названию |
| `doc_code` | string | Поиск по номеру |
| `source_type` | string | `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `OTHER` |
| `mks_oks_code` | string | Фильтр по коду МКС/ОКС |
| `okstu_code` | string | Фильтр по коду ОКСТУ |
| `status` | string | FSM-статус документа |
| `era` | string | `USSR`, `CIS`, `RF`, `CURRENT` |
| `validity_status` | string | `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `jurisdiction` | string | `RU`, `EU`, `US`, `NO`, `INTL` |
| `issuing_body` | string | Организация-издатель |
| `title_hash_sha256` | string | Точный поиск по бизнес-ключу |
| `date_from` / `date_to` | date | Фильтр по дате создания |
| `page` | int | Номер страницы |
| `page_size` | int | Записей на странице (max 200) |

**Ответ `200`:**

```json
{
  "data": [
    {
      "id": "b3a8f1c2-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "title": "Стойки установочные",
      "doc_code": "20868-81",
      "source_type": "GOST",
      "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "status": "approved",
      "era": "USSR",
      "validity_status": "active",
      "jurisdiction": "RU",
      "issuing_body": "Госстандарт СССР",
      "mks_oks_code": "31.240",
      "mks_name": "Электроника. Монтажные изделия",
      "okstu_code": null,
      "okstu_name": null,
      "classification_status": {
        "mks_status": "CONFIRMED",
        "okstu_status": "NOT_USED"
      },
      "successor_doc_id": null,
      "predecessor_doc_id": null,
      "total_versions": 2,
      "chunk_count": 34,
      "created_by": "system_registry_sync",
      "updated_by": "ivanov_ai",
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T14:00:00Z"
    }
  ],
  "meta": { "total": 56, "page": 1, "page_size": 50 }
}
```

---

### 3.2. Один документ

```
GET /registry/documents/{doc_id}
```

**Ответ `200`** — полный объект документа с версиями файлов, цепочками преемственности.

---

### 3.3. Создать (основной / из Пайплайна 1)

```
POST /registry/documents
```

**Назначение:** создание карточки документа. Используется как при прямом вызове из UI/админки, так и со стороны этапа **«Реестр документов»** Пайплайна 1 (Формирование документа).

В режиме пайплайна оркестратор передаёт JSON-контейнер (результат валидации) как непрозрачный артефакт — сервис сам маппит поля в модель данных.

**Тело запроса (прямое создание):**

```json
{
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
    "mks_status": "CONFIRMED",
    "okstu_status": "NOT_USED"
  },
  "successor_doc_id": null,
  "predecessor_doc_id": null,
  "metadata": { "year": "1981", "udc": "629.5.021" }
}
```

**Тело запроса (из пайплайна — сквозной JSON-контейнер от этапа Валидации):**

```json
{
  "document_id": "b3a8f1c2-...",
  "version_id": "c4b9f2d3-...",
  "document_reference": [],
  "structure": {
    "type": "normative",
    "sections": [
      {
        "clause": "1. Общие положения",
        "title": "Общие положения",
        "level": 1,
        "type": "section",
        "content": { "text": "Настоящий стандарт..." },
        "page": 1,
        "bbox": "x1,y1,x2,y2",
        "subsections": []
      }
    ]
  },
  "classification": {
    "mks_oks_code": "47.020",
    "okstu_code": null,
    "udk_code": "629.5.021",
    "year": "1981"
  },
  "quality": {
    "confidence": 0.94,
    "pages_processed": 12,
    "pages_failed": 0
  },
  "validation": {
    "id": "val-001",
    "structure_valid": true,
    "classifiers": {
      "mks_status": "CONFIRMED",
      "okstu_status": "NOT_USED",
      "overall_status": "CONFIRMED"
    },
    "uniqueness": {
      "is_duplicate_file": false,
      "is_duplicate_document": false,
      "content_hash_sha256": "abc123...",
      "title_hash_sha256": "def456..."
    },
    "matching": {
      "predecessor_doc_id": null,
      "successor_doc_id": null
    },
    "decision": "auto",
    "status": "completed"
  }
}
```

> Registry сохраняет данные в БД и **возвращает тот же JSON**, но с проставленными идентификаторами и ссылками. Сервис не меняет структуру документа — только enrich.

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `title` | string | Да* | Полное название |
| `doc_code` | string | Нет | Регистрационный номер |
| `source_type` | string | Нет | Тип источника |
| `era` | string | Нет | Эра документа |
| `validity_status` | string | Нет | Статус действия |
| `jurisdiction` | string | Нет | Юрисдикция |
| `issuing_body` | string | Нет | Организация-издатель |
| `mks_oks_code` | string | Нет | Код МКС/ОКС (FK) |
| `okstu_code` | string | Нет | Код ОКСТУ (FK) |
| `classification_status` | JSONB | Нет | Статусы извлечения кодов |
| `successor_doc_id` | UUID | Нет | Преемник |
| `predecessor_doc_id` | UUID | Нет | Предшественник |
| `metadata` | JSONB | Нет | Доп. данные |

> *`title` обязателен при прямом создании; в режиме пайплайна берётся из структуры JSON-контейнера.

Система **автоматически вычисляет** `title_hash_sha256` по формуле:  
`SHA-256(era|source_type|mks_oks_code|okstu_code|doc_code|normalized_title)`

**Ответ `201`:** возвращает полную структуру документа со ссылками в БД — все данные, необходимые RAG для индексации и цитирования.

```json
{
  "document_id": "b3a8f1c2-...",
  "version_id": "c4b9f2d3-...",
  "registry": {
    "title": "ГОСТ Р 12345-77",
    "doc_code": "20868-81",
    "source_type": "GOST",
    "era": "USSR",
    "validity_status": "active",
    "jurisdiction": "RU",
    "issuing_body": "Госстандарт СССР",
    "title_hash_sha256": "a1b2c3d4...",
    "order": 0,
    "links": {
      "document": "/api/v1/registry/documents/42",
      "versions": "/api/v1/registry/documents/42/versions"
    },
    "created_at": "2026-05-15T12:00:00Z"
  },
  "classification": {
    "mks_oks_code": "47.020",
    "mks_display_name": "Конструкция корпуса",
    "mks_status": "CONFIRMED",
    "okstu_code": null,
    "okstu_status": "NOT_USED",
    "udk_code": "629.5.021",
    "year": "1981"
  },
  "structure": {
    "type": "normative",
    "sections": [
      {
        "id": "sec-001",
        "clause": "1. Общие положения",
        "title": "Общие положения",
        "level": 1,
        "type": "section",
        "content": { "text": "Настоящий стандарт распространяется..." },
        "page": 1,
        "bbox": "x1,y1,x2,y2",
        "subsections": [
          {
            "id": "sec-001-1",
            "clause": "1.1 Область применения",
            "title": "Область применения",
            "level": 2,
            "type": "subsection",
            "content": { "text": "..." },
            "page": 1,
            "bbox": "x1,y1,x2,y2"
          }
        ]
      }
    ]
  },
  "document_reference": [
    {
      "id": "ref-001",
      "target_doc_code": "ГОСТ 12345-88",
      "reference_type": "normative",
      "is_resolved": false
    }
  ],
  "files": {
    "original": "/api/v1/files/file-xyz",
    "preview": "/api/v1/documents/b3a8f1c2.../pages/1/preview"
  },
  "quality": {
    "confidence": 0.94,
    "pages_processed": 12,
    "pages_failed": 0
  },
  "status": "archived"
}
```

| Поле | Тип | Описание |
|---|---|---|
| `document_id` | string | UUID документа (единый первичный ключ) |
| `version_id` | string | UUID версии файла |
| `registry` | object | Карточка документа в реестре (nsi) с метаданными и ссылками |
| `registry.links` | object | Ссылки на ресурсы документа в API реестра |
| `registry.order` | int | Порядковый номер документа (используется при построении текста страницы) |
| `classification` | object | Коды классификации со статусами верификации |
| `structure` | object | Полная структура документа: секции (с ID сущностей в БД) |
| `structure.sections[].id` | string | ID секции в `nsi.document_sections` |
| `structure.sections[].clause` | string | Номер пункта/заголовка (напр. «1.», «1.1») |
| `structure.sections[].title` | string | Название секции без номера |
| `structure.sections[].level` | int | Уровень вложенности (1 — верхний) |
| `structure.sections[].type` | string | Тип элемента (`section`, `subsection`, `paragraph`) |
| `structure.sections[].content` | JSONB | Содержимое секции (`{"text": "..."}`) |
| `structure.sections[].page` | int | Номер страницы |
| `structure.sections[].bbox` | string | Координаты bounding box (`x1,y1,x2,y2`) |
| `document_reference[]` | array | Ссылки на другие документы |
| `document_reference[].id` | string | ID ссылки |
| `document_reference[].target_doc_code` | string | Код целевого документа |
| `document_reference[].reference_type` | string | Тип ссылки (`normative`, `informative`, `replacement`) |
| `document_reference[].is_resolved` | bool | Разрешена ли ссылка (документ найден в реестре) |
| `files` | object | Ссылки на оригинальный файл и превью страниц |
| `quality` | object | Оценка качества распознавания |
| `status` | string | Статус (`archived` — документ готов к индексации) |

**Ошибки**: `409` — `DUPLICATE_DOCUMENT`.

---



### 3.4. Обновить

```
PUT /registry/documents/{doc_id}
```

Полное обновление. При изменении ключевых полей (`title`, `era`, `source_type`, `mks_oks_code`, `okstu_code`, `doc_code`) — `title_hash_sha256` пересчитывается автоматически.

---

### 3.5. Частичное обновление

```
PATCH /registry/documents/{doc_id}
```

**Тело** — любое подмножество полей.

---

### 3.6. Обновить статус

```
PATCH /registry/documents/{doc_id}/status
```

**Тело запроса:**

```json
{
  "status": "archived",
  "comment": "Документ устарел",
  "changed_by": "ivanov_ai"
}
```

**Допустимые статусы (FSM)**: `draft`, `uploaded`, `validating`, `processing`, `review_required`, `ready_for_promotion`, `approved`, `failed`, `archived`.

**Ответ `200`:**

```json
{
  "data": {
    "id": "b3a8f1c2-...",
    "status": "archived",
    "previous_status": "approved",
    "history_id": "h-006",
    "updated_at": "2026-05-15T13:00:00Z"
  }
}
```

---

### 3.7. История статусов

```
GET /registry/documents/{doc_id}/history
```

Полный аудит переходов статусов документа.

**Ответ `200`:**

```json
{
  "data": [
    {
      "history_id": "h-001",
      "old_status": null,
      "new_status": "uploaded",
      "comment": { "reason": "initial_upload" },
      "changed_by": "system_registry_sync",
      "changed_at": "2026-04-27T10:00:00Z"
    }
  ],
  "meta": { "total": 6 }
}
```

---

### 3.8. Цепочка преемственности

```
GET /registry/documents/{doc_id}/succession
```

**Ответ `200`:**

```json
{
  "data": {
    "document_id": "b3a8f1c2-...",
    "title": "ГОСТ 20868-81",
    "chain": [
      { "id": "a1b2c3d4-...", "title": "ГОСТ 20868-75", "doc_code": "20868-75", "era": "USSR", "relation": "predecessor", "depth": -1 },
      { "id": "b3a8f1c2-...", "title": "ГОСТ 20868-81", "doc_code": "20868-81", "era": "USSR", "relation": "self", "depth": 0 },
      { "id": "e5d0c3b4-...", "title": "ГОСТ Р 20868-2025", "doc_code": "20868-2025", "era": "RF", "relation": "successor", "depth": 1 }
    ]
  }
}
```

---

### 3.9. Удалить

```
DELETE /registry/documents/{doc_id}
```

---

### 3.10. Экспорт

```
GET /registry/documents/export
```

Фильтры те же, что в списке. **Ответ**: CSV-файл.

---

### 3.11. Массовый импорт

```
POST /registry/documents/import
```

Файл + mapping.

---

## Группа common

### 4.1. Статистика

```
GET /registry/stats
```

**Ответ `200`:**

```json
{
  "data": {
    "classifiers_total": {
      "MKS": 287,
      "OKSTU": 143,
      "UDC": 52,
      "EXTERNAL": 18
    },
    "classifiers_pending": 7,
    "terminology_total": 1204,
    "documents_total": 56,
    "documents_by_status": {
      "draft": 2,
      "uploaded": 5,
      "parsing": 3,
      "validation": 1,
      "review_required": 2,
      "ready_for_promotion": 4,
      "approved": 30,
      "failed": 1,
      "archived": 8
    },
    "documents_by_source_type": {
      "GOST": 20,
      "GOST_R": 12,
      "OST": 5,
      "TU": 8,
      "ISO": 3,
      "DNV": 6,
      "ASTM": 2
    },
    "documents_by_era": {
      "USSR": 18,
      "CIS": 3,
      "RF": 25,
      "CURRENT": 10
    }
  }
}
```

---

### 4.2. Допустимые значения

```
GET /registry/enums
```

**Ответ `200`:**

```json
{
  "data": {
    "classifier_system": ["MKS", "OKSTU", "UDC", "EXTERNAL"],
    "classifier_status": ["active", "deprecated", "archived"],
    "source_type": ["GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "OTHER"],
    "document_status": ["draft", "uploaded", "validating", "processing", "review_required", "ready_for_promotion", "approved", "failed", "archived"],
    "era": ["USSR", "CIS", "RF", "CURRENT"],
    "validity_status": ["active", "superseded", "cancelled", "historical", "draft"],
    "jurisdiction": ["RU", "EU", "US", "NO", "INTL"],
    "term_type": ["acronym", "foreign_term", "standard_code", "avatar", "symbol"],
    "classification_status_code": ["CONFIRMED", "PENDING_REVIEW", "NOT_FOUND", "NOT_USED", "UNASSIGNED"],
    "pending_status": ["new", "mapped", "rejected"],
    "validation_status": ["pending", "valid", "invalid"],
    "chunk_type": ["text", "table", "image", "formula"]
  }
}
```

---

## Модели данных

### 5.1. classifier_node

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `classifier_system` | varchar(20) | PK (составной), `MKS`, `OKSTU`, `UDC`, `EXTERNAL` |
| `code` | text | PK (составной) |
| `parent_code` | text | FK → self (`classifier_system`, `code`), nullable |
| `full_name` | text | NOT NULL |
| `status` | varchar(20) | DEFAULT `'active'` |
| `effective_date` | date | nullable |
| `replaced_by` | text | nullable |
| `created_at` | timestamptz | NOT NULL |

> FK гарантирует, что родитель принадлежит той же системе классификации.

### 5.2. classifier_pending

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | uuid | PK |
| `system` | varchar(20) | NOT NULL |
| `code` | text | NOT NULL |
| `found_in_document_id` | uuid | FK → documents, nullable |
| `status` | varchar(20) | `new`, `mapped`, `rejected` |
| `admin_comment` | text | nullable |
| `created_at` | timestamptz | NOT NULL |
| UNIQUE | | (`system`, `code`) |

### 5.3. terminology_entry

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | uuid | PK |
| `raw_term` | text | NOT NULL, UNIQUE |
| `standard_term` | text | NOT NULL |
| `normalized_value` | text | NOT NULL |
| `term_type` | varchar(30) | DEFAULT `'term'` |
| `is_case_sensitive` | boolean | DEFAULT false |
| `definition` | text | nullable |
| `synonyms` | jsonb | DEFAULT `[]` |
| `related_docs` | jsonb | DEFAULT `[]` |
| `scope` | jsonb | DEFAULT `[]` |
| `is_blocked` | boolean | DEFAULT false |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

### 5.4. registry_document

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | uuid | PK |
| `classifier_code` | text | nullable |
| `doc_code` | text | nullable |
| `title` | text | NOT NULL |
| `title_hash_sha256` | text | UNIQUE — бизнес-ключ |
| `status` | varchar(30) | NOT NULL |
| `era` | varchar(10) | nullable |
| `validity_status` | varchar(20) | nullable |
| `jurisdiction` | varchar(10) | nullable |
| `issuing_body` | text | nullable |
| `industry_code` | text | nullable |
| `enterprise_id` | uuid | nullable |
| `mks_oks_code` | text | FK → classifier_registry (MKS) |
| `okstu_code` | text | FK → classifier_registry (OKSTU) |
| `classification_status` | jsonb | DEFAULT `{}` |
| `successor_doc_id` | uuid | FK → self, nullable |
| `predecessor_doc_id` | uuid | FK → self, nullable |
| `chunk_container_id` | uuid | nullable |
| `metadata` | jsonb | DEFAULT `{}` |
| `created_at` | timestamptz | NOT NULL |
| `created_by` | text | nullable |
| `updated_at` | timestamptz | NOT NULL |
| `updated_by` | text | nullable |

> Сгенерированные колонки `mks_system` и `okstu_system` (GENERATED ALWAYS AS 'MKS'/'OKSTU') обеспечивают строгую FK-проверку к системе классификации.

---

## Примечания

1. **DB shared:** Все таблицы registry находятся в общей БД. Другие сервисы читают их напрямую.
2. **title_hash_sha256** вычисляется автоматически, гарантирует дедупликацию. Формула: `SHA-256(era|source_type|mks|okstu|doc_code|normalized_title)`.
3. **Параллельная классификация:** Документ может одновременно ссылаться на МКС/ОКС и ОКСТУ через разные FK.
4. **Журнал статусов:** Все изменения `documents.status` автоматически логируются в `status_history` триггером БД.
5. **Карантин кодов:** Коды, не найденные в справочнике, попадают в `classifier_pending`. Администратор разбирает их через UI.