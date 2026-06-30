# todo_pipeline.md — Ситуации отказоустойчивости Оркестратора

Сводный набор ситуаций, которые должен учитывать Оркестратор (Pipeline 1: Формирование, Pipeline 2: Индексация), чтобы сервер работал и восстанавливался из любых ситуаций.

**Область применения:** только Оркестратор (8081). Pipeline 3 (Query Service) работает самостоятельно и **не рассматривается**. Горизонтальное масштабирование **не требуется** (single-instance) — ситуации leader election / multi-Scheduler / distributed lock между инстансами не учитываются.

Источники: `docs/pipelines/*`, `guide.md`, `specificity.md`. Пункты — чек-лист для проверки/реализации поведения.

---

## Приоритизация

- **P0 — выживание сервера** (без них «восстанавливается из любых ситуаций» не достигается):
  §1 Отказы внешних сервисов · §2 Краш/рестарт · §3 Идемпотентность · §4 Зависшие состояния · §8 Saga · §12 Longpoll · §13 Celery · §14 Advisory lock · §17 Транзакционность БД.
- **P1 — важно** (повышают надёжность, реальные краши):
  §5 Race conditions · §6 Ошибки данных · §7 Circuit Breaker · §15 Backpressure · §16 Реконнект clients · §18 OOM/resource · §19 Reprocess counter · §20 Cleanup orphaned · §22 Сводная карта ошибок · §23 Env-конфиги.
- **P2 — желательно** (полная полнота, профилактика):
  §9 Health/мониторинг · §10 Инфра-краши извне · §11 Специфичные аномалии · §21 SLO/метрики · §24 Clock drift · §25 Тестирование отказоустойчивости · §26 Cache invalidation · §27 Граничные.

---

## 1. Отказы и недоступность внешних сервисов

### 1.1. Определяемые сервисы
OCR (8088), Parser (8087), Converter-validator (8086), Registry (8084), RAG Builder (8090), MinIO (9000), БД Оркестратора (SQLite/PG), Redis (очередь Celery).

### 1.2. OCR / Parser
- [ ] Таймаут: preview 60с (OCR) / 30с (Parser); full 300с. Retry: preview 1, full 3 (exp 1→2→4с).
- [ ] Недоступность Parser → fallback на OCR (`PARSER_FALLBACK_TO_OCR=true`, `OCR_ENABLED=true`).
- [ ] Полное отключение движка через `PARSER_ENABLED` / `OCR_ENABLED`.
- [ ] Превышение retry → `failed` (full) / `discarded` (preview) с `OCR_FAILED` / `PARSER_FAILED`.

### 1.3. Converter-validator
- [ ] Таймаут: preview 15с (0 retry), full 120с (2 retry, 1→2с).
- [ ] Ошибка извлечения метаданных в preview → `ready_for_approve` с флагом ошибки (не `discarded`).
- [ ] Ошибка структуры JSON в full → `validation.errors`, `failed` (`VALIDATION_FAILED`).

### 1.4. Registry
- [ ] `check-uniqueness` (preview/full): 15с, 1 retry (immediate). Ошибка → `ready_for_approve` (повтор при доступности).
- [ ] Запись документа: 30с, 2 retry (500мс→1с). Откат транзакции, при исчерпании — `failed`.
- [ ] Отличать `502 REGISTRY_UNAVAILABLE` / `503` от бизнес-ошибок (409).
- [ ] Прокси-эндпоинты (`GET /drafts/{id}`, `PATCH /metadata`): проброс ошибок Registry → UI без потери статуса.

### 1.5. RAG Builder
- [ ] Запуск индексации: embeddings 300с (5 мин), retry 2 (2→4с). Vector Index запись 60с, retry 2 (1→2с).
- [ ] Целостность: post-indexation self-check + фоновая проверка Scheduler (каждые 6ч).
- [ ] `indexed → failed` при `INTEGRITY_CHECK_FAILED` (chunk_count != expected / embedding IS NULL / дубли `chunk_index`).
- [ ] RAG Search автоматически исключает `processing_status != 'indexed'`.

### 1.6. MinIO
- [ ] Загрузка файла: 60с, 0 retry. Ошибка → удалить запись из БД (компенсация), вернуть 503 `STORAGE_UNAVAILABLE`.
- [ ] Чтение downstream-сервисами — вне зоны, но при отсутствии файла Оркестратор фиксирует `STORAGE_UNAVAILABLE`.

### 1.7. БД Оркестратора и Redis
- [ ] Потеря соединения с БД → `/health/live` = UNHEALTHY, идемпотентное переподключение, процесс не падает.
- [ ] Redis недоступен → Celery не принимает задачи; задачи уже в очереди (ack-late) не теряются, перепланируются после восстановления.
- [ ] Очередь переполнена / worker упал → задача остаётся `active`, не `completed`; Scheduler не считает её зависшей преждевременно (см. §4, §13).

---

## 2. Краш и рестарт процесса/контейнера

- [ ] Celery task упал mid-step → при рестарте worker'а задача возобновима по `task_id` (дубликат блокируется UNIQUE(draft_id, pipeline_type)).
- [ ] Падение Оркестратора mid-flight: незавершённый TaskStep остаётся `active`/`running` → не препятствует рестарту; конкурентный запуск блокируется констрейнтом.
- [ ] `autorestart=false` / `startretries=0`: упавший процесс не бесконечно рестартит, логи не плодятся. Оркестратор должен падать чисто (flush логов, закрытие соединений,.unlock advisory lock в finally).
- [ ] CRLF в entrypoint.sh на Windows → restart loop (`#!/bin/bash\r`). Подстраховка: strip `\r`. Инфра-аномалия.
- [ ] Stale volume `app_logs` — логи прошлых запусков. Чистить `down -v`. На логику не влияет.
- [ ] Graceful shutdown (SIGTERM / docker stop): досрочно закрывать longpoll-соединения, сохранять state шагов, не ронять in-flight HTTP резко.

---

## 3. Восстановление и идемпотентность

- [ ] `POST /drafts` — Idempotency-Key (TTL 1ч): повтор ключа → тот же `draft_id`.
- [ ] `POST /drafts/{draft_id}/preview` — 409 `PREVIEW_IN_PROGRESS` при повторе; второй preview не запускать.
- [ ] Task creation — UNIQUE(draft_id, pipeline_type): конкурент → 409 `TASK_ALREADY_EXISTS`.
- [ ] `decide` для терминального (`approved`/`discarded`) → 409 `DRAFT_ALREADY_DECIDED`.
- [ ] Повторный `reprocess` на активном документе → 409 `DOCUMENT_IN_PROCESSING`.
- [ ] Повторная запись в Registry — `INSERT ... ON CONFLICT (file_hash_sha256) DO NOTHING` → идемпотентна.
- [ ] No-retry для идемпотентных записей: успешный HTTP не повторяется; повтор — только при таймауте/сетевой ошибке.
- [ ] `reprocess` (переиндексация): `DELETE /rag/build/{doc_id}` для очистки, и только при успехе — новый `POST /rag/build`. Ошибка удаления → отмена с `CLEANUP_FAILED`.
- [ ] Rerun забытых задач — Scheduler каждые 5 мин (см. §4).

---

## 4. Зависшие состояния (Scheduler)

Scheduler каждые 5 минут проверяет `registry.drafts` и `registry.documents` напрямую (вне FSM Оркестратора). Оркестратор при срабатывании — НЕ инициирует активных действий, только пишет в `audit.events`.

- [ ] `uploaded` > 1ч → `discarded` с `PREVIEW_TRIGGER_TIMEOUT`.
- [ ] `previewing` > 30 мин → `discarded` с `PREVIEW_TIMEOUT`.
- [ ] `ready_for_approve` > 24ч → `discarded` с `DECISION_TIMEOUT`.
- [ ] `validation` > 1ч → `discarded` с `VALIDATION_TIMEOUT`.
- [ ] `pending_index` > 1ч → `failed` с `INDEX_TRIGGER_TIMEOUT`.
- [ ] Абсолютный таймаут задачи пайплайна — 48ч → `ABSOLUTE_TIMEOUT`.
- [ ] При переходе в `failed` — событие в `registry.document_history` + уведомление ответственному; документ НЕ удаляется (доступен для повторной загрузки).

---

## 5. Race conditions и консистентность

- [ ] Race `check-uniqueness` ↔ `approve-запись` (окно решение-пользователя минуты–часы):
  - на approve пересчитать бизнес-ключ через `POST /validate/metadata`;
  - повторный `POST /registry/documents/check-uniqueness` с актуальным `title_hash_sha256`;
  - `INSERT ... ON CONFLICT (file_hash_sha256) DO NOTHING RETURNING id`;
  - при 409 → `discarded` с `DUPLICATE_FILE_AFTER_APPROVE`, `conflict_document_id` в ответ, `severity: CRITICAL`.
- [ ] `BUSINESS_KEY_DRIFT` — бизнес-ключ изменился между preview и approve → 409.
- [ ] `preview_not_supported=true` → fallback на OCR либо пропуск full-фазы.
- [ ] Double `create_document` — защититься от повторного вызова на одном task_id.
- [ ] Concurrent `decide` для одного draft_id — FSM-матрица (5 actions × 6 stages) → 409 `INVALID_STATE_TRANSITION`.
- [ ] `data.get("id") or data.get("draft_id")` — `0` is falsy (исправлено): всегда брать явный `draft_id`, не падать на id=0.
- [ ] Duplicate steps + Registry 409 (истор. аномалия) — не плодить дубли `task_steps` на повторе.

---

## 6. Ошибки и аномалии данных

- [ ] Пустой файл (0 байт) → 400 `EMPTY_FILE`. < 1 КБ → 400 `FILE_TOO_SMALL`. > 100 МБ → 413 `FILE_TOO_LARGE`.
- [ ] Неподдерживаемый MIME → 422 `UNSUPPORTED_FILE_TYPE`.
- [ ] 0 страниц при approve → 400 `EMPTY_DOCUMENT`. 0 секций при full → 400 `EMPTY_DOCUMENT`.
- [ ] Некорректный JSON metadata в `POST /drafts` → 422.
- [ ] `partially_indexed` — `chunk_count_actual < expected`: документ исключён из RAG Search; candidate на reprocess; UI предупреждение.
- [ ] Неидемпотентное состояние upstream: если preview-артефакты очищены по TTL (7 дней) → full-фаза запускается с самого начала (все страницы).
- [ ] Mock-real gap: расхождения `id` vs `draft_id`, `data["id"]=0` — не ломать логику только на mock-данных.

---

## 7. Circuit Breaker / Retry-политики (глобальные)

- [ ] `max_retries_per_stage` = 3 (default), jitter ±10% (анти thundering herd).
- [ ] Circuit breaker: 5 последовательных ошибок этапа → отключение на 30с.
- [ ] Exponential backoff с jitter; immediate retry — только для операций < 100мс с идемпотентным эффектом.
- [ ] Все retry логировать в `pipeline.task_steps.error_code/error_message` и `GET /documents/{id}/errors`.

---

## 8. Saga-компенсация невосстановимых ошибок

- [ ] `SagaCoordinator.compensate`: при неисправимой ошибке откат выполненных шагов в обратном порядке.
- [ ] Pipeline 1 компенсации: MinIO-запись → удалить из БД; Registry-создание → `DELETE` документ; preview/full — stateless шаги не компенсируются.
- [ ] Pipeline 2: откат транзакции `BEGIN...INSERT...COMMIT` → `ROLLBACK`; при невозможности (ошибка post-COMMIT) → `DELETE FROM rag.document_chunks WHERE document_id AND indexing_txn_id`; retry перед saga.
- [ ] Order: retry → saga → fallback; не комбинировать произвольно.

---

## 9. Health, мониторинг, трассировка

- [ ] `/system/health`, `/health/live`, `/health/ready`: при недоступности БД/Redis — UNHEALTHY, но процесс не крашится.
- [ ] Корреляционные заголовки во всех downstream: `X-Request-ID`, `X-Trace-ID`, `X-User-ID`, `X-Draft-ID`, `X-Document-ID`.
- [ ] OTEL SDK включён (`main.py`): spans на steps, ошибки помечены.
- [ ] `GET /tasks*`, `/tasks/stats` — мониторинг pipeline-задач (active/completed/failed).
- [ ] Аудит: `audit.events` severity CRITICAL/ERROR/WARNING; `pipeline.task_steps` на каждом вызове (в т.ч. при ошибке).

---

## 10. Инфраструктурные краши и восстановление извне

- [ ] Auth Service (8082) `MissingGreenlet` — чужая зона, но Gateway возвращает 401/403 ⇒ Оркестратор корректно отвечает при недоступных User-ID (не 500).
- [ ] Gateway Mock ImportError — зона Gateway; Оркестратор работает автономно.
- [ ] Миграции БД во время работы: Оркестратор должен переживать unavailable-момент (retry health), не падать насмерть.
- [ ] Partial network partition внутри Docker-сети `internal`: отличать connection-refused (сервис упал) от timeout (висит) — разные retry-стратегии.
- [ ] После рестарта с volumes/logs — не доверять stale state, перечитывать `pipeline.tasks` / `registry.drafts`.

---

## 11. Специфичные аномалии (specificity)

- [ ] `DATABASE_URL` — обязательный (без default): быстрый отказ, а не молчаливый SQLite-фолбэк в проде.
- [ ] Сериализация JSONB для SQLite (тесты) ≠ прод-PG: не опираться на JSON-операторы в логике оркестратора.
- [ ] Celery задачи через `_run_async` — корректно завершать event-loop при ошибке, не течь.
- [ ] Longpoll в тестах — дефолт 15с, не завышать.
- [ ] PATCH /metadata (Pydantic-схема, Optional preview_metadata) — опциональные поля не ломают partial update.
- [ ] Preview status дедупликация в раннем return — не плодить дубли step-записей.
- [ ] approve/proceed/force_new_version — обязательная проверка наличия preview.

---

## 12. Longpoll-цикл (P1/P2) — P0

Longpoll 15с (`poll_interval` 1с серверная) — основной механизм ожидания в Pipeline 1 (preview/full) и Pipeline 2 (indexing).

- [ ] **Обрыв клиентского соединения mid-longpoll** (UI закрыл вкладку / Gateway timeout): сервер корректно закрывает соединение, не оставляет «зомби»-обработку, не блокирует event-loop.
- [ ] **Зависание downstream > 15с**: сервер возвращает текущий прогресс (нефинальный статус), клиент повторяет. Оркестратор отличает «indexing в процессе» от «висит» (по `updated_at` шага).
- [ ] **Крах Оркестратора во время удержания longpoll**: task остаётся `active`/`running`, после рестарта клиент повторяет longpoll и получает прогресс; НЕ создавать новую задачу.
- [ ] **Накопление longpoll-соединений на один документ** — resource leak (FD, coroutines). Лимит одновременных longpoll на `document_id` / `draft_id`.
- [ ] **Gateway timeout < суммарного ожидания** (Gateway режет 30–60с раньше 15с×N циклов): Gateway возвращает 502/empty, клиент обязан повторять по получении.
- [ ] **Longpoll на терминальном статусе**: при `completed`/`failed` — немедленный ответ без ожидания 15с.

---

## 13. Celery-надёжность — P0

- [ ] **Visibility timeout**: задача у упавшего/зависшего worker'а возвращается в очередь после `visibility_timeout` → повторная выдача (at-least-once). Защита — только идемпотентность (UNIQUE-констрейнты, step-level state).
- [ ] **At-least-once семантика**: задача может выполниться дважды (redelivery после worker crash, partition Redis↔worker). Дублирующие side-effect'ы блокируются: UNIQUE(draft_id, pipeline_type), ON CONFLICT, step_idempotency_key.
- [ ] **Dead-letter / poisoned messages**: задача валит worker каждый retry (бесконечный цикл). Нужен `max_retries` Celery + отправка в DLX / пометка task `failed` (не зависать в `active`).
- [ ] **OOM-kill worker'а mid-step**: OS убивает процесс — равносильно visibility_timeout. Защита идемпотентностью + step-progress checkpoint.
- [ ] **Revoked tasks**: отменённая задача (revoke) корректно завершает in-flight step, не оставляет half-written state.
- [ ] **Prefork vs solo**: при prefork падение child не роняет worker; при solo — падает весь worker. Учитывать при планировании.
- [ ] **Переполнение очереди / backpressure**: queue depth → reject / slow consumer, не копить бесконечно (см. §15).
- [ ] **ack-late**: задача не ack'ается до завершения → при crash возвращается в очередь (надёжность + двойное выполнение).
- [ ] **`_run_async` обёртка**: корректно завершать event-loop при ошибке, не течь resources.

---

## 14. Advisory lock lifecycle (P2I-7) — P0

Advisory lock удерживается на время индексации (защита от конкурентной переиндексации одного документа).

- [ ] **Holder процесса упал**: PG advisory lock auto-освобождается при закрытии сессии. Но через пул соединений — lock может «висеть». Явный `pg_advisory_unlock` в `finally` + lock-timeout.
- [ ] **Lock завис навсегда** (сессия жива, процесс завис): watchdog, снимающий lock по истечении max-индексации (5 мин × N retry), либо `pg_advisory_lock` с timeout.
- [ ] **Reprocess при занятом lock**: `POST /documents/{id}/reprocess` → 409 `DOCUMENT_IN_PROCESSING`, не ждать.
- [ ] Корреляция: advisory lock ↔ `processing_status='indexing'` — снимаются вместе (атомарно), иначе orphan lock / orphan status.

---

## 15. Backpressure / ограничение входа — P1

- [ ] Массовые `POST /drafts` (1000 одновременных): rate-limit / semaphore на создание tasks, лимит concurrent uploads в MinIO, лимит active Celery tasks.
- [ ] При превышении → 429 Too Many Requests / 503 с `Retry-After`, не 500.
- [ ] Очередь Celery переполнена → reject новых задач с 503, не копить бесконечно.
- [ ] Semaphore на concurrent downstream-вызовы к тяжёлым сервисам (OCR/RAG Builder), чтобы не положить их под нагрузкой.

---

## 16. Реконнект service clients (httpx pool) — P1

- [ ] Connection pool exhaustion при множестве таймаутов: лимит connections, keep-alive, recycle.
- [ ] Реконнект после восстановления сервиса: не держать stale connections, retry с backoff.
- [ ] Circuit breaker per-client (не глобальный): упавший OCR не отключает Registry.
- [ ] Таймауты клиентов: `connect` и `read` отдельно, не один общий.

---

## 17. Транзакционность БД Оркестратора — P0

- [ ] `UPDATE pipeline.tasks SET status=...` + `INSERT pipeline.task_steps` — атомарно (одна транзакция). Если БД упала между ними → inconsistent.
- [ ] SQLite (тесты) vs PG (прод): атомарность работает, но JSONB-операторы отличаются — не опираться в логике.
- [ ] Compensating write при обнаружении orphan step (step без task / task без финального step).
- [ ] DDL во время работы (миграции) — schema lock: Оркестратор должен retry, не падать (см. §27).

---

## 18. OOM / Docker resource limits — P1

- [ ] Процесс убит по памяти (OOM-killer): при рестарте состояние из БД восстанавливается, in-memory кэши — нет (приемлемо).
- [ ] Ограничения FD (file descriptors): longpoll-соединения + httpx-pool + БД-пул → упереться в ulimit. Мониторинг.
- [ ] CPU throttling (Docker limits): замедление → таймауты срабатывают преждевременно. Учитывать при настройке timeout.

---

## 19. Reprocess retry counter — P1

- [ ] Защита от бесконечного `POST /documents/{id}/reprocess`: max attempts (например 3), backoff между попытками, счётчик в `pipeline.tasks` или `registry.documents`.
- [ ] При превышении → 429/409 `REPROCESS_LIMIT_EXCEEDED`, не запускать.

---

## 20. Cleanup orphaned data — P1

- [ ] `discarded` drafts: периодическая очистка после N дней (аудит сохраняется).
- [ ] Stale `pipeline.tasks` без прогресса > absolute timeout → `failed` (см. §4).
- [ ] Orphan MinIO-объекты: MinIO ok, БД-запись упала → компенсация удалить объект. БД ok, MinIO упал → `file_missing`.
- [ ] Preview-артефакты TTL 7 дней — есть; остальные cleanup-политики — добавить.

---

## 21. SLO / метрики / alerting — P2

- [ ] p99 latency по этапам, error-rate по сервисам, queue-depth Celery, retry-count per step, longpoll-cycle count.
- [ ] Alerting пороги: error-rate > X%, queue-depth > Y, retry-exhausted > Z.
- [ ] OTEL spans + metrics экспорт.

---

## 22. Сводная карта «сбой → код → поведение UI» — P1

Единая таблица (канон взята из `pipeline1-orchestrator_details.md §13` + `guide.md` Error codes):

| HTTP | code | Условие | Поведение UI | Восстановление |
|------|------|---------|--------------|----------------|
| 400 | `EMPTY_FILE` / `FILE_TOO_SMALL` / `FILE_TOO_LARGE` | размер | сообщение | новая загрузка |
| 400 | `EMPTY_DOCUMENT` | 0 страниц/секций | сообщение | reprocess |
| 400 | `INVALID_ACTION_FOR_STATUS` | FSM | сообщение | проверить статус |
| 408 | `DECISION_TIMEOUT` / `PREVIEW_TRIGGER_TIMEOUT` | Scheduler | уведомление | новая загрузка |
| 409 | `DUPLICATE_FILE` / `DUPLICATE_FILE_AFTER_APPROVE` | SHA-256 | переход к `conflict_document_id` | — |
| 409 | `DRAFT_ALREADY_DECIDED` / `PREVIEW_IN_PROGRESS` / `TASK_ALREADY_EXISTS` / `DOCUMENT_IN_PROCESSING` | идемпотентность | сообщение | ждать / новый запрос |
| 409 | `BUSINESS_KEY_DRIFT` / `INVALID_STATE_TRANSITION` | консистентность | сообщение | перепроверить |
| 422 | `UNSUPPORTED_FILE_TYPE` / `VALIDATION_ERROR` / `VALIDATION_FAILED` / `PREVIEW_NOT_SUPPORTED` | данные | сообщение | исправить |
| 500 | `INTERNAL_ERROR` | непредвиденное | retry | залогировать |
| 502 | `OCR_FAILED` / `PARSER_FAILED` / `CONVERTER_UNAVAILABLE` / `REGISTRY_UNAVAILABLE` | downstream 5xx | retry / fallback | ждать восстановления |
| 503 | `SERVICE_UNAVAILABLE` / `STORAGE_UNAVAILABLE` | MinIO/БД | retry с backoff | ждать |
| — | `INTEGRITY_CHECK_FAILED` / `PENDING_TIMEOUT` / `PIPELINE_TIMEOUT` / `ABSOLUTE_TIMEOUT` | внутренние | admin-уведомление | reprocess |

- [ ] Проверить, что каждый код возвращается именно в указанных условиях (расхождение docs vs code — историческая аномалия).

---

## 23. Env-конфиги (ситуация → флаг → поведение) — P1

| Флаг | Поведение при `true` | Поведение при `false` |
|------|----------------------|------------------------|
| `PARSER_ENABLED` | Parser пробуется первым (parser-first) | Parser отключен, сразу OCR |
| `OCR_ENABLED` | OCR доступен как fallback и как основной | OCR отключен, только Parser |
| `PARSER_FALLBACK_TO_OCR` | при недоступности Parser / `preview_not_supported` → OCR | ошибка Parser → `failed`/`discarded` |
| `DATABASE_URL` | прод-PG | (нет default — отказ старта) |
| `MOCK_MODE` (service clients) | mock-ответы | реальные HTTP-вызовы |

- [ ] Проверить, что отключение обоих (`PARSER_ENABLED=false` AND `OCR_ENABLED=false`) даёт понятную ошибку, не падает молча.

---

## 24. Clock drift / NTP — P2

- [ ] Таймауты Scheduler отсчитываются по `created_at`/`updated_at` timestamp. Рассинхрон часов Оркестратор ↔ БД → преждевременные/поздние `failed`.
- [ ] Использовать `now()` БД (не app-clock) для таймстампов состояния; Scheduler сравнивает с БД-временем.

---

## 25. Тестирование отказоустойчивости — P2

- [ ] Chaos / fault injection: убить downstream mid-call, уронить БД mid-transaction, убить worker mid-step.
- [ ] Сопоставить с покрытием (`guide.md` Coverage): saga, race, full_phase_errors, state_machine, consistency уже есть; **longpoll-cleanup, visibility-timeout redelivery, advisory-lock-recovery** — проверить наличие.
- [ ] Тест: двойное выполнение Celery-задачи (redelivery) → идемпотентность.
- [ ] Тест: крах Оркестратора mid-longpoll → повторный longpoll получает прогресс, не создаёт дубль.

---

## 26. Cache invalidation — P2

- [ ] Service clients кэшируют справочники (Converter читает справочники Registry) → invalidate при обновлении.
- [ ] Preview-артефакты TTL 7 дней — есть.
- [ ] Локальный кэш метаданных draft между preview и approve → invalidate при PATCH /metadata.

---

## 27. Граничные ситуации — P2

- [ ] **Timeout cascading**: upstream timeout (Gateway 30с) < downstream (OCR 300с) → upstream режет, downstream продолжает вхолостую. Согласовать timeout-каскад или отменять downstream при обрыве upstream.
- [ ] **FSM-guard на неизвестный/кривой `status` в БД**: если в `registry.drafts.status` значение не из FSM (ручная правка, баг миграции) → Оркестратор не падает, логирует, игнорирует/`failed`.
- [ ] **Горячие миграции БД (Alembic)**: schema lock во время работы → retry, не падать. Миграции — offline окна либо online-safe DDL.
- [ ] **Протухшие секреты (JWT signing key)**: массовый 401 от Gateway → Оркестратор не 500 при отсутствии `X-User-ID` на internal-call. Различать external (нужен JWT) vs internal (trusted network).

---

## Финальные принципы восстановления (держать в фокусе)

1. **Сервер отвечает, не падает** — недоступность downstream = degraded answer (502/503 + retry), не 500 crash.
2. **Состояние всегда консистентно** — task_step на каждый вызов, аудит событий, UNIQUE-констрейнты, saga-откат, атомарные транзакции БД.
3. **Перезапуск безопасен** — идемпотентные endpoints, ack-late очереди, visibility-timeout + идемпотентность, Scheduler на зависших, advisory lock в `finally`.
4. **Дубли не создаются** — Idempotency-Key, ON CONFLICT, PREVIEW_IN_PROGRESS / TASK_ALREADY_EXISTS / DOCUMENT_IN_PROCESSING.
5. **Потеря данных исключена** — MinIO+БД+Registry компенсируют друг друга; ничего не удалять без journal; cleanup orphaned.
6. **Логи и трассировка сохраняются** — даже при ошибке шаг пишет step-запись, severity корректный, OTEL spans.
