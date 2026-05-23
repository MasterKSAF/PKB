# Сравнение структур данных: `docs/` vs Purgatory (полное)

> Сводное сравнение двух технических проектов ПКБ «Петробалт» (Purgatory v2.3 — слой staging + Knowledge Base — слой `nsi`) с документацией `docs/`.
> Без учёта архитектурных подходов — только таблицы, поля, типы, эндпоинты и их сигнатуры.
>
> **Важно:** сравнение `docs/` выполнено по фактически принятой ER-диаграмме БД.

---

## 0. Общая архитектура: две схемы Purgatory

```
Purgatory (полный проект) = purgatory.* (staging) + nsi.* (knowledge base)
```

| Слой | Схема | Назначение | Описан в |
|---|---|---|---|
| Staging | `purgatory.*` | Приём, дедупликация, OCR + Parser, Converter-validator, FSM | Purgatory v2.3 |
| Knowledge Base | `nsi.*` | Поисковые индексы, граф связей, контент для RAG Builder + RAG Search | KB MVP v1.1 |

Оба слоя — части единого проекта. `docs/` описывает аналогичную функциональность, но с другой декомпозицией сервисов.

---

## 1. Сводная карта соответствия таблиц (все схемы)

| Purgatory — схема | `docs/` — таблица | Соответствие |
|---|---|---|
| **purgatory.documents** | `purgatory_documents` | 🟢 Почти полное |
| **purgatory.document_versions** | (в составе Orchestrator API) | 🟡 Частичное |
| **purgatory.chunk_containers** | (концепция container_id в API) | 🟡 Иная модель |
| **purgatory.status_history** | (в составе Orchestrator API) | 🟢 Почти идентично |
| **purgatory.classifier_registry** | (Registry API / справочник) | 🟢 Почти идентично |
| **purgatory.classifier_pending** | (Registry API / pending) | 🟡 Частичное |
| **purgatory.terminology_registry** | (Registry API / terminology) | 🟢 Идентично |
| **purgatory.format_registry** | ❌ Нет аналога | 🔴 Отсутствует |
| **nsi.document_sections** | `registry.document_sections` | 🟢 Почти полное |
| **nsi.chunks** | `rag.chunks` | 🟢 Почти полное |
| **nsi.images** | 🔹 `registry.document_sections (type='image')` | 🟡 Иная модель |
| **nsi.extracted_tables** | 🔹 `registry.document_sections (type='table')` | 🟡 Иная модель |
| **nsi.formulas** | ❌ Нет аналога | 🔴 Отсутствует |
| **nsi.formula_parameters** | ❌ Нет аналога | 🔴 Отсутствует |
| **nsi.cross_references** | `registry.document_references` | 🟢 Почти полное |
| **nsi.promotion_history** | `registry.document_history` | 🟡 Частичное |
| Нет отдельной таблицы док-в | (нет — только purgatory_documents) | 🟢 Согласовано |
| ❌ Нет аналога | Чат/сессии (Query Service) | 🆕 Выходит за рамки Purgatory |
| ❌ Нет аналога | Auth / Users / Roles | 🆕 Выходит за рамки Purgatory |

> 🔹 — в `docs/` изображения и таблицы хранятся как секции документа с типом `'image'` / `'table'`, а не отдельными таблицами.

---

# Часть A. Слой staging: схема `purgatory.*`

---

## A1. Таблица `documents`

### A1.1. Совпадающие поля

| Поле | Purgatory | `docs/` | Тип |
|---|---|---|---|
| `id` / `document_id` | `UUID PK` | `uuid id PK` | UUID |
| `title` | `TEXT NOT NULL` | `text title` | TEXT |
| `doc_code` | `TEXT` | `text doc_code` | TEXT |
| `validity_status` | `ENUM` | `text validity_status` | ENUM ✅ |

> В ERD `docs/` показаны только ключевые поля `purgatory_documents`. Полный набор полей (status, era, jurisdiction, issuing_body, mks_oks_code, okstu_code, title_hash_sha256 и т.д.) присутствует в API-спецификации Orchestrator/Registry. См. детальное сравнение в differents.md.

---

## A2. Таблица `document_versions`

### A2.1. Совпадающие поля

| Поле | Purgatory | `docs/` | Комментарий |
|---|---|---|---|
| `id` | `UUID PK` | `version_id UUID` | Переименовано |
| `document_id` | `UUID FK` | (через endpoint) | Неявно |
| `source_filename` | `TEXT NOT NULL` | `TEXT` | ✅ добавлено в `docs/` |
| `content_hash_sha256` | `TEXT UNIQUE` | `TEXT` | ✅ |
| `size_bytes` | `BIGINT` | `INTEGER` | BIGINT ✅ |
| `uploaded_at` | `TIMESTAMP` | `TIMESTAMP` | ✅ |
| `uploaded_by` | `TEXT` | `TEXT` | ✅ |

### A2.2. Различающиеся поля

| Поле (Purgatory) | `docs/` аналог | Разница |
|---|---|---|
| `format_code TEXT FK→format_registry` | `format_code TEXT` | FK-ограничение есть только в Purgatory |
| `file_path TEXT NOT NULL` (CAS) | `file_key TEXT` | Purgatory: `{doc_id}/v{n}/{hash}.ext`; `docs/`: `file_key` (не CAS) |


### A2.3. CAS-путь

**Purgatory:** `file_path = '{doc_id}/v{n}/{content_hash_sha256}.{ext}'` — строгий CAS по content_hash.

**`docs/`:** `file_key` — точный формат не специфицирован.

---

## A3. Таблица `chunk_containers`

### A3.1. Purgatory: единый JSONB

| Поле | Тип | Назначение |
|---|---|---|
| `id` | UUID PK | |
| `document_id` | UUID FK UNIQUE | 1 документ → 1 контейнер |
| `version_hash` | TEXT | SHA-256 самого JSON |
| `json_payload` | JSONB | Полный манифест: чанки, эмбеддинги, bounding boxes |
| `validation_status` | ENUM (pending/valid/invalid) | |
| `validation_errors` | JSONB | |
| `created_at` | TIMESTAMP | |

### A3.2. `docs/`: поштучное хранение

В `docs/` чанки — построчные записи (`rag.chunks`). Ответ API содержит:

| Поле | Описание |
|---|---|
| `container_id` | UUID — возможный аналог chunk_containers.id |
| `validation_status` | статус |
| `chunks[]` | массив чанков |
| ∟ `section_id`, `chunk_index`, `clause`, `content`, `page` | данные чанка |
| ∟ `strategy`, `has_embedding`, `bbox`, `table_data` | метаданные |

**Ключевое:** Purgatory → один JSONB на документ; `docs/` → N строк в таблице.

---

## A4. Таблица `status_history`

Практически идентичны.

| Поле (Purgatory) | `docs/` (history) | Совпадение |
|---|---|---|
| `id` | `history_id` | ✅ переименовано |
| `document_id` | (через endpoint path) | ✅ неявно |
| `old_status` | `old_status` | ✅ |
| `new_status` | `new_status` | ✅ |
| `comment JSONB {reason, details}` | `comment JSONB {reason, details}` | ✅ `details` добавлен в `docs/` |
| `changed_by TEXT` | `changed_by TEXT` | ✅ |
| `changed_at TIMESTAMP` | `changed_at TIMESTAMP` | ✅ |

---

## A5. Таблица `classifier_registry`

### A5.1. Поля

| Поле | Purgatory | `docs/` (Registry API) | Тип |
|---|---|---|---|
| `classifier_system` | `ENUM (MKS/OKSTU/UDC/EXTERNAL)` | `TEXT` | ENUM ✅ |
| `code` | `TEXT PK` (composite) | `TEXT PK` (composite) | ✅ |
| `parent_code` | `TEXT FK→self` | `TEXT FK→self` | ✅ |
| `full_name` | `TEXT NOT NULL` | `TEXT NOT NULL` | ✅ |
| `status` | `TEXT DEFAULT 'active'` | `TEXT` | ✅ |
| `effective_date` | `DATE` | `DATE` | ✅ |
| `replaced_by` | `TEXT` | `TEXT` | ✅ |
| `created_at` | `TIMESTAMP DEFAULT NOW()` | `TIMESTAMP` | ✅ |

### A5.2. Ключевое различие: FK constraint на parent_code

**Purgatory (v2.3):**
```sql
FOREIGN KEY (classifier_system, parent_code) 
  REFERENCES purgatory.classifier_registry(classifier_system, code)
```
Гарантирует, что дочерний узел МКС ссылается на родителя из той же системы. Деревья изолированы.

**`docs/`:** FK-ограничение не специфицировано. Возможно смешение систем.

---

## A6. Таблица `classifier_pending`

| Поле (Purgatory) | `docs/` (Registry API) | Разница |
|---|---|---|
| `id UUID PK` | `id UUID PK` | ✅ |
| `system TEXT` | `system TEXT` | ✅ |
| `code TEXT` | `code TEXT` | ✅ |
| `source_document_id UUID FK→documents` | `source_document_id UUID` | ✅ переименовано в `docs/` |
| `source_version_id UUID FK→document_versions` | `source_version_id UUID` | ✅ добавлено в `docs/` |
| `status TEXT ('new'/'mapped'/'rejected')` | `status TEXT ('new'/'mapped'/'rejected')` | ✅ специфицированы статусы |
| `admin_comment TEXT` | `admin_comment TEXT` | ✅ |
| `created_at TIMESTAMP` | `created_at TIMESTAMP` | ✅ |

---

## A7. Таблица `format_registry`

**Purgatory:**
```sql
CREATE TABLE purgatory.format_registry (
  code TEXT PRIMARY KEY,
  mime_type TEXT NOT NULL,
  parser_plugin TEXT NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**В `docs/`:** ➕ Добавлен. Реестр форматов с MIME-типами, парсерами и `created_at`.

---

## A8. Таблица `terminology_registry`

Поля **полностью идентичны** (12 из 12):

| Поле | Purgatory | `docs/` (Registry API) |
|---|---|---|
| `id` | UUID PK | UUID PK |
| `raw_term` | TEXT UNIQUE | TEXT UNIQUE |
| `standard_term` | TEXT | TEXT |
| `normalized_value` | TEXT | TEXT |
| `term_type` | TEXT | TEXT |
| `is_case_sensitive` | BOOLEAN | BOOLEAN |
| `definition` | TEXT | TEXT |
| `synonyms` | JSONB | JSONB |
| `related_docs` | JSONB | JSONB |
| `scope` | JSONB | JSONB |
| `is_blocked` | BOOLEAN | BOOLEAN |
| `created_at` | TIMESTAMP | TIMESTAMP |
| `updated_at` | TIMESTAMP | TIMESTAMP |

**Вывод:** таблица `terminology_registry` полностью согласована между Purgatory и `docs/`.

---

# Часть B. Слой Knowledge Base: схема `nsi.*`

---

## B1. Таблица `document_sections`

### B1.1. Поля

| Поле | Purgatory (`nsi.document_sections`) | `docs/` (`registry.document_sections`) | Совпадение |
|---|---|---|---|
| `id` | `UUID PK` | `uuid id PK` | ✅ |
| `document_id` | `UUID FK → purgatory.documents.id` | `uuid document_id FK → purgatory_documents` | ✅ |
| `parent_id` | `UUID FK → self` | `uuid parent_id FK → self` | ✅ |
| `clause` | `TEXT NOT NULL` | `text clause` | ✅ |
| `title` | `TEXT` | `text title` | ✅ |
| `level` | `INT NOT NULL DEFAULT 1` | `int level` | ✅ |
| `path` | `LTREE NOT NULL` | `ltree path` | ✅ |
| `page` | `INT` | `int page` | ✅ |
| `bbox` | `JSONB` | `jsonb bbox` | ✅ |
| `type` | ❌ (типы в отдельных таблицах) | `text type` ('section', 'table', 'image', 'formula') | 🔴 Purgatory: типы разнесены |
| `content` | ❌ (контент в `nsi.chunks`) | `jsonb content` | 🔴 Purgatory: контент в чанках |
| `created_at` | `TIMESTAMPTZ` | `TIMESTAMPTZ` | ✅ добавлен в `docs/` |
| `valid_ltree_path` CHECK | ✅ | ❌ | 🆕 Purgatory |

### B1.2. Модель иерархии

Обе схемы используют `parent_id FK→self` для рекурсивной иерархии и `LTREE` для типа поля `path`. ✅ согласовано.

---

## B2. Таблица `chunks`

### B2.1. Поля

| Поле | Purgatory (`nsi.chunks`) | `docs/` (`rag.chunks`) | Совпадение |
|---|---|---|---|
| `id` | `UUID PK` | `uuid id PK` | ✅ |
| `document_id` | `UUID FK → purgatory.documents.id` | `uuid document_id FK → registry.documents` | ✅ |
| `section_id` | `UUID FK → nsi.document_sections.id` | `bigint section_id FK → registry.document_sections` | ✅ |
| `content` | `TEXT NOT NULL` | `text content` | ✅ |
| `embedding` | `VECTOR(N)` — pgvector | `vector embedding` | ✅ |
| `tsv` | `TSVECTOR` (автотриггер) | `tsvector tsv` | ✅ |
| `clause` | `TEXT` | ❌ (находится в `registry.document_sections.clause`) | 🔴 |
| `page` | `INT` | `int page` | ✅ |
| `chunk_index` | `INT` | `int chunk_index` | ✅ |
| `chunk_strategy` / `strategy` | `TEXT` | `text strategy` | ⚠️ переименовано |
| `bbox` | `JSONB` | `jsonb bbox` | ✅ |
| `confidence` | `FLOAT (0–1)` | `float confidence` | ✅ |
| `tenant_id` | `TEXT DEFAULT 'default'` | `text tenant_id` | ✅ |
| `deleted_at` | `TIMESTAMPTZ` | `timestamptz deleted_at` | ✅ |
| `created_at` | `TIMESTAMPTZ` | `TIMESTAMPTZ` | ✅ добавлен в `docs/` |

### B2.2. Ключевые различия

1. **Связь с документом:** Purgatory хранит `document_id` напрямую в `nsi.chunks`. `docs/` идёт через `section_id → registry.document_sections.document_id`. Это на один JOIN больше для поиска.
2. **`tenant_id` и `deleted_at`:** Есть в обеих схемах — ✅ согласовано.
3. **`clause`:** В Purgatory — в чанках (денормализация для скорости). В `docs/` — только в `document_sections` (нужен JOIN).
4. **Тип `bbox`:** ✅ Согласовано — обе схемы используют `jsonb`.
5. **Тип `deleted_at`:** ✅ Согласовано — обе схемы используют `timestamptz`.

### B2.3. Индексы и триггер

| Индекс | Purgatory (`nsi`) | `docs/` |
|---|---|---|
| HNSW по embedding | ✅ | ✅ (implied by vector type) |
| GIN по tsv | ✅ | ✅ (implied by tsvector type) |
| B-tree по document_id | ✅ (с WHERE deleted_at IS NULL) | ❌ (нет document_id) |
| B-tree по section_id | ✅ (с WHERE deleted_at IS NULL) | ✅ (implied by FK) |
| Триггер tsv | ✅ `tsvector_update_trigger` | не указан |

---

## B3. Изображения (`images`) и таблицы (`extracted_tables`)

### B3.1. Модели

**Purgatory:** две отдельные таблицы — `nsi.images` и `nsi.extracted_tables` с богатыми метаданными (caption, footnotes, unit, DPI, image_s3_path).

**`docs/`:** изображения и таблицы хранятся как записи в `registry.document_sections` с `type='image'` / `type='table'`, а содержимое — в `jsonb content`:

- Для таблиц: `content = {"headers": [...], "rows": [...]}`
- Для изображений: `content = {"image_id": "...", "file_key": "...", "width": ..., "height": ...}`

### B3.2. Поля изображений (сопоставление)

| Поле Purgatory (`nsi.images`) | `docs/` аналог |
|---|---|
| `id UUID PK` | `registry.document_sections.id` |
| `document_id UUID FK` | `registry.document_sections.document_id` |
| `figure_id TEXT` | в `content.image_id` |
| `title TEXT` | `registry.document_sections.title` |
| `caption TEXT` | `content.caption` |
| `description TEXT` | `content.description` |
| `file_path TEXT` (S3) | в `content.file_key` |
| `file_type TEXT` | `content.file_type` |
| `metadata JSONB` (размеры, DPI) | `content.width`, `content.height` |
| `page INT` | `registry.document_sections.page` |
| `bbox JSONB` | `registry.document_sections.bbox` (TEXT) |

### B3.3. Поля таблиц (сопоставление)

| Поле Purgatory (`nsi.extracted_tables`) | `docs/` аналог |
|---|---|
| `id UUID PK` | `registry.document_sections.id` |
| `document_id UUID FK` | `registry.document_sections.document_id` |
| `section_id UUID FK` | ❌ (сама является секцией) |
| `table_id TEXT` | ❌ |
| `caption TEXT` | `registry.document_sections.title` |
| `page INT` | `registry.document_sections.page` |
| `bbox JSONB` | `registry.document_sections.bbox` (TEXT) |
| `unit TEXT` | `content.unit` |
| `headers JSONB` | в `content.headers` |
| `rows JSONB` | в `content.rows` |
| `footnotes JSONB` | `content.footnotes` |
| `image_s3_path TEXT` | `content.image_s3_path` |
| `created_at TIMESTAMPTZ` | `TIMESTAMPTZ` |

---

## B4. Таблицы `formulas` + `formula_parameters`

**В Purgatory (`nsi`):** `nsi.formulas` (id, document_id, formula_id, latex, image_s3_path, meaning, context_clause, page, bbox) + `nsi.formula_parameters` (id, formula_id FK, symbol, description, unit).

**В `docs/`:** ❌ Полностью отсутствуют.

---

## B5. Таблица `cross_references`

### B5.1. Поля

| Поле | Purgatory (`nsi.cross_references`) | `docs/` (`registry.document_references`) | Совпадение |
|---|---|---|---|
| `id` | `UUID PK` | `uuid id PK` | ✅ |
| `source_document_id` | `UUID FK → purgatory.documents.id` | `uuid source_document_id FK → purgatory_documents` | ✅ |
| `target_doc_code` | `TEXT NOT NULL` | `text target_doc_code` | ✅ |
| `reference_type` | `ENUM (reference/conflict/mandatory/derived)` | `varchar "ENUM reference/conflict/mandatory/derived"` | ✅ |
| `context` | `TEXT` | `text context` | ✅ |
| `current_status` | `TEXT` | `text current_status` | ✅ |
| `replaced_by` | `TEXT` | `text replaced_by` | ✅ |
| `replacement_date` | `DATE` | `date replacement_date` | ✅ |
| `is_resolved` | `BOOLEAN DEFAULT FALSE` | `bool is_resolved` | ✅ |
| `resolved_document_id` | `UUID FK → purgatory.documents.id` | `uuid resolved_document_id FK → purgatory_documents` | ✅ |
| `created_at` | `TIMESTAMPTZ` | `TIMESTAMPTZ` | ✅ добавлен в `docs/` |
| UNIQUE | `(source, target, type)` | ✅ `UK: UNIQUE(source_document_id, target_doc_code, reference_type)` | ✅ |

### B5.2. Вывод

**Таблицы полностью идентичны.** ✅ Все поля (reference_type ENUM, context, current_status, replaced_by, replacement_date, resolved_document_id, UNIQUE-ограничение, `created_at`) совпадают.

---

## B6. Таблица `promotion_history`

### B6.1. Поля

| Поле | Purgatory (`nsi.promotion_history`) | `docs/` (`registry.document_history`) | Совпадение |
|---|---|---|---|
| `id` | `UUID PK` | `uuid id PK` | ✅ |
| `document_id` | `UUID FK → purgatory.documents.id` | `uuid document_id FK → purgatory_documents` | ✅ |
| `event_type` / — | ❌ (всегда promotion) | `text event_type` | 🆕 docs |
| `promoted_at` / `event_at` | `TIMESTAMPTZ` | `timestamptz event_at` | ✅ |
| `promoted_by` / `event_by` | `TEXT` | `text event_by` | ✅ |
| `comment` | `TEXT` | `text comment` | ✅ |
| `source_version_id` | `UUID` (версия файла) | ❌ | 🆕 Purgatory |
| `source_container_id` | `UUID` (контейнер чанков) | ❌ | 🆕 Purgatory |
| `document_snapshot` | ❌ | `jsonb document_snapshot` | 🆕 docs |
| `source_task_id` | ❌ | `TEXT` (ID задачи оркестратора) | 🆕 docs; ссылка на первичный источник |

### B6.2. Ключевые различия

**Purgatory:** специализированная таблица только для промоушенов, с привязкой к версии файла (`source_version_id`) и контейнеру чанков (`source_container_id`).

**`docs/`:** универсальная event-таблица для всех событий жизненного цикла (`event_type`). Содержит `document_snapshot` — снимок состояния документа на момент события и `source_task_id` — ссылку на задачу оркестратора (первичный источник). Нет привязки к версии/контейнеру.

---

# Часть C. Сквозные расхождения

---

## C1. Таблица документов в `nsi`

| Аспект | Purgatory | `docs/` |
|---|---|---|
| Отдельная таблица документов в `nsi` | ❌ Нет. Только `purgatory.documents` | ✅ **Есть.** `registry.documents` — таблица core-слоя с метаданными документа |
| JOIN для поиска | `JOIN purgatory.documents` | `JOIN registry.documents` |

**Вывод:** ✅ **Полностью согласовано.** Оба подхода хранят метаданные документа только в `purgatory.documents` / `purgatory_documents` и используют FK из `nsi`.

---

## C2. Энумерации (ENUM) — расхождения

### C2.1. `classifier_system`

| Значение | Purgatory | `docs/` |
|---|---|---|
| `MKS` / `OKSTU` / `UDC` / `EXTERNAL` | `ENUM` | `TEXT` (в справочнике) |

### C2.2. Статусы классификации

| Статус | Purgatory | `docs/` |
|---|---|---|
| `CONFIRMED` | ✅ | ✅ |
| `PENDING_REVIEW` | ✅ | ✅ |
| `NOT_FOUND` | ✅ | ✅ |
| `NOT_USED` | ✅ | ✅ |
| `UNASSIGNED` | ✅ | ✅ |

### C2.3. Статусы документа (FSM)

**Purgatory:**
`draft → uploaded → processing → review_required → ready_for_promotion → approved → failed → archived`

**`docs/` (Pipeline 1 + 2):**
`draft → uploaded → parsing → validation → ready_for_promotion → review_required → approved → registry → archived → pending_index → indexing → indexed`

Дополнительные статусы в `docs/`: `parsing` (vs `processing`), `validation`, `registry`, `pending_index/indexing/indexed`.

---

## C3. API — структурные расхождения

### C3.1. Создание документа

**Flow:** Оркестратор создаёт задачу → получает `task_id` → передаёт `task_id` в OCR + Parser (не `document_id`).
`document_id` назначается на стадии Converter-validator, когда можно оценить уникальность документа:
либо извлекается существующий `document_id` (для дубликатов), либо генерируется новый.

> **Примечание:** Preview-фаза не существует в Purgatory. В `docs/` это новый этап — быстрая проверка уникальности документа до полной обработки (см. Пайплайн 1: Формирование документа, двухфазный).

| Аспект | Purgatory | `docs/` |
|---|---|---|
| Путь | `POST /upload` | `POST /documents` |
| Первичный идентификатор | `document_id` (назначается при загрузке) | `task_id` (назначается оркестратором); `document_id` — на стадии валидации |
| `version_id` в ответе | ❌ | ✅ |
| `content_hash_sha256` | ❌ | ✅ |
| `title_hash_sha256` | ❌ | ✅ |
| `is_duplicate_file` / `is_duplicate_document` | ❌ | ✅ |

### C3.2. Аппрув

| Аспект | Purgatory | `docs/` |
|---|---|---|
| Параметр `force` | ❌ | ✅ |
| Ответ: `promotion_task_id` | ❌ | ✅ |
| Ответ: `approved_by` / `approved_at` | ❌ | ✅ |

### C3.3. Промотирование

| Аспект | Purgatory | `docs/` |
|---|---|---|
| Механизм | Автоматический шаг воркера | — |
| `target_schema` | ❌ (всегда nsi) | ✅ |
| `options.reindex` | ❌ | ✅ |
| Переиндексация | `repromote_document()` — транзакция очистки+вставки | `DELETE /rag/index/{id}` (RAG Builder) + повторный `POST` |

### C3.4. Гибридный поиск

| Аспект | Purgatory | `docs/` |
|---|---|---|
| Векторный | `cosine_similarity` | `cosine_similarity` |
| Полнотекстовый | `ts_rank` (BM25) | `ts_rank` (BM25) |
| Нечёткий (pg_trgm) | ❌ | ✅ (в Pipeline 3) |
| Ранжирование | RRF (k=60) | RRF (k=60) |
| Фильтры | ❌ | `document_type`, `date_from`, `date_to` |
| JOIN для цитат | `JOIN purgatory.documents` | `JOIN purgatory_documents` |

---

# Часть D. Сводный реестр изменений для согласования

---

## D1. Что можно добавить в `docs/` (из Purgatory)

| № | Изменение | Слой | Обоснование |
|---|---|---|---|
| 1 | Поле `classifier_code` в документ | purgatory | Общая привязка к классификатору |
| 2 | Generated columns `mks_system`, `okstu_system` | purgatory | FK-изоляция деревьев классификаторов |
| 3 | Таблица `format_registry` | purgatory | Реестр форматов с MIME-типами и парсерами |
| 4 | Поле `source_filename` в версию документа | purgatory | Исходное имя файла |
| 5 | CAS-путь `{doc_id}/v{n}/{hash}.ext` | purgatory | Гарантия целостности файлов |
| 6 | Поле `source_version_id` в `classifier_pending` | purgatory | Привязка кода к версии файла |
| 7 | Статус `UNASSIGNED` для классификации | purgatory | ✅ Добавлено — начальное состояние до парсинга |
| 8 | `metadata.author`, `metadata.language` | purgatory | Дополнительные метаданные |
| 9 | `comment` → `{reason, details}` в `status_history` | purgatory | ✅ Добавлено — структурированная причина перехода |
| 10 | `path LTREE` в `registry.document_sections` | nsi | Иерархические запросы (сейчас TEXT) |
| 11 | Прямой `document_id` в `rag.chunks` | nsi | Ускорение поиска (сейчас через section_id) |
| 12 | `clause` в `rag.chunks` | nsi | Денормализация для скорости (сейчас в sections) |
| 13 | `created_at` в `rag.chunks`, `registry.document_references` | nsi | Стандартное поле аудита |
| 14 | UNIQUE `(source, target, type)` на cross_references | nsi | Защита от дублей |
| 15 | ENUM для `reference_type` | nsi | Валидация на уровне БД |
| 16 | Отдельная таблица `nsi.images` | nsi | Изображения как самостоятельные сущности |
| 17 | Отдельная таблица `nsi.extracted_tables` | nsi | Unit, footnotes, image_s3_path |
| 18 | `nsi.formulas` + `nsi.formula_parameters` | nsi | Поддержка формул |
| 19 | `source_version_id`, `source_container_id` в promotion_history | nsi | Трассировка промоушенов |
| 20 | Триггер автообновления tsv | nsi | Автоматическая синхронизация |

## D2. Что можно добавить в Purgatory (из `docs/`)

| № | Изменение | Слой | Обоснование |
|---|---|---|---|
| 1 | Поле `user_id` в документ | purgatory | Привязка к пользователю UI |
| 2 | Поле `tags` в `metadata` | purgatory | Гибкое тегирование |
| 3 | `version_number` в `document_versions` | purgatory | Нумерация версий |
| 4 | `suggested_parent_code/name` в `classifier_pending` | purgatory | Подсказки парсера |
| 5 | Промотирование с `target_schema` | purgatory | Явное указание схемы |
| 6 | `is_duplicate_file` / `is_duplicate_document` | purgatory | Прозрачность дедупликации |
| 7 | `force` флаг при аппруве | purgatory | Принудительное утверждение |
| 8 | `section_title` в `nsi.chunks` | nsi | Ускорение поиска |
| 9 | Фильтры `(document_type, date_from, date_to)` | nsi | Фильтрация поиска |
| 10 | Нечёткий поиск pg_trgm | nsi | Поиск по названиям |
| 11 | `event_type` в promotion_history | nsi | Универсальная история событий |
| 12 | `document_snapshot` JSONB в promotion_history | nsi | Снимок состояния документа на момент события |
| 13 | Тип `informative` для cross_references | nsi | Дополнительный тип связи |
| 14 | `bbox TEXT` (вместо JSONB) | nsi | Упрощение |

## D3. Требующие обсуждения расхождения

| № | Вопрос | Purgatory | `docs/` |
|---|---|---|---|
| 1 | **ENUM vs TEXT** | Все статусы — ENUM в БД | Частично согласовано: `validity_status`, `type`, `reference_type` — ENUM; `classifier_system`, `doc_status` — TEXT (не согласовано) |
| 2 | **Хранение чанков** | Один JSONB-контейнер (`chunk_containers`) | Построчные записи (`rag.chunks`) |
| 3 | **CAS-пути** | Строгий CAS через content_hash | `file_key` без спецификации |
| 4 | **FK-изоляция классификатора** | Composite FK с generated columns | FK без гарантии изоляции |
| 5 | **Изображения/таблицы** | Отдельные таблицы | Секции с type='image'/'table' |
| 6 | **Связь chunks→document** | Прямой `document_id` | Через `section_id` → документ |
| 7 | **`clause` в чанках** | Да (денормализация) | Нет (только в sections) |
| 8 | **Тип `bbox`** | JSONB | `jsonb` (согласовано) |
| 9 | **Тип `deleted_at`** | TIMESTAMPTZ | `timestamptz` (согласовано) |
| 10 | **История: специализированная vs event** | `promotion_history` (только промоуты) | `registry.document_history` (все события) |
| 11 | **Формулы** | Входят в MVP | Не поддерживаются |
| 12 | **Статус FSM** | `processing` (единый) | `parsing` + `validation` (раздельные) |

---

## D4. Полностью согласованные сущности

- `purgatory.classifier_registry` / classifiers — ⚠️ (ENUM vs TEXT для classifier_system — не согласовано)
- **`nsi.cross_references` / `registry.document_references`** — 🟢 на ~95% (разница: `created_at`)
- **`nsi.chunks` / `rag.chunks`** — 🟢 на ~90% (разница: связь с документом и clause)
- **`nsi.document_sections` / `registry.document_sections`** — 🟢 на ~95% (разница: bbox, content, type)

## D5. Частично согласованные

- `purgatory.documents` — ✅ на ~90% (отличия: ENUM vs TEXT, отсутствие user_id/tags)
- `purgatory.classifier_pending` — ⚠️ на ~70%
- `purgatory.document_versions` — ⚠️ на ~65%
- `nsi.promotion_history` / `registry.document_history` — ⚠️ на ~60% (специализированная vs event-модель)

## D6. Не согласованные

- `purgatory.format_registry` — 🔴 только в Purgatory
- `purgatory.chunk_containers` — 🔴 разная модель (JSONB vs таблица)
- `nsi.images` — 🔴 только в Purgatory (docs: секции)
- `nsi.extracted_tables` — 🔴 только в Purgatory (docs: секции)
- `nsi.formulas` + `nsi.formula_parameters` — 🔴 только в Purgatory

---

## D7. Ключевые решения для согласования

1. **ENUM vs TEXT** — выбрать единый подход для оставшихся статусных полей (`classifier_system`, `doc_status`).
2. **Изображения/таблицы: отдельные таблицы или секции?** Отдельные таблицы дают richer метаданные (caption, footnotes, unit). Секции проще для пайплайна (единая структура JSON). Возможен компромисс: `sections` для иерархии + `images`/`tables` для контента.
3. **Связь chunks→document:** прямой `document_id` (Purgatory) vs через `section_id` (docs). Прямой путь быстрее для поиска, через section_id — нормализованнее.
4. **Формулы** — Purgatory включает их в MVP; `docs/` не поддерживает.
5. **Хранение чанков** — JSONB-контейнер vs нормализованные таблицы (возможно и то, и другое: контейнер для целостности, таблицы для поиска).
6. **CAS-пути** — внедрить CAS как стандарт де-факто.
7. **FK-изоляция классификаторов** — внедрить composite FK с generated columns.
8. **История: специализированная (`promotion_history`) или event-модель (`registry.document_history`)?** Event-модель универсальнее; специализированная — точнее для трейсинга промоутов.
9. **FSM** — согласовать единую FSM на 10–14 состояний (дополнив Purgatory статусами `parsing`, `validation`, `registry`, а `docs/` — исключив `pending_index` если это не входит в MVP).
