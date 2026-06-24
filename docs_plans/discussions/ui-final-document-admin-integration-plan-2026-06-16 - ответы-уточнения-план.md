# Уточнение по UI-store и план доработки

## 1. UI-store — зачем

Вы правы, что автономного UI-store для данных **не должно быть**. Но UI-store остаётся в трёх случаях:

| Сценарий               | Зачем UI-store                                                                                                          | Где хранится                                                     |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **UI-state**           | Какая вкладка открыта, выбранный draft_id/document_id, фильтры, состояние модалок, dirty-флаг редактора                 | `useState` / Zustand / Redux — **только UI**, не данные          |
| **Кеш запросов**       | Результаты `GET /drafts`, `GET /documents`, `GET /classifiers/tree` — чтобы не дёргать Gateway при переключении вкладок | TanStack Query / SWR — **только кеш**, source of truth = backend |
| **Optimistic updates** | При `PATCH /metadata` UI сразу меняет отображение, не дожидаясь ответа. Если backend вернёт 409 — откат                 | Query cache — **только optimistic**, persisted state = backend   |

**Что НЕ должно быть в UI-store:**

- Ручные правки метаданных до отправки в backend (P0 в редакторе с dirty-флагом).
- Список черновиков/документов (только кеш).
- Audit-timeline (только агрегация из backend при каждом открытии).
- Список неизвестных кодов (только кеш).

**Итог:** все 10 пунктов «не сделанного» из прошлого ответа касались либо кеша/UI-state (нормально), либо **персистентного хранения данных** (неправильно). Ниже — пересмотренный план.

---

## 2. Пересмотренный план «не сделанного»

### 2.1. Что решается без backend (доступные варианты)

| #   | Проблема                                           | Доступные варианты                                                                                                                                                                                                                             | Рекомендация                                                                                                           |
| --- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 1   | Audit-timeline собирается из нескольких источников | **A)** Параллельные `Promise.all([history, tasks, steps, versions, errors])` + склейка по `occurred_at` (только для admin роли) <br><br> **B)** Последовательные вызовы с прогресс-баром <br><br> **C)** Кешировать в TanStack Query на 30 сек | **A** + кеш C. UI — единственный агрегатор. Зафиксировать в `docs/audit/ui_admin_questions_2026-06_16.md` как решение. |
| 2   | Per-field diff LLM ↔ ручное                        | Вычисляется UI по двум snapshot'ам (`preview_metadata` + `manual_metadata`)                                                                                                                                                                    | Готово без backend.                                                                                                    |
| 3   | Сравнение версий                                   | UI-side diff по `version_id, format_code, file_hash_sha256, size_bytes, uploaded_at, uploaded_by`. **Контент не сравниваем** (тяжело)                                                                                                          | Зафиксировать в `docs/audit/ui_admin_questions_2026-06_16.md`.                                                         |
| 4   | Subject_area read-only                             | Уже подтверждено: `classification_status.subject_area` не принимается в `PATCH /registry/documents/{id}` body (пример в `registry_service_api.md:1247–1253`)                                                                                   | Зафиксировать в `docs/api/registry_service_api.md` явно (A39).                                                         |
| 5   | Кеш запросов                                       | TanStack Query с `staleTime: 30s` для списков, `Infinity` для текущего выбранного draft/document                                                                                                                                               | Не требует документации — это UI-решение.                                                                              |
| 6   | `If-Match` / версионирование draft                 | Если backend не отдаёт `etag` — **не блокирует MVP**. UI просто перезаписывает последним выигрышем. Логировать в audit                                                                                                                         | Зафиксировать ограничение в `specificity.md` как **A43**.                                                              |
| 7   | Optimistic updates                                 | При PATCH /metadata — UI сразу обновляет `preview_metadata` + ставит `dirty: false`. При 409/DRAFT_NOT_READY — откат + toast                                                                                                                   | UI-логика, документация не нужна.                                                                                      |
| 8   | Демо-режим vs prod                                 | `import.meta.env.VITE_USE_MOCK` — флаг. **При ошибке Gateway в prod — показать ошибку, не mock**                                                                                                                                               | Зафиксировать в `docs/audit/ui_admin_questions_2026-06_16.md` как обязательное правило.                                |

### 2.2. Что блокировано и требует backend (предлагаю варианты)

| #   | Проблема                      | Варианты для backend                                                                                                                                                                                                       | Что делать UI до ответа                                                                                                                                                              |
| --- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 9   | Endpoint для ручных правок    | **A1)** `PATCH /drafts/{id}/metadata` (новый) <br><br> **A2)** Расширить `PATCH /drafts/{id}/decide` полем `metadata_overrides` <br><br> **A3)** UI держит ручные правки в localStorage до approve, в /decide передаёт всё | До ответа — UI работает в режиме **A3** (localStorage), при approve целиком отправляет в `/decide.metadata_overrides`. Если backend выберет A1 — UI мигрирует на отдельный endpoint. |
| 10  | Audit-timeline admin-действий | **B1)** `GET /admin/audit?entity=document&id={id}` с фильтром <br><br> **B2)** `POST /registry/documents/{id}/audit-event` (UI пишет) <br><br> **B3)** Нет, UI собирает из существующих                                    | До ответа — **B3** (Promise.all из п.1). Если backend выберет B1/B2 — UI добавляет источник.                                                                                         |
| 11  | Классификация при approve     | **C1)** В `PATCH /drafts/{id}/metadata` <br><br> **C2)** В `PATCH /drafts/{id}/decide.metadata_overrides` <br><br> **C3)** После approve через `PATCH /registry/documents/{id}`                                            | До ответа — UI держит классификацию в localStorage вместе с метаданными (тот же A3).                                                                                                 |
| 12  | subject_area editability      | **D1)** Read-only (предпочтительно) <br><br> **D2)** Editable                                                                                                                                                              | До ответа — UI не отправляет subject_area в PATCH ни в каком случае.                                                                                                                 |

### 2.3. Что отменяется / не делается

| #   | Пункт                             | Решение                                                                                                                                                          |
| --- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 13  | UI-store для персистентных данных | **Отменяется.** Только UI-state + кеш запросов.                                                                                                                  |
| 14  | localStorage для метаданных       | **Временное решение** до ответа backend (п. 9, A3). Документировать как `A44` в `specificity.md` с пометкой «мигрировать на backend endpoint при подтверждении». |
| 15  | Server-side audit-event от UI     | **Не делать.** UI не пишет в backend audit-event — только читает.                                                                                                |
| 16  | Per-field confidence              | **Не запрашивать.** UI вычисляет статус по двум значениям (LLM vs ручное).                                                                                       |
| 17  | Compare-таб                       | **Не делать.** В MVP — только diff в карточке метаданных.                                                                                                        |
| 18  | Backend-side compare версий       | **Не запрашивать.** Только UI-side diff по метаданным версий.                                                                                                    |
| 19  | Полноценный CSV/XLSX импорт в UI  | **Не делать.** Только отображение результата `POST /registry/classifiers/import`.                                                                                |

### 2.4. Что остаётся в плане (не относится к UI-store)

| #   | Задача                                      | Когда                                |
| --- | ------------------------------------------- | ------------------------------------ |
| 20  | Реализация `DocumentTimelineEvent` маппинга | После ответа backend по Q3           |
| 21  | Реализация `MetadataEditorState`            | После ответа backend по Q1           |
| 22  | Тестирование optimistic updates             | После реализации PATCH /metadata     |
| 23  | Smoke сценарий                              | После стабилизации backend-контракта |

---

## 3. Обновлённый план доработки документации

### 3.1. `docs/specificity.md` — добавить

**A44. UI не персистирует данные локально.**
UI Final не имеет собственной БД. Все данные — в backend. UI-store используется только для: (1) UI-state (открытая вкладка, фильтры, dirty-флаг), (2) кеш запросов (TanStack Query), (3) optimistic updates. **Исключение (временное, до Q1):** localStorage хранит draft ручных правок метаданных до approve, чтобы не потерять ввод при refresh. Мигрировать на backend endpoint при подтверждении `PATCH /drafts/{id}/metadata`.

**A45. Timeline агрегируется на стороне UI.**
`GET /documents/{id}/history` не содержит событий `metadata_edited`, `classification_changed`, `soft_deleted`. UI делает `Promise.all` из 4-5 endpoints, склеивает по `occurred_at`, нормализует в `DocumentTimelineEvent`. Зафиксировать источники в `docs/audit/ui_admin_questions_2026-06_16.md`.

**A46. Кеш запросов в UI имеет TTL.**
TanStack Query (или эквивалент): `staleTime: 30s` для списков, `Infinity` для текущей сущности. После PATCH — `invalidateQueries`. После navigate-away — кеш остаётся, при возврате — fresh check.

### 3.2. `docs/audit/ui_admin_questions_2026-06_16.md` (новый)

Структура:

```markdown
# Вопросы к backend по UI Admin (16.06.2026)

## Контекст
UI Final получает админские функции документов.
Принципы:
- UI не персистирует данные (только UI-state + кеш запросов).
- Все CRUD — через backend.
- Timeline — UI-side агрегация (если backend не предоставит единый endpoint).

## Решения UI (без backend)
- D1: Per-field diff LLM ↔ ручное — UI вычисляет.
- D2: Сравнение версий — UI-side diff по метаданным (контент не сравниваем).
- D3: Optimistic updates — UI обновляет сразу, откат при ошибке backend.
- D4: При ошибке Gateway в prod — показать ошибку, не mock (фикс #5 docs_ui_compare).

## Открытые вопросы

### Q1. Endpoint для ручных правок метаданных черновика
Проблема: PATCH /drafts/{id}/decide принимает только action+comment.
Варианты:
  A1) PATCH /drafts/{id}/metadata (новый endpoint, рекомендую)
  A2) Расширить /decide полем metadata_overrides
  A3) UI использует localStorage + передаёт всё в /decide (временное решение)
UI до ответа: работает в A3.

### Q2. Классификация при approve
Проблема: mks_oks_code, okstu_code, categories — где передавать?
Варианты:
  C1) В PATCH /drafts/{id}/metadata (если есть)
  C2) В /decide.metadata_overrides
  C3) После approve через PATCH /registry/documents/{id}
Рекомендация: C1 (атомарно с остальными метаданными).
UI до ответа: держит в localStorage, передаёт в /decide.

### Q3. Audit-timeline admin-действий
Проблема: GET /documents/{id}/history содержит только статусы FSM.
Варианты:
  B1) GET /admin/audit?entity=document&id={id} (с фильтром)
  B2) POST /registry/documents/{id}/audit-event
  B3) Нет — UI собирает из существующих
UI до ответа: B3 (Promise.all из history, steps, versions, errors).
Маппинг источников: см. A45 в specificity.md.

### Q4. Subject_area — read-only?
Проблема: classification_status.subject_area приходит в ответе, но не описано
  в PATCH /registry/documents/{id} body.
Варианты:
  D1) Read-only (предпочтительно — автогенерируется)
  D2) Editable
UI до ответа: не отправляет subject_area в PATCH ни в каком случае.

### Q5. Поведение при concurrent edit draft
Проблема: два пользователя редактируют один draft.
Варианты:
  E1) If-Match: etag + 412 Precondition Failed
  E2) Optimistic merge (последний выигрывает)
  E3) Lock на draft (только один редактор)
UI до ответа: E2 с логированием в audit.
```

### 3.3. `docs/api/registry_service_api.md` — изменить

**PATCH /registry/documents/{id} (`:1240–1269`)** — явно разделить поля:

```markdown
**Редактируемые поля (admin):**
- `title, doc_code, source_type, document_type, era, validity_status, jurisdiction, issuing_body, mks_oks_code, okstu_code, status_note, metadata, category_ids`

**Запрещены в PATCH (immutable):**
- `id, title_hash_sha256 (пересчитывается), file_hash_sha256, created_at, created_by, current_version_id, updated_by, updated_at`

**Read-only (приходит в ответе, не принимается в body):**
- `subject_area` (из classification_status) — автогенерируется, см. A39
- `chunk_count` — вычисляется RAG Builder
- `total_versions` — вычисляется по document_versions
```

### 3.4. `docs/api/orchestrator_service_api.md` — изменить

**PATCH /drafts/{id}/decide (`:1244`)** — добавить поле `metadata_overrides`:

```json
{
  "action": "approve",
  "comment": "Метаданные проверены",
  "metadata_overrides": {
    "doc_code": "ГОСТ 20868-81",
    "title": "...",
    "mks_oks_code": "47.020",
    "categories": [1, 3]
  }
}
```

> `metadata_overrides` — полный снимок полей, которые админ подтвердил. Orchestrator использует их (если переданы) вместо `preview_metadata` при создании документа в Registry.

### 3.5. `docs/api/frontend_types.md` (новый)

Зафиксировать UI-типы. **Добавить явно:**

```typescript
// UI-state (useState / Zustand)
interface UIStore {
  activeTab: 'knowledge' | 'processing' | 'admin' | 'qa' | 'chat' | 'search' | 'history';
  selectedDraftId: number | null;
  selectedDocumentId: number | null;
  processingSubTab: 'drafts' | 'registry' | 'queue';
  adminSubTab: 'users' | 'roles' | 'audit' | 'classifiers' | 'terminology' | 'unknown_codes';
  editorDirty: boolean;
  // ...
}

// Query cache (TanStack Query) — НЕ персистентный, только кеш
interface QueryCache {
  drafts: Draft[];                          // staleTime: 30s
  documents: DocumentRegistryItem[];        // staleTime: 30s
  classifiers: { [system: string]: ClassifierNode[] }; // staleTime: 5min
  terminology: Term[];                      // staleTime: 5min
  currentDraft: DraftFull | null;           // staleTime: Infinity
  currentDocument: DocumentRegistryItem | null; // staleTime: Infinity
  documentTimeline: DocumentTimelineEvent[]; // staleTime: 30s
  // ...
}

// Optimistic update layer
interface OptimisticUpdate<T> {
  type: 'metadata_edit' | 'classification_change' | 'category_update';
  data: T;
  rollbackOnError: true;
}
```

### 3.6. `docs/README.md` — изменить таблицу экранов UI (`:131`)

Добавить строки:

| **Подрежим «Черновики» (внутри «Обработка базы знаний»)** | Админский workflow: загрузка → preview → редактор метаданных → классификация → approve/reject | Список черновиков слева, карточка справа, **редактор с diff LLM↔ручное**, raw JSON, timeline |
| **Подрежим «Реестр» (внутри «Обработка базы знаний»)** | Администрирование принятых документов | Таблица + карточка + редактор метаданных + timeline + классификация + soft-delete |
| **Подрежим «Очередь и журнал»** | Технический мониторинг | `GET /documents/queue` + `GET /documents/{id}/errors` + логи пайплайна |

### 3.7. `docs/glossary.md` — добавить

- `ui-state` — состояние UI (открытая вкладка, фильтры), не персистентное.
- `query-cache` — кеш HTTP-ответов в TanStack Query, source of truth = backend.
- `optimistic-update` — UI обновляет отображение до ответа backend, откат при ошибке.
- `timeline` — агрегированный журнал документа, собирается UI из 4-5 endpoints.
- `editor-dirty` — флаг наличия несохранённых правок в редакторе метаданных.

---

## 4. Итоговый чек-лист изменений документации

| Файл                                          | Действие                                                                                            | Зависит от |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------- |
| `docs/audit/ui_admin_questions_2026-06_16.md` | Создать с Q1–Q5                                                                                     | —          |
| `docs/specificity.md`                         | +A44, A45, A46 (3 аномалии про UI-store)                                                            | —          |
| `docs/api/frontend_types.md`                  | Создать с типами UI-state, QueryCache, OptimisticUpdate, DocumentTimelineEvent, MetadataEditorState | —          |
| `docs/api/registry_service_api.md`            | Разделить поля PATCH на editable/immutable/read-only                                                | —          |
| `docs/api/orchestrator_service_api.md`        | Добавить `metadata_overrides` в PATCH /decide                                                       | —          |
| `docs/api/common_api.md`                      | Коды ошибок `DRAFT_NOT_READY`, `INVALID_CLASSIFIER_CODE`                                            | —          |
| `docs/README.md`                              | Расширить таблицу экранов UI                                                                        | —          |
| `docs/glossary.md`                            | +5 терминов (ui-state, query-cache, optimistic-update, timeline, editor-dirty)                      | —          |
| `docs/pipelines/overview.md`                  | Упомянуть `metadata_edited` как read-only событие                                                   | —          |

---

## 5. Что осталось несделанным (финальный список)

1. **Не получены ответы backend** по Q1–Q5 (4 из 5 — про редактирование метаданных, 1 — про audit-timeline).
2. **Не подтверждён** mock Gateway для `PATCH /drafts/{id}/decide` с `metadata_overrides` — UI нельзя полноценно протестировать локально.
3. **Не описана** транзакционная семантика для Q5 (concurrent edit) — UI временно работает в режиме «последний выигрывает», логирование в audit.
4. **Не верифицировано**, что `current_version_id` действительно есть в `registry.documents` (LP-V9/X6 — задокументировано как решённое, но не проверено в текущем `db_diagrams.md`).
5. **Не описано** поведение UI при пустом ответе `GET /drafts/{id}/preview/status` (статус `pending` без `preview`) — нужно явно показать «preview не запущен, нажмите кнопку».
6. **Не определён** формат `payload` для `metadata_overrides` в `/decide` — какие именно поля принимаются. В `docs/api/orchestrator_service_api.md:1248` тело `decide` содержит только `action` + `comment`. Нужно дополнить перечнем полей (аналогично `POST /drafts` body, `:42–53`).
7. **Не описано** поведение UI при `409 DRAFT_ALREADY_DECIDED` — нужно явно отключить редактор и показать «решение уже принято».
8. **Не синхронизирован** `db_diagrams.md` — нужно проверить, что таблица `registry.drafts` содержит (или не содержит) поле `manual_metadata`, и обновить ER-диаграмму при подтверждении Q1.
9. **Не зафиксирована** версия API для `metadata_overrides` — breaking change или backward-compatible? Если `decide` уже используется клиентами, добавление поля — backward-compatible (мино́рная версия).
10. **Не описаны** все 5 аномалий (A38–A46) в `docs/specificity.md` — A38, A39, A40, A41, A42, A43, A44, A45, A46. В этом ответе — все сформулированы, но **в файл не внесены**.
