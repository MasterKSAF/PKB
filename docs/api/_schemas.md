# Общие схемы данных (Source of Truth)

> Повторяющиеся схемы, на которые ссылаются API-спеки и пайплайны.
> **Единый источник.** При изменении поля — править только здесь, в спецификациях — ссылка.

---

## PreviewMetadata

Извлекается Converter-validator на этапе preview. Возвращается во всех ответах, содержащих метаданные черновика.

| Поле | Тип | Описание |
|------|-----|----------|
| `doc_code` | string \| null | Регистрационный номер документа (напр. `20868-81`) |
| `title` | string \| null | Название документа |
| `mks_oks_code` | string \| null | Код МКС/ОКС |
| `okstu_code` | string \| null | Код ОКСТУ |
| `udk_code` | string \| null | Код УДК |
| `pkb_codes` | array[string] | Коды предметных областей ПКБ |
| `document_type` | string \| null | Тип документа: `normative`, `technical`, `drawing`, `specification`, `archival_scan` |
| `year` | int \| null | Год издания/утверждения |
| `era` | string \| null | Эра: `USSR`, `CIS`, `RF`, `CURRENT` |
| `validity_status` | string \| null | Юридический статус: `active`, `superseded`, `cancelled`, `historical`, `draft` |
| `issuing_body` | string \| null | Организация-издатель |
| `jurisdiction` | string \| null | Юрисдикция: `RU`, `EU`, `US`, `NO`, `INTL` |
| `source_type` | string \| null | Тип источника: `GOST`, `GOST_R`, `OST`, `RD`, `TU`, `ISO`, `DNV`, `ASTM`, `RMRS`, `OTHER` |
| `language` | string \| null | Язык документа (`ru`, `en`) |
| `title_hash_sha256` | string | SHA-256 бизнес-ключа (6-польная формула) |
| `title_key` | string | Исходная строка конкатенации для аудита |

**Используется в:**
- `orchestrator_service_api.md` — GET /drafts (items.preview_metadata), GET /drafts/{id} (preview_metadata)
- `registry_service_api.md` — GET /registry/drafts, GET /registry/drafts/{id}
- `converter_validator_service_api.md` — POST /converter/preview/metadata
- `pipeline1-formation.md` — пример Preview-фазы

---

## DraftItem

Элемент списка черновиков. Публичный API (Orchestrator) расширяет базовый набор Registry.

### Registry internal (базовый)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | bigint | ID черновика |
| `file_key` | string | Ссылка на файл в MinIO |
| `document_key` | string | Бизнес-ключ документа (SHA-256 содержимого) |
| `status` | string | Статус черновика |
| `confidence` | float \| null | Оценка качества распознавания (0..1) |
| `preview_metadata` | object | PreviewMetadata |
| `created_by` | string | Создатель (сервис или пользователь) |
| `created_at` | string | Время создания (ISO 8601) |

### Orchestrator (публичный, расширенный)

Включает все поля Registry + добавляет:

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | Маппинг из Registry `id` |
| `task_id` | bigint | ID задачи пайплайна |
| `document_id` | bigint \| null | ID документа в Registry |
| `has_notifications` | bool | Есть ли уведомления |
| `critical_count` | int | Количество critical-уведомлений |
| `error_code` | string \| null | Код ошибки при `discarded` |
| `error_message` | string \| null | Описание ошибки |
| `updated_at` | string | Время обновления (ISO 8601) |

---

## DecideResponse

Ответ на PATCH /drafts/{draft_id}/decide.

| Поле | Тип | Описание |
|------|-----|----------|
| `draft_id` | bigint | ID черновика |
| `status` | string | Новый статус: `approved`, `validation`, `discarded` |
| `action` | string | Выполненное действие: `approve`, `confirm`, `reject` |
| `document_id` | bigint \| null | ID документа в Registry |
| `message` | string | Описание результата |
| `decided_by` | string | Кто принял решение |
| `decided_at` | string | Время решения (ISO 8601) |

---

## SearchResultItem

Элемент результатов поиска документов.

| Поле | Тип | Описание |
|------|-----|----------|
| `document_id` | bigint | ID документа в Registry |
| `title` | string | Название документа |
| `doc_code` | string \| null | Код документа |
| `source_type` | string | Тип источника |
| `era` | string | Эра |
| `score` | float | Релевантность (0..1) |
| `fragments` | array[SearchResultFragment] | Совпадающие фрагменты |

### SearchResultFragment

| Поле | Тип | Описание |
|------|-----|----------|
| `page` | int | Номер страницы |
| `section_id` | bigint | ID секции |
| `content` | string | Текст фрагмента |
| `score` | float | Релевантность фрагмента |
