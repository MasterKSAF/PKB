# Аудит логических пайплайнов и схемы данных
## PKB Neuroassistant — Отчёт по правилу check_rule.md (п.2 и п.3)

**Дата аудита:** 2026-06-06  
**Источники:** `docs/pipelines/*.md`, `docs/database/*.md`, `docs/schema/*`, `docs/specifications/*`, `docs/checks/check_rule.md`

---

# Часть 1. Проверка логических пайплайнов (п.2 check_rule.md)

## 1.1. Критичные проблемы

### LP-C1. Потеря бинарных объектов на страницах preview при переходе к full-фазе
**Где:** `docs/pipelines/pipeline1-formation.md` (раздел «Кэширование результатов preview-фазы»), `docs/pipelines/pipeline1-formation_detail.md` (раздел «Режимы работы» OCR/Parser)
**Факт:**
- Preview-режим OCR/Parser: «**Не выполняет** сохранение бинарных объектов в файловое хранилище» (`pipeline1-formation_detail.md`).
- Full-фаза: «OCR/Parser full начинает обработку со страницы `max_pages + 1`, избегая повторной обработки preview-страниц» (`pipeline1-formation.md`).
**Проблема:** если full-фаза начинает обработку со страницы 4 (при `max_pages=3`), то бинарные объекты (картинки, таблицы-картинки, формулы) со страниц 1–3 **никогда не сохраняются в MinIO**. В итоговом документе эти объекты будут отсутствовать.
**Рекомендация:** либо отменить оптимизацию «начинать со страницы max_pages+1» для full-режима, либо в preview-режиме сохранять бинарные объекты.

### LP-C2. Противоречие в назначении `document_id`
**Где:** `docs/pipelines/overview.md` (раздел «Единый `document_id`»), `docs/pipelines/pipeline1-formation.md` (раздел «Этап 3: Registry»), `docs/pipelines/pipeline1-formation_detail.md` (раздел «Registry»)
**Факт:**
- `overview.md`: «`document_id` назначается на этапе **Validation** (Пайплайн 1, Этап 2) после проверки уникальности».
- `pipeline1-formation.md`: «Registry: создание карточки документа → `document_id` (финальный ID)».
- `pipeline1-formation_detail.md`: «Формирует и сохраняет карточку документа (**уникальный ID**, обозначение, наименование...)».
**Проблема:** в одном месте ID назначается Converter-validator (Validation), в другом — Registry. Это блокирует согласование реализации: кто генерирует PK, кто отвечает за уникальность.
**Рекомендация:** зафиксировать единого владельца `document_id` (рекомендуется Registry, т.к. оно записывается в БД).

### LP-C3. Неатомарность проверки уникальности + отсутствие компенсации при дубликате после `approve`
**Где:** `docs/pipelines/pipeline1-formation.md` (раздел «Проверка уникальности»)
**Факт:**
- Явно задокументировано: «Проверка уникальности через `check-uniqueness` **неатомарна** с последующей записью. Между check и write может быть вставлен другой документ».
- Решение предлагается на уровне БД (`UNIQUE + ON CONFLICT`), но в самом пайплайне (бизнес-логике) не описано, как обрабатывается `ON CONFLICT` и что вернёт Registry.
- Пользователь может нажать `approve` на preview, но на full-этапе документ стать дубликатом. В sequence diagram показано, что финальный `is_duplicate=true` возвращает `status: duplicate`, но пользователь уже потратил время на решение, а документ в БД не записан — UX-трагедия и неявный откат.
**Рекомендация:** внести в пайплайн явный шаг «атомарная вставка с проверкой уникальности в рамках транзакции Registry» и описать UX для случая «дубликат обнаружен после approve».

### LP-C4. Отсутствие состояния `discarded` в FSM документа
**Где:** `docs/pipelines/pipeline1-formation.md` (FSM, таблица «Связь состояний черновика с состояниями документа»)
**Факт:**
- Draft FSM содержит терминальное состояние `discarded`.
- Таблица связи утверждает: `discarded` → `failed` / `archived`.
- Но в основном FSM документа (lifecycle) состояние `discarded` отсутствует; есть только `failed`.
**Проблема:** невозможно отличить отклонённый пользователем черновик от технического сбоя.
**Рекомендация:** добавить `discarded` в FSM документа как отдельное терминальное состояние.

## 1.2. Важные проблемы

### LP-V1. Тупиковое состояние `archived` без выхода
**Где:** `docs/pipelines/overview.md` (FSM), `docs/pipelines/pipeline1-formation.md` (FSM)
**Факт:** `review_required --> archived` (таймаут 48ч), `registry --> archived`. Из `archived` в FSM **нет ни одного перехода**. Это тупик.
**Рекомендация:** добавить переход `archived --> uploaded : reprocess` или явно указать, что archived необратимо.

### LP-V2. Статус `partially_indexed` упомянут в тексте, но отсутствует в FSM Пайплайна 2
**Где:** `docs/pipelines/pipeline2-indexation.md` (раздел «Неполная индексация» и FSM)
**Факт:** В тексте: «документ индексируется частично. Пользователь уведомляется через статус документа: `partially_indexed`». В FSM Пайплайна 2 состояний: `pending_index`, `indexing`, `indexed`, `failed` — `partially_indexed` отсутствует.
**Рекомендация:** либо добавить состояние в FSM, либо убрать упоминание `partially_indexed` и оставить `failed` с комментарием.

### LP-V3. `indexed --> failed : Integrity check failed` — не описан механизм
**Где:** `docs/pipelines/pipeline2-indexation.md` (FSM)
**Факт:** В FSM есть переход `indexed --> failed : Integrity check failed`, но в документе нигде не описано, когда и как запускается проверка целостности после перехода в `indexed`.
**Рекомендация:** либо удалить переход, либо описать триггер и алгоритм integrity-check.

### LP-V4. Нет таймаута для состояния `pending` в Пайплайне 3
**Где:** `docs/pipelines/pipeline3-search.md` (раздел «Защита от зависших сообщений»)
**Факт:** Таймауты есть для `enriching` (30с), `searching` (60с), `generating` (180с), `enriching_citations` (30с). Для `pending` (между сохранением сообщения и началом обогащения) таймаут не указан. Если Query Service упал после `INSERT` и до начала обработки, сообщение зависнет.
**Рекомендация:** добавить таймаут `pending` (например, 30 с) и обработку через Scheduler.

### LP-V5. Несоответствие формулы `title_hash_sha256`
**Где:** `docs/pipelines/pipeline1-formation.md`, `docs/database/db_diagrams.md`
**Факт:**
- `pipeline1-formation.md`: `title_hash_sha256` = SHA-256(`era` | `source_type` | `doc_code` | `normalized_title`).
- `db_diagrams.md` (примечания): «Хэш `doc_code + title + era` (вычисляется в Converter)».
**Проблема:** разные формулы дают разные хэши для одного документа.
**Рекомендация:** единообразно зафиксировать формулу во всех документах.

### LP-V6. Отсутствие описания повторного запуска preview / full
**Где:** `docs/pipelines/pipeline1-formation.md`, `docs/pipelines/pipeline1-formation_detail.md`
**Факт:** Не описано, что происходит при повторном вызове `POST /drafts/{draft_id}/preview` (двойной клик пользователя). Нет механизма idempotency-ключа или блокировки.
**Рекомендация:** добавить описание поведения при повторном запуске (409 / игнорирование / перезапуск).

### LP-V7. Пустой документ (0 секций) — обработка описана только в Пайплайне 2, но не в Пайплайне 1
**Где:** `docs/pipelines/pipeline2-indexation.md` (раздел «Обработка пустого документа»)
**Факт:** В Пайплайне 2 сказано, что пустой документ «не может быть завершён» и черновик переводится в `discarded`. Но в Пайплайне 1 (`pipeline1-formation.md`) нет перехода в `discarded` для пустого документа; только `failed`.
**Рекомендация:** синхронизировать обработку пустого документа между пайплайнами.

### LP-V8. Нет указания, кто запускает повторную валидацию (`review_required --> validation`)
**Где:** `docs/pipelines/pipeline1-formation.md` (FSM)
**Факт:** В FSM есть переход `review_required --> validation : повторная валидация`, но не описан триггер (ручной вызов оператором? автоматический? через какой endpoint?).
**Рекомендация:** добавить триггер и API-эндпоинт для повторной валидации.

### LP-V9. Нет поля текущей версии в `registry.documents`
**Где:** `docs/pipelines/pipeline1-formation.md` (раздел «Процесс создания новой версии»), `docs/database/db_diagrams.md`
**Факт:** Пайплайн описывает создание новой версии (`force_new_version`) с записью в `registry.document_versions`, но в `registry.documents` отсутствует поле `current_version_id` или `version_number`. Невозможно понять, какая версия актуальна, не делая подзапрос.
**Рекомендация:** добавить `current_version_id` в `registry.documents` (FK → `document_versions.id`) или хранить актуальный номер версии в documents.

### LP-V10. Противоречие в компенсации Пайплайна 2
**Где:** `docs/pipelines/pipeline2-indexation.md`
**Факт:** С одной стороны, «сохранение чанков и эмбеддингов выполняется в рамках **одной транзакции** БД. Если сбой — транзакция откатывается целиком». С другой стороны, в таблице компенсаций: «Ошибка БД → Компенсация: откат транзакции, **удалить сохранённые чанки**». Если транзакция откатилась, чанков нет — зачем их удалять?
**Рекомендация:** унифицировать описание: либо транзакция покрывает всё (тогда компенсация — только retry), либо чанки сохраняются вне транзакции (тогда нужен явный cleanup).

### LP-V11. Журнал Оркестратора — неотражённое хранилище
**Где:** `docs/pipelines/overview.md` (раздел «Ключевые архитектурные решения»)
**Факт:** «Preview-данные в журнале Оркестратора», «Orchestrator не имеет доступа к БД (кроме пре-стейджа загрузки)». Но в схеме БД (`db_diagrams.md`) нет таблицы для журнала Оркестратора. Получается, либо журнал вне БД (Redis? Файл?), либо противоречие.
**Рекомендация:** явно задокументировать, где физически хранится журнал Оркестратора.

### LP-V12. Несогласованность терминов `duplicate` / `new_version`
**Где:** `docs/pipelines/pipeline1-formation.md` (sequence diagram vs FSM)
**Факт:** В sequence diagram: `status: duplicate`, `status: new_version_created`. В FSM: `duplicate`, `new_version` (без `_created`).
**Рекомендация:** унифицировать названия статусов.

## 1.3. Улучшения

### LP-U1. Не описаны граничные значения (max размер файла, max секций)
**Где:** все пайплайны
**Рекомендация:** добавить лимиты (`max_file_size`, `max_sections_per_document`, `max_content_length`) во входные параметры.

### LP-U2. Не описана идемпотентность `POST /rag/build` при повторном запуске
**Где:** `docs/pipelines/pipeline2-indexation.md`
**Рекомендация:** явно указать, повторный вызов `POST /rag/build` для уже проиндексированного документа — перестроение индекса или 409.

### LP-U3. Не описано поведение при `approve` + повторный `approve` до завершения full-фазы
**Где:** `docs/pipelines/pipeline1-formation.md`
**Рекомендация:** добавить механизм блокировки черновика на время full-фазы.

### LP-U4. Неопределённость алгоритма обогащения цитирований
**Где:** `docs/pipelines/pipeline3-search.md`
**Факт:** «заменить её на вариант с `section_id` через регулярное выражение **или просто дописать** идентификатор». Два разных алгоритма.
**Рекомендация:** зафиксировать один алгоритм.

---

# Часть 2. Проверка схемы данных (п.3 check_rule.md)

## 2.1. Ошибки

### DB-E1. Перечислимые типы без CHECK / ENUM (повтор из db_audit_report.md, подтверждаю)
**Где:** `docs/database/db_diagrams.md`, `docs/database/db_audit_report.md` (DB-E1)
**Факт:** Поля `source_type`, `document_type`, `era`, `validity_status`, `jurisdiction`, `processing_status`, `reference_type`, `current_status`, `status` (projects, messages), `role`, `strategy` объявлены как `varchar`/`text` без CHECK/ENUM.
**Проверка по check_rule.md:** «использование ENUM» — отсутствует. «Значения по умолчанию» — не указаны. «NOT NULL» — не указан явно для многих.

### DB-E2. Хэш-поля как `text` вместо `CHAR(64)` (DB-E2)
**Где:** `docs/database/db_diagrams.md` — `registry.documents.file_hash_sha256`, `title_hash_sha256`; `registry.document_versions.file_hash_sha256`
**Факт:** SHA-256 — ровно 64 hex-символа. `text` допускает любую длину.

### DB-E3. `chat.sessions.document_ids` — массив `bigint[]`, нарушение 1НФ (DB-E3)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Массив ID документов в сессии. Невозможен эффективный поиск «все сессии с документом X».

### DB-E4. Отсутствие UNIQUE-ограничений для бизнес-ключей (DB-E4)
**Где:** `docs/database/db_diagrams.md`, `docs/database/db_audit_report.md`
**Факт:** Нет UNIQUE на:
- `registry.documents` — `(doc_code, era)`, `file_hash_sha256`
- `registry.document_sections` — `(document_id, path)`
- `registry.document_versions` — `(document_id, version_number)`
- `registry.document_chunks` — `(section_id, chunk_index)`
- `chat.projects` — `code`

### DB-E5. Отсутствие ON DELETE / ON UPDATE для всех FK (DB-E5)
**Где:** `docs/database/db_diagrams.md`
**Факт:** В ER-диаграмме не указаны правила каскадного удаления. По умолчанию — `NO ACTION` (эквивалент `RESTRICT`). Удаление документа заблокировано секциями, чанками, ссылками, историей.

### DB-E6. `chat.sessions.user_id` — phantom FK (DB-E6)
**Где:** `docs/database/db_diagrams.md`
**Факт:** FK `user_id -> auth.users.id`, но таблицы `auth.users` в схеме нет.

### DB-E7. Отсутствие индексов для часто запрашиваемых полей (DB-E7)
**Где:** `docs/database/db_diagrams.md`
**Факт:** В ER-диаграмме указаны только 5 индексов. Нет индексов на `doc_code`, `path` (GiST ltree), `target_doc_code`, `(session_id, created_at)` и др.

### DB-E8. Отсутствие `updated_at` в критичных таблицах — противоречие в документации
**Где:** `docs/database/db_diagrams.md` (ER-диаграмма) vs `docs/database/db_audit_report.md` (DB-E9)
**Факт:**
- ER-диаграмма показывает `updated_at` в `registry.document_sections`, `registry.document_references`, `registry.document_chunks`.
- `db_audit_report.md` утверждает, что `updated_at` **отсутствует** в этих таблицах.
**Проблема:** невозможно понять, какая версия схемы актуальна.

### DB-E9. Отсутствие soft-delete
**Где:** `docs/database/db_diagrams.md`
**Факт:** Нигде нет `deleted_at`. Для реестра нормативных документов физическое удаление недопустимо.

### DB-E10. Отсутствие таблицы `users` при наличии FK (DB-E11)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `chat.sessions.user_id` ссылается на `auth.users.id`, таблица не описана.

### DB-E11. `document_sections.content` — JSONB без GIN-индекса (DB-E12)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Поле `content` гетерогенное (разная структура для text/table/image/formula). GIN-индекс не указан, хотя в примечаниях сказано «GIN» для `content` в одном месте, но в ER-диаграмме это поле `document_sections.content` без индекса, а GIN указан только для `registry.document_sections.content` в таблице индексов с примечанием `content.amendments[].type`. Однако в списке индексов ER-диаграммы `document_sections` — `content` GIN. Но в `db_audit_report.md` DB-E12 утверждает, что GIN отсутствует. **Противоречие внутри документации.**

## 2.2. Предупреждения

### DB-W1. `float` для `confidence` — избыточен (W1)
**Где:** `docs/database/db_diagrams.md` — `rag.document_chunks.confidence`
**Факт:** `float` (8 байт) для значения 0..1. `real` (4 байта) достаточно. Нет CHECK `BETWEEN 0 AND 1`.

### DB-W2. Отсутствие DEFAULT у счётчиков (W2)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `chunk_count`, `is_resolved`, `message_count`, `processing_time_ms` без DEFAULT. При INSERT — NULL.

### DB-W3. `document_sections.content` — JSONB без схемы (W3)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Разные структуры под одним полем. Нет JSON Schema валидации на уровне БД.

### DB-W4. `document_snapshot` — неограниченный JSONB (W4)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Полный слепок документа на каждое событие. Может занимать мегабайты на строку.

### DB-W5. `format_code` + `format_label` — частичная функциональная зависимость (W5)
**Где:** `docs/database/db_diagrams.md` — `registry.document_versions`
**Факт:** `format_label` определяется `format_code`.

### DB-W6. Нет составного индекса для диапазонных запросов по дате (W6)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `adoption_date`, `effective_from` — частые фильтры в реестре.

### DB-W7. Нет CHECK на положительность счётчиков (W8)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `chunk_count`, `message_count`, `processing_time_ms`, `file_size_bytes`, `version_number` — могут быть отрицательными.

### DB-W8. Денормализация `document_chunks.document_id` (DB-E8)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Поле дублирует `document_sections.document_id`. Риск рассинхронизации.

### DB-W9. `chat.sessions.message_count` без механизма синхронизации (W9)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Денормализованный счётчик. Нет триггера или описания обновления.

### DB-W10. `chat.messages.sources` — JSONB вместо таблицы (W10)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Затрудняет агрегацию и ссылочную целостность.

### DB-W11. Несогласованность именования timestamp-полей (W12)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `uploaded_at` (document_versions), `event_at` (document_history) вместо `created_at`/`updated_at`.

### DB-W12. Несогласованность полей «кто изменил» (W13)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `created_by`/`updated_by` (documents), `uploaded_by` (versions), `changed_by` (history).

### DB-W13. Несогласованность полей «статус» (W14)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `validity_status`, `processing_status`, `current_status`, `status` — разные суффиксы для одной семантики.

### DB-W14. Разные стили FK-наименования (W15)
**Где:** `docs/database/db_diagrams.md`
**Факт:** `source_document_id` vs `successor_doc_id`/`predecessor_doc_id` vs `resolved_document_id`.

### DB-W15. `document_versions.updated_at` — противоречие
**Где:** `docs/database/db_diagrams.md` vs `docs/database/db_audit_report.md` (DB-E9)
**Факт:** ER-диаграмма показывает `updated_at`; аудит утверждает, что его нет.

### DB-W16. Таблица `pipeline.drafts` не отражена в ER-диаграмме (W17)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Таблица описана в `db_diagrams.md` (примечания), но в ER-диаграмме отсутствует.

## 2.3. Предложения

### DB-S1. `adoption_date` / `effective_from` — подтвердить тип `date` (S1)
**Где:** `docs/database/db_diagrams.md`
**Факт:** В JSON-схемах даты без времени. Тип `date` корректен, если нет времени.

### DB-S2. `replaces` + `predecessor_doc_id` — задокументировать семантику (S2)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Два поля для одной связи. Рекомендуется чётко разделить: текст для человека, FK для машины.

### DB-S3. Нормализация `issuing_body` и `group` (S6)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Повторяющиеся строки. Lookup-таблицы сократят объём.

### DB-S4. Единый справочник `document_type` + `source_type` (S7)
**Где:** `docs/database/db_diagrams.md`
**Факт:** Похожие перечисления. Можно объединить или вынести в отдельные таблицы.

### DB-S5. Частичные индексы для FSM-фильтров (S4)
**Где:** `docs/database/db_diagrams.md`
**Рекомендация:** `WHERE processing_status IN ('uploaded', 'previewing', 'pending_index')`.

### DB-S6. Партиционирование для высоконагруженных таблиц (W18)
**Где:** `docs/database/db_diagrams.md`
**Рекомендация:** `document_history`, `document_chunks`, `messages`.

### DB-S7. HNSW вместо IVFFlat на старте (W19)
**Где:** `docs/database/db_diagrams.md`
**Факт:** IVFFlat требует ~1000 векторов для обучения. На старте лучше HNSW.

### DB-S8. COVERING-индексы (W20)
**Где:** `docs/database/db_diagrams.md`
**Рекомендация:** `(processing_status, era) INCLUDE (doc_code, title)` и др.

### DB-S9. Таблица `terminology` (W11)
**Где:** `docs/schema/schema_converter_result.json`, `docs/schema/schema_registry_for_rag.json`
**Факт:** Массив `terminology` есть в JSON, но нет таблицы в БД.

---

# Перекрёстные несоответствия (Пайплайны ↔ Схема данных)

| # | Проблема | Критичность | Источники |
|---|----------|-------------|-----------|
| X1 | `document_id` назначается в разных местах (Converter vs Registry) | **Критично** | `overview.md`, `pipeline1-formation.md`, `pipeline1-formation_detail.md` |
| X2 | `title_hash_sha256` — разные формулы в пайплайне и ER-диаграмме | **Важно** | `pipeline1-formation.md`, `db_diagrams.md` |
| X3 | `partially_indexed` — есть в тексте пайплайна 2, нет в FSM и в БД | **Важно** | `pipeline2-indexation.md` |
| X4 | `discarded` (draft) → `failed` (document) — потеря семантики | **Важно** | `pipeline1-formation.md` |
| X5 | Журнал Оркестратора не отображён в схеме БД, но упомянут в архитектуре | **Важно** | `overview.md`, `db_diagrams.md` |
| X6 | `document_versions` — нет связи `documents.current_version_id` | **Важно** | `pipeline1-formation.md`, `db_diagrams.md` |
| X7 | `terminology` есть в JSON-схемах, нет в БД | **Предупреждение** | `schema_converter_result.json`, `db_diagrams.md` |
| X8 | `amendments` — в JSON вложены, в БД нет отдельной таблицы | **Предупреждение** | `schema_converter_result.json`, `db_diagrams.md` |

---

# Итоговая сводка

## Пайплайны
| Уровень | Количество | Примеры |
|---------|------------|---------|
| **КРИТИЧНО** | 4 | LP-C1 (потеря бинарных объектов), LP-C2 (владелец document_id), LP-C3 (неатомарность uniqueness), LP-C4 (отсутствие discarded в FSM) |
| **ВАЖНО** | 12 | LP-V1..LP-V12 |
| **УЛУЧШЕНИЕ** | 4 | LP-U1..LP-U4 |

## Схема данных
| Уровень | Количество | Примеры |
|---------|------------|---------|
| **ОШИБКА** | 11 | DB-E1..DB-E11 (ENUM, хэши как text, 1НФ, UNIQUE, ON DELETE, phantom FK, индексы, противоречие updated_at, soft-delete, GIN) |
| **ПРЕДУПРЕЖДЕНИЕ** | 16 | DB-W1..DB-W16 (float, DEFAULT, JSONB без схемы, денормализация, именование) |
| **ПРЕДЛОЖЕНИЕ** | 9 | DB-S1..DB-S9 (lookup-таблицы, партиционирование, HNSW, COVERING, terminology) |

## Рекомендуемые следующие шаги
1. Срочно: устранить противоречия в назначении `document_id` и формуле `title_hash_sha256`.
2. Срочно: решить вопрос с сохранением бинарных объектов в preview (LP-C1).
3. Важно: внести `discarded` и `partially_indexed` в FSM; добавить таймаут `pending` в Pipeline 3.
4. Важно: синхронизировать ER-диаграмму с `db_audit_report.md` по полям `updated_at` и GIN-индексам.
5. Провести DDL-миграцию: ENUM/CHECK, UNIQUE, ON DELETE, DEFAULT, soft-delete (`deleted_at`).
