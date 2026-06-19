# Specificity — аномалии и трудные моменты

> Только то, что **не решено**, **не очевидно** или **требует внимания**.

---

## 🟡 Открытые вопросы

### A25. `project_id` в `POST /chat/sessions` — mock не принимает

В `query_service_api.md` поле `project_id` есть в запросе `POST /chat/sessions` (обязательное, bigint), но свежий mock Gateway `CreateSessionRequest` его не принимает. UI отправляет `project_id`, но mock не связывает сессию с проектом. См. подробный разбор в `docs/audit/ui_gateway_sync_analysis.md` (2.1).

**Решение:** `project_id` объявлено обязательным полем в документации. Ожидается синхронизация mock Gateway.

### A26. `GET /chat/projects` возвращает пустой список

Без seed/project data дерево проектов в UI показывает только fallback «Рабочие диалоги». Проекты создаются через `POST /chat/projects` (UI). См. `docs/audit/ui_gateway_sync_analysis.md` (2.2).

**Решение:** уточнено в документации. Ожидается seed-данные или создание проектов через UI.

### A27. `POST /chat/feedback` — рассогласование типа `rating`

Документация описывает `rating: "positive" | "negative" | "neutral"`, mock Gateway принимает числовой `rating`. UI оставлен на числовом варианте.

**Решение:** контракт приведён к двум полям: `rating` (int, 1–5) + `rating_status` (string: positive/negative/neutral). Добавлен код ответа 422 для невалидных значений. См. `query_service_api.md`.

### A28. `GET /chat/history/export` — URL возвращает 404

Gateway возвращал объект с `url`, но GET по этому URL возвращал 404. UI сделал локальный CSV-fallback.

**Решение:** контракт изменён — файл возвращается потоком (stream) напрямую, без промежуточного URL. См. `query_service_api.md`.

### A29. Канонический Gateway-путь для классификаторов не зафиксирован

В Gateway routing table есть `/classifiers/*`, в registry docs — `/registry/classifiers/tree`. UI пробовал сначала `/classifiers/tree`, затем fallback `/registry/classifiers/tree`.

**Решение:** зафиксирован единый принцип: все пути Registry содержат префикс `/registry/` (`/registry/classifiers/*`, `/registry/terminology/*` и т.д.). Gateway маршрутизирует `/api/v1/registry/*` в Registry Service. Добавлен принцип категоризации путей в Gateway. См. `gateway_service_api.md`, `registry_service_api.md`.

### A30. Mock-данные Registry и Classifiers не синхронизированы

Классификатор MKS «47 / Судостроение», а у seed-документа `mks_oks_code: 31.240`. Из-за этого в разделе «Судостроение» документов 0. UI корректен, но проверить полный UX невозможно. См. `docs/audit/ui_gateway_sync_analysis.md` (2.7).

**Решение:** добавить второй seed-документ с реальным кодом `mks_oks_code: 47.020` (Судостроение → Конструкция корпуса). Классификатор не изменять — он системный, коды извлекаются из документов.

### A31. Server-side upload-by-url — нет endpoint

Сейчас `POST /drafts` только для файла (multipart). Для загрузки по ссылке UI использует client-side сценарий. См. `docs/audit/ui_gateway_sync_analysis.md` (2.8).

**Решение:** не в MVP. Загрузка только с ПК пользователя через `POST /drafts`. Server-side upload-by-url отложен.

### A32. Публичный контракт для pipeline artifacts/logs не определён

Маршрут `/api/v1/tasks/*` помечен как internal, но UI использует его для админ-мониторинга. Фактически endpoint работает и возвращает данные, передаваемые между сервисами. См. `docs/audit/ui_gateway_sync_analysis.md` (2.9).

**Решение:** зафиксирован публичный контракт:
- `GET /tasks/{task_id}/status` — статус и метаданные пайплайна
- `GET /tasks/{task_id}/steps` — поэтапный лог шагов
- `GET /drafts/{draft_id}/tasks` — список задач для черновика

Доступ: `system_admin` (steps, status) / `knowledge_admin` (drafts). См. `orchestrator_service_api.md`, `gateway_service_api.md`, `common_api.md`.

### A33. Auth/Admin namespace — двойные пути в документации

Сейчас UI использует `/admin/users`, `/admin/roles`, `/admin/audit`. В части документации встречались также `/users/*`, `/roles`, `/audit`.

**Решение:** все пути приведены к единому `/admin/*` namespace. RBAC-матрица в `common_api.md` обновлена. Добавлен принцип категоризации путей.

### A11. Analyse Service заморожен

Analyse Service (`analyse_service_api.md`) спроектирован, но **не разрабатывается** в текущих спринтах. Старт — после стабилизации Пайплайна 1. Документация сохранена как проектная. `comparison_id` и `batch_id` отложены до старта разработки Analyse.

### A5. Черновики (drafts) — UI сравнения не реализован

API черновиков и FSM документированы, но **UI сравнения черновиков** отложен до Спринта 2. Решение по аномалиям — до 10.06.

### A6. Пустой документ — блокировка завершения черновика

Пустой документ (0 страниц после распознавания) не может быть завершён — документ не будет создан в Registry. Черновик переводится в `discarded` с кодом `EMPTY_DOCUMENT`. UI должен показывать сообщение об ошибке и предлагать загрузить файл заново. Реализовано в API.

### A23. Черновики перенесены в Registry

Таблица черновиков перенесена из `pipeline.drafts` (БД Orchestrator) в `registry.drafts` (БД Registry). Добавлены новые поля. Управление — через Orchestrator, который вызывает Registry internal API. `pipeline.tasks` и `pipeline.task_steps` — новые таблицы в БД Orchestrator. `registry.documents.draft_id` — новое поле для связи документа с черновиком.

### A24. `task_id` — внутренний ID задачи пайплайна

`task_id` теперь ID задачи в `pipeline.tasks` (БД Orchestrator). Агрегирует этапы (`task_steps`) с входными/выходными данными сервисов. Внешние клиенты используют `draft_id`.

### A35. `GET /drafts` — поддержка `draft_id` и `document_key` как опциональных фильтров

Ранее `GET /drafts` требовал `document_key` как обязательный параметр, что не позволяло администратору получить полный список всех черновиков. Также нельзя было найти черновик по `draft_id` через список.

**Решение (13.06):**
- `document_key` — опциональный фильтр (история попыток обработки одного документа)
- Добавлен `draft_id` — опциональный фильтр по ID черновика
- Без параметров — возвращаются все черновики (доступно `system_admin`, `knowledge_admin`)
- Добавлены параметры пагинации `page`, `page_size`

Синхронизированы:
- `orchestrator_service_api.md` — публичный `GET /drafts`
- `gateway_service_api.md` — таблица маршрутов
- `registry_service_api.md` — internal `GET /registry/drafts`
- `README.md` — описание экрана загрузки

### A37. Резолвер графа связей — не реализован

В `registry.document_references` есть поля `is_resolved` и `resolved_document_id`, но не описан сервис или механизм, который их проставляет. При загрузке нового документа все ссылки создаются с `is_resolved = FALSE` и остаются в этом состоянии.

**Что нужно:**
- Спецификация резолвера в `registry_service_api.md`.
- Триггеры: по событию (создание документа) + CRON-задача.
- SQL: `UPDATE ref SET is_resolved=TRUE, resolved_document_id=d.id FROM registry.documents d WHERE d.doc_code=ref.target_doc_code AND ref.is_resolved=FALSE`.
- Частичный индекс `WHERE is_resolved = FALSE`.
- Единый нормализатор `doc_code` в Converter-validator и Registry.

**Статус:** требуется реализация. См. `analyse_alternative_project.md` (п. 1.1).



### A36. Классификация ПКБ — расширение `categories` вместо отдельной таблицы

В `registry_document` обнаружены два конкурирующих набора полей классификации:
- **Новые:** `mks_oks_code`, `okstu_code` — используются в API
- **Старые:** `classifier_code`, `industry_code` — есть в модели данных, но не используются в API (архитектурный запах, неполная миграция)

Поле `group` использовалось в API, но отсутствовало в модели данных.
`PKB_DOMAIN` как `classifier_system` enum не существует.

**Решение (13.06, уточнено):** Вместо отдельной таблицы `pkb_domains` — используются существующие `categories` (M:N):
- `classifier_code`, `industry_code`, `group` — удалены из модели
- Предметные области ПКБ — это категории, привязанные к документам через `document_category`
- `classifier_system` enum остаётся без изменений: `MKS, OKSTU, UDC, EXTERNAL`

### A34. Битый путь к sprint-плану в README.md + отсутствие документации пользовательских категорий

В `docs/README.md` строка 151 ссылалась на `plans/sprint1_04_06_10_06.md` — файл не существовал по указанному пути (фактически находился в `docs_plans/features/`). Пользовательские категории документов (many-to-many) были спроектированы в вопросе 4.5 спринт-плана, но не были отражены в основной документации (`registry_service_api.md`, `db_diagrams.md`).

**Решение:**
- Путь в README исправлен
- Добавлены API и модель данных для категорий в `registry_service_api.md` (группа categories) и `db_diagrams.md` (раздел 11)
- Реализация — приоритет Спринта 3

---

## 🔴 Схема данных (требуют DDL)

| Код | Проблема | Статус |
|-----|----------|--------|
| A15 (DB-E4) | Нет UNIQUE-ограничений для 6 бизнес-ключей | 🔄 DDL |
| A16 (DB-E5) | Нет ON DELETE (NO ACTION по умолч.) | ✅ не нужно — soft-delete через deleted_at, DELETE не происходит |
| A17 | Нет таблиц `auth.users`, `registry.terminology` | 🔄 исправлено: таблицы есть, но не были описаны в db_diagrams.md. Добавлены в ER-диаграмму и примечания |
| A18 (DB-E10) | Нет soft-delete и `updated_at` | 🔄 решение |
| A19 (DB-E1) | VARCHAR для ENUM без CHECK | 🔄 DDL |
| A20 (DB-E8) | `document_chunks.document_id` денормализация — логика простановки в RAG Builder | 🔄 решено: проставляет RAG Builder |
| A21 (DB-E2) | `file_hash_sha256` как `text` вместо `CHAR(64)` | 🟡 открыто |
| A22 | `sessions.message_count` без триггера синхронизации | 🔄 исправлено: поле удалено из схемы БД и API. Количество сообщений вычисляется по факту через COUNT |

---

## 🔴 Security (требуют реализации)

| Код | Проблема | Статус |
|-----|----------|--------|
| S3 | Rate limiting не реализован (Nginx) | 🔄 код |
| S10 | `/internal/auth/validate` без сетевой изоляции | ✅ не нужно — межсервисная авторизация отсутствует |

---

## 🟡 API-документация (найдено 06.06, аудит check_rule.md п.1)

| Код | Проблема | Статус |
|-----|----------|--------|
| API-B1 | RAG Builder: тип секции `drawing` не существует в системе (должен быть `image`) | 🔄 исправлено |
| API-B2 | RAG Builder: в таблице полей `sections[].id`, в примере и Registry — `section_id` | 🔄 исправлено |
| API-B3 | Registry `POST /registry/documents`: два несовместимых формата тела, не описана детекция режима | 🔄 исправлено |
| API-B4 | Registry enum `document_status` содержит только статусы документа (`created`, `pending_index`, `indexing`, `indexed`, `failed`), статусы черновика вынесены в `registry.drafts` | 🔄 исправлено |
| API-S1 | Auth: `POST /admin/roles` → `id` (bigint), `GET /admin/roles` → `role_id` (string) | 🔄 исправлено |
| API-S2 | Common: `promotion_task_id` — bigint в таблице идентификаторов, string в Orchestrator | 🔄 исправлено — поле не используется |
| API-S3 | Common: упоминается `POST /chat/ask` (не существует, заменён на `/chat/sessions/{id}/messages`) | 🔄 исправлено |
| API-S4 | Gateway: `/api/v1/tasks/*` маршрутизируется, но объявлен internal — нет RBAC-ограничения | 🔄 исправлено — Gateway разруливает internal-маршруты |
| API-S5 | OCR/Parser: `document.pages[].width/height` — "в мм", но в `raw_ocr_v4` единицы пиксели | 🔄 исправлено |
| API-S6 | OCR/Parser → Registry: множества `block[].type` и `section.type` не сопоставлены | 🔄 исправлено |
| API-S7 | Orchestrator `reprocess`: дублирование `mode` и `options.engine` (могут противоречить) | 🔄 исправлено |
| API-S8 | Orchestrator `reprocess`: ответ "аналогичен POST /drafts" — неясно, создаётся ли draft | 🔄 исправлено |
| API-S9 | Query: статусы `processing`, `needs_clarification`, `source_conflict` отсутствуют в longpoll-логике | 🔄 исправлено — текущий FSM полный, эти статусы не используются |
| API-S10 | Query `POST /chat/feedback`: два формата не разграничены (взаимоисключение?) | 🔄 исправлено |
| API-S11 | Query `GET /chat/sessions/{id}`: longpoll устарел, но нет плана депрекации | 🔄 исправлено — longpoll удалён |
| API-S12 | Analyse Service: отсутствуют специфичные коды ошибок | ⬜ открыто — сервис заморожен |
| API-S13 | Converter-Validator: отсутствуют специфичные коды ошибок | 🔄 исправлено |
| API-S14 | Gateway: Rate limiting задокументирован (429), но не реализован | 🔄 код |
| API-S15 | RAG Search: только 200/500, нет 400/422 для невалидных параметров | 🔄 исправлено |
| API-S16 | Registry: PUT/PATCH/DELETE/Export/Import документов — без примеров запросов/ответов | 🔄 исправлено |
| API-S17 | Registry `PATCH /registry/documents/{id}/status`: internal, но не описана защита | 🔄 исправлено — Gateway разруливает internal |
| API-S18 | Common: bbox описан как нормализованный [0,1] на всех этапах, но OCR/Parser — пиксели | 🔄 исправлено |
| API-S19 | Integration `POST /meridian/export`: `document_id` тип string вместо bigint | ⬜ заморожено — интеграции не в MVP |
| API-S20 | Все internal-сервисы: не описана аутентификация service-to-service | 🔄 исправлено — внутренние вызовы изолированы Gateway |

## 🔴 Пайплайны (критичные — блокируют корректную реализацию)

| Код | Проблема | Статус |
|-----|----------|--------|
| LP-C1 | Потеря бинарных объектов на страницах preview при переходе к full-фазе | 🔄 решено: preview/full — единый эндпоинт с `mode`; если движок не поддерживает постраничный парсинг — full сразу с флагом `preview_not_supported: true`; решение принимает пользователь, full-фаза пропускается |
| LP-C2 | Противоречие в назначении `document_id`: Converter-validator vs Registry | 🔄 исправлено: `document_id` полностью удалён из Converter-validator API (16.06) |
| LP-C3 | Неатомарность проверки уникальности — нет компенсации при дубликате после `approve` | ⬜ открыто |
| LP-C4 | `discarded` (черновик) отсутствует в FSM документа — корректно, так как `discarded` — статус черновика, `failed` — статус документа | 🔄 исправлено |

## 🟡 Пайплайны (важные — вызовут ошибки или путаницу)

| Код | Проблема | Статус |
|-----|----------|--------|
| LP-V1 | Тупиковое состояние `archived` без выхода в FSM — `archived` удалён из FSM | 🔄 исправлено |
| LP-V2 | `partially_indexed` упомянут в тексте, но отсутствует в FSM Пайплайна 2 — не входит в основную модель статусов, редкий крайний случай | ⬜ открыто |
| LP-V3 | `indexed --> failed : Integrity check failed` — не описан механизм | ⬜ открыто |
| LP-V4 | Нет таймаута для состояния `pending` в Пайплайне 3 | ⬜ открыто |
| LP-V5 | Несоответствие формулы `title_hash_sha256` между пайплайном и ER-диаграммой | ⬜ открыто |
| LP-V9 | Нет поля текущей версии (`current_version_id`) в `registry.documents` | ⬜ открыто |
| LP-V10 | Противоречие в компенсации Пайплайна 2: транзакция откатывается, но требуется "удалить чанки" | ⬜ открыто |
| PL-E2 | Идемпотентность сообщений (Idempotency-Key) | 🔄 код |
| PL-E3 | TTL preview-артефактов — не определён | 🔄 решено: preview-режим не сохраняет бинарные объекты (`image_key` отсутствует), артефактов нет |
| B6 | `chat.messages.status` — значения не формализованы в БД | ⬜ DBA |
| B7 | RAG Builder — API-спецификация | 🔄 синхронизирована с пайплайнами (15.06) |
| B7a | Auth Service, RAG Search — API-спецификации | ⬜ открыто (P1-1, 17.06): фактического аудита RAG Search не проводилось. Документация RAG Search в `rag_search_service_api.md` дополнена секциями (конфигурация, стратегии, метрики) в рамках P13, но **это не заменяет полноценный аудит**. Auth Service: спецификация актуальна (12.06), но детальный аудит не проводился. Приоритет: 🟠 |

## 🟡 Перекрёстные несоответствия (кросс-проверка)

| Код | Проблема | Статус |
|-----|----------|--------|
| X1 | `document_id` назначается в разных местах (Converter vs Registry) | 🔄 исправлено: зафиксировано — `document_id` назначает Registry. overview.md актуализирован |
| X2 | `title_hash_sha256` — разные формулы в пайплайне и ER-диаграмме | 🔄 исправлено: формула приведена к `doc_code + title + era`. overview.md и db_diagrams.md синхронизированы |
| X3 | `partially_indexed` — есть в тексте пайплайна 2, нет в FSM и в БД | 🔄 решено: удалено из текста пайплайна 2 как нестатус — редкий крайний случай, не требующий отдельного статуса |
| X4 | `discarded` (draft) → `failed` (document) — решено: `discarded` — только статус черновика, `failed` — только статус документа | 🔄 исправлено |
| X5 | Журнал Оркестратора не отображён в схеме БД | ⬜ открыто |
| X6 | `document_versions` — нет связи `documents.current_version_id` | 🔄 решено: поле `current_version_id` добавлено в `registry.documents` (FK → `registry.document_versions.id`, nullable). Актуализировано в `db_diagrams.md` |
| X7 | `terminology` есть в JSON-схемах, нет таблицы в БД | 🔄 исправлено: таблица `registry.terminology` добавлена в ER-диаграмму и примечания db_diagrams.md |
| X8 | `amendments` — в JSON вложены, в БД нет отдельной таблицы | 🔄 решено: осознанное решение — поправки хранятся в JSONB внутри `document_sections.content`. Отдельная таблица не требуется до появления бизнес-требования на поиск/фильтрацию по поправкам |

---

## 🔵 Неочевидные архитектурные решения

- **`document_id` в `chat.sessions` как массив `bigint[]`** — нарушение 1НФ, осознанное, отложено.
- **`messages.sources` как `jsonb`** — невозможна индексация по document_id, осознанное ограничение.
- **OpenAPI/Swagger не делаем** — Markdown достаточно (решение от 29.05).
- **Все ID — bigint (sequence)**, включая document_id и version_id (04.06).
- **bbox** — пиксели (px) в OCR/Parser, нормализованные [0,1] в Converter-validator.
- **Двухфазный пайплайн**: preview → full (от 23.05).
- **OCR и Parser — два независимых сервиса** (от 23.05).
- **Унификация health-эндпоинта Orchestrator** (13.06): `/api/v1/monitor/health` → `/api/v1/health` как у всех внутренних сервисов. Health Orchestrator больше не проксируется через Gateway (внутренний, как Auth и др.). Gateway предоставляет `/api/v1/system/health` для внешнего мониторинга.
- **Перенос `/api/v1/monitor/metrics` в Gateway** (13.06): эндпоинт метрик качества пайплайнов перенесён из Orchestrator в Gateway как собственный (не проксируемый). Спецификация удалена из `orchestrator_service_api.md` и добавлена в `gateway_service_api.md`.

### 🔄 Добавление `title_key` в `registry.documents` (19.06)

**Проблема:** `title_hash_sha256` — бизнес-ключ, но без исходной строки конкатенации невозможно восстановить, из каких именно полей он вычислен. Это затрудняет аудит и отладку при расхождении хешей.

**Решение:** добавлено поле `title_key` (text) в `registry.documents` — исходная строка конкатенации 6 полей: `era | source_type | mks_oks_code | okstu_code | doc_code | normalized_title`. Хранится для аудита и отладки. Возвращается в API-ответах где присутствует `title_hash_sha256`.

**Затронутые документы:**
- `docs/glossary.md` — новый термин
- `docs/specifications/normalizer_specification.md` — описание title_key
- `docs/specifications/converter_specification.md` — шаг 6, раздел 6.1
- `docs/database/db_diagrams.md` — ER-диаграмма, описание registry.documents
- `docs/api/converter_validator_service_api.md` — preview, fingerprint, validate
- `docs/api/orchestrator_service_api.md` — drafts, documents
- `docs/api/registry_service_api.md` — документы, check-uniqueness, примечания
- `docs/6.dev_tasks_17_06.md` — DB-28

### 🔄 Схлопывание `quality.warnings[]` + `quality.issues[]` в `quality.notifications[]` (18.06)

**Проблема:** два параллельных массива в `quality` с почти одинаковой структурой, но разной семантикой (P3-5 security vs P12-3 операторские замечания). Разделение усложняет контракт и UI.

**Решение:** единый массив `quality.notifications[]` с полем `category: security | quality`. БД-таблица `pipeline.draft_notifications` (единая, без history).

**Обоснование:**
- Оба массива адресованы оператору — сервисы лишь передают данные
- Security-предупреждения тоже требуют внимания оператора (critical → подтверждение перед approve)
- Единый контракт проще для UI и consumer'ов
- Система новая — нет необходимости в патчах и обратной совместимости
- P3-5 поглощён P12-3: отдельный `warnings[]` не создаётся

**Затронутые документы:**
- `docs/api/parser_service_api.md` — `warnings[]` + `issues[]` → `notifications[]`
- `docs/api/ocr_service_api.md` — зеркальное изменение
- `docs/specifications/parsing_specifications.md` — `warnings` → `notifications`
- `docs/database/ddl_migrations_17_06.md` — `draft_issues` → `draft_notifications`
- `docs/pipelines/pipeline1-formation.md` — `draft_issues` → `draft_notifications`
- `docs/glossary.md` — `draft_issues` → `draft_notifications`
- `docs/5.docs_action_plan_17_06.md` — P12-3 актуализирован, P3-5 помечен поглощённым
- `docs/guide.md` — new: зафиксировано решение

### 🔄 Схлопывание `/parser/preview` и `/parser/process` (08.06)

**Проблема:** два эндпоинта с разными паттернами ответа (sync 200 vs async 202) усложняют контракт. Не все движки поддерживают постраничный парсинг.

**Решение:** единый эндпоинт `POST /{parser|ocr}/process` с полем `mode: "preview" | "full"`. Ответ всегда асинхронный (202). Если движок не поддерживает постраничный парсинг при `mode=preview` — возвращается полный документ с флагом `preview_not_supported: true` в метаданных. 

**Важно:** при `preview_not_supported: true` full-фаза OCR/Parser пропускается (JSON уже полный), но решение принимает пользователь как обычно. Все стадии preview (Converter-validator, проверка уникальности, отображение пользователю) выполняются в полном объёме.

**Затронутые документы:**
- `docs/api/parser_service_api.md` — схлопнут preview в process
- `docs/api/ocr_service_api.md` — зеркальное изменение
- `docs/schema/schema_converter_preview.json` (бывш. schema_parser_preview.json) — переименован, добавлены `mode`, `preview_not_supported`
- `docs/pipelines/{overview,pipeline1-formation,pipeline1-formation_detail}.md` — обновлены диаграммы и описания
- `docs/specifications/parsing_specifications.md` — обновлён контракт

---

## ⚙ Особенности рабочего окружения

### G1. Git-репозиторий выше корня документации

Корень проекта в Zed — `docs/`, а git-репозиторий находится на уровень выше (`H:/Projects/PKB_neuroassistant_docs`). Из-за этого прямые git-команды через `cd`, ограниченный `docs/`, не работают. Требуется `git -C <путь к корню репозитория>` или `--git-dir`/`--work-tree` с абсолютным путём.

**Важно:** терминал Zed на Windows использует Unix-стиль путей (`/h/Projects/...`), не Windows (`H:\...`). Команды с Windows-путями завершаются ошибкой.

### G2. Мусорный файл `nul` в репозитории

Обнаружен пустой файл `docs/nul` (19.06.2026). На Windows `nul` — зарезервированное имя устройства, из-за чего Git не может индексировать этот файл и прерывает `git add -A` с ошибкой. Файл удалён. Причина появления не установлена (возможно, артефакт работы одного из инструментов).

**Рекомендация:** при ошибке `unable to index file 'docs/nul'` — удалить файл и повторить `git add`.


