# Оркестратор в Пайплайне 2 (Индексация): сценарии поведения

> **Назначение документа.** Описание сценариев поведения Оркестратора при прогоне Пайплайна 2 (индексация). Документ дополняет:
> - [Пайплайн 2: Индексация документа](../pipeline2-indexation.md) — основной поток, FSM
> - [API Orchestrator Service](../../api/orchestrator_service_api.md) — эндпоинты
> - [API RAG Builder Service](../../api/rag_builder_service_api.md) — детали RAG Builder
>
> Стиль описания: **Ситуация → Поведение Оркестратора → Результат / Статус → Код ошибки**.

**Охват документа:** Пайплайн 2 (`pending_index → indexing → indexed / failed`). Пайплайн 1 (формирование) — в [pipeline1-orchestrator_details.md](pipeline1-orchestrator_details.md). Пайплайн 3 (поиск, через Query Service) — в [pipeline3-orchestrator_details.md](pipeline3-orchestrator_details.md).

---

## 0. Общая модель

**Pipeline 2 запускается после `created`** (документ записан в Registry). Координатор — Оркестратор, исполнитель — RAG Builder. **Запись в БД (pgvector) — только RAG Builder** (см. [overview.md §Матрица ответственности](../overview.md#матрица-ответственности-сервисов)). Оркестратор не имеет прямого доступа к `rag.*` таблицам.

**FSM Пайплайна 2** (см. [pipeline2-indexation.md §Статусная модель](../pipeline2-indexation.md#статусная-модель-fsm)):

```
[*] → pending_index (created) → indexing (запуск) → indexed (готово) → [*]
                          ↘                ↘
                           failed (timeout / retry exhausted / integrity)
```

**Документ-источник статуса:** `registry.documents.processing_status` (см. [glossary.md](../../glossary.md#статусы-документов-registrydocuments)). Оркестратор читает/пишет через `PATCH /registry/documents/{id}/status` (internal Registry endpoint).

---

## 1. Триггер индексации: Scheduler

**Расписание:** Scheduler-сервис (или CRON-задача) запускается каждые 15 минут (см. [pipeline2-indexation.md §Этап 1](../pipeline2-indexation.md#этап-1-rag-builder-пишет-бд)).

| Сценарий | Поведение Scheduler | Результат | Код |
|----------|---------------------|-----------|-----|
| Норма | `SELECT id FROM registry.documents WHERE processing_status = 'created' FOR UPDATE SKIP LOCKED` (или через `pg_try_advisory_xact_lock` per-doc) | Для каждого `id` создать `pipeline.tasks` (Orchestrator), статус `pending_index → indexing` | — |
| Документ уже в `indexing` | Пропустить (advisory lock удерживается) | Никаких действий | — |
| Документ в `indexed` | Пропустить | Никаких действий | — |
| Документ в `failed` | Не запускать автоматически (требуется `reprocess` или ручной `reindex`) | Никаких действий | — |
| Документ в `pending_index` дольше 1 часа | **Таймаут** Scheduler: перевести в `failed` | `status: failed` | `INDEX_TRIGGER_TIMEOUT` |

> **Связь Оркестратор ↔ Scheduler:** Scheduler инициирует `pipeline.tasks` (status=active) и уведомляет Оркестратора о необходимости запуска. Оркестратор вызывает RAG Builder, ведёт `task_steps` для Пайплайна 2.
>
> **Защита от двойного запуска:** `pg_try_advisory_xact_lock` на `document_id` (per-doc) предотвращает параллельный запуск RAG Builder. Дополнительно — проверка `processing_status != 'indexing'` перед стартом.

---

## 2. Запуск RAG Builder

**Точка вызова:** Оркестратор → `POST /rag/build` (RAG Builder internal).

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| Норма — `status: pending_index`, документ в Registry | Получить обогащённый JSON от Registry (`GET /registry/documents/{id}?include=sections`), сформировать `registry_for_rag_v2` (плоский JSON с секциями), вызвать `POST /rag/build` | `202 { task_id }` | — |
| Документ не найден в Registry | — | `404 DOCUMENT_NOT_FOUND` | `DOCUMENT_NOT_FOUND` |
| Документ в терминальном состоянии `indexed` | Не запускать (Scheduler пропустит). При ручном вызове — отказать | `409 DOCUMENT_ALREADY_INDEXED` | `DOCUMENT_ALREADY_INDEXED` |
| Документ в `indexing` (advisory lock удерживается) | — | `409 INDEXING_IN_PROGRESS` | `INDEXING_IN_PROGRESS` |
| `POST /rag/build` вернул 5xx | Retry 3 раза (Exponential 1с → 2с → 4с). Circuit Breaker | После исчерпания — `failed` | `RAG_BUILDER_UNAVAILABLE` |
| `POST /rag/build` вернул таймаут | Retry 3 раза | `failed` | `RAG_BUILDER_TIMEOUT` |
| Документ в `failed` (reprocess) | Не запускать автоматически. Только через `POST /documents/{doc_id}/reprocess mode=reindex` | — | — |
| Документ в `failed` (ручной `reindex` через reprocess) | `DELETE /rag/build/{doc_id}` → `POST /rag/build` | — | — |

> **Longpoll:** после `POST /rag/build` Оркестратор вызывает `GET /rag/build/{doc_id}/status?longpoll=15` (см. [pipeline2-indexation.md §Longpoll-механизм](../pipeline2-indexation.md#longpoll-механизм-для-pipeline-2)). Держит соединение до 15с, ответ — при изменении статуса или таймауте.

---

## 3. Ожидание результата (longpoll)

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| `status: pending_index` (не начато) | Повторить longpoll через 1с | (промежуточный ответ) | — |
| `status: indexing` (идёт) | Повторить longpoll | (промежуточный ответ с `chunks_generated`, `embeddings_count`) | — |
| `status: indexed` (готово) | Завершить longpoll, записать `indexed` в `registry.documents.processing_status`, обновить `pipeline.tasks.status=completed`, записать `task_step "rag_build"` | `200 { status: indexed, chunks_count }` | — |
| `status: failed` (ошибка RAG Builder) | Завершить longpoll, перевести документ в `failed` с `error_code` от RAG Builder | `200 { status: failed, error_code }` | (см. §6) |
| Таймаут longpoll 15с при незавершённой индексации | Повторить longpoll | (промежуточный ответ) | — |
| Абсолютный таймаут индексации (`indexing` дольше N минут) | Перевести в `failed` | `status: failed` | `RAG_BUILDER_TIMEOUT` |

> **Абсолютный таймаут `indexing`:** настраиваемый параметр (по умолчанию 30 минут). Проверяется Scheduler каждые 5 минут. Документ → `failed` с `RAG_BUILDER_TIMEOUT`.

---

## 4. Integrity check (целостность индекса)

**Источник:** [pipeline2-indexation.md §Механизм перехода `indexed → failed`](../pipeline2-indexation.md#механизм-перехода-indexed--failed-p1-17-уточнение).

Проверка целостности выполняется **в две стадии**:

| Стадия | Когда | Что проверяется | Действие Оркестратора | Код |
|--------|-------|------------------|------------------------|-----|
| Self-check | В конце `indexing` (RAG Builder) | `SELECT count(*) FROM rag.document_chunks WHERE document_id = $1` vs `expected_chunk_count`. `total_tokens > 0`. Уникальность `chunk_index`. | — (RAG Builder) | `INTEGRITY_CHECK_FAILED` (если падает) |
| Фоновая проверка | Scheduler каждые 6 часов | `chunk_count_actual < chunk_count_expected` ИЛИ `embedding IS NULL` для `indexed`-документов старше 1 часа | Перевести в `failed`, записать в `audit.events` (уровень `ERROR`) | `INTEGRITY_CHECK_FAILED` |
| Self-check не прошёл | RAG Builder вернул `status=failed` с `INTEGRITY_CHECK_FAILED` | — | Перевести в `failed` немедленно | `INTEGRITY_CHECK_FAILED` |

> **Автоматическое исключение из RAG Search:** документ в `failed` **не возвращается** в результатах поиска (RAG Search фильтрует `WHERE processing_status = 'indexed'`). Это происходит без участия Оркестратора — на уровне RAG Search.
>
> **Уведомление UI:** документ в `failed` помечается как кандидат на `reprocess` (`POST /documents/{doc_id}/reprocess mode=reindex`). UI показывает предупреждение (см. [pipeline2-indexation.md §Механизм перехода](../pipeline2-indexation.md#механизм-перехода-indexed--failed-p1-17-уточнение)).

---

## 5. Partial indexation

**Источник:** [glossary.md §Статусы документов](../../glossary.md#статусы-документов-registrydocuments) — `partially_indexed` упоминается как edge-case, **не выделен** в FSM (LP-V2, планируется в Sprint 4 / SPEC-19).

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| `chunk_count_actual < chunk_count_expected` после `indexing` | RAG Builder возвращает `indexed` с пометкой `partial: true`. Оркестратор **не выделяет** в отдельный статус (LP-V3, открыто). Записать в `registry.documents` предупреждение | `status: indexed` (с warning) | `PARTIAL_INDEXATION` |
| Целая секция пропущена (chunking failed) | RAG Builder пропускает секцию, продолжает остальные. Логирует `WARN` | `status: indexed` | `SECTION_SKIPPED` |
| Embedding failed для части чанков | RAG Builder пропускает чанк (до 2 retry на чанк), продолжает | `status: indexed` (с warning) | `EMBEDDING_PARTIAL_FAILED` |
| Пользователь инициирует `reprocess mode=reindex` | Полная переиндексация документа | — | — |

> **Текущее поведение (LP-V2, open):** `partially_indexed` не выделен в `processing_status` (нет `enum`-значения). Документ остаётся в `indexed` с warning. **Исключён** из RAG Search, если `chunk_count_actual == 0` (RAG фильтрует по наличию чанков). Планируется Sprint 4.

---

## 6. Ошибки RAG Builder и компенсация

**Источник:** [pipeline2-indexation.md §Компенсация ошибок (P1-18)](../pipeline2-indexation.md#компенсация-ошибок-p1-18-устранение-противоречия).

**Канонический механизм:** запись чанков и эмбеддингов — в **одной транзакции**. При ошибке — `ROLLBACK` отменяет весь пакет.

| Сценарий | Поведение RAG Builder | Поведение Оркестратора | Результат | Код |
|----------|------------------------|------------------------|-----------|-----|
| JSON Parsing (входной JSON невалиден) | Вернуть `failed` | Перевести документ в `failed` | `status: failed` | `INVALID_INPUT_JSON` |
| Chunking failed (секция не парсится) | Пропустить секцию, продолжить | Логировать warning | `indexed` (с warning) | `SECTION_SKIPPED` |
| Embedding failed (один чанк) | Retry 2 раза (Exponential 2с → 4с), затем пропустить | Логировать warning | `indexed` (с warning) | `EMBEDDING_PARTIAL_FAILED` |
| Embedding failed (все чанки документа) | Retry 2 раза, затем `failed` | Перевести в `failed` | `status: failed` | `EMBEDDING_FAILED` |
| Vector Index (запись в pgvector) failed | **ROLLBACK** (вся транзакция), retry 2 раза (Exponential 1с → 2с) | — (RAG Builder) | — | — |
| Vector Index — `ROLLBACK` невозможен (ошибка после COMMIT) | **Compensating DELETE:** `DELETE FROM rag.document_chunks WHERE document_id = $1 AND indexing_txn_id = $txn_id` (P2-9, новая колонка `indexing_txn_id`) | Логировать `WARN` | Retry на новой транзакции | `COMPENSATION_DELETE` |
| Все retry исчерпаны | Вернуть `failed` | Перевести документ в `failed` с `error_code` | `status: failed` | (см. выше) |

> **`indexing_txn_id`:** уникальный ID индексирующей транзакции (P2-9). Записывается в `rag.document_chunks.indexing_txn_id` при `INSERT`. Используется для compensating DELETE при сбое после COMMIT.

---

## 7. Reprocess: `POST /documents/{doc_id}/reprocess mode=reindex`

**Источник:** [pipeline2-indexation.md §Переиндексация](../pipeline2-indexation.md#переиндексация) и [orchestrator_service_api.md §POST /documents/{doc_id}/reprocess](../../api/orchestrator_service_api.md#post-documentsdoc_idreprocess).

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| `mode: reindex`, статус `indexed` или `failed` (норма) | `DELETE /rag/build/{doc_id}` (RAG Builder) → `POST /rag/build` (после успешного DELETE) | `202 { task_id, mode: "reindex", status: "processing" }` | — |
| `DELETE /rag/build/{doc_id}` вернул ошибку | Отменить переиндексацию, оставить документ в текущем статусе | `status: failed` (reindex cancelled) | `CLEANUP_FAILED` |
| `DELETE` вернул таймаут | Retry 1 раз. При повторном таймауте — `CLEANUP_FAILED` | `CLEANUP_FAILED` | `CLEANUP_TIMEOUT` |
| Документ в `indexing` (активная индексация) | — | `409 DOCUMENT_IN_PROCESSING` | `DOCUMENT_IN_PROCESSING` |
| Документ в `pending_index` (ещё не запущен) | — | `409 DOCUMENT_IN_PROCESSING` | `DOCUMENT_IN_PROCESSING` |
| `mode: chunking_only` (только чанкинг) | Аналогично `reindex`, но без `DELETE` (чанки перезаписываются) | — | — |
| `mode: validation_only` (только Converter-validator) | Только Пайплайн 1 (см. [pipeline1-orchestrator_details.md §10](pipeline1-orchestrator_details.md#10-post-documentsdoc_idreprocess-переобработка)) | — | — |

> **Важно:** при `reindex` обязателен двухшаговый процесс (DELETE → POST). Если DELETE упал, POST **не выполняется** — это предотвращает дубли чанков.

---

## 8. Связь с Pipeline 1

| Сценарий | Поведение Оркестратора | Результат |
|----------|------------------------|-----------|
| Pipeline 1 завершился успешно (`created`) | Создать `pipeline.tasks` для Pipeline 2, статус `pending_index`. Уведомить Scheduler (через запись `processing_status='created'`) | `pending_index` |
| Pipeline 1 завершился с `discarded` | Не запускать Pipeline 2 (черновик отклонён, документа нет) | — |
| Pipeline 1 завершился с `failed` | Не запускать Pipeline 2. Документ не создан | — |
| Pipeline 2 упал (`failed`), Pipeline 1 был `created` | Документ остаётся в `failed`. UI предлагает `reprocess` | `failed` |
| Новая версия (`POST /versions`) | Pipeline 2 запускается заново (новая `version_id`, новая `pipeline.tasks`) | `pending_index` → `indexing` → `indexed` |

---

## 9. Висящие состояния и таймауты

| Состояние | Таймаут | Действие | Код |
|-----------|---------|----------|-----|
| `pending_index` | 1 час | Scheduler → `failed` | `INDEX_TRIGGER_TIMEOUT` |
| `indexing` | 30 минут (настраиваемый) | Scheduler → `failed` | `RAG_BUILDER_TIMEOUT` |
| `indexed` (старше 1 часа) | Проверка каждые 6 часов | При нарушении целостности → `failed` | `INTEGRITY_CHECK_FAILED` |
| `failed` (нет активности > 7 дней) | Уведомление админу | `audit.events` | `STALE_FAILED_DOCUMENT` |

> **См. также:** общая защита от зависших состояний — [overview.md §Глобальные настройки longpoll](../overview.md#глобальные-настройки-longpoll). Circuit Breaker (5 ошибок подряд) — отключение RAG Builder на 30с.

---

## 10. Журналирование

| Артефакт | Хранилище | Назначение |
|----------|-----------|------------|
| `pipeline.tasks` (отдельная запись для Pipeline 2) | Orchestrator DB | Сквозной `task_id` |
| `pipeline.task_steps` (этапы Pipeline 2) | Orchestrator DB | `step_name: "rag_build"`, `service_name: "rag_builder"`, `input_data` (JSON от Registry), `output_data` (`chunks_count`, `index_stats`), `started_at`, `completed_at`, `error_code`, `error_message` |
| `rag.document_chunks` (запись) | RAG Builder DB (pgvector) | `chunk_id`, `document_id`, `indexing_txn_id`, `embedding` |
| `registry.documents.processing_status` | Registry DB | Фактический статус |
| `audit.events` | Audit DB | Аудит изменений статуса |

> **Поведение Оркестратора:**
> - На каждом этапе Pipeline 2 — запись в `pipeline.task_steps`.
> - `severity: ERROR` — для всех `failed` переходов.
> - `severity: WARNING` — для `partial_indexation`, `compensation_delete`.
> - `severity: CRITICAL` — для `INTEGRITY_CHECK_FAILED` (потеря консистентности индекса).

---

## 11. Сводка HTTP-кодов ошибок

| HTTP | Код | Когда |
|------|-----|-------|
| 404 | `DOCUMENT_NOT_FOUND` | Нет документа в Registry |
| 404 | `RAG_BUILDER_NOT_FOUND` | RAG Builder вернул 404 |
| 409 | `DOCUMENT_IN_PROCESSING` | reprocess на активном документе |
| 409 | `DOCUMENT_ALREADY_INDEXED` | Запуск индексации для `indexed` |
| 409 | `INDEXING_IN_PROGRESS` | Параллельный запуск (advisory lock) |
| 500 | `INVALID_INPUT_JSON` | Входной JSON от Registry невалиден |
| 500 | `EMBEDDING_FAILED` | Embedding provider упал |
| 500 | `RAG_BUILDER_INTERNAL_ERROR` | Непредвиденная ошибка RAG Builder |
| 502 | `RAG_BUILDER_UNAVAILABLE` | RAG Builder вернул 5xx |
| 503 | `SERVICE_UNAVAILABLE` | pgvector / Scheduler недоступны |
| (таймаут) | `RAG_BUILDER_TIMEOUT` | Абсолютный таймаут индексации |
| (таймаут) | `INDEX_TRIGGER_TIMEOUT` | `pending_index` > 1 часа |
| (integrity) | `INTEGRITY_CHECK_FAILED` | `chunk_count` mismatch |
| (compensate) | `CLEANUP_FAILED` | DELETE перед reindex упал |

---

## 12. Связанные спецификации и файлы

- [Пайплайн 2: Индексация документа](../pipeline2-indexation.md) — основной поток
- [Сводный обзор пайплайнов](../overview.md) — общая картина
- [API Orchestrator Service](../../api/orchestrator_service_api.md) — эндпоинты
- [API RAG Builder Service](../../api/rag_builder_service_api.md) — детали
- [Пайплайн 1: сценарии поведения Оркестратора](pipeline1-orchestrator_details.md)
- [Пайплайн 3: сценарии поведения (Query Service)](pipeline3-orchestrator_details.md)
- [Глоссарий: статусы документов](../../glossary.md#статусы-документов-registrydocuments)
- [Схема БД (rag.*)](../../database/db_diagrams.md) — таблицы pgvector
- [Specificity.md: LP-V2, LP-V3, LP-V10](../../specificity.md) — открытые вопросы
