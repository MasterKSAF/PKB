# Аудит схемы данных PKB NeuroAssistant

> Дата: 2026-06-05
> Источники: `db_diagrams.md`, `diagrams.md`, `schema_converter_result.json`, `schema_registry_for_rag.json`, `specificity.md`

---

## Сводка

| Категория | Ошибки | Предупреждения | Предложения |
|-----------|--------|----------------|-------------|
| Моделирование и типы | 3 | 5 | 3 |
| Ключи и ограничения | 4 | 3 | 2 |
| Нормализация и избыточность | 1 | 3 | 2 |
| Именование и консистентность | 0 | 4 | 1 |
| Пропущенные атрибуты | 3 | 2 | 1 |
| Производительность | 1 | 3 | 2 |
| **Итого** | **12** | **20** | **11** |

---

## 1. Моделирование и типы данных

### 🔴 DB-E1. VARCHAR-поля для перечислимых типов без CHECK-ограничений

> **⏳ Требует реализации в коде**: DDL-миграция — добавить ENUM-типы или CHECK-ограничения. Не входит в объём документации.

**Таблицы**: `registry.documents`, `registry.document_sections`, `registry.document_references`, `chat.projects`, `chat.messages`

Поля `source_type`, `document_type`, `group`, `era`, `validity_status`, `jurisdiction`, `processing_status` (documents), `type` (sections — CHECK указан в примечаниях, но не в DDL), `reference_type`, `current_status`, `status` (projects, messages), `role` (messages), `strategy` (chunks) — все объявлены как `varchar`/`text` без CHECK-ограничений на уровне БД.

Для `document_sections.type` CHECK указан в примечаниях к ER-диаграмме, но не формализован в DDL. Остальные перечисления не имеют даже описанных ограничений.

**Рекомендация**: либо создать ENUM-типы PostgreSQL (`source_type_enum`, `document_type_enum` и т.д.), либо добавить CHECK-ограничения. Пример:

```sql
ALTER TABLE registry.documents ADD CONSTRAINT chk_era
  CHECK (era IN ('USSR','CIS','RF','CURRENT'));
ALTER TABLE registry.documents ADD CONSTRAINT chk_validity_status
  CHECK (validity_status IN ('active','superseded','expired'));
```

---

### 🔴 DB-E2. Хэш-поля `file_hash_sha256` и `title_hash_sha256` объявлены как `text`

SHA-256 хэш всегда ровно 64 шестнадцатеричных символа. `text` допускает строки любой длины и любого содержания.

**Рекомендация**: `CHAR(64)` или `VARCHAR(64)`. Это даёт:
- Гарантию целостности (нельзя записать некорректный хэш)
- Экономию хранения (6 байт разницы на строку, + TOAST не нужен для коротких строк)
- Возможность индекса по хэшу с предсказуемым размером

---

### 🔴 DB-E3. `chat.sessions.document_ids` — массив `bigint[]` (нарушение 1НФ)

Уже зафиксировано в specificity.md (A6) как «осознанное решение, отложено». Фиксирую как ошибку: в обратной зависимости повторю.

**Неотложная проблема**: невозможен эффективный запрос «найти все сессии, работающие с документом X» без сканирования всего массива.

---

### 🟡 W1. `float` для `confidence` в `rag.document_chunks`

`float` (в PostgreSQL это `float8` / `double precision`, 8 байт) — избыточно для значения 0..1. `real` (4 байта) достаточно. Также не определён диапазон, значение по умолчанию и допустимость NULL.

**Рекомендация**: `real NOT NULL DEFAULT 0.0 CHECK (confidence BETWEEN 0 AND 1)` или явно `CHECK (confidence >= 0 AND confidence <= 1)`.

---

### 🟡 W2. Отсутствуют значения по умолчанию

| Таблица | Поле | Рекомендуемый DEFAULT |
|---------|------|-----------------------|
| `registry.documents` | `chunk_count` | `0` |
| `registry.document_references` | `is_resolved` | `false` |
| `chat.sessions` | `message_count` | `0` |
| `chat.messages` | `processing_time_ms` | `0` |

Без DEFAULT при INSERT без указания этих полей будет получен NULL, что нарушит бизнес-логику (счётчик чанков = NULL).

---

### 🟡 W3. `content` в `document_sections` — JSONB без схемы

Поле `content` хранит принципиально разные структуры в зависимости от `type` ('section', 'table', 'image', 'formula', 'list', 'headerFooter', 'textBlock'). Нет JSON Schema валидации, нет GIN-индекса.

**Риск**: неконсистентные данные, невозможность индексации по внутренним полям, нет защиты от записи несогласованных структур.

**Рекомендация**: добавить CHECK с,jsonb-проверкой через PL/pgSQL-функцию, либо вынести структурированные типы в отдельные таблицы (`section_tables`, `section_formulas`, `section_images`).

---

### 🟡 W4. `document_snapshot` в `document_history` — неограниченный JSONB

Хранение полного слепка документа при каждом событии. Для документов с десятками секций и амендментов — мегабайты на строку.

**Рекомендация**:
- Добавить COMMENT с описанием структуры
- Рассмотреть хранение diff вместо полного слепка
- Или хранить только изменённые поля

---

### 🟡 W5. `format_code` + `format_label` в `document_versions` — частичная функциональная зависимость

`format_label` определяется `format_code` ('pdf' → 'PDF Document'). Хранение обеих вариантов — денормализация.

**Рекомендация**: либо убрать `format_label` (вычислять на клиенте), либо создать lookup-таблицу `doc_formats(code, label)`.

---

### 💡 S1. `adoption_date` и `effective_from` — тип `date`

В JSON-схемах (converter_result.json, schema_registry_for_rag.json) эти поля — полные ISO-timestamp'ы (`"1981-04-15"`). Если дата принятия — всегда только дата (без времени), тип `date` корректен. Если возможно указание времени — нужен `timestamptz`.

**Рекомендация**: подтвердить, что `date` достаточен. Если возможна точность до дня — `date` подходит.

---

### 💡 S2. `replaces` (text) и `predecessor_doc_id` (bigint FK) семантически пересекаются

`replaces` — свободный текст («ГОСТ 20868-75»), а `predecessor_doc_id` — точная FK-ссылка. Они описывают одну и ту же связь, но на разных уровнях.

**Рекомендация**: чётко задокументировать: `replaces` — человекочитаемая строка (может содержать несколько кодов через запятую, диапазоны), `predecessor_doc_id` — однозначная ссылка на конкретную запись в БД, NULL если предшественник не в реестре.

---

### 💡 S3. `okstu_code` и `udc` — `text`, но в примерах NULL

В schema_converter_result.json оба поля — `null`. Если они редко заполняются, `text` избыточен; если ожидается массовое заполнение — стоит добавить индекс.

---

## 2. Ключи и ограничения

### 🔴 DB-E4. Не определены UNIQUE-ограничения для бизнес-ключей

> **⏳ Требует реализации в коде**: DDL-миграция — добавить UNIQUE-ограничения. Не входит в объём документации.

| Таблица | Ключ | Обоснование |
|---------|------|-------------|
| `registry.documents` | `(doc_code, era)` | Один и тот же ГОСТ может быть в разных эпохах |
| `registry.documents` | `file_hash_sha256` | Упоминается как дубликат-детектор, но без UNIQUE |
| `registry.document_sections` | `(document_id, path)` | Один путь в рамках одного документа — уникален |
| `registry.document_versions` | `(document_id, version_number)` | Версия документа уникальна в рамках документа |
| `registry.document_chunks` | `(section_id, chunk_index)` | Порядок чанков в секции уникален |
| `chat.projects` | `code` | Код проекта должен быть уникален |

**Риск**: дублирование данных, невозможность guarantee уникальности на уровне БД.

---

### 🔴 DB-E5. Не определены ON DELETE-правила для всех FK

> **⏳ Требует реализации в коде**: DDL-миграция — добавить ON DELETE CASCADE/SET NULL. Не входит в объём документации.

Ни один FK не имеет указанного поведения `ON DELETE` / `ON UPDATE`. Это значит PostgreSQL по умолчанию использует `NO ACTION` (эквивалент `RESTRICT`).

Это создаёт проблемы:
- Удаление документа невозможно, пока существуют секции, чанки, ссылки, версии, история — нужно каскадно удалять вручную
- Удаление проекта блокируется сессиями
- Удаление секции не удаляет связанные чанки

**Рекомендация**:

| FK | ON DELETE |
|----|-----------|
| `document_sections.document_id → documents.id` | `CASCADE` |
| `document_sections.parent_id → document_sections.id` | `SET NULL` |
| `document_references.source_document_id → documents.id` | `CASCADE` |
| `document_references.resolved_document_id → documents.id` | `SET NULL` |
| `document_versions.document_id → documents.id` | `CASCADE` |
| `document_history.document_id → documents.id` | `CASCADE` |
| `document_chunks.document_id → documents.id` | `CASCADE` |
| `document_chunks.section_id → document_sections.id` | `CASCADE` |
| `documents.successor_doc_id → documents.id` | `SET NULL` |
| `documents.predecessor_doc_id → documents.id` | `SET NULL` |
| `sessions.project_id → projects.id` | `SET NULL` |

---

### 🔴 DB-E6. `user_id` в `chat.sessions` не имеет целевой таблицы

> **⏳ Требует реализации в коде**: создание таблицы `auth.users` — часть разработки Auth Service. Не входит в объём документации.

FK `user_id` ссылается на «Auth Service», но таблицы `users` нет в схеме. Это phantom-FK — невозможно определить ссылочную целостность.

**Рекомендация**: либо включить таблицу `auth.users` (или её stub), либо описать FK как отложенный/внешний.

---

### 🔴 DB-E7. Отсутствуют индексы для часто запрашиваемых полей

Многие поля, критичные для фильтрации и соединений, не имеют явно указанных индексов:

**Требуемые индексы** (помимо PK/FK):

| Таблица | Поле/комбинация | Тип индекса | Назначение |
|---------|------------------|--------------|------------|
| `registry.documents` | `doc_code` | B-tree | Поиск по коду ГОСТ |
| `registry.documents` | `(doc_code, era)` | B-tree UNIQUE | Бизнес-ключ |
| `registry.documents` | `file_hash_sha256` | B-tree UNIQUE | Дубликат-детектор |
| `registry.documents` | `title_hash_sha256` | B-tree | Дубликат-детектор |
| `registry.documents` | `processing_status` | B-tree (частичный) | FSM-фильтр |
| `registry.documents` | `validity_status` | B-tree | Фильтр по статусу |
| `registry.documents` | `era` | B-tree | Фильтр по эпохе |
| `registry.documents` | `"group"` | B-tree | Фильтр по группе |
| `registry.documents` | `source_type` | B-tree | Фильтр по типу |
| `registry.document_sections` | `path` | GiST (ltree) | Иерархические запросы |
| `registry.document_sections` | `type` | B-tree | Фильтр по типу секции |
| `registry.document_references` | `target_doc_code` | B-tree | Поиск ссылок на документ |
| `registry.document_history` | `(document_id, event_at)` | B-tree | Хронология документа |
| `rag.document_chunks` | `strategy` | B-tree | Фильтр по стратегии |
| `chat.sessions` | `user_id` | B-tree | Сессии пользователя |
| `chat.sessions` | `project_id` | B-tree | Сессии проекта |
| `chat.messages` | `(session_id, created_at)` | B-tree | Хронология сообщений |
| `chat.messages` | `role` | B-tree (частичный) | Фильтр по роли |

**Уже указанные в схеме**: `(file_hash_sha256, file_size_bytes)` — дубликат-детектор; GIN на `tsv`; IVFFlat на `embedding`.

---

### 🟡 W6. Нет составного индекса для диапазонных запросов по дате

`documents.adoption_date` и `documents.effective_from` — частые фильтры в реестре нормативных документов («все документы, действующие на дату X»). Без составного индекса `(validity_status, effective_from, adoption_date)` такие запросы будут медленными.

---

### 🟡 W7. Нет CHECK для `version_number > 0` в `document_versions`

Нет ограничения на положительные значения номера версии.

---

### 🟡 W8. Нет CHECK на неотрицательность `chunk_count`, `message_count`, `processing_time_ms`, `file_size_bytes`

Эти поля содержат счётчики и размеры — не могут быть отрицательными.

---

### 💡 S4. Частичные индексы для распространённых фильтров

Для `processing_status` вместо полного B-tree эффективнее частичный индекс:
```sql
CREATE INDEX idx_documents_pending ON registry.documents (id)
  WHERE processing_status IN ('uploaded', 'previewing', 'awaiting_decision');
```

---

### 💡 S5. Индекс на GIN для `document_history.document_snapshot`

Если по `document_snapshot` нужны запросы (поиск по `event_type` внутри JSON), добавьте GIN-индекс. Если нет — не нужен.

---

## 3. Нормализация и избыточность

### 🔴 DB-E8. `document_chunks.document_id` — осознанная, но рискованная денормализация

Поле `document_id` в чанке дублирует `document_sections.document_id → documents.id`. Это ускоряет запросы «все чанки документа» (без JOIN через sections), но создаёт риск inconsistency: если секция переместится в другой документ, `chunk.document_id` останется устаревшим.

**Рекомендация**: если денормализация сохраняется, добавить триггер или приложение-логику, синхронизирующую `chunk.document_id` с `section.document_id`. Либо убрать поле и всегда JOIN через sections.

---

### 🟡 W9. `chat.sessions.message_count` — денормализованный счётчик без механизма синхронизации

Нет триггера, нет описания механизма обновления. При ручном обновлении возможен drift.

**Рекомендация**: либо добавить триггер `AFTER INSERT/DELETE ON messages`, либо убрать поле и вычислять на лету `COUNT(*)`.

---

### 🟡 W10. `chat.messages.sources` — JSONB-массив с вложенными объектами

Поле `sources` содержит `[{chunk_id, section_id, document_id, excerpt, score}]`. Это затрудняет:
- Запрос «все чаты, где использовался документ X» (нужен GIN + jsonb_path_query)
- Агрегацию по `chunk_id`

**Рекомендация**: рассмотреть выделенную таблицу `chat.message_sources (message_id, chunk_id, section_id, document_id, score)` для аналитики и гарантии ссылочной целостности. Альтернатива — GIN-индекс на `sources` с `jsonb_path_ops`.

---

### 🟡 W11. Таблица `terminology` отсутствует в схеме БД

И `schema_converter_result.json`, и `schema_registry_for_rag.json` содержат массив `terminology` с полями `term`, `definition`, `source_clause`, `normalized_term`. В БД соответствующей таблицы нет.

**Рекомендация**: создать `registry.terminology (id, document_id FK, term, normalized_term, definition, source_clause)` — это важно для полнотекстового поиска терминов и связывания определений с документами.

---

### 💡 S6. Рассмотреть нормализацию `issuing_body` и `group`

Значения `issuing_body` («Государственный Комитет СССР по стандартам») и `group` («ПО4») повторяются для десятков документов. Нормализация в lookup-таблицы сократит хранение и упростит изменение.

---

### 💡 S7. `document_type` + `source_type` в одном справочнике

Оба поля — перечисления с перекрывающимися контекстами. Рассмотреть единый справочник `registry.doc_type_catalog` или PostgreSQL ENUM.

---

## 4. Именование и консистентность

### 🟡 W12. Несогласованное именование timestamp-полей

| Таблица | Поле | Паттерн |
|---------|------|---------|
| `documents` | `created_at`, `updated_at` | `*_at` ✅ |
| `document_sections` | `created_at` | `*_at` ✅ |
| `document_references` | `created_at` | `*_at` ✅ |
| `document_versions` | `uploaded_at` | `*_at` ⚠️ |
| `document_history` | `event_at` | `*_at` ⚠️ |
| `document_chunks` | `created_at` | `*_at` ✅ |
| `projects` | `created_at`, `updated_at` | `*_at` ✅ |
| `sessions` | `created_at`, `updated_at` | `*_at` ✅ |
| `messages` | `created_at` | `*_at` ✅ |

`uploaded_at` и `event_at` — семантически верные, но нарушают паттерн «для бизнес-времени — `*_at`, для аудита — `created_at`/`updated_at`».

**Рекомендация**: для `document_versions` добавить `created_at`/`updated_at`, а `uploaded_at` сделать псевдонимом/алиасом `created_at`. Для `document_history` `event_at` нормален (это событие, не аудит строки).

---

### 🟡 W13. Несогласованное именование полей «кто изменил»

| Таблица | Поле | Паттерн |
|---------|------|---------|
| `documents` | `created_by`, `updated_by` | `*_by` ✅ |
| `document_versions` | `uploaded_by` | `*_by` ⚠️ |
| `document_history` | `changed_by` | `*_by` ⚠️ |

Ситуация аналогична W12: `uploaded_by` и `changed_by` семантически точны, но нарушают единообразие.

---

### 🟡 W14. Несогласованное именование полей «статус»

| Таблица | Поле | Значения |
|---------|------|----------|
| `documents` | `validity_status` | active, superseded, expired |
| `documents` | `processing_status` | uploaded, previewing, ... |
| `document_references` | `current_status` | active, superseded |
| `projects` | `status` | active, archived, draft |
| `messages` | `status` | idle, pending, ... |

Три разных суффикса (`_status`, без суффикса) и пересекающиеся значения.

**Рекомендация**: унифицировать: `_status` для всех, без варинтов.

---

### 🟡 W15. В FK-наименовании разные стили

- `source_document_id` — описательный префикс
- `successor_doc_id` — суффикс `_doc_id` вместо `_document_id`
- `predecessor_doc_id` — то же
- `resolved_document_id` — полный `_document_id`

**Рекомендация**: выбрать один стиль: `_document_id` для всех FK или `_doc_id` для коротких.

---

### 💡 S8. Схема `registry` vs `rag` vs `chat` — разумное разделение

Три схемы логически разделены. Хорошо, что нет перекрёстных FK между `registry`/`rag` и `chat`. Продолжайте в том же духе.

---

## 5. Пропущенные атрибуты

### 🔴 DB-E9. Отсутствуют поля `updated_at` в критичных таблицах

| Таблица | Есть `created_at` | Есть `updated_at` |
|---------|--------------------|-------------------|
| `document_sections` | ✅ | ❌ |
| `document_references` | ✅ | ❌ |
| `document_versions` | ✅ (uploaded_at) | ❌ |
| `document_chunks` | ✅ | ❌ |
| `messages` | ✅ | ❌ |

**Риск**: невозможно отследить, когда строка была изменена. Для `messages` `updated_at` критичен — статус сообщения меняется (idle → pending → ... → answered).

**Рекомендация**: добавить `updated_at` во все таблицы с мутабельными данными.

---

### 🔴 DB-E10. Нет механизма soft-delete ни в одной таблице

> **⏳ Требует реализации в коде**: DDL-миграция + изменение запросов (фильтр `WHERE deleted_at IS NULL`). Не входит в объём документации.

Поле `deleted_at` отсутствует везде. Физическое удаление документа разрушит все связанные данные (CASCADE) и историю. Для реестра нормативных документов это неприемлемо — удалённый документ может быть восстановлен.

**Рекомендация**: добавить `deleted_at TIMESTAMPTZ DEFAULT NULL` в `registry.documents`, `chat.sessions`, `chat.projects`. Изменить запросы на фильтрацию `WHERE deleted_at IS NULL`.

---

### 🔴 DB-E11. Таблица `users` отсутствует, но FK на неё существует

> **⏳ Требует реализации в коде**: создание таблицы `auth.users` + FK. Часть разработки Auth Service. Не входит в объём документации.

`chat.sessions.user_id` — FK к несуществующей таблице. Без неё нельзя обеспечить ссылочную целостность.

**Рекомендация**: создать stub-таблицу `auth.users (id BIGINT PK, username TEXT, email TEXT, created_at TIMESTAMPTZ)` или описать FK как внешний (deferred).

---

### 🟡 W16. Таблица `amendments` отсутствует как отдельная сущность

Амендменты хранятся внутри JSONB-контента секций (`content.amendments[]`) и в метаданных документа (в `schema_registry_for_rag.json`). Нет отдельной таблицы для поиска и отслеживания амендментов.

**Рекомендация**: для MVP — допустимо хранить в JSONB. Для продакшена — рассмотреть `registry.document_amendments (id, document_id FK, type, source, affected_clauses[], note)`.

---

### 🟡 W17. Таблица `pipeline.drafts` не отражена в ER-диаграмме

В specificity.md (A5) описана таблица `pipeline.drafts`, но в ER-диаграмме её нет. Это создает расхождение между документацией и схемой.

---

### 💡 S9. Стандартные справочники не выделены в отдельные таблицы

Значения `era`, `validity_status`, `source_type`, `document_type`, `jurisdiction`, `processing_status`, `reference_type`, `role` (chat), `strategy` (chunks) — все хранятся как строки без lookups. Для стационарных справочников (era, jurisdiction) полезны отдельные таблицы или хотя бы ENUM-типы.

---

## 6. Производительность

### 🔴 DB-E12. `document_sections.content` — JSONB-поле с гетерогенной структурой, без GIN

> **⏳ Требует реализации в коде**: DDL-миграция — создать GIN-индекс. Не входит в объём документации.

Для таблицы, которая может содержать миллионы записей (сотни секций × тысячи документов), отсутствие GIN-индекса на `content` означает невозможность эффективного поиска по внутренним полям (например, `content.amendments[].type`).

**Рекомендация**: добавить GIN-индекс:
```sql
CREATE INDEX idx_sections_content ON registry.document_sections
  USING GIN (content);
```
Или создать частичные индексы по типу секции.

---

### 🟡 W18. Партиционирование не предусмотрено

Таблицы с высокой скоростью роста (`document_history`, `document_chunks`, `messages`) не имеют стратегии партиционирования. При объёме >10M строк запросы замедлятся.

**Рекомендация**:
- `document_history` — партиционировать по `event_at` (RANGE по месяцу/кварталу)
- `document_chunks` — партиционировать по `document_id` (HASH)
- `messages` — партиционировать по `created_at` (RANGE по месяцу)

---

### 🟡 W19. Векторный поиск: IVFFlat при малом объёме данных

Примечания упоминают `IVFFlat` для `embedding`. Этот алгоритм требует обучения (building) на достаточном количестве векторов (минимум ~1000). На ранних стадиях проекта, когда чанков мало, `HNSW` обеспечивает лучший recall без обучения.

**Рекомендация**: начать с `HNSW`, перейти на `IVFFlat` при >100K чанков.

---

### 🟡 W20. Нет COVERING-индексов для типовых запросов

Частые запросы:
- «Документы по статусу + эпоха» → `(processing_status, era) INCLUDE (doc_code, title)`
- «Чанки документа для RAG» → `(document_id) INCLUDE (section_id, chunk_index, content)`
- «Сообщения сессии хронологически» → `(session_id, created_at) INCLUDE (role, content)`

**Рекомендация**: добавить COVERING-индексы после анализа реальных запросов на продакшене.

---

### 💡 S10. Рассмотреть TOAST-сжатие для больших полей

`document_sections.content`, `document_history.document_snapshot`, `chat.messages.sources` — потенциально крупные JSONB-поля. PostgreSQL автоматически использует TOAST, но явное сжатие через `EXTENDED` стратегию (по умолчанию) может быть неоптимальным для векторизованных полей.

**Рекомендация**: мониторить средний размер строки. При avg > 8KB — рассмотреть партиционирование или вынос в отдельную таблицу.

---

### 💡 S11. `file_hash_sha256` + `file_size_bytes` как уникальный детектор дубликатов

Примечания указывают на использование `(file_hash_sha256, file_size_bytes)` для дубликат-детекции. Это корректно, но `file_size_bytes` избыточен для уникальности — SHA-256 уже практически уникален. Добавление `file_size_bytes` — defence in depth (защита от коллизий).

**Рекомендация**: оставить как есть, но убедиться, что UNIQUE-индекс создан именно на комбинацию `(file_hash_sha256, file_size_bytes)`, а не только на хэш.

---

## Приложение А. Сводная таблица отсутствующих таблиц

| Сущность | JSON-схема | БД-таблица | Статус |
|----------|------------|------------|--------|
| `terminology` | ✅ (converter_result, registry_for_rag) | ❌ | 🔴 Требуется |
| `amendments` | ✅ (встроен в content + metadata) | ❌ | 🟡 MVP — в JSONB, прод — вынести |
| `auth.users` | ✅ (FK) | ❌ | 🔴 Требуется для RI |
| `pipeline.drafts` | ✅ (specificity.md A5) | ❌ | 🟡 Вне ER-диаграммы |
| `document_amendments` | ✅ (встроен) | ❌ | 🟡 Будущее |
| `message_sources` | ✅ (встроен в sources) | ❌ | 🟡 Будущее |

---

## Приложение Б. Сводная таблица недостающих UNIQUE-ограничений

| Таблица | Ограничение | Приоритет |
|---------|-------------|-----------|
| `registry.documents` | `UNIQUE (doc_code, era)` | 🔴 Критичное |
| `registry.documents` | `UNIQUE (file_hash_sha256)` | 🔴 Критичное |
| `registry.document_sections` | `UNIQUE (document_id, path)` | 🟡 Желательное |
| `registry.document_versions` | `UNIQUE (document_id, version_number)` | 🟡 Желательное |
| `registry.document_chunks` | `UNIQUE (section_id, chunk_index)` | 🟡 Желательное |
| `chat.projects` | `UNIQUE (code)` | 🟡 Желательное |

---

## Приложение В. Сводная таблица недостающих CHECK-ограничений

| Таблица | Ограничение | Приоритет |
|---------|-------------|-----------|
| `registry.documents` | `era IN ('USSR','CIS','RF','CURRENT')` | 🔴 |
| `registry.documents` | `validity_status IN ('active','superseded','expired')` | 🟡 |
| `registry.documents` | `processing_status IN (...)` | 🟡 |
| `registry.documents` | `source_type IN ('GOST','GOST_R','OST','RD','TU','ISO','DNV','ASTM','OTHER')` | 🟡 |
| `registry.documents` | `document_type IN ('normative','technical','drawing','specification','archival_scan')` | 🟡 |
| `registry.documents` | `jurisdiction IN ('RU','EU','US','NO','INTL')` | 🟡 |
| `registry.document_sections` | `type IN ('text','textBlock','headerFooter','table','list','image','formula')` | ✅ Указано в примечаниях |
| `registry.document_references` | `reference_type IN ('single','range')` | 🟡 |
| `registry.document_references` | `is_resolved DEFAULT FALSE` | 🔴 |
| `registry.document_chunks` | `confidence BETWEEN 0 AND 1` | 🟡 |
| `registry.document_versions` | `version_number > 0` | 🟡 |
| `chat.projects` | `status IN ('active','archived','draft')` | 🟡 |
| `chat.messages` | `role IN ('user','assistant','system')` | 🟡 |