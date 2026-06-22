## API Registry Service / Registry (registry-service:8084)

Базовый реестр НСИ (нормативно-справочной информации).  
Хранит классификаторы, документы, терминологию и данные черновиков (drafts).  
Управление данными черновиков: хранение, статусы, метаданные.  
Соответствует этапу **«Registry» Пайплайна 1 (Формирование документа)** — **пишет** данные в БД.  
Также участвует в этапе **«Validation»** — **читает** справочники классификаторов для проверки кодов.

**Внутренний сервис**. API — через Gateway Service.

**Базовый URL**: `http://127.0.0.1:8084/api/v1`

### Формат ответа

Формат ошибок — см. [common_api.md](common_api.md#формат-ответа).

Списочные ответы обёрнуты в `{ data, meta }`:
```json
{
  "data": [ ... ],
  "meta": { "total": 150, "page": 1, "page_size": 50 }
}
```
Для одиночных объектов:
```json
{
  "data": { "id": 1, "title": "..." }
}
```

### Коды ошибок

Общие коды (400, 404, 500) — см. [common_api.md](common_api.md#коды-ответов-http-и-ошибок).

| HTTP | `error.code` | Описание |
|------|-------------|----------|

---

## Межсервисное взаимодействие

Авторизацию контролирует только Gateway. Внутренние сервисы не имеют своей аутентификации — см. [common_api.md](common_api.md#межсервисное-взаимодействие).
| 404 | `CLASSIFIER_NOT_FOUND` | Узел классификатора не найден |
| 404 | `TERM_NOT_FOUND` | Термин не найден |
| 404 | `DOCUMENT_NOT_FOUND` | Документ не найден |
| 404 | `DRAFT_NOT_FOUND` | Черновик не найден |
| 404 | `CATEGORY_NOT_FOUND` | Категория не найдена |
| 409 | `CATEGORY_HAS_DOCUMENTS` | Нельзя удалить категорию, к которой привязаны документы |
| 409 | `DUPLICATE_CATEGORY_NAME` | Категория с таким именем уже существует |
| 409 | `DRAFT_ALREADY_DECIDED` | Решение по черновику уже принято |
| 409 | `DRAFT_ALREADY_PREVIEWED` | Черновик уже прошёл preview |
| 400 | `EMPTY_DOCUMENT` | Нельзя завершить черновик с 0 страниц |
| 409 | `DUPLICATE_CODE` | Код (в системе) уже существует |
| 409 | `DUPLICATE_DOCUMENT` | Документ с таким бизнес-ключом уже есть |
| 409 | `DUPLICATE_TERM` | Термин уже существует |
| 409 | `HAS_CHILDREN` | Нельзя удалить узел с дочерними |
| 409 | `HAS_DOCUMENTS` | Есть документы, ссылающиеся на код |
| 409 | `CROSS_SYSTEM_PARENT` | Родитель в другой системе классификации |

---

### Содержание

| Группа | Описание |
|--------|----------|
| `classifiers` | Иерархический справочник классификаторов (МКС, ОКСТУ, УДК, внешние) |
| `terminology` | Реестр терминов, синонимов и правил нормализации |
| `documents` | Реестр логических документов НСИ |
| `drafts` | Управление данными черновиков |
| `common` | Статистика и справочные значения |
| `categories` | Пользовательские категории документов (many-to-many) |

---

## Группа classifiers

### О системе кодирования МКС/ОКС

Классификатор МКС (ОК 001-2021, ICS) использует трёхуровневую иерархию:

- **Раздел (XX)** — двузначный код, например `47 Судостроение и морские сооружения`
- **Группа (XX.XXX)** — трёхзначный код после точки, например `47.020 Конструкция корпуса`
- **Подгруппа (XX.XXX.XX)** — двузначный код, например `47.020.30 Корпусные конструкции`
- **Национальное расширение (XX.XXX.XX-XX)** — дополнительный двузначный код через дефис, например `27.010-01 Энергосбережение`

**Валидация кода:**
```
^\d{2}(?:\.\d{3}(?:\.\d{2})?)?(?:-\d{2})?$
```

> ⚠️ **Недопустимо**: использовать усечённые коды (например, `31.24` вместо `31.240`). Подгруппы должны иметь полный трёхуровневый код `XX.XXX.XX`. Нарушение приводит к ошибкам классификации документов.

**Источник:** ОК 001-2021 (ИСО МКС), гармонизированный с ISO ICS. Демонстрационный набор кодов — в `specifications/mks_oks_classifier.csv`. Корневые узлы классификаторов — в `specifications/classifier_roots.csv`.

**Запрет:** ОКС — рубрики-папки, документ — файл с метаданными. Не следует «встраивать» тип документа в дерево классификаторов.

---

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/registry/classifiers` | Список (плоский) |
| GET | `/registry/classifiers/tree` | Дерево (иерархическое) |
| GET | `/registry/classifiers/{code}` | Один узел |
| POST | `/registry/classifiers` | Создать |
| PUT | `/registry/classifiers/{code}` | Обновить |
| PATCH | `/registry/classifiers/{code}` | Частичное обновление |
| DELETE | `/registry/classifiers/{code}` | Удалить |
| POST | `/registry/classifiers/import` | Импорт |
| GET | `/registry/classifiers/pending` | Неизвестные коды классификатора |
| POST | `/registry/classifiers/pending/{pending_id}/accept` | Принять неизвестный код |
| POST | `/registry/classifiers/pending/{pending_id}/reject` | Отклонить неизвестный код |
| POST | `/registry/classifiers/validate` | Валидация классификации |

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

### 1.9. Неизвестные коды классификатора

```
GET /registry/classifiers/pending
```

Коды классификатора (МКС, ОКСТУ, УДК), найденные в документах при распознавании, но отсутствующие в справочнике. Требуют административного разбора.

**Query-параметры**: `system` (`MKS`, `OKSTU`, `UDC`, `EXTERNAL`), `status` (`new`, `mapped`, `rejected`), `page`, `page_size`.

**Ответ `200`:**

```json
{
  "data": [
    {
      "id": 1,
      "system": "MKS",
      "code": "47.020.99",
      "found_in_document_id": 1,
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

### 1.10. Принять неизвестный код

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
    "pending_id": 1,
        "classifier_system": "MKS",
    "code": "47.020.99",
    "status": "mapped",
    "registry_created": true
  }
}
```

---

### 1.11. Отклонить неизвестный код

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
  "data": { "pending_id": 1, "status": "rejected" }
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

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/registry/terminology` | Список |
| GET | `/registry/terminology/{term_id}` | Один термин |
| POST | `/registry/terminology` | Создать |
| PUT | `/registry/terminology/{term_id}` | Обновить |
| DELETE | `/registry/terminology/{term_id}` | Удалить |
| GET | `/registry/terminology/normalize` | Поиск нормализованной формы |
| POST | `/registry/terminology/import` | Импорт |

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

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET | `/registry/documents` | Список документов | public |
| GET | `/registry/documents/search` | **Полнотекстовый поиск (BM25)** — поиск по `doc_code`, `title`, `classifier_links` | public |
| POST | `/registry/documents/search` | **Семантический поиск** — поиск документов по structured-запросу | public |
| GET | `/registry/documents/{doc_id}` | Один документ (описание) | public |
| GET | `/registry/documents/{doc_id}/sections` | Секции документа (для RAG Builder) | public |
| GET | `/registry/documents/{doc_id}/pages` | Список страниц документа | public |
| GET | `/registry/documents/{doc_id}/pages/{page_num}` | Конкретная страница (bbox) | public |
| GET | `/registry/documents/{doc_id}/pages/{page_num}/text` | Текстовый слой страницы | public |
| GET | `/registry/documents/{doc_id}/pages/{page_num}/preview` | Превью страницы (изображение + blocks) | public |
| GET | `/registry/documents/{doc_id}/file` | Скачивание файла документа | public |
| GET | `/registry/documents/{doc_id}/history` | История статусов документа | public |
| GET | `/registry/documents/{doc_id}/versions` | Список версий документа | public |
| GET | `/registry/documents/{doc_id}/parameters` | Извлечённые параметры (формулы) | public |
| GET | `/registry/documents/{doc_id}/succession` | Цепочка преемственности | public |
| POST | `/registry/documents/check-uniqueness` | Проверить уникальность | public |
| POST | `/registry/documents` | Создать (из Пайплайна 1 или вручную) | **internal** (только Orchestrator) |
| PUT | `/registry/documents/{doc_id}` | Полное обновление карточки | public |
| PATCH | `/registry/documents/{doc_id}` | Частичное обновление карточки | public |
| PATCH | `/registry/documents/{doc_id}/status` | Обновить FSM-статус | **internal** (только Orchestrator) |
| DELETE | `/registry/documents/{doc_id}` | Мягкое удаление | public |
| POST | `/registry/documents/{doc_id}/reprocess` | Переобработка документа (reprocess) | public |
| GET | `/registry/documents/export` | Экспорт карточек | public |
| POST | `/registry/documents/import` | Массовый импорт | public |

> **public** — Gateway проксирует запрос напрямую в Registry.
> **internal** — недоступен через Gateway, вызывается только Orchestratorом по внутренней сети.

### 3.1. Список

```
GET /registry/documents
```

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `title` | string | Поиск по названию |
| `doc_code` | string | Поиск по номеру |
| `source_type` | string | `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `mks_oks_code` | string | Фильтр по коду МКС/ОКС |
| `okstu_code` | string | Фильтр по коду ОКСТУ |
| `status` | string | FSM-статус документа (управляется Оркестратором, фильтр read-only) |
| `era` | string | `USSR`, `CIS`, `RF`, `CURRENT` |
| `validity_status` | string | `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `jurisdiction` | string | `RU`, `EU`, `US`, `NO`, `INTL` |
| `issuing_body` | string | Организация-издатель |
| `document_type` | string | Категория контента: `normative`, `technical`, `drawing`, `specification`, `archival_scan` |
| `title_hash_sha256` | string | Точный поиск по бизнес-ключу |
| `category_id` | int | Фильтр по ID категории (документы, привязанные к категории) |
| `date_from` / `date_to` | date | Фильтр по дате создания |
| `valid_at` | date | **P12-5 (новое)**: выборка документов, действующих на указанную дату (`valid_from <= ? AND valid_until >= ?`). Использует индекс `idx_documents_validity_range` |
| `sort_by` | string | Поле сортировки: `title`, `doc_code`, `source_type`, `era`, `created_at`, `updated_at` (по умолчанию `created_at`) |
| `order` | string | Направление: `asc`, `desc` (по умолчанию `desc`) |
| `page` | int | Номер страницы |
| `page_size` | int | Записей на странице (max 200) |

**Ответ `200`:**

```json
{
  "data": [
    {
      "id": 1,
      "title": "Стойки установочные",
      "doc_code": "20868-81",
      "source_type": "GOST",
      "document_type": "normative",
      "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
      "title_key": "USSR|gost|47.020||20868-81|стойки установочные...",
      "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "file_size_bytes": 2048576,
      "status": "indexed",
      "era": "USSR",
      "validity_status": "active",
      "jurisdiction": "RU",
      "issuing_body": "Госстандарт СССР",
      "mks_oks_code": "31.240",
      "mks_name": "Электроника. Монтажные изделия",
      "okstu_code": null,
      "okstu_name": null,
      "classification_status": {
        "mks": ["31.240"],
        "okstu": [],
        "udk": [],
        "subject_area": ["Электроника", "Монтажные изделия"]
      },
      "adoption_date": "1981-07-01",
      "effective_from": "1982-01-01",
      "replaces": null,
      "status_note": null,
      "successor_doc_id": null,
      "predecessor_doc_id": null,
      "total_versions": 2,
      "chunk_count": 34,
      "categories": [
        { "id": 1, "name": "Корпусные конструкции" },
        { "id": 3, "name": "Материалы" }
      ],
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

### 3.1a. Полнотекстовый поиск (BM25)

```
GET /registry/documents/search
```

Поиск по `doc_code`, `title`, `classifier_links` с использованием `ts_rank` + `pg_trgm`. 

> **Внутренний эндпоинт.** Используется для межсервисного взаимодействия (RAG Search → Registry). Не предназначен для прямого вызова из UI. RBAC не применяется — запросы идут напрямую между сервисами, минуя Gateway.

---

### 3.1b. Семантический поиск документов (POST)

```
POST /registry/documents/search
```

Поиск документов по structured-запросу с семантическим поиском по содержимому. Возвращает документы с релевантными фрагментами.

**Запрос**:

```json
{
  "query": "толщина обшивки ледового пояса Arc4",
  "filters": {
    "source_type": ["GOST", "RMRS"],
    "document_type": ["normative"],
    "era": ["RF", "CURRENT"],
    "valid_at": "2026-06-18"
  },
  "page": 1,
  "page_size": 20
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|-------------|----------|
| `query` | string | Да | Поисковый запрос |
| `filters` | object | Нет | Фильтры (все поля опциональны): `source_type[]`, `document_type[]`, `era[]`, `valid_at` |
| `page` | int | Нет | Номер страницы (по умолчанию 1) |
| `page_size` | int | Нет | Размер страницы (по умолчанию 20) |

**Ответ `200`**:

```json
{
  "items": [
    {
      "document_id": 1,
      "title": "Правила РС, часть I",
      "doc_code": "20868-81",
      "source_type": "RMRS",
      "era": "CURRENT",
      "score": 0.94,
      "fragments": [
        {
          "page": 42,
          "section_id": 420042,
          "content": "Для ледового класса Arc4 толщина обшивки...",
          "score": 0.94
        }
      ]
    }
  ],
  "meta": {
    "total": 7,
    "page": 1,
    "page_size": 20
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `items` | array | Массив результатов поиска |
| `items[].document_id` | bigint | ID документа в Registry |
| `items[].title` | string | Название документа |
| `items[].doc_code` | string | Код документа |
| `items[].source_type` | string | Тип источника |
| `items[].era` | string | Эра |
| `items[].score` | float | Релевантность (0..1) |
| `items[].fragments` | array | Совпадающие фрагменты |
| `items[].fragments[].page` | int | Номер страницы |
| `items[].fragments[].section_id` | bigint | ID секции |
| `items[].fragments[].content` | string | Текст фрагмента |
| `items[].fragments[].score` | float | Релевантность фрагмента |
| `meta.total` | int | Общее количество результатов |
| `meta.page` | int | Текущая страница |
| `meta.page_size` | int | Размер страницы |

---

**Query-параметры:**

| Параметр | Тип | Обязательность | Описание |
|----------|-----|---------------|----------|
| `q` | string | Да | Поисковый запрос (BM25 по `doc_code`, `title`, `classifier_links`) |
| `limit` | int | Нет | Количество результатов (max 50, по умолчанию 10) |
| `offset` | int | Нет | Смещение (по умолчанию 0) |

**Ответ `200`:**

```json
{
  "data": [
    {
      "document_id": 1,
      "title": "Стойки установочные",
      "doc_code": "20868-81",
      "source_type": "GOST",
      "score": 0.85
    }
  ],
  "meta": { "total": 5, "page": 1, "page_size": 10 }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `data[].document_id` | bigint | ID документа |
| `data[].title` | string | Название документа |
| `data[].doc_code` | string \| null | Код документа |
| `data[].source_type` | string \| null | Тип источника |
| `data[].score` | float | Релевантность (BM25) |
| `meta` | object | Пагинация (`total`, `page`, `page_size`) |

---

### 3.2. Один документ (описание)

```
GET /registry/documents/{doc_id}
```

**Ответ `200`** — метаданные документа (описание карточки) из таблицы `registry_documents`.
Без секций, терминологии и ссылок.

Ключевые поля:
- `id` — bigint ID документа
- `doc_code` — код документа (ГОСТ, ОСТ и т.д.)
- `title` — название документа
- `title_hash_sha256` — хэш бизнес-ключа
- `title_key` — исходная строка конкатенации для `title_hash_sha256` (аудит/отладка)
- `preview_snapshot` — исходный JSON ответа Converter-validator preview, скопированный из черновика при approve (JSONB, nullable). Для истории и аудита
- `status` — FSM-статус обработки (управляется Оркестратором, Registry — read-only)
- `era` — эпоха (`USSR`, `CIS`, `RF`, `CURRENT`)
- `validity_status` — юридический статус (`active`, `superseded`, `cancelled`, `historical`, `draft`)
- `jurisdiction` — юрисдикция (`RU`, `EU`, `US`, `NO`, `INTL`)
- `issuing_body` — организация-издатель
- `source_type` — тип источника (`GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER`)
- `document_type` — категория контента (`normative`, `technical`, `drawing`, `specification`, `archival_scan`)
- `mks_oks_code` — код МКС/ОКС
- `okstu_code` — код ОКСТУ
- `classification_status` — статус классификации (`{ mks: string[], okstu: string[], udk: string[], subject_area: string[] }`)
- `adoption_date` — дата принятия документа
- `effective_from` — дата введения в действие
- `valid_from` — **P12-5 (новое)**: дата начала действия документа. NOT NULL. См. конвенцию `dateMax` в `glossary.md`
- `valid_until` — **P12-5 (новое)**: дата окончания действия документа. NOT NULL (в БД). Для бессрочных — в БД хранится `9999-12-31` (конвенция `dateMax`), но в API-ответах возвращается как `null`. При `null` от клиента backend подставляет `dateMax`
- `replaces` — сведения о заменяемом документе
- `status_note` — примечание к статусу
- `successor_doc_id` — ID документа-преемника
- `predecessor_doc_id` — ID документа-предшественника
- `metadata` — произвольные метаданные (JSONB)
- `categories` — список категорий документа: `[{ id, name }]`
- `created_at` / `updated_at` — даты создания и обновления
- `created_by` / `updated_by` — кем создан/обновлён

**Пример ответа:**

```json
{
  "data": {
    "id": 1,
    "doc_code": "ГОСТ 20868-81",
    "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования",
    "title_hash_sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    "title_key": "USSR|gost|31.240||20868-81|стойки установочные крепежные...",
    "preview_snapshot": { /* см. _schemas.md#PreviewMetadata */ },
    "document_type": "normative",
    "status": "indexed",
    "era": "USSR",
    "validity_status": "active",
    "jurisdiction": "RU",
    "issuing_body": "Государственный Комитет СССР по стандартам",
    "source_type": "GOST",
    "mks_oks_code": "31.240",
    "okstu_code": null,
    "udk_code": null,
    "classification_status": {
      "mks": ["31.240"],
      "okstu": [],
      "udk": [],
      "subject_area": ["Электроника", "Монтажные изделия"]
    },
    "adoption_date": "1981-07-01",
    "effective_from": "1982-01-01",
    "valid_from": "1982-01-01",
    "valid_until": null,
    "replaces": null,
    "status_note": null,
    "successor_doc_id": null,
    "predecessor_doc_id": null,
    "categories": [
      { "id": 1, "name": "Корпусные конструкции" },
      { "id": 3, "name": "Материалы" }
    ],
    "metadata": {},
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T14:00:00Z",
    "created_by": "system_registry_sync",
    "updated_by": "ivanov_ai"
  }
}
```

> 📖 **Схема полей `preview_snapshot`** — [_schemas.md](_schemas.md#PreviewMetadata).

---

### 3.2.1. Секции документа (полный объект для RAG Builder)

```
GET /registry/documents/{doc_id}/sections
```

**Ответ `200`** — полный объект документа со всеми секциями, терминологией и ссылками.
Этот JSON используется RAG Builder для построения чанков: RAG Builder самостоятельно
разбирает `content` каждой секции в зависимости от `type`.

Формат ответа — см. [`schema_registry_for_rag.json`](../schema/schema_registry_for_rag.json).

Ключевые поля:
- `document` — метаданные документа (id, doc_code, title, era, validity_status и др.)
- `sections[]` — массив секций с полями: `section_id`, `document_id`, `parent_id`, `clause`, `title`, `level`, `path`, `page`, `type`, `content`, `created_at`
  - `content` — объектный, зависит от `type` (см. описание схемы БД)
- `terminology[]` — термины документа
- `references[]` — ссылки документа

**Пример ответа (сокращён):**

```json
{
  "document": {
    "id": 1,
    "doc_code": "ГОСТ 20868-81",
    "title": "СТОЙКИ УСТАНОВОЧНЫЕ...",
    "era": "USSR",
    "validity_status": "active"
  },
  "sections": [
    {
      "section_id": 1001,
      "document_id": 1,
      "parent_id": null,
      "clause": "1",
      "title": null,
      "level": 1,
      "path": "1",
      "page": 1,
      "type": "text",
      "content": { "text": "...", "amendments": [] }
    },
    {
      "section_id": 1005,
      "document_id": 1,
      "parent_id": 1003,
      "clause": "6.1",
      "title": "Допуск соосности при степени точности",
      "level": 2,
      "path": "6.1.table1",
      "page": 2,
      "type": "table",
      "content": { "columns": [...], "rows": [...], "footnotes": [...] }
    }
  ],
  "terminology": [],
  "references": []
}
```

> **RAG Builder** получает этот JSON и строит чанки:
> - `type=text` / `type=textBlock` → `content.text` разбивается на чанки ≤512 токенов
> - `type=headerFooter` → весь `content.text` → один чанк
> - `type=table` / `type=list` → `content.markdown` (если есть), иначе сборка из структуры → один чанк
> - `type=image` → `content.markdown` или `content.caption + content.description` → один чанк
> - `type=formula` → `content.markdown` или `content.latex + content.meaning` → один чанк

---

### 3.2.2. Страницы документа

```
GET /registry/documents/{doc_id}/pages
```

Список страниц документа с размерами и статусом OCR.

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "pages_total": 10,
    "pages": [
      {
        "page": 1,
        "width": 595.0,
        "height": 842.0,
        "ocr_status": "completed",
        "confidence": 0.98,
        "has_text_layer": true
      }
    ]
  },
  "meta": { "total": 10, "page": 1, "page_size": 50 }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | bigint | ID документа |
| `pages_total` | int | Общее количество страниц |
| `pages[].page` | int | Номер страницы |
| `pages[].width` | float | Ширина страницы в пунктах (pt) |
| `pages[].height` | float | Высота страницы в пунктах (pt) |
| `pages[].ocr_status` | string | Статус OCR: `pending`, `processing`, `completed`, `failed` |
| `pages[].confidence` | float | Уверенность распознавания (0..1) |
| `pages[].has_text_layer` | bool | Есть ли текстовый слой в PDF |

---

### 3.2.3. Конкретная страница

```
GET /registry/documents/{doc_id}/pages/{page_num}
```

Метаданные одной страницы (bbox-координаты блоков).

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "page": 1,
    "width": 595.0,
    "height": 842.0,
    "blocks": [
      {
        "number": 1,
        "type": "text",
        "bbox": [56.7, 70.9, 481.9, 18.0],
        "content": "ГОСТ 20868-81",
        "confidence": 0.99
      }
    ]
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | bigint | ID документа |
| `page` | int | Номер страницы |
| `width` | float | Ширина страницы в pt |
| `height` | float | Высота страницы в pt |
| `blocks[].number` | int | Порядковый номер блока на странице |
| `blocks[].type` | string | Тип блока: `text`, `table`, `image`, `header`, `footer` |
| `blocks[].bbox` | array | Координаты [x1, y1, x2, y2] (0..1) |
| `blocks[].content` | string | Содержимое блока |
| `blocks[].confidence` | float | Уверенность (0..1) |

---

### 3.2.4. Текст страницы

```
GET /registry/documents/{doc_id}/pages/{page_num}/text
```

Детальный текстовый слой страницы: блоки с bbox, таблицы и формулы.

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "page": 1,
    "width": 595.0,
    "height": 842.0,
    "blocks": [
      {
        "number": 1,
        "type": "text",
        "bbox": [56.7, 70.9, 481.9, 18.0],
        "content": "ГОСТ 20868-81",
        "confidence": 0.99
      },
      {
        "number": 2,
        "type": "table",
        "bbox": [56.7, 100.0, 481.9, 200.0],
        "content": { "columns": [], "rows": [] },
        "confidence": 0.95
      }
    ]
  }
}
```

Формат `blocks[].content` соответствует типу блока (см. `_schemas.md`).

---

### 3.2.5. Превью страницы

```
GET /registry/documents/{doc_id}/pages/{page_num}/preview
```

Изображение превью страницы с наложенными bbox-блоками.

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "page": 1,
    "image_url": "http://minio:9000/pkb/previews/1/p1.png",
    "blocks": [
      {
        "number": 1,
        "type": "text",
        "bbox": [56.7, 70.9, 481.9, 18.0],
        "content": "ГОСТ 20868-81"
      }
    ],
    "text_layer": "ГОСТ 20868-81\nНастоящий стандарт..."
  }
}
```

---

### 3.2.6. Файл документа

```
GET /registry/documents/{doc_id}/file
```

Скачивание файла последней версии документа (или конкретной версии, если передан `?version_id=`).

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `version_id` | bigint | ID конкретной версии (если не указан — последняя) |
| `format` | string | Формат ответа: `json` (по умолчанию, возвращает URL), `binary` (поток) |

**Ответ `200` (format=json):**

```json
{
  "data": {
    "file_url": "http://minio:9000/pkb/documents/f-abc123.pdf",
    "file_size": 2048576,
    "content_type": "application/pdf"
  }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `file_url` | string | Прямая ссылка на файл в MinIO (pre-signed URL) |
| `file_size` | int | Размер файла в байтах |
| `content_type` | string | MIME-тип файла |

---

### 3.2.7. История статусов

```
GET /registry/documents/{doc_id}/history
```

История изменения статусов документа.

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "history": [
      {
        "history_id": 1,
        "event_type": "created",
        "old_status": null,
        "new_status": "created",
        "comment": "Документ создан из черновика",
        "changed_by": "orchestrator",
        "event_at": "2026-05-17T09:15:00Z"
      },
      {
        "history_id": 2,
        "event_type": "status_changed",
        "old_status": "pending_index",
        "new_status": "indexed",
        "comment": "Индексация завершена",
        "changed_by": "orchestrator",
        "event_at": "2026-05-17T09:20:00Z"
      }
    ]
  },
  "meta": { "total": 2 }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `history[].history_id` | bigint | ID записи истории |
| `history[].event_type` | string | Тип события: `created`, `status_changed`, `decided`, `reprocessed` |
| `history[].old_status` | string | Предыдущий статус |
| `history[].new_status` | string | Новый статус |
| `history[].comment` | string | Комментарий |
| `history[].changed_by` | string | Субъект (пользователь или сервис) |
| `history[].event_at` | datetime | Время события (ISO 8601) |

---

### 3.2.8. Версии документа

```
GET /registry/documents/{doc_id}/versions
```

Список версий документа.

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "versions": [
      {
        "version_id": 1,
        "version_number": 1,
        "format_code": "pdf",
        "format_label": "PDF/A",
        "file_key": "f-abc123",
        "file_hash_sha256": "e3b0c442...",
        "size_bytes": 2048576,
        "created_at": "2026-05-17T09:15:00Z",
        "created_by": "orchestrator"
      }
    ]
  },
  "meta": { "total": 1 }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `versions[].version_id` | bigint | ID версии |
| `versions[].version_number` | int | Номер версии (начиная с 1) |
| `versions[].format_code` | string | Код формата: `pdf`, `pdfa`, `tiff`, `png` |
| `versions[].format_label` | string | Человекочитаемое название формата |
| `versions[].file_key` | string | Ключ файла в MinIO |
| `versions[].file_hash_sha256` | string | SHA-256 хеш файла |
| `versions[].size_bytes` | int | Размер файла в байтах |
| `versions[].created_at` | datetime | Время создания версии |
| `versions[].created_by` | string | Субъект-создатель |

---

### 3.2.9. Параметры документа

```
GET /registry/documents/{doc_id}/parameters
```

Извлечённые из документа параметры (символы, формулы с единицами измерения).

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "parameters": [
      {
        "symbol": "t",
        "description": "Толщина обшивки",
        "unit": "mm",
        "value": 12.5,
        "source_clause": "2.3.1",
        "source_page": 5
      },
      {
        "symbol": "σ_y",
        "description": "Предел текучести",
        "unit": "MPa",
        "range": { "min": 235, "max": 355 },
        "source_clause": "2.3.5",
        "source_page": 6
      }
    ]
  },
  "total": 2
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `parameters[].symbol` | string | Символ/обозначение параметра |
| `parameters[].description` | string | Описание |
| `parameters[].unit` | string | Единица измерения |
| `parameters[].value` | number | Значение параметра |
| `parameters[].range` | object | Диапазон значений: `{ min, max }` |
| `parameters[].source_clause` | string | Пункт документа-источника |
| `parameters[].source_page` | int | Страница источника |

---

### 3.2.10. Проверить уникальность документа

```
POST /registry/documents/check-uniqueness
```

Быстрая проверка уникальности документа по метаданным. Вызывается **Оркестратором**
на preview- и full-этапах Пайплайна 1 для поиска дубликатов до записи в Registry.

**Тело запроса:**

| Поле | Тип | Обязательность | Описание |
|------|-----|----------------|----------|
| `title` | string | Да | Название документа (нормализованное) |
| `doc_code` | string | Нет | Код документа (ГОСТ, ОСТ и т.д.) |
| `era` | string | Нет | Эпоха действия документа |
| `source_type` | string | Нет | Тип источника |
| `file_size_bytes` | int | Нет | Размер файла в байтах. Используется для pre-filtering при поиске кандидатов |

```json
{
  "title": "Стойки установочные крепежные. Технические требования",
  "doc_code": "ГОСТ 20868-81",
  "era": "USSR",
  "file_size_bytes": 2048576
}
```

**Ответ `200`:**

```json
{
  "data": {
    "is_duplicate": false,
    "is_duplicate_file": false,
    "candidates": [
      {
        "document_id": 1,
        "title": "ГОСТ 20868-81",
        "doc_code": "20868-81",
        "similarity": 0.98,
        "status": "failed",
        "file_size_bytes": 1048576
      }
    ],
    "file_hash_sha256": null,
    "title_hash_sha256": "a1b2c3d4e5f6...",
    "title_key": "USSR|gost|47.020||20868-81|стойки установочные...",
    "file_size_bytes": 2048576,
    "checked_at": "2026-05-15T12:00:00Z"
  }
}
```

**Логика определения дубликатов:**
1. Pre-filter по размеру: если передан `file_size_bytes`, кандидаты с существенно отличающимся размером отфильтровываются (`|size₁ - size₂| > 0.5% max(size₁, size₂)` — false positive отличия метаданных в архиве).
2. Поиск по `title_hash_sha256` (точное совпадение нормализованного названия).
3. Поиск по `doc_code` + `era` (документ с тем же кодом в ту же эпоху).
4. Если кандидат найден и имеет статус обработки `created` или `indexed` — считается дубликатом.
5. Если кандидат найден, но находится в `failed` — возвращается как кандидат,
   решение принимает пользователь.

> **P0-3 (неатомарность check-uniqueness):** раздельные шаги «проверить» + «создать» могут привести к race condition при конкурентных загрузках одного документа. **Решение**: `INSERT INTO registry.documents (...) VALUES (...) ON CONFLICT (title_hash_sha256) DO NOTHING RETURNING id`. При `duplicate_file_hash` — `SELECT id FROM registry.document_versions WHERE file_hash_sha256 = ?`. Таким образом, проверка уникальности и вставка — атомарны. Отдельный эндпоинт `check-uniqueness` остаётся для preview (информационные цели), но финальная запись всегда использует `INSERT ... ON CONFLICT`.

---

### 3.3. Создать (основной / из Пайплайна 1)

```
POST /registry/documents
```

**Назначение:** создание карточки документа. Используется как при прямом вызове из UI/админки, так и со стороны этапа **«Registry»** Пайплайна 1 (Формирование документа).

> **Важно:** Registry использует `document_id` (bigint, sequence) как **единый первичный ключ**. `document_id` назначается Registry при создании карточки документа (после проверки уникальности): для дубликата извлекается существующий, для нового документа генерируется новый (sequence). Собственный numeric ID не создаётся — `document_id` проходит сквозь все сервисы без маппинга.

Registry принимает enriched JSON (схема `validated_v3`) напрямую от Converter-validator.
Формат — см. [`schema_converter_result.json`](../schema/schema_converter_result.json).

Ключевые элементы запроса:
- `document.metadata.*` — метаданные документа (doc_code, title, title_hash_sha256, era и др.)
- `document.content[]` — единый плоский массив секций с полем `type` (`text`, `table`, `image`, `formula`, `list`, `headerFooter`, `textBlock`)
- `document.terminology[]` — термины документа
- `document.references[]` — перекрёстные ссылки на другие нормативные документы

```json
{
  "document": {
    "source": { "file_name": "...", "file_hash_sha256": "...", "page_count": 2 },
    "metadata": {
      "doc_code": "ГОСТ 20868-81",
      "title": "СТОЙКИ УСТАНОВОЧНЫЕ...",
      "normalized_title": "стойки установочные...",
      "title_hash_sha256": "a1b2c3d4...",
      "title_key": "USSR|gost|47.020||20868-81|стойки установочные...",
      "era": "USSR",
      "validity_status": "active",
      "mks_oks_code": "31.240"
    },
    "content": [
      {
        "clause": "1",
        "title": null,
        "level": 1,
        "path": "1",
        "page": 1,
        "type": "text",
        "content": { "text": "Настоящий стандарт...", "amendments": [] }
      },
      {
        "clause": "6.1",
        "title": "Допуск соосности при степени точности",
        "level": 2,
        "path": "6.1.table1",
        "page": 2,
        "type": "table",
        "content": { "columns": [...], "rows": [...], "footnotes": [...], "amendments": [...], "image_key": "..." }
      }
    ],
    "terminology": [
      {
        "term": "стойка установочная крепежная",
        "definition": "Металлическая деталь для монтажа радиоэлектронной аппаратуры.",
        "source_clause": "1",
        "normalized_term": "стойка установочная крепежная"
      }
    ],
    "references": [
      {
        "target_doc_code": "ГОСТ 24705-81",
        "type": "single",
        "context": "резьбы",
        "current_status": "superseded",
        "replaced_by": "ГОСТ 24705-2004",
        "replacement_date": "2005-07-01"
      }
    ]
  }
}
```

> Registry сохраняет данные в БД, **сегментирует** документ на **секции** (`registry.document_sections`) и возвращает **плоский JSON** — список секций с проставленными `id`, без иерархии `subsections`. Этот плоский JSON передаётся в RAG Builder для чанкования.

Система **автоматически вычисляет** `title_hash_sha256` по формуле:  
`SHA-256(era | source_type | doc_code | normalized_title)`  
где `normalized_title` — `title` в нижнем регистре с удалёнными лишними пробелами

> **Полный формат данных:** см. [`docs/schema/schema_registry_for_rag.json`](../schema/schema_registry_for_rag.json) (схема `for_rag_v1`).
> Приведённый ниже пример — сокращённый. Все 7 типов секций и полный состав полей — в эталонном JSON.

**Ответ `201`:** Registry назначает DB-ID и возвращает компактный ответ с идентификаторами.

```json
{
  "document_id": 1,
  "version_id": 420001,
  "sections": [
    {
      "section_id": 1001,
      "type": "text",
      "clause": "1",
      "path": "1",
      "page": 1
    },
    {
      "section_id": 1002,
      "type": "textBlock",
      "clause": "1",
      "path": "1.note1",
      "page": 1
    },
    {
      "section_id": 1005,
      "type": "table",
      "clause": "6.1",
      "path": "6.1.table1",
      "page": 2
    },
    {
      "section_id": 1008,
      "type": "list",
      "clause": "6.2",
      "path": "6.2.list1",
      "page": 2
    },
    {
      "section_id": 1009,
      "type": "image",
      "clause": "6.1",
      "path": "6.1.fig1",
      "page": 2
    },
    {
      "section_id": 1011,
      "type": "formula",
      "clause": "6.1",
      "path": "6.1.formula1",
      "page": 1
    }
  ],
  "registry": {
    "document_id": 1,
    "version_id": 420001,
    "sections_count": 11,
    "references_count": 4,
    "created_at": "2026-05-17T09:15:00Z"
  }
}
```

> **Формат данных для RAG Builder:** Registry хранит секции в БД. Для индексации Orchestrator запрашивает `GET /registry/documents/{doc_id}/sections` и получает полный JSON с объектным `content` — см. [`schema_registry_for_rag.json`](../schema/schema_registry_for_rag.json). RAG Builder самостоятельно разбирает `content` по `type`.
> **Полный формат ответа `GET /registry/documents/{doc_id}/sections`** — см. [`schema_registry_for_rag.json`](../schema/schema_registry_for_rag.json).

**Особенности формата секций:**
- Секции — плоский массив (нет вложенных `subsections`)
- Иерархия задаётся через `parent_id` → `id`
- Каждая секция имеет `type`: `text`, `textBlock`, `headerFooter`, `table`, `list`, `image`, `formula`
- `image_key` для бинарных объектов (изображения таблиц, фигуры)
- Для `table`/`list`/`image`/`formula` доступен `content.markdown` — единое текстовое представление для RAG
- `bbox` присутствует только в validated_v3; в for_rag удалён (не нужен для индексации)

| Поле | Тип | Описание |
|---|---|---|
| `document.id` | bigint | PK документа |
| `document.doc_code` | string | Обозначение документа |
| `document.title` | string | Полное название |
| `document.normalized_title` | string | Нормализованное название |
| `document.mks_oks_code` | string | Код МКС/ОКС |
| `document.okstu_code` | string\|null | **D-51**: переименовано из `okstu`. Код ОКСТУ |
| `document.udk_code` | string\|null | **D-51**: переименовано из `udc` для консистентности с `*_code` |
| `document.era` | string | Эра документа |
| `document.validity_status` | string | Статус действия |
| `document.issuing_body` | string | Организация-издатель |
| `document.adoption_date` | string | Дата принятия |
| `document.effective_from` | string | Дата введения в действие |
| `document.replaces` | string\|null | Заменяемый документ |
| `document.page_count` | int | Количество страниц |
| `document.file_hash_sha256` | string | SHA-256 хеш файла |
| `sections[].section_id` | bigint | ID секции в `registry.document_sections` |
| `sections[].document_id` | bigint | ID документа |
| `sections[].parent_id` | bigint\|null | ID родительской секции (`null` для корневых) |
| `sections[].clause` | string | Номер пункта |
| `sections[].title` | string\|null | Заголовок секции |
| `sections[].level` | int | Уровень вложенности (1 — верхний) |
| `sections[].path` | string | ltree-путь для иерархии |
| `sections[].type` | string | Тип: `text`, `table`, `image`, `formula`, `list`, `headerFooter`, `textBlock` |
| `sections[].content` | JSONB | Содержимое секции (см. ниже) |
| `sections[].page` | int | Номер страницы |
| `sections[].bbox` | array | Координаты bbox `[x1,y1,x2,y2]` (0..1) |
| `terminology` | array | Массив терминов документа |
| `terminology[].term` | string | Термин |
| `terminology[].definition` | string | Определение термина |
| `terminology[].source_clause` | string | Пункт-источник |
| `terminology[].normalized_term` | string | Нормализованная форма термина |
| `registry` | object | Метаданные записи в БД |
| `registry.document_id` | bigint | ID документа |
| `registry.version_id` | bigint | ID версии |
| `registry.created_at` | datetime | Дата создания записи |
| `registry.sections_count` | int | Количество сохранённых секций |
| `registry.references_count` | int | Количество ссылок |

**Структура `sections[].content` по типам:**

Для `type: "text"`:
```json
{
  "text": "...",
  "amendments": []
}
```

Для `type: "table"`:
```json
{
  "columns": [
    { "name": "...", "header": "...", "index": 0, "type": "range|value", "value_type": "number|string", "unit": "..." }
  ],
  "rows": [
    {
      "row_index": 0, "type": "data|header",
      "cells": {
        "column_name": { "value": ..., "label": "...", "range": { "min": ..., "max": ..., "min_inclusive": true, "max_inclusive": true } }
      }
    }
  ],
  "footnotes": [
    { "text": "...", "applies_to": "whole_table|cell", "bbox": [0.095, 0.438, 0.952, 0.673] }
  ],
  "amendments": [
    { "amendment_id": "...", "type": "...", "source": "...", "affected_columns": [], "action": "...", "note": "..." }
  ],
  "image_key": "purgatory/assets/.../tables/t1.png"
}
```

Для `type: "image"`:
```json
{
  "caption": "...",
  "file_key": "purgatory/assets/.../fig1.png",
  "description": "..."
}
```

Для `type: "formula"`:
```json
{
  "latex": "...",
  "meaning": "...",
  "parameters": [
    { "symbol": "...", "description": "...", "unit": "..." }
  ]
}
```

**Ошибки**: `409` — `DUPLICATE_DOCUMENT`.

---



### 3.4. Обновить

```
PUT /registry/documents/{doc_id}
```

Полное обновление карточки документа. Тело запроса — enriched JSON (схема `validated_v3`), аналогично `POST /registry/documents`.
При изменении ключевых полей (`title`, `era`, `source_type`, `mks_oks_code`, `okstu_code`, `doc_code`) — `title_hash_sha256` и `title_key` пересчитываются автоматически.

**Ответ `200`:**
```json
{
  "data": {
    "id": 1,
    "title": "СТОЙКИ УСТАНОВОЧНЫЕ КРЕПЕЖНЫЕ. Технические требования (ред. 2)",
    "doc_code": "20868-81",
    "updated_at": "2026-06-12T14:00:00Z"
  }
}
```

---

### 3.5. Частичное обновление

```
PATCH /registry/documents/{doc_id}
```

**Тело** — любое подмножество полей карточки документа.

```json
{
  "metadata": { "tags": ["важное", "обновлено"] },
  "validity_status": "superseded",
  "status_note": "Заменён ГОСТ Р 20868-2025",
  "category_ids": [1, 3, 5],
  "valid_from": "1982-01-01",
  "valid_until": null
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `category_ids` | bigint[] | Массив ID категорий для назначения документу. Передаётся полный список — заменяет текущую привязку категорий |
| `valid_from` | date | **P12-5 (новое)**: дата начала действия. Редактируемое поле |
| `valid_until` | date | **P12-5 (новое)**: дата окончания действия. Редактируемое поле. Для бессрочных — в API передаётся `null`, в БД хранится `9999-12-31` (конвенция `dateMax`, см. `glossary.md`). При `null` от клиента backend подставляет `dateMax` |

**P12-5 (разделение editable/immutable — D14):**

| Категория | Поля |
|-----------|------|
| **editable** | `title`, `metadata`, `validity_status`, `status_note`, `category_ids`, `valid_from`, `valid_until`, `mks_oks_code`, `okstu_code`, `udk_code` |
| **immutable** | `id`, `doc_code`, `title_hash_sha256`, `title_key`, `file_hash_sha256`, `created_at`, `created_by`, `current_version_id` |
| **read-only** | `chunk_count`, `total_versions`, `subject_area` (вычисляется из `mks_oks_code` / `okstu_code` / `udk_code` через справочник) |

При попытке изменить immutable-поле возвращается `400 IMMUTABLE_FIELD` с указанием имени поля.

**Ответ `200`:**
```json
{
  "data": {
    "id": 1,
    "updated_at": "2026-06-12T14:30:00Z",
    "updated_fields": ["metadata", "validity_status", "status_note", "category_ids"]
  }
}
```

---

### 3.6. Обновить статус (internal)

```
PATCH /registry/documents/{doc_id}/status
```

> **Internal:** Вызывается только Оркестратором при завершении индексации (после Pipeline 2). Внешним клиентам недоступен — маршрут не проксируется через Gateway.

Оркестратор уведомляет Registry о финальном статусе документа после прохождения всех этапов обработки.

**Тело запроса:**

```json
{
  "status": "indexed",
  "comment": "Индексация завершена, документ готов к поиску",
  "changed_by": "orchestrator"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|---------------|----------|
| `status` | string | Да | FSM-статус документа (`created`, `pending_index`, `indexing`, `indexed`, `failed`) |
| `comment` | string | Нет | Причина смены статуса |
| `changed_by` | string | Нет | Субъект (пользователь или сервис). По умолчанию `orchestrator` |

**Ответ `200`:**

```json
{
  "data": {
    "id": 1,
    "status": "indexed",
    "previous_status": "indexing",
    "updated_at": "2026-06-05T14:00:00Z"
  }
}
```

---

### 3.7. Цепочка преемственности

```
GET /registry/documents/{doc_id}/succession
```

**Ответ `200`:**

```json
{
  "data": {
    "document_id": 1,
    "title": "ГОСТ 20868-81",
    "chain": [
      { "id": 2, "title": "ГОСТ 20868-75", "doc_code": "20868-75", "era": "USSR", "relation": "predecessor", "depth": -1 },
      { "id": 1, "title": "ГОСТ 20868-81", "doc_code": "20868-81", "era": "USSR", "relation": "self", "depth": 0 },
      { "id": 3, "title": "ГОСТ Р 20868-2025", "doc_code": "20868-2025", "era": "RF", "relation": "successor", "depth": 1 }
    ]
  }
}
```

---

### 3.10. Удалить

```
DELETE /registry/documents/{doc_id}
```

**Ответ `200`:**
```json
{
  "data": {
    "id": 1,
    "deleted_at": "2026-06-12T15:00:00Z",
    "message": "Документ мягко удалён. Запись сохранена в БД."
  }
}
```

**Ошибки**: `409` — есть связанные сущности (секции, версии), нельзя удалить.

---

### 3.11. Экспорт

```
GET /registry/documents/export
```

Фильтры те же, что в списке.

**Query-параметры:**
| Параметр | Тип | Описание |
|----------|-----|----------|
| `format` | string | `csv` (по умолчанию), `json` |
| `fields` | string | Список полей через запятую (по умолчанию все) |

**Ответ**: файл в указанном формате.

---

### 3.12. Массовый импорт

```
POST /registry/documents/import
```

**Запрос**: `multipart/form-data`
| Поле | Тип | Описание |
|------|-----|----------|
| `file` | File | CSV-файл с карточками документов |
| `mode` | string | `create` — только новые, `update` — обновить существующие, `upsert` — создать/обновить |

**Ответ `200`:**
```json
{
  "data": {
    "imported": 45,
    "updated": 3,
    "errors": [
      { "row": 12, "code": "DUPLICATE_TITLE_HASH", "message": "Документ с таким title_hash уже существует" }
    ]
  }
}
```

---

### 3.13. POST /registry/documents/{doc_id}/reprocess — переобработка документа

Асинхронная переобработка документа без создания нового черновика.
Перезапускает указанный этап обработки для существующего документа. Новый `draft_id` **не создаётся**.

**Запрос**:

```json
{
  "mode": "full",
  "options": { "ocr_engine": "paddleocr", "language": "ru", "pages": "1-5" }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `mode` | string | Режим переобработки: `full`, `ocr_only`, `chunking_only`, `validation_only`, `reindex` |
| `options` | object | Опциональные параметры обработки (см. таблицу ниже) |

**Поле `options`** (опционально):
| Поле | Тип | Описание | Допустимые значения |
|------|-----|----------|-------------------|
| `ocr_engine` | string | Движок OCR | `paddleocr`, `tesseract` |
| `parser_engine` | string | Движок парсинга | `docling` |
| `language` | string | Язык OCR | `rus` (по умолчанию), `eng` |
| `pages` | string | Диапазон страниц | `"1-5"`, `"1,3,5"`, `"all"` (по умолчанию) |

**Ответ `202`**:
```json
{
  "task_id": 420002,
  "document_id": 1,
  "mode": "full",
  "status": "processing",
  "message": "Переобработка запущена. Новый черновик не создаётся — используется существующий документ."
}
```

**Особенности переиндексации (`mode: reindex`):**
Registry регистрирует задачу на переобработку. Orchestrator, получив уведомление, вызывает `DELETE /rag/build/{doc_id}` для очистки существующих чанков документа из векторного индекса. Только после успешного удаления запускается новый `POST /rag/build`. Если `DELETE` вернул ошибку, переиндексация отменяется с кодом `CLEANUP_FAILED`.

**Ошибки**: `404` — документ не найден, `409` — документ в обработке.

---

## Группа drafts

Данные черновиков хранятся в `registry.drafts`. Управление жизненным циклом — через Orchestrator.

**Доступ:** GET-эндпоинты (чтение) — доступны через Gateway для просмотра. PATCH/DELETE — internal, доступны только Orchestrator.

| Метод | Путь | Описание | Доступ |
|-------|------|----------|--------|
| GET  | `/registry/drafts` | Список черновиков | public |
| GET  | `/registry/drafts/{draft_id}` | Полная информация о черновике | public |
| GET  | `/registry/drafts/{draft_id}/preview` | Preview-метаданные | public |
| POST | `/registry/drafts` | Создать запись черновика | **internal** |
| PATCH| `/registry/drafts/{draft_id}/status` | Обновить статус (FSM) | **internal** |
| PATCH| `/registry/drafts/{draft_id}/metadata` | Обновить метаданные черновика | **internal** |
| DELETE| `/registry/drafts/{draft_id}` | Удалить запись черновика | **internal** |

> **public** — Gateway проксирует запрос напрямую в Registry.
> **internal** — недоступен через Gateway, вызывается только Orchestratorом.
> Registry не имеет публичных write-эндпоинтов для черновиков. Создание и смена статуса — только через Orchestrator.

**Канонический список статусов черновика** (владелец — Registry, все остальные сервисы синхронизируются с этим списком):

| Статус | Описание |
|--------|----------|
| `uploaded` | Файл загружен, черновик создан |
| `previewing` | Выполняется preview-фаза |
| `ready_for_approve` | Preview завершён, ожидание решения |
| `review_required` | Preview показал низкое качество, требуется ручная проверка |
| `validation` | Оператор подтвердил, выполняется повторная валидация |
| `approved` | Черновик утверждён, документ создаётся в Registry |
| `discarded` | Черновик отклонён |

### 4.1. POST /registry/drafts — Создать запись черновика

Создаёт запись черновика в `registry.drafts`.  
Вызывается Orchestrator после `POST /drafts`.

**Запрос**: `application/json`

```json
{
  "file_key": "f-abc123",
  "document_key": "sha256:def456",
  "status": "uploaded",
  "raw_data": { ... },
  "created_by": "orchestrator"
}
```

**Ответ `201`**:

```json
{
  "data": {
    "id": 1,
    "file_key": "f-abc123",
    "document_key": "sha256:def456",
    "status": "uploaded",
    "created_at": "2026-06-05T10:00:00Z"
  }
}
```

---

### 4.2. GET /registry/drafts — Список черновиков

**Query-параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `draft_id` | bigint | Нет | Фильтр по ID черновика |
| `document_key` | string | Нет | Фильтр по бизнес-ключу документа |
| `status` | string | Нет | Фильтр по статусу |

**Ответ `200`**:

```json
{
  "data": [
    {
      "id": 1,
      "file_key": "f-abc123",
      "document_key": "sha256:def456",
      "status": "approved",
      "confidence": 0.92,
      "preview_metadata": { /* см. [_schemas.md](_schemas.md#PreviewMetadata) */ },
      "created_by": "orchestrator",
      "created_at": "2026-06-18T10:00:00Z"
    }
  ],
  "meta": { "total": 1, "page": 1, "page_size": 50 }
}
```

> Схема полей `preview_metadata` — [_schemas.md](_schemas.md#PreviewMetadata).

> **Примечание:** Registry internal API возвращает базовый набор полей черновика. Публичный API (через Orchestrator) расширяет этот ответ полями: `task_id`, `has_notifications`, `critical_count`, `error_code`, `error_message`, `updated_at`. Orchestrator получает эти данные из `pipeline.tasks` и `pipeline.draft_notifications`, а не из Registry.
> 
> Поле `id` в Registry internal API маппится в `draft_id` в публичном API.

---

### 4.3. GET /registry/drafts/{draft_id} — Полная информация

**Ответ `200`**:

```json
{
  "data": {
    "id": 1,
    "file_key": "f-abc123",
    "document_key": "sha256:def456",
    "status": "ready_for_approve",
    "confidence": 0.92,
    "preview_metadata": { /* см. [_schemas.md](_schemas.md#PreviewMetadata) */ },
    "raw_data": {
      "schema": "raw_ocr_v4",
      "pages": []
    },
    "error_code": null,
    "error_message": null,
    "created_by": "orchestrator",
    "updated_by": null,
    "created_at": "2026-06-18T10:00:00Z",
    "updated_at": "2026-06-18T10:02:00Z"
  }
}
```

> Схема полей `preview_metadata` — [_schemas.md](_schemas.md#PreviewMetadata).

---

### 4.4. GET /registry/drafts/{draft_id}/preview — Preview-метаданные

**Ответ `200`**:

```json
{
  "data": {
    "id": 1,
    "file_key": "f-abc123",
    "status": "ready_for_approve",
    "confidence": 0.92,
    "preview_metadata": { /* см. [_schemas.md](_schemas.md#PreviewMetadata) */ },
    "created_at": "2026-06-18T10:00:00Z"
  }
}
```

> Схема полей `preview_metadata` — [_schemas.md](_schemas.md#PreviewMetadata).

---

### 4.5. PATCH /registry/drafts/{draft_id}/status — Обновить статус

Обновляет статус черновика. Вызывается Orchestrator при изменении жизненного цикла.

**Запрос**:

```json
{
  "status": "ready_for_approve",
  "confidence": 0.92,
  "preview_metadata": { /* см. _schemas.md#PreviewMetadata */ },
  "error_code": null,
  "error_message": null,
  "updated_by": "orchestrator"
}
```

**Ответ `200`**:

```json
{
  "data": {
    "id": 1,
    "status": "ready_for_approve",
    "previous_status": "previewing",
    "updated_at": "2026-06-05T10:03:00Z"
  }
}
```

> **Примечание:** Для статуса `discarded` можно передать `error_code` и `error_message`.  
> Для статусов `approved` и `discarded` дополнительно обновляется `updated_by`.
> 
> Поля `decided_by` и `decided_at` Registry **не хранит и не возвращает**. Они проставляются Orchestrator в `registry.document_history` (event_type = `decided`) при вызове `PATCH /drafts/{draft_id}/decide`.

---

### 4.6. PATCH /registry/drafts/{draft_id}/metadata — Обновить метаданные черновика (internal)

Вызывается Orchestrator при `PATCH /drafts/{draft_id}/metadata`. Сохраняет ручные правки метаданных в `registry.drafts.preview_metadata`, включая пересчитанный `title_hash_sha256` и `title_key`.

**Запрос:**

```json
{
  "preview_metadata": {
    "doc_code": "311-05-1950ц-ИЗМ1",
    "title": "ЦИРКУЛЯРНОЕ ПИСЬМО № 311-05-1950ц (изм.1)",
    "title_hash_sha256": "<новый-хеш>",
    "title_key": "<новая-строка>",
    ...
  },
  "metadata_overrides": {
    "valid_from": "2026-01-01",
    "valid_until": null
  },
  "updated_by": "orchestrator"
}
```

**Поля запроса:**

| Поле | Тип | Описание |
|------|-----|----------|
| `preview_metadata` | object | Полный объект preview_metadata с обновлёнными полями и пересчитанными `title_hash_sha256`/`title_key` |
| `metadata_overrides` | object | Опционально. Временные overrides оператора: `valid_from`, `valid_until` и др. Хранятся до approve |
| `updated_by` | string | Кто обновил |

**Ответ `200`:**

```json
{
  "data": {
    "id": 1,
    "status": "ready_for_approve",
    "preview_metadata": { ... },
    "updated_at": "2026-06-05T10:03:00Z"
  }
}
```

---

### 4.7. DELETE /registry/drafts/{draft_id} — Удалить запись

Каскадное удаление записи черновика из `registry.drafts`.  
Вызывается Orchestrator при `DELETE /drafts/{draft_id}`.

**Ответ `200`**:

```json
{
  "data": {
    "id": 1,
    "deleted_at": "2026-06-05T12:00:00Z"
  }
}
```

**Коды ошибок:**
| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 404 | `DRAFT_NOT_FOUND` | Черновик не найден |
| 409 | `DRAFT_ALREADY_DECIDED` | Черновик уже в финальном статусе (`approved`/`discarded`) |

---

## Группа common

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/registry/stats` | Статистика |
| GET | `/registry/enums` | Допустимые значения |

### 6.1. Статистика

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
      "created": 10,
      "pending_index": 3,
      "indexing": 2,
      "indexed": 32,
      "failed": 1
    },
    "documents_by_source_type": {
      "GOST": 20,
      "GOST_R": 12,
      "OST": 5,
      "TU": 8,
      "ISO": 3,
      "DNV": 6,
      "ASTM": 2,
      "RMRS": 4
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

### 6.2. Допустимые значения

```
GET /registry/enums
```

**Ответ `200`:**

```json
{
  "data": {
    "classifier_system": ["MKS", "OKSTU", "UDC", "EXTERNAL"],
    "classifier_status": ["active", "deprecated", "archived"],
    "source_type": ["GOST", "GOST_R", "OST", "RD", "TU", "ISO", "DNV", "ASTM", "RMRS", "OTHER"],
    "document_type": ["normative", "technical", "drawing", "specification", "archival_scan"],
    "document_status": ["created", "pending_index", "indexing", "indexed", "failed"],
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

## Группа categories

> Управление пользовательскими категориями документов (many-to-many).

### 7.1. Список категорий

```
GET /registry/categories
```

**Ответ `200`:**

```json
{
  "data": [
    {
      "id": 1,
      "name": "Корпусные конструкции",
      "description": "Документы по корпусу, набору, обшивке, палубам",
      "color": "#4CAF50",
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-06-10T14:00:00Z"
    }
  ],
  "meta": { "total": 5, "page": 1, "page_size": 50 }
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | ID категории |
| `name` | string | Название категории |
| `description` | string | Описание (необязательное) |
| `color` | string | Цвет в hex (#RRGGBB) для отображения в UI |
| `created_at` | datetime | Дата создания |
| `updated_at` | datetime | Дата обновления |

---

### 7.2. Одна категория

```
GET /registry/categories/{category_id}
```

**Ответ `200`:**

```json
{
  "data": {
    "id": 1,
    "name": "Корпусные конструкции",
    "description": "Документы по корпусу, набору, обшивке, палубам",
    "color": "#4CAF50",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-06-10T14:00:00Z"
  }
}
```

---

### 7.3. Создать категорию

```
POST /registry/categories
```

**Тело запроса:**

```json
{
  "name": "Корпусные конструкции",
  "description": "Документы по корпусу, набору, обшивке, палубам",
  "color": "#4CAF50"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|---------------|----------|
| `name` | string | Да | Название категории (уникальное) |
| `description` | string | Нет | Описание категории |
| `color` | string | Нет | Цвет в hex (#RRGGBB) |

**Ответ `201`:**

```json
{
  "data": {
    "id": 6,
    "name": "Корпусные конструкции",
    "description": "Документы по корпусу, набору, обшивке, палубам",
    "color": "#4CAF50",
    "created_at": "2026-06-12T14:00:00Z",
    "updated_at": "2026-06-12T14:00:00Z"
  }
}
```

---

### 7.4. Обновить категорию

```
PUT /registry/categories/{category_id}
```

**Тело запроса:**

```json
{
  "name": "Корпусные конструкции и набор",
  "description": "Обновлённое описание",
  "color": "#2196F3"
}
```

| Поле | Тип | Обязательность | Описание |
|------|-----|---------------|----------|
| `name` | string | Нет | Название категории |
| `description` | string | Нет | Описание категории |
| `color` | string | Нет | Цвет в hex (#RRGGBB) |

**Ответ `200`:**

```json
{
  "data": {
    "id": 1,
    "name": "Корпусные конструкции и набор",
    "description": "Обновлённое описание",
    "color": "#2196F3",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-06-12T15:00:00Z"
  }
}
```

---

### 7.5. Удалить категорию

```
DELETE /registry/categories/{category_id}
```

**Ответ `200`:**

```json
{
  "data": {
    "id": 1,
    "deleted_at": "2026-06-12T15:30:00Z",
    "message": "Категория удалена"
  }
}
```

**Возможные ошибки:**

| HTTP | `error.code` | Описание |
|------|-------------|----------|
| 404 | `CATEGORY_NOT_FOUND` | Категория не найдена |
| 409 | `CATEGORY_HAS_DOCUMENTS` | Категория привязана к документам, удалите связи или переназначьте документы |

---

### 7.6. Ошибки групп categories (справочно)

| HTTP | `error.code` | Когда возникает |
|------|-------------|----------------|
| 404 | `CATEGORY_NOT_FOUND` | GET/PUT/DELETE по несуществующему ID |
| 409 | `DUPLICATE_CATEGORY_NAME` | POST/PUT с именем, которое уже существует |
| 409 | `CATEGORY_HAS_DOCUMENTS` | DELETE категории, к которой привязаны документы |

---

## Модели данных

### 5.1. classifier_node

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `classifier_system` | classifier_system_enum | PK (составной), ENUM: `MKS`, `OKSTU`, `UDC`, `EXTERNAL` |
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
| `id` | bigint | PK |
| `system` | varchar(20) | NOT NULL |
| `code` | text | NOT NULL |
| `found_in_document_id` | bigint | FK → documents, nullable |
| `status` | varchar(20) | `new`, `mapped`, `rejected` |
| `admin_comment` | text | nullable |
| `created_at` | timestamptz | NOT NULL |
| UNIQUE | | (`system`, `code`) |

### 5.3. terminology_entry

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | bigint | PK |
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
| `id` | bigint | PK |
| `draft_id` | bigint | FK → `registry.drafts`, nullable — исходный черновик |
| `doc_code` | text | nullable |
| `title` | text | NOT NULL |
| `title_hash_sha256` | text | UNIQUE — бизнес-ключ |
| `title_key` | text | Исходная строка конкатенации для бизнес-ключа (аудит/отладка) |
| `file_hash_sha256` | text | **P2-2**: хеш бинарного файла (CAS-дедупликация) |
| `file_size_bytes` | bigint | CHECK > 0 |
| `source_type` | varchar(20) | nullable — `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `document_type` | varchar(30) | nullable — `normative`, `technical`, `drawing`, `specification`, `archival_scan` |
| `status` | varchar(30) | NOT NULL — `created`, `pending_index`, `indexing`, `indexed`, `failed` |
| `processing_status` | varchar(20) | nullable — FSM: `created`, `pending_index`, `indexing`, `indexed`, `partially_indexed`, `failed` |
| `chunk_count` | int | nullable, CHECK ≥ 0 — количество чанков после индексации |
| `preview_snapshot` | jsonb | nullable — копия `preview_metadata` из черновика при approve |
| `era` | varchar(10) | nullable — `USSR`, `CIS`, `RF`, `CURRENT` |
| `validity_status` | varchar(20) | nullable — `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `valid_from` | date | NOT NULL DEFAULT `'1000-01-01'` — дата начала действия |
| `valid_until` | date | NOT NULL DEFAULT `'9999-12-31'` — дата окончания действия, CHECK ≥ valid_from |
| `deleted_at` | timestamptz | nullable — soft-delete |
| `jurisdiction` | varchar(10) | nullable — `RU`, `EU`, `US`, `NO`, `INTL` |
| `issuing_body` | text | nullable |
| `adoption_date` | date | nullable — дата принятия из документа |
| `effective_from` | date | nullable — дата введения в действие из документа |
| `replaces` | text | nullable — код заменяемого документа |
| `status_note` | text | nullable — примечание к статусу |
| `enterprise_id` | bigint | nullable |
| `mks_oks_code` | text | FK → classifier_registry (MKS) |
| `okstu_code` | text | FK → classifier_registry (OKSTU) |
| `udk_code` | text | nullable — код УДК |
| `classification_status` | jsonb | DEFAULT `'{}'` — см. спецификацию ниже |
| `successor_doc_id` | bigint | FK → self, nullable |
| `predecessor_doc_id` | bigint | FK → self, nullable |
| `current_version_id` | bigint | FK → `registry.document_versions`, nullable |
| `metadata` | jsonb | DEFAULT `{}` |
| `created_at` | timestamptz | NOT NULL |
| `created_by` | text | nullable |
| `updated_at` | timestamptz | NOT NULL |
| `updated_by` | text | nullable |

> Удалены поля `classifier_code` и `industry_code` (старая модель, не использовались в API).
> `group` удалён — классификация по предметным областям ПКБ выполняется через `categories` (M:N).
> Сгенерированные колонки `mks_system` и `okstu_system` (GENERATED ALWAYS AS 'MKS'/'OKSTU') обеспечивают строгую FK-проверку к системе классификации.

**Спецификация `classification_status` (JSONB):**

Поле содержит статусы извлечения кодов классификации и метаданные парсинга:

```json
{
  "mks_status": "CONFIRMED",
  "okstu_status": "NOT_USED",
  "udk_code": "629.5.021",
  "extracted_at": "2026-06-13T10:00:00Z",
  "extracted_by": "converter_validator_v3",
  "confidence": 0.89
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `mks_status` | string | Статус кода МКС/ОКС. Один из: `CONFIRMED`, `PENDING_REVIEW`, `NOT_FOUND`, `NOT_USED`, `UNASSIGNED` |
| `okstu_status` | string | Статус кода ОКСТУ. Аналогичные значения |
| `udk_code` | string or null | Извлечённый код УДК (если найден) |
| `extracted_at` | timestamp or null | Время извлечения кодов |
| `extracted_by` | string | Идентификатор парсера |
| `confidence` | float (0..1) | Уверенность в извлечении кодов |

**Значения статусов:**

| Статус | Отображение | Значение |
|--------|-------------|----------|
| `CONFIRMED` | ✅ | Код найден в справочнике и верифицирован |
| `PENDING_REVIEW` | \<PENDING\> | Извлечён автоматически, требует подтверждения |
| `NOT_FOUND` | \<NOT_FOUND\> | Парсер не обнаружил код на первых страницах |
| `NOT_USED` | \<NOT_USED\> | Не применяется для данной эры/типа документа |
| `UNASSIGNED` | \<FREE\> | Классификация не назначалась |

> **Важно**: поля `mks_oks_code` и `okstu_code` содержат только реальные коды или NULL (для целостности FK). Статусы `PENDING_REVIEW`, `NOT_FOUND`, `NOT_USED` хранятся только в `classification_status`, а не в самих кодовых полях.

### 5.5. format_registry

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | bigint | PK |
| `format_code` | text | UNIQUE, NOT NULL — `pdf`, `png`, `jpg`, `tiff`, `docx` |
| `mime_type` | text | NOT NULL — `application/pdf`, `image/png` и т.д. |
| `parser_engine` | text | NOT NULL — `docling`, `tesseract`, `easyocr` |
| `supported` | boolean | DEFAULT true |
| `created_at` | timestamptz | NOT NULL |

> **Примечание:** `file_hash_sha256` в `registry.document_versions` должен иметь UNIQUE-ограничение для обеспечения CAS-дедупликации файлов. Один хэш = одна версия файла в системе. Попытка загрузить файл с существующим хэшом вызывает `unique_violation` и должна обрабатываться как дубликат файла.

---

### 5.6. category

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | bigint | PK, sequence |
| `name` | varchar(255) | NOT NULL, UNIQUE |
| `description` | text | nullable |
| `color` | varchar(7) | nullable, hex-код (#RRGGBB) |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

### 5.7. document_category

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `document_id` | bigint | PK (составной), FK → `registry.documents.id` ON DELETE CASCADE |
| `category_id` | bigint | PK (составной), FK → `registry.categories.id` ON DELETE CASCADE |

### 5.8. document_reference

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `id` | bigint | PK |
| `source_document_id` | bigint | FK → `registry.documents.id`, NOT NULL |
| `target_doc_code` | text | NOT NULL — обозначение документа из текста (напр. «ГОСТ 24705-81») |
| `reference_type` | varchar(20) | NOT NULL — `single`, `range` |
| `context` | text | nullable — контекст ссылки |
| `current_status` | varchar(20) | nullable — `active`, `superseded` |
| `replaced_by` | text | nullable |
| `replacement_date` | date | nullable |
| `is_resolved` | boolean | DEFAULT false — связь проведена к `registry.documents` |
| `resolved_document_id` | bigint | FK → `registry.documents.id`, nullable — целевой документ в реестре |
| `created_at` | timestamptz | NOT NULL |
| `updated_at` | timestamptz | NOT NULL |

---

## Фоновые задачи

### Резолвер графа связей (background task within registry-service)

**Назначение:** сопоставить `target_doc_code` из `document_references` с `registry.documents.doc_code` и проставить `resolved_document_id`.

**Проблема:** при создании документа все его перекрёстные ссылки сохраняются с `is_resolved = FALSE`, так как целевой документ может ещё не существовать в системе.

**Триггеры запуска:**
- **По событию:** после создания документа в `registry.documents` Registry запускает резолвер для всех `is_resolved = FALSE`, где `target_doc_code` совпадает с `doc_code` нового документа.
- **Фоново:** CRON-задача (период настраиваемый, рекомендуемый — 1 час) для обработки оставшихся неразрешённых ссылок.

**SQL:**
```sql
UPDATE registry.document_references AS ref
SET is_resolved = TRUE,
    resolved_document_id = d.id,
    updated_at = NOW()
FROM registry.documents AS d
WHERE d.doc_code = ref.target_doc_code
  AND ref.is_resolved = FALSE;
```

**Индекс для производительности:**
```sql
CREATE INDEX idx_refs_unresolved
ON registry.document_references(target_doc_code)
WHERE is_resolved = FALSE;
```

**Важно:** корректная работа резолвера требует единого нормализатора `doc_code` как в Converter-validator (при извлечении ссылки из текста), так и в Registry (при сохранении карточки документа). Иначе «ГОСТ 24705-81» и «ГОСТ 24705-81» с разным количеством пробелов не совпадут.

---

## Примечания

1. **DB shared:** Все таблицы registry находятся в общей БД. Другие сервисы читают их напрямую.
2. **title_hash_sha256** вычисляется автоматически, гарантирует дедупликацию. Формула: `SHA-256(era | source_type | mks_oks_code | okstu_code | doc_code | normalized_title)`, где `normalized_title` — `title` в нижнем регистре с удалёнными лишними пробелами. **title_key** — исходная строка конкатенации тех же полей, сохраняется для аудита и отладки. Коды классификации (mks_oks_code, okstu_code) включены в формулу для разграничения документов с одинаковым номером, но разной тематической привязкой. Детальный алгоритм нормализации — в `specifications/normalizer_specification.md`.
3. **Параллельная классификация:** Документ может одновременно ссылаться на МКС/ОКС и ОКСТУ через разные FK.
4. **Журнал статусов:** Все изменения `documents.status` логируются в `status_history` на уровне сервиса (Registry).
5. **Неизвестные коды классификатора:** Коды, не найденные в справочнике, попадают в `classifier_pending`. Администратор разбирает их через UI.