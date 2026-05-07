## API Registry Service (registry-service:8085)

Сервис управления справочными данными НСИ: классификаторы, терминология, реестр документов.

Базовый путь: `/api/v1/registry`

### Формат ответа

Успех:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Ошибка:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "CLASSIFIER_NOT_FOUND",
    "message": "Классификатор с кодом 'OKS_99_999' не найден"
  }
}
```

Для списковых ответов `meta` содержит пагинацию:

```json
{
  "meta": {
    "total": 150,
    "page": 1,
    "page_size": 50
  }
}
```

Параметры пагинации для всех list-эндпоинтов:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `page` | int | 1 | Номер страницы |
| `page_size` | int | 50 | Записей на странице (max 200) |

### Коды ошибок

| HTTP-код | Код ошибки | Описание |
|----------|-----------|----------|
| 400 | `VALIDATION_ERROR` | Некорректные входные данные |
| 404 | `CLASSIFIER_NOT_FOUND` | Узел классификатора не найден |
| 404 | `TERM_NOT_FOUND` | Термин не найден |
| 404 | `DOCUMENT_NOT_FOUND` | Документ реестра не найден |
| 409 | `HAS_CHILDREN` | Нельзя удалить узел, имеющий дочерние |
| 409 | `DUPLICATE_CODE` | Код классификатора уже существует |
| 409 | `DUPLICATE_TERM` | Термин с таким контекстом уже существует |
| 500 | `INTERNAL_ERROR` | Внутренняя ошибка сервера |

### Содержание

| Группа | Описание |
|--------|----------|
| `classifiers` | Иерархический классификатор (OKS, GOST, ...) |
| `terminology` | Реестр терминов с нормализацией |
| `documents` | Реестр справочных документов НСИ |
| `common` | Статистика и допустимые значения |

---

## 1. Классификаторы

### 1.1. Список (плоский)

```
GET /registry/classifiers
```

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `code` | string | Нет | Частичное совпадение по коду |
| `full_name` | string | Нет | Поиск по названию (ILIKE) |
| `doc_type` | string | Нет | Фильтр по типу (OKS, GOST, ...) |
| `jurisdiction` | string | Нет | Фильтр по юрисдикции |
| `language` | string | Нет | Фильтр по языку |
| `is_thematic` | bool | Нет | true/false — только тематические |
| `parent_code` | string | Нет | Прямые дети указанного узла |

**Ответ (200):**

```json
{
  "success": true,
  "data": [
    {
      "code": "OKS_47_020",
      "parent_code": "OKS_47",
      "full_name": "Судостроение. Общие требования",
      "doc_type": "OKS",
      "jurisdiction": "RF",
      "language": "ru",
      "oks_code": "47.020",
      "is_thematic": true,
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-04-01T14:22:00Z"
    }
  ],
  "error": null,
  "meta": { "total": 43, "page": 1, "page_size": 50 }
}
```

### 1.2. Дерево (иерархическое)

```
GET /registry/classifiers/tree
```

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `root_code` | string | Нет | Если не указан — все корневые |
| `max_depth` | int | Нет (default 10) | Максимальная глубина |
| `search` | string | Нет | Поиск с раскрытием веток |

**Ответ (200):**

```json
{
  "success": true,
  "data": [
    {
      "code": "OKS_47",
      "full_name": "Судостроение",
      "doc_type": "OKS",
      "oks_code": "47",
      "is_thematic": true,
      "children": [
        {
          "code": "OKS_47_020",
          "full_name": "Общие требования",
          "doc_type": "OKS",
          "oks_code": "47.020",
          "is_thematic": true,
          "children": []
        }
      ]
    }
  ],
  "error": null,
  "meta": { "total": 2, "max_depth_reached": false }
}
```

### 1.3. Один узел

```
GET /registry/classifiers/{code}
```

**Ответ (200):** структура как в 1.2, включая `children` первого уровня вложенности.

### 1.4. Создать

```
POST /registry/classifiers
```

**Тело запроса:**

```json
{
  "code": "OKS_47_020_01",
  "parent_code": "OKS_47_020",
  "full_name": "Корпуса судов. Сварка",
  "doc_type": "GOST",
  "jurisdiction": "RF",
  "language": "ru",
  "oks_code": "47.020.01",
  "is_thematic": true
}
```

**Обязательные поля:** `code`, `full_name`.
**По умолчанию:** `doc_type = "OKS"`, `jurisdiction = "RF"`, `language = "ru"`, `is_thematic = true`.

**Ответ (201):** созданный объект (без children).

### 1.5. Обновить

```
PUT /registry/classifiers/{code}
```

**Тело:** все поля как в создании (кроме `code`).
**Ответ (200):** обновлённый объект.

### 1.6. Частичное обновление

```
PATCH /registry/classifiers/{code}
```

**Тело:** только изменяемые поля.

### 1.7. Удалить

```
DELETE /registry/classifiers/{code}
```

**Query-параметры:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `force` | bool | false | Удалить рекурсивно вместе с детьми |

**Ответ (200):** `{ "deleted_code": "OKS_47_020_01" }`

**Ответ (409) при наличии детей и force=false:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "HAS_CHILDREN",
    "message": "Нельзя удалить: узел имеет 3 дочерних. Используйте force=true"
  }
}
```

### 1.8. Импорт

```
POST /registry/classifiers/import
```

**Content-Type:** `multipart/form-data`

| Поле | Тип | Обязательный | Описание |
|------|-----|-------------|----------|
| `file` | file | Да | Файл .xlsx или .csv |
| `mapping` | JSON | Да | Соответствие колонок |

**Структура `mapping`:**

```json
{
  "code": "col_A",
  "full_name": "col_B",
  "parent_code": "col_C",
  "doc_type": null,
  "oks_code": "col_D"
}
```

Значение `null` — колонка не сопоставлена, используется значение по умолчанию.

**Ответ (200):**

```json
{
  "success": true,
  "data": {
    "inserted": 152,
    "updated": 10,
    "errors": [
      { "row": 5, "code": "OKS_XX", "message": "Код уже существует" }
    ]
  },
  "error": null
}
```

---

## 2. Термины

### 2.1. Список

```
GET /registry/terminology
```

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `term` | string | Нет | Поиск по term (ILIKE) |
| `normalized_term` | string | Нет | Поиск по normalized_term |
| `context` | string | Нет | Точное совпадение контекста |
| `source` | string | Нет | Поиск по источнику |

**Ответ (200):**

```json
{
  "success": true,
  "data": [
    {
      "term_id": 1,
      "term": "стойки установочные",
      "normalized_term": "стойки крепежные",
      "context": "Судостроение",
      "source": "ГОСТ 20868-81",
      "created_at": "2026-02-10T09:00:00Z"
    }
  ],
  "error": null,
  "meta": { "total": 1, "page": 1, "page_size": 50 }
}
```

### 2.2. Один термин

```
GET /registry/terminology/{term_id}
```

### 2.3. Создать

```
POST /registry/terminology
```

**Тело:**

```json
{
  "term": "РЭА",
  "normalized_term": "радиоэлектронная аппаратура",
  "context": "Общий",
  "source": "Словарь сокращений"
}
```

**Обязательные:** `term`, `normalized_term`.
**По умолчанию:** `context = "Общий"`.
**Уникальность:** составной ключ `(term, context)`. При конфликте — `DUPLICATE_TERM`.

### 2.4. Обновить

```
PUT /registry/terminology/{term_id}
```

### 2.5. Удалить

```
DELETE /registry/terminology/{term_id}
```

### 2.6. Поиск нормализованной формы

```
GET /registry/terminology/normalize
```

**Query:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `term` | string | Да | Исходный термин |
| `context` | string | Нет | Контекст |

**Ответ (200):**

Если найдено: `{ "term": "РЭА", "normalized_term": "радиоэлектронная аппаратура" }`
Если не найдено: `{ "term": "РЭА", "normalized_term": "РЭА" }` (возвращает исходный)

### 2.7. Импорт

```
POST /registry/terminology/import
```

Аналогично классификаторам: файл + mapping.

---

## 3. Реестр документов НСИ

### 3.1. Список

```
GET /registry/documents
```

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `title` | string | Нет | Поиск по названию |
| `doc_number` | string | Нет | Поиск по номеру |
| `classifier_code` | string | Нет | Фильтр по коду классификатора |
| `status` | string | Нет | draft/active/obsolete/need_to_buy/searching |
| `source` | string | Нет | Поиск по источнику |
| `date_from` | date | Нет | Созданы после (YYYY-MM-DD) |
| `date_to` | date | Нет | Созданы до |

**Ответ (200):**

```json
{
  "success": true,
  "data": [
    {
      "doc_id": 1,
      "title": "Стойки установочные",
      "doc_number": "ГОСТ 20868-81",
      "classifier_code": "OKS_31_240",
      "classifier_name": "Электроника. Монтажные изделия",
      "status": "active",
      "source": "cntd.ru",
      "notes": "Есть скан в архиве",
      "created_at": "2026-03-01T11:00:00Z",
      "updated_at": "2026-03-15T16:30:00Z"
    }
  ],
  "error": null,
  "meta": { "total": 1, "page": 1, "page_size": 50 }
}
```

### 3.2. Один документ

```
GET /registry/documents/{doc_id}
```

**Ответ (200):** полный объект с `classifier_name`.

### 3.3. Создать

```
POST /registry/documents
```

**Тело:**

```json
{
  "title": "Стойки установочные",
  "doc_number": "ГОСТ 20868-81",
  "classifier_code": "OKS_31_240",
  "status": "draft",
  "source": "cntd.ru",
  "notes": "Ожидается загрузка файла"
}
```

**Обязательные:** `title`.
**По умолчанию:** `status = "draft"`.

### 3.4. Обновить

```
PUT /registry/documents/{doc_id}
```

### 3.5. Обновить статус

```
PATCH /registry/documents/{doc_id}/status
```

**Тело:**

```json
{
  "status": "active"
}
```

Допустимые статусы: `draft`, `active`, `obsolete`, `need_to_buy`, `searching`.

### 3.6. Удалить

```
DELETE /registry/documents/{doc_id}
```

### 3.7. Экспорт

```
GET /registry/documents/export
```

**Query:** те же фильтры, что и в списке.
**Ответ (200):** файл CSV с заголовком `Content-Type: text/csv; charset=utf-8-sig`.

### 3.8. Массовый импорт

```
POST /registry/documents/import
```

Файл + mapping (аналогично классификаторам).

---

## 4. Общие

### 4.1. Статистика

```
GET /registry/stats
```

**Ответ (200):**

```json
{
  "success": true,
  "data": {
    "classifiers_total": 287,
    "terminology_total": 1204,
    "documents_total": 56,
    "documents_by_status": {
      "draft": 10,
      "active": 30,
      "obsolete": 5,
      "need_to_buy": 8,
      "searching": 3
    }
  },
  "error": null
}
```

### 4.2. Допустимые значения

```
GET /registry/enums
```

Сводный справочник enum-значений, используемых всеми сервисами системы.

**Ответ (200):**

```json
{
  "success": true,
  "data": {
    "doc_type": ["OKS", "GOST", "GOST_R", "OST", "TU", "ISO", "FSN"],
    "jurisdiction": ["RF", "EAES", "INTL", "US", "EU", "DE"],
    "language": ["ru", "en", "de"],
    "document_status": ["draft", "active", "obsolete", "need_to_buy", "searching"],
    "context": ["Общий", "Судостроение", "Электроника", "Металлургия", "Строительство"],
    "file_document_type": ["normative", "archival_scan", "drawing", "specification"],
    "file_document_status": ["queued", "processing", "processed", "error"],
    "check_result_status": ["OK", "WARNING", "ERROR"],
    "match_status": ["match", "possible_discrepancy", "not_found_in_project", "not_found_in_norm", "insufficient_data"],
    "ocr_engine": ["paddleocr", "tesseract"],
    "chat_status": ["answered", "needs_clarification", "source_conflict"]
  },
  "error": null
}
```

---

## 5. Модели данных

Таблицы находятся в общей БД, доступны напрямую всем сервисам.

### 5.1. ClassifierNode

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `code` | varchar(50) | PK |
| `parent_code` | varchar(50) | FK → classifier_registry.code, nullable |
| `full_name` | varchar(500) | NOT NULL |
| `doc_type` | varchar(20) | NOT NULL, DEFAULT 'OKS' |
| `jurisdiction` | varchar(10) | NOT NULL, DEFAULT 'RF' |
| `language` | varchar(5) | NOT NULL, DEFAULT 'ru' |
| `oks_code` | varchar(20) | nullable |
| `is_thematic` | boolean | NOT NULL, DEFAULT true |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

### 5.2. TerminologyEntry

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `term_id` | serial | PK |
| `term` | varchar(500) | NOT NULL |
| `normalized_term` | varchar(500) | NOT NULL |
| `context` | varchar(100) | NOT NULL, DEFAULT 'Общий' |
| `source` | varchar(500) | nullable |
| `created_at` | timestamptz | NOT NULL |
| UNIQUE | | (`term`, `context`) |

### 5.3. RegistryDocument

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `doc_id` | serial | PK |
| `title` | varchar(500) | NOT NULL |
| `doc_number` | varchar(100) | nullable |
| `classifier_code` | varchar(50) | FK → classifier_registry.code, nullable |
| `status` | varchar(20) | NOT NULL, DEFAULT 'draft' |
| `source` | varchar(500) | nullable |
| `notes` | text | nullable |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

---

## 6. Примечания

1. **DB shared:** Все таблицы registry находятся в общей БД. Другие сервисы читают их напрямую без вызова Registry Service.
2. **Импорт:** Все форматы файлов — `.xlsx` и `.csv`. Параметр `mapping` определяет соответствие колонок файла полям модели.
3. **Поиск:** Все текстовые поиски регистронезависимые (ILIKE).
4. **Валидация:** Все `POST/PUT/PATCH` валидируются через Pydantic V2 модели.
