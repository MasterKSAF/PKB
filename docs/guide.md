# Guide — архитектурные решения и стиль

## Нейминг: `notifications` вместо `warnings` и `issues`

**Дата:** 18.06.2026
**Решение:** P3-5 (`quality.warnings[]`) и P12-3 (`quality.issues[]`) схлопнуты в единый массив `quality.notifications[]`.

**Обоснование:**
- Оба массива адресованы оператору (человеку за UI) — сервисы лишь передают данные, потребитель один.
- Нет технической причины разделять security-предупреждения и замечания по качеству: и те и другие — уведомления оператору.
- Единый массив упрощает контракт и UI (один рендер, одна фильтрация).
- Система новая, истории миграций нет — таблица БД с самого начала называется `pipeline.draft_notifications`.

**Структура:**
```json
{
  "code": "EMBEDDED_JS",
  "severity": "info | warning | error | critical",
  "category": "security | quality",
  "message": "human readable",
  "location": {"page": 1, "block": 5},
  "suggested_action": "reprocess | manual_edit | review | ignore | null"
}
```

**БД:** `pipeline.draft_notifications` (единая таблица, `category` разводит типы).

**P3-5 поглощён P12-3:** отдельный `warnings[]` не создаётся, security-предупреждения пишутся в `notifications[]` с `category: "security"`.

---

## Чеклист синхронизации при правках

При любом изменении статусной модели, enum-значений, полей БД или формата ответов API — обязательно проверить все точки, где эти значения перечислены.

**Конвенция регистра enum-значений:**
- `source_type`, `era`, `jurisdiction` — **UPPERCASE** (аббревиатуры и коды: `GOST`, `RMRS`, `USSR`, `RU`). Канонический регистр задан в `/registry/enums`.
- `document_type`, `validity_status` — строчные (`normative`, `technical`, `active`, `superseded`). Это слова, а не коды.
- Исключение — `normalizer_specification.md`: нормализатор приводит `source_type` к нижнему регистру для вычисления бизнес-ключа (осознанное решение для единообразия хеша).

DB CHECK-ограничения, DDL-миграции и спецификации должны использовать тот же регистр, что и API.

### При изменении FSM / добавлении статуса черновика

- [ ] `orchestrator_service_api.md` — поле `status` в `GET /drafts` (список enum)
- [ ] `orchestrator_service_api.md` — параметр фильтра `?status=`
- [ ] `orchestrator_service_api.md` — `PATCH /decide`: условие доступности действия
- [ ] `pipeline1-formation.md` — основная FSM-таблица (состояния)
- [ ] `pipeline1-formation.md` — упрощённая Draft FSM-таблица
- [ ] `pipeline1-formation.md` — FSM-диаграмма (mermaid)
- [ ] `gateway_service_api.md` — таблица ошибок: коды `DRAFT_ALREADY_DECIDED`
- [ ] `gateway_service_api.md` — RBAC и описание в route table
- [ ] `db_diagrams.md` — примечание о статусах черновика (если есть)
- [ ] `specificity.md` — зафиксировать изменение как решённое (при закрытии аномалии)

### При изменении enum-значения (source_type, era и т.п.)

- [ ] `registry_service_api.md` — `/registry/enums` (актуальный список, канонический регистр — UPPERCASE)
- [ ] `db_diagrams.md` — примечание enum в разделе `registry.documents`
- [ ] `db_diagrams.md` — CHECK-ограничение (регистр должен совпадать с API)
- [ ] `ddl_migrations_17_06.md` — DDL-Migration (список значений)
- [ ] `converter_validator_service_api.md` — `POST /converter/preview` (поле `source_type`)
- [ ] `converter_specification.md` — шаг 5 (классификация), если enum упомянут
- [ ] `glossary.md` — определение термина (если enum перечислен)
- [ ] `orchestrator_service_api.md` — `POST /drafts` (поле `source_type` обязательно при загрузке)
- [ ] Все JSON-примеры — содержат ли новое значение (если уместно)

### При добавлении поля в API-ответ/запрос

- [ ] Gateway route table — отражено ли изменение в описании эндпоинта
- [ ] Gateway sequence diagram — нужен ли новый шаг / нота
- [ ] Orchestrator API — описание поля и его тип
- [ ] Registry API (если applicable) — internal-эндпоинт
- [ ] Registry API модель 5.4 (registry_document) — добавлено ли поле в таблицу модели?
- [ ] `db_diagrams.md` — ER-диаграмма и примечание (если поле меняет БД)
- [ ] JSON-примеры — обновлены
- [ ] Если поле меняет lifecycle — проверен FSM и его документация

### При изменении модели данных (БД)

- [ ] `registry_service_api.md` 5.4 (registry_document) — все ли поля из ER-диаграммы `db_diagrams.md` отражены в модели?
- [ ] `db_diagrams.md` CHECK-ограничения — совпадают ли с enum в `/registry/enums` и DDL-миграциях?
- [ ] Регистр значений: DB CHECK должен совпадать с API (UPPERCASE). Исключение — нормализатор (lowercase для хеша)

### При изменении точек входа Gateway

- [ ] `gateway_service_api.md` — таблица маршрутизации (префикс, сервис, порт)
- [ ] `gateway_service_api.md` — секция read-only контракта (если admin-эндпоинт)
- [ ] `gateway_service_api.md` — секция middleware / заголовков (если новый заголовок)
- [ ] `gateway_service_api.md` — таблица специфичных ошибок

---

## Маппинг статусных моделей

**Дата:** 19.06.2026

В системе три разные статусные модели, которые ссылаются друг на друга:

| Модель | Документ | Статусы | Назначение |
|--------|----------|---------|-----------|
| `task.status` | `orchestrator_service_api.md` | `uploaded`, `previewing`, `ready_for_approve`, `processing`, `created`, `indexing`, `indexed`, `failed` | Статус сквозной задачи пайплайна (`pipeline.tasks`). Агрегирует все этапы обработки одной загрузки |
| `draft.status` | `orchestrator_service_api.md`, `pipeline1-formation.md` | `uploaded`, `previewing`, `ready_for_approve`, `review_required`, `validation`, `approved`, `discarded` | Статус черновика (`registry.drafts`). Отражает жизненный цикл черновика от загрузки до принятия решения |
| `document.processing_status` | `pipeline2-indexation.md`, `db_diagrams.md` | `pending_index`, `indexing`, `indexed`, `failed` (+ `partially_indexed` в тексте) | Статус индексации документа (`registry.documents.processing_status`). Отражает состояние Пайплайна 2 |

**Связь моделей:**
- `task.status` — сквозной агрегатор, покрывает все этапы (preview + full + registry + indexation)
- `draft.status` — покрывает только Пайплайн 1 (до `approved`/`discarded`)
- `document.processing_status` — покрывает только Пайплайн 2 (после `created`)

После `approved` → создаётся документ, начинается Пайплайн 2:
`task.status = "indexing"` → `document.processing_status = "indexing"` (одновременно).

`partially_indexed` — не выделен в отдельный FSM-статус, но фиксируется в `processing_status` при `chunk_count_actual < chunk_count_expected`. См. LP-V2.

---

## Health-формат: внутренние сервисы vs Gateway

**Дата:** 19.06.2026

В системе два разных health-эндпоинта:

| Тип | Путь | Формат | Где описан |
|-----|------|--------|-----------|
| **Внутренние сервисы** (Orchestrator, Registry, Auth, Query) | `GET /api/v1/health` | `status`, `version`, `service` | `common_api.md` (эталон) |
| **Gateway (внешний мониторинг)** | `GET /api/v1/system/health` | `status`, `version`, `services{}`, `timestamp`, `endpoints_total` | `gateway_service_api.md` |

**Правила:**
1. Все внутренние сервисы возвращают **одинаковый** минимальный набор: `status`, `version`, `service`.
2. Gateway не проксирует health внутренних сервисов — у него собственный сводный health.
3. `uptime_seconds`, `database`, `search_index`, `ocr_queue`, `storage` — **НЕ входят** в health внутренних сервисов. Это метрики, а не health. Они должны быть в `/api/v1/monitor/metrics` (Gateway) или в отдельном debug-эндпоинте.
4. При добавлении нового внутреннего сервиса — health эндпоинт должен соответствовать формату common_api.md.

---

## Редактирование сообщений не поддерживается

**Дата:** 20.06.2026

Редактирование сообщений в чате **не реализуется**. Причина: ответ ассистента строится на основе всей предшествующей истории сессии. Если пользователь изменит ранее отправленное сообщение, контекст нарушается и ответ ассистента становится устаревшим/некорректным.

Вместо редактирования:
- Пользователь может отправить новое сообщение с уточнением/исправлением
- При необходимости — удалить сессию целиком (hard-delete) и начать новую

---

## Бизнес-ключ вычисляет только Converter-validator

**Дата:** 20.06.2026
**Решение:** Converter-validator — единственная точка вычисления `title_hash_sha256` и `title_key`.

**Обоснование:**
- Нормализатор (нормализация названия, терминологический реестр, детект аватаров, приведение регистра) — компонент Converter-validator. Оркестратор **не имеет** собственного нормализатора.
- `POST /drafts` не возвращает бизнес-ключ — он будет вычислен на этапе preview.
- `PATCH /drafts/{id}/metadata` и `metadata_overrides` в `PATCH /decide` отправляются в Converter-validator (`POST /validate/metadata`) для пересчёта бизнес-ключа и нормализации.
- Registry проверяет уникальность (`check-uniqueness`), но не вычисляет бизнес-ключ.

**Затронутые сервисы:**
- Converter-validator: endpoint `POST /validate/metadata` — единая точка входа для пересчёта.
- Orchestrator: удалена локальная логика вычисления бизнес-ключа.

**Контракт:**
```
POST /validate/metadata
Вход: метаданные (era, source_type, mks_oks_code, okstu_code, doc_code, title)
Выход: title_hash_sha256, title_key, normalized_title
```

---

## Разграничение ответственности Orchestrator vs Registry

**Дата:** 23.06.2026

В системе действует строгое разделение: **Registry — только данные, Orchestrator — только пайплайн**.

### Принцип

| Сервис | Отвечает за | Операции | БД |
|--------|------------|----------|-----|
| **Registry** | Данные реестра | CRUD `registry.*` (чтение и безопасная запись) | `registry.drafts`, `registry.documents`, `registry.document_*`, `registry.classifier_*`, `registry.terminology`, `registry.categories` |
| **Orchestrator** | Пайплайн обработки | Управление задачами (`pipeline.*`), координация сервисов, FSM черновиков и статус обработки документов | `pipeline.tasks`, `pipeline.task_steps`, `pipeline.draft_notifications` |
| **Gateway** | Маршрутизация + RBAC + иденпотентность | Прокси: чтение Registry напрямую, пайплайн — в Orchestrator | — |

### Registry — что через Gateway напрямую

Чтение черновиков и документов (и их связных сущностей) — Registry. Gateway проксирует напрямую без участия Orchestratorа:

```
GET    /api/v1/drafts
GET    /api/v1/drafts/{id}
GET    /api/v1/drafts/{id}/preview

GET    /api/v1/documents
GET    /api/v1/documents/{id}
GET    /api/v1/documents/{id}/sections
GET    /api/v1/documents/{id}/pages/*
GET    /api/v1/documents/{id}/file
GET    /api/v1/documents/{id}/history
GET    /api/v1/documents/{id}/parameters
GET    /api/v1/documents/{id}/versions
GET    /api/v1/documents/{id}/succession
PUT    /api/v1/documents/{id}
PATCH  /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
GET    /api/v1/documents/search
POST   /api/v1/documents/search
GET    /api/v1/documents/export
POST   /api/v1/documents/import
POST   /api/v1/documents/check-uniqueness
```

### Orchestrator — что через Gateway

Операции, связанные с пайплайном, FSM и управлением жизненным циклом:

```
# Draft lifecycle (запись черновика ТОЛЬКО через Orchestrator)
POST   /api/v1/drafts
POST   /api/v1/drafts/{id}/preview
PATCH  /api/v1/drafts/{id}/decide
PATCH  /api/v1/drafts/{id}/metadata
DELETE /api/v1/drafts/{id}

# Document lifecycle (запись только через Orchestrator)
POST   /api/v1/documents/{id}/versions
POST   /api/v1/documents/{id}/reprocess

# Pipeline status
GET    /api/v1/documents/{id}/status
GET    /api/v1/documents/queue
GET    /api/v1/documents/{id}/errors

# Task links (связь данных Registry с задачами Orchestratorа)
GET    /api/v1/drafts/{id}/tasks
GET    /api/v1/documents/{id}/tasks

# Task monitoring (admin)
GET    /api/v1/tasks
GET    /api/v1/tasks/stats
GET    /api/v1/tasks/{task_id}/status
GET    /api/v1/tasks/{task_id}/steps
GET    /api/v1/tasks/{task_id}/notifications (если есть)
```

### Registry — internal endpoint'ы (только для Orchestrator, не через Gateway)

Следующие эндпоинты Registry закрыты от Gateway. Их вызывает только Orchestrator для координации:

| Метод | Эндпоинт | Когда вызывается |
|-------|----------|-----------------|
| `POST` | `/registry/drafts` | `POST /drafts` — создать запись черновика |
| `PATCH` | `/registry/drafts/{id}/status` | `PATCH /decide`, `POST /preview` — смена статуса |
| `PATCH` | `/registry/drafts/{id}/metadata` | `PATCH /metadata` — обновление метаданных |
| `DELETE` | `/registry/drafts/{id}` | `DELETE /drafts/{id}` — удаление черновика |
| `POST` | `/registry/documents` | `PATCH /decide action:approve` — создание документа |
| `PATCH` | `/registry/documents/{id}/status` | Завершение Pipeline 2 — обновление статуса |

### Правило для разработки

1. **Чтение — Registry.** Если endpoint читает данные из `registry.*` — он идёт напрямую в Registry. Gateway проксирует без участия Orchestratorа.
2. **Пайплайн — Orchestrator.** Если endpoint создаёт/читает `pipeline.*` или управляет FSM — он идёт в Orchestrator.
3. **Связь — Orchestrator.** `GET /{drafts,documents}/{id}/tasks` — всегда Orchestrator, т.к. `pipeline.tasks` принадлежит ему.
4. **Запись черновиков и документов — только через Orchestrator.** Registry не имеет публичных write-эндпоинтов для `registry.drafts` и `registry.documents` (кроме PUT/PATCH для редактирования полей). Создание и смена статуса — только через Orchestrator.
5. **Gateway — только маршрутизация.** Gateway не обогащает ответы. Если UI нужны связанные данные (черновик + задачи), он делает два запроса.

---

## Рабочие практики

- **Кэш перед чтением.** Перед `read_file` проверять, загружен ли файл в кэш текущей сессии. Повторное чтение уже загруженных файлов — потеря токенов и времени. Исключение — если файл гарантированно изменился между сессиями.

## Правило `resolved` в specificity.md

Статус `✅ resolved` проставляется ТОЛЬКО после выполнения всех условий:
1. Все затронутые файлы перечислены в записи аномалии
2. По каждому файлу внесена правка (подтверждено diff-ом)
3. Запущен `check_cross_references.py` — все проверки пройдены
4. Если поле добавлено/изменено — обновлён `_data_dictionary.md`
5. Если схема изменена — обновлён `_schemas.md`

Без выполнения любого из пунктов — статус остаётся `🔄 исправляется` или `📝 спеки`.

---

## Правило: не дублировать схемы

Повторяющиеся структуры данных (PreviewMetadata, DraftItem, DecideResponse) **не должны дублироваться** в API-спеках и пайплайнах.

- **Source of truth:** `docs/api/_schemas.md`.
- **В таблицах:** вместо перечисления всех полей — ссылка `см. [_schemas.md](_schemas.md#PreviewMetadata)`.
- **В JSON-примерах:** вместо полного JSON с 17 полями — `{ /* см. _schemas.md#PreviewMetadata */ }`.
- **Исключение:** уникальные поля, специфичные для конкретного эндпоинта, могут описываться отдельно.

Нарушение правила — **CRITICAL** при code review.

---

## Стиль оформления документации

- Таблицы API: столбцы `Поле | Тип | Описание`. Тип — краткий (string, int, object, array).
- Ссылки на P#-задачи: `**P#**` в тексте.
- Ссылки на файлы: полный относительный путь от `docs/`.
- DDL-миграции описываются в табличном/списочном виде, без SQL-кода. CHECK-ограничения, FK, индексы — списком или таблицей. Для DBA эквивалентный SQL восстанавливается из описания однозначно (см. `docs/database/ddl_migrations_17_06.md`).

## Infinity: optimum + CPUExecutionProvider

Для реранкинга используется Infinity (`michaelf34/infinity:latest`, не `latest-cpu`).

**Параметры запуска:**
- `--engine optimum` — ONNX Runtime от Microsoft
- `--device cpu` — принудительно CPUExecutionProvider (OpenVINO EP несовместим с DynamicQuantizeMatMul в quantized ONNX)
- `--model-id onnx-community/bge-reranker-v2-m3-ONNX` — bge-reranker-v2-m3 в ONNX формате
- `--batch-size 4` — пиковое потребление ~3-5 GB

**Volume:** `huggingface_cache:/app/.cache` — кеш модели персистентный.

**Связь:** сервисы через Docker DNS `http://infinity:80`.


## Конвенция нейминга полей

| Суффикс | Семантика | Тип | Описание |
|---------|-----------|-----|----------|
| `_at` | Момент времени | `datetime` | Время события. Формат ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`). Примеры: `created_at`, `updated_at`, `started_at`, `completed_at`, `decided_at`, `deleted_at`, `checked_at` |
| `_by` | Субъект действия | `string` | Субъект (пользователь или сервис). Примеры: `created_by`, `updated_by`, `decided_by`, `changed_by`, `initiated_by` |

**Правила:**
1. Поля с суффиксом `_at` — всегда `datetime`, описание заканчивается на `(ISO 8601)`.
2. Поля с суффиксом `_by` — всегда `string`, описание: «Субъект (пользователь или сервис)».
3. Если поле содержит не время/не субъекта — суффикс не используется (`timestamp` — отдельное поле, не `_at`).
