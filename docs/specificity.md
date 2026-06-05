# Specificity — аномалии и трудные моменты

> Только то, что **не решено**, **не очевидно** или **требует внимания**.
> Закрытые аномалии — в разделе «История решений».

---

## 🟡 Открытые вопросы

### A11. Analyse Service заморожен

Analyse Service (`analyse_service_api.md`) спроектирован, но **не разрабатывается** в текущих спринтах. Старт — после стабилизации Пайплайна 1. Документация сохранена как проектная. `comparison_id` и `batch_id` отложены до старта разработки Analyse.

### A5. Черновики (drafts) — UI сравнения не реализован

API черновиков и FSM документированы, но **UI сравнения черновиков** отложен до Спринта 2. Решение по аномалиям — до 10.06.

### A6. Пустой документ — блокировка завершения черновика

Пустой документ (0 страниц после распознавания) не может быть завершён — документ не будет создан в Registry. Черновик переводится в `discarded` с кодом `EMPTY_DOCUMENT`. UI должен показывать сообщение об ошибке и предлагать загрузить файл заново. Реализовано в API.

---

## 🔴 Схема данных (требуют DDL)

| Код | Проблема | Статус |
|-----|----------|--------|
| A15 (DB-E4) | Нет UNIQUE-ограничений для 6 бизнес-ключей | 🔄 DDL |
| A16 (DB-E5) | Нет ON DELETE (NO ACTION по умолч.) | 🔄 DDL |
| A17 | Нет таблиц `auth.users`, `registry.terminology` | 🔄 разработка |
| A18 (DB-E10) | Нет soft-delete и `updated_at` | 🔄 решение |
| A19 (DB-E1) | VARCHAR для ENUM без CHECK | 🔄 DDL |
| A20 (DB-E8) | `document_chunks.document_id` денормализация без синхронизации | 🟡 открыто |
| A21 (DB-E2) | `file_hash_sha256` как `text` вместо `CHAR(64)` | 🟡 открыто |
| A22 | `sessions.message_count` без триггера синхронизации | 🟡 открыто |

---

## 🔴 Security (требуют реализации)

| Код | Проблема | Статус |
|-----|----------|--------|
| S3 | Rate limiting не реализован (Nginx + Redis) | 🔄 код |
| S10 | `/internal/auth/validate` без сетевой изоляции (mTLS) | 🔄 код |

---

## 🟡 API-документация (найдено 06.06, аудит check_rule.md п.1)

| Код | Проблема | Статус |
|-----|----------|--------|
| API-B1 | RAG Builder: тип секции `drawing` не существует в системе (должен быть `image`) | ⬜ открыто |
| API-B2 | RAG Builder: в таблице полей `sections[].id`, в примере и Registry — `section_id` | ⬜ открыто |
| API-B3 | Registry `POST /registry/documents`: два несовместимых формата тела, не описана детекция режима | ⬜ открыто |
| API-B4 | Registry enum `document_status` содержит только статусы документа (`created`, `pending_index`, `indexing`, `indexed`, `failed`), статусы черновика вынесены в `pipeline.drafts` | 🔄 исправлено |
| API-S1 | Auth: `POST /admin/roles` → `id` (bigint), `GET /admin/roles` → `role_id` (string) | ⬜ открыто |
| API-S2 | Common: `promotion_task_id` — bigint в таблице идентификаторов, string в Orchestrator | ⬜ открыто |
| API-S3 | Common: упоминается `POST /chat/ask` (не существует, заменён на `/chat/sessions/{id}/messages`) | ⬜ открыто |
| API-S4 | Gateway: `/api/v1/tasks/*` маршрутизируется, но объявлен internal — нет RBAC-ограничения | ⬜ открыто |
| API-S5 | OCR/Parser: `document.pages[].width/height` — "в мм", но в `raw_ocr_v4` единицы пиксели | ⬜ открыто |
| API-S6 | OCR/Parser → Registry: множества `block[].type` и `section.type` не сопоставлены | ⬜ открыто |
| API-S7 | Orchestrator `reprocess`: дублирование `mode` и `options.engine` (могут противоречить) | ⬜ открыто |
| API-S8 | Orchestrator `reprocess`: ответ "аналогичен POST /drafts" — неясно, создаётся ли draft | ⬜ открыто |
| API-S9 | Query: статусы `processing`, `needs_clarification`, `source_conflict` отсутствуют в longpoll-логике | ⬜ открыто |
| API-S10 | Query `POST /chat/feedback`: два формата не разграничены (взаимоисключение?) | ⬜ открыто |
| API-S11 | Query `GET /chat/sessions/{id}`: longpoll устарел, но нет плана депрекации | ⬜ открыто |
| API-S12 | Analyse Service: отсутствуют специфичные коды ошибок | ⬜ открыто |
| API-S13 | Converter-Validator: отсутствуют специфичные коды ошибок | ⬜ открыто |
| API-S14 | Gateway: Rate limiting задокументирован (429), но не реализован | 🔄 код |
| API-S15 | RAG Search: только 200/500, нет 400/422 для невалидных параметров | ⬜ открыто |
| API-S16 | Registry: PUT/PATCH/DELETE/Export/Import документов — без примеров запросов/ответов | ⬜ открыто |
| API-S17 | Registry `PATCH /registry/documents/{id}/status`: internal, но не описана защита | ⬜ открыто |
| API-S18 | Common: bbox описан как нормализованный [0,1] на всех этапах, но OCR/Parser — пиксели | ⬜ открыто |
| API-S19 | Integration `POST /meridian/export`: `document_id` тип string вместо bigint | ⬜ открыто |
| API-S20 | Все internal-сервисы: не описана аутентификация service-to-service | ⬜ открыто |

## 🔴 Пайплайны (критичные — блокируют корректную реализацию)

| Код | Проблема | Статус |
|-----|----------|--------|
| LP-C1 | Потеря бинарных объектов на страницах preview при переходе к full-фазе (начало со страницы `max_pages+1`) | ⬜ открыто |
| LP-C2 | Противоречие в назначении `document_id`: Converter-validator vs Registry | ⬜ открыто |
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
| PL-E3 | TTL preview-артефактов — не определён | ⬜ бизнес-решение |
| B6 | `chat.messages.status` — значения не формализованы в БД | ⬜ DBA |
| B7 | Auth Service, RAG Builder, RAG Search — API-спецификации | ⬜ аналитик |

## 🟡 Перекрёстные несоответствия (кросс-проверка)

| Код | Проблема | Статус |
|-----|----------|--------|
| X1 | `document_id` назначается в разных местах (Converter vs Registry) | ⬜ открыто |
| X2 | `title_hash_sha256` — разные формулы в пайплайне и ER-диаграмме | ⬜ открыто |
| X3 | `partially_indexed` — есть в тексте пайплайна 2, нет в FSM и в БД | ⬜ открыто |
| X4 | `discarded` (draft) → `failed` (document) — решено: `discarded` — только статус черновика, `failed` — только статус документа | 🔄 исправлено |
| X5 | Журнал Оркестратора не отображён в схеме БД | ⬜ открыто |
| X6 | `document_versions` — нет связи `documents.current_version_id` | ⬜ открыто |
| X7 | `terminology` есть в JSON-схемах, нет таблицы в БД | ⬜ открыто |
| X8 | `amendments` — в JSON вложены, в БД нет отдельной таблицы | ⬜ открыто |

---

## 🔵 Неочевидные архитектурные решения

- **`document_id` в `chat.sessions` как массив `bigint[]`** — нарушение 1НФ, осознанное, отложено.
- **`messages.sources` как `jsonb`** — невозможна индексация по document_id, осознанное ограничение.
- **OpenAPI/Swagger не делаем** — Markdown достаточно (решение от 29.05).
- **Все ID — bigint (sequence)**, включая document_id и version_id (04.06).
- **bbox** — пиксели (px) в OCR/Parser, нормализованные [0,1] в Converter-validator.
- **Двухфазный пайплайн**: preview → full (от 23.05).
- **OCR и Parser — два независимых сервиса** (от 23.05).

---

## История решений

| Дата | Решение |
|------|---------|
| 06.06 | **Новая модель статусов**: статусы документов и черновиков разделены. `pipeline.drafts.status`: `uploaded`, `previewing`, `ready_for_approve`, `approved`, `discarded`. `registry.documents.processing_status`: `created`, `pending_index`, `indexing`, `indexed`, `failed`. Удалены `draft`, `awaiting_decision`, `parsing`, `validation`, `ready_for_promotion`, `review_required`, `registry`, `duplicate`, `new_version`, `archived` из `registry.documents`. `registry.document_history.event_type`: `promoted` → `approved`. |
| 07.06 | **Tasks — только read-only**: `POST /tasks/{task_id}/preview` и `POST /tasks/{task_id}/decide` удалены. `GET /tasks/{task_id}/preview/status` → `GET /tasks/{task_id}/status`. Задачи — только просмотр статуса. Всё управление через `/drafts/{draft_id}/...`. |
| 07.06 | **Registry — статус только от Оркестратора**: `PATCH /registry/documents/{doc_id}/status` — internal, вызывается только Оркестратором при завершении индексации. Удалён публичный эндпоинт и `GET /registry/documents/{doc_id}/history` (история — в Оркестраторе). |
| 06.06 | **Миграция task→drafts**: управление загрузкой документов переведено с `/tasks/{task_id}/...` на `/drafts/{draft_id}/...`. `task_id` — внутренний сквозной ID (internal). Внешние клиенты используют `draft_id` и `document_id`. Добавлены эндпоинты `POST /drafts/{draft_id}/preview`, `GET /drafts/{draft_id}/preview/status`. `POST /tasks/{task_id}/decide` помечен как internal. |
| 06.06 | **Пустой документ**: пустой документ (0 страниц) не может покинуть черновики. Черновик переводится в `discarded` с кодом `EMPTY_DOCUMENT`. Решение `approve` недоступно. |
| 06.06 | Исправлены коды ошибок: `VALIDATION_FAILED` убран с 500, `VALIDATION_ERROR` на 400 во всех сервисах |
| 06.06 | Унифицированы коды ошибок: каждый сервис хранит только свои специфичные коды, общие — в `common_api.md` |
| 06.06 | Исправлены все двусмысленные формулировки A23–A34 |
| 06.06 | API-документация: Б1–Б4, С1–С11, К1–К8 — все исправлены |
| 06.06 | Пайплайны: PL-E1, C1, L1, P2, P4, R2, L3–L7, PL-E4 — исправлены |
| 06.06 | Security: S1, S2, S4–S9, S11, S12 — документированы; S3, S10 — code-level |
| 06.06 | Кросс-проверка: КП1–КП4, В1–В5, В8–В10 — исправлены/согласованы |
| 06.06 | Схема: DB-E7 (индексы), DB-E8 (денормализация), DB-E9 (updated_at) — документированы |
| 05.06 | Документированы API черновиков, FSM, Gateway-маршрутизация |
| 04.06 | Все ID → bigint |
| 04.06 | Добавлены `chat.projects` и `project_id` в `chat.sessions` |
| 04.06 | `document_type` унифицирован |
| 29.05 | OpenAPI не делаем, Markdown достаточно |
| 26.05 | Поиск удалён из Orchestrator |
| 23.05 | OCR и Parser — два независимых сервиса |
| 23.05 | Двухфазный пайплайн: preview → full |
