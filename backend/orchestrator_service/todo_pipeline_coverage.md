# todo_pipeline_coverage.md — Сопоставление `todo_pipeline.md` с кодом + тест-план

Документ сверяет каждый пункт чек-листа `todo_pipeline.md` с реализацией в коде и существующими тестами. По результатам — набор недостающих тестов с привязкой к файлам.

**Обозначения статусов:**
- ✅ реализовано и закрыто тестами;
- ⚠️ реализовано частично / расхождение docs↔code / нужен тест;
- ❌ не реализовано (см. `specificity.md` §3 «Технические долги»);
- ➖ вне зоны (P3/Query Service — не рассматривается).

---

## 0. Сводная статистика сопоставления

| Раздел | ✅ | ⚠️ | ❌ | ➖ | Тестов нужно |
|---|---|---|---|---|---|
| 1. Отказы внешних сервисов | 5 | 4 | 0 | 0 | 4 |
| 2. Краш/рестарт | 1 | 3 | 0 | 0 | 3 |
| 3. Восстановление/идемпотентность | 3 | 3 | 1 | 0 | 5 |
| 4. Зависшие состояния (Scheduler) | 2 | 1 | 0 | 0 | 3 |
| 5. Race conditions | 5 | 2 | 1 | 0 | 3 |
| 6. Ошибки и аномалии данных | 4 | 2 | 0 | 0 | 3 |
| 7. Circuit Breaker | 1 | 2 | 0 | 0 | 3 |
| 8. Saga-компенсация | 1 | 1 | 0 | 0 | 2 |
| 9. Health/мониторинг/трассировка | 2 | 3 | 0 | 0 | 4 |
| 10. Инфра-краши извне | 0 | 1 | 0 | 0 | 1 |
| 11. Специфичные аномалии | 3 | 1 | 1 | 0 | 2 |
| 12. Longpoll-цикл | 1 | 4 | 0 | 0 | 6 |
| 13. Celery-надёжность | 1 | 3 | 0 | 0 | 5 |
| 14. Advisory lock lifecycle | 2 | 3 | 0 | 0 | 4 |
| 15. Backpressure | 0 | 0 | 0 | 0 | 2 (новый код) |
| 16. Реконнект httpx-pool | 1 | 2 | 0 | 0 | 3 |
| 17. Транзакционность БД | 0 | 1 | 0 | 0 | 2 |
| 18. OOM / resource limits | 0 | 0 | 0 | 0 | ➖ (chaos-уровень) |
| 19. Reprocess retry counter | 0 | 1 | 0 | 0 | 2 |
| 20. Cleanup orphaned | 1 | 1 | 0 | 0 | 2 |
| 21. SLO/метрики | 1 | 1 | 0 | 0 | 2 |
| 22. Сводная карта ошибок | 1 | 1 | 0 | 0 | 1 |
| 23. Env-конфиги | 1 | 1 | 0 | 0 | 1 |
| 24. Clock drift | 0 | 0 | 0 | 0 | ➖ (требует clock injection) |
| 25. Тестирование отказоустойчивости | — | — | — | — | целый раздел |
| 26. Cache invalidation | 0 | 1 | 0 | 0 | 1 |
| 27. Граничные | 0 | 2 | 0 | 0 | 3 |

**Итого:** ~38 пунктов ⚠️/❌ требуют новых или дополненных тестов.

---

## 1. Отказы и недоступность внешних сервисов

### 1.2. OCR / Parser
- ✅ `tests/unit/test_celery_tasks_all.py::TestRunOcrPreviewStep/TestRunParserPreviewStep` — happy/failure paths.
- ⚠️ **fallback Parser→OCR** в `app/core/pipeline/orchestrator.py::on_step_failed` (строки 1493–1555). Тест `test_full_phase_errors.py::TestOnStepFailedRetry::test_on_step_failed_retries_with_backoff` покрывает retry, но **не покрывает OCR-fallback-ветку**.
- ⚠️ Отключение через `PARSER_ENABLED=false` / `OCR_ENABLED=false` — тестов нет.

### 1.3. Converter-validator
- ✅ `tests/unit/test_celery_tasks_all.py::TestRunConverterPreviewStep/TestRunConverterFullStep`.
- ⚠️ Preview-ошибка → `ready_for_approve` с флагом ошибки (не `discarded`) — поведение в коде, но **тест не выделен** явно.

### 1.4. Registry
- ✅ `tests/test_service_clients_registry.py::test_check_uniqueness_duplicate`.
- ⚠️ Запись документа с 409 + saga-компенсация — частично в `tests/orchestrator/test_race_conditions.py::TestApproveDraftCreateDocumentError`.
- ⚠️ Проксирование 5xx Registry → UI: тестов нет.

### 1.5. RAG Builder
- ✅ `tests/unit/test_celery_tasks_all.py::TestRunRagIndexStep` (happy/lock_held/integrity_check_failure).
- ✅ `tests/unit/test_integrity_check.py::TestBackgroundIntegrityCheck`.
- ⚠️ `partially_indexed` ветка — не покрыта (см. `pipeline1-orchestrator_details.md §13`).
- ⚠️ `delete_index` ошибка при reprocess (`CLEANUP_FAILED`) — частично `TestDeleteFromVectorIndex`, нет позитивной проверки.

### 1.6. MinIO
- ✅ `conftest.py` мокает `upload_file` (см. `specificity.md §3.7`).
- ❌ Тест компенсации «MinIO ok → БД упала» — отсутствует (требуется fault injection на БД).

### 1.7. БД и Redis
- ⚠️ Health при недоступности БД — **расхождение docs↔code**: `health_ready` (`app/api/v1/endpoints/health.py:73-86`) не делает реальный `SELECT 1`, только импортирует `get_db`. Тест `tests/test_health.py::test_health_ready_returns_ready` — статичный.
- ⚠️ Redis недоступен: `app/celery_app.py` не имеет fallback, нет теста деградации.

**Тесты, которые нужно создать (раздел 1):**
- `tests/orchestrator/test_parser_ocr_fallback.py::TestParserToOcrFallback` — параметризованный happy/failure: parser fail → ocr-fallback создаёт новый step, не retry.
- `tests/unit/test_pipeline_repository.py::TestServiceDisabledFlags` — `PARSER_ENABLED=false` → preview возвращает ошибку сразу, `OCR_ENABLED=false` → fallback отключён.
- `tests/test_health.py::TestHealthReadyDbDown` — БД недоступна (мок сессии raises) → `/health/ready` отдаёт 503 или degraded.
- `tests/orchestrator/test_registry_proxy_errors.py::TestRegistryProxyErrors` — 5xx Registry при `GET /drafts/{id}` пробрасывается, не теряется.

---

## 2. Краш и рестарт

- ✅ Удаление БД-записи при MinIO-ошибке: тест в `tests/orchestrator/test_full_phase_errors.py` косвенно.
- ⚠️ **Celery mid-step crash** — код в `app/celery_app.py` (`task_acks_late=True`) рассчитан на это, но **отсутствует тест на повторное выполнение** (redelivery). См. §13.
- ⚠️ **Крах Оркестратора mid-longpoll** — нет теста (см. §12).
- ⚠️ **Graceful shutdown** — `app/main.py::lifespan` (строки 22–59) вызывает `engine.dispose()`, но **longpoll-соединения и in-flight HTTP не отменяются явно**; `httpx.AsyncClient.aclose()` на service clients тоже нет. Тестов нет.

**Тесты (раздел 2):**
- `tests/integration/test_graceful_shutdown.py::TestGracefulShutdown` — в Task в работе, затем SIGTERM, проверять: state-task `active`/running, после рестарта worker берёт задачу повторно.
- `tests/unit/test_lifespan.py::TestLifespanClosesHttpClients` — фикстура инстанцирует ServiceClient, lifespan закрывает engine, проверять httpx-клиент не висит.
- `tests/test_drafts.py::TestMinioFailureCompensatesDb` — MinIO upload fail → БД-запись draft удалена, не остаётся orphan.

---

## 3. Восстановление и идемпотентность

- ✅ `tests/orchestrator/test_drafts_consistency.py::TestIdempotency` — `test_double_post_drafts_idempotent`, `test_preview_idempotency_409`.
- ✅ `test_delete_after_draft_creation_succeeds` в `tests/orchestrator/test_delete_draft.py`.
- ⚠️ **`POST /drafts/{draft_id}/preview` Idempotency-Key** — код в `drafts.py:650-661` (через `_IDEMPOTENCY_CACHE` in-memory), но в `specificity.md §3.11` явно указано: «Идемпотентность по Idempotency-Key для preview **не реализована**». **Расхождение docs↔code.**
- ⚠️ **`_IDEMPOTENCY_CACHE` — in-memory dict, не переживает рестарт** (`drafts.py:60`). При рестарте — повтор с тем же ключом создаст новый draft.
- ⚠️ **`reprocess` под cleanup-fail (DELETE /rag/build)** — `TestDeleteFromVectorIndex` проверяет happy/failure метода, но не «reprocess при занятом/неудалённом индексе».

**Тесты (раздел 3):**
- `tests/orchestrator/test_idempotency_persistence.py::TestIdempotencyCachePersistence` — после «эквивалента рестарта» (новый app-state) повтор с тем же ключом → в текущей реализации **создаёт новый draft** (зафиксировать как дефект или улучшить до Redis).
- `tests/orchestrator/test_reprocess_cleanup_fail.py::TestReprocessCleanupFailed` — `RAG.delete_index` raise → reprocess возвращает `CLEANUP_FAILED`, task остаётся в текущем статусе, не запускает `build`.
- `tests/orchestrator/test_terminal_draft_replay.py::TestDecideIdempotency` — повторный `decide` для `discarded`/`approved` с тем же body → 409; повторный `decide` с разными полями → 409 (FSM-guard).

---

## 4. Зависшие состояния (Scheduler)

- ✅ `tests/unit/test_celery_tasks_all.py::TestCleanupStaleTasks::test_happy_path` — общий happy.
- ✅ `tests/unit/test_celery_tasks_all.py::TestRunRagIndexStep::test_lock_held_skips`.
- ⚠️ `cleanup_stale_tasks` (`app/core/pipeline/orchestrator.py:1652–1704`) обрабатывает: stale running > `MAX_JOB_RUNNING_TIME`, stale pending > `PENDING_STATE_TIMEOUT` (30с), absolute timeout > `ABSOLUTE_TASK_TIMEOUT_HOURS` (48ч). **Покрыт только happy**, нет отдельных тестов на каждый из трёх сценариев.

**Тесты (раздел 4):**
- `tests/unit/test_schedulers.py::TestStalePendingTimeout` — task_step `pending` > 30с → `fail_task_step(PENDING_TIMEOUT)`.
- `tests/unit/test_schedulers.py::TestAbsoluteTimeout` — task старше 48ч → `failed` + `error_code=ABSOLUTE_TIMEOUT`.
- `tests/unit/test_schedulers.py::TestStaleRunningJob` — `current_step_started_at` > `MAX_JOB_RUNNING_TIME` → `failed`.

---

## 5. Race conditions и консистентность

- ✅ `tests/orchestrator/test_race_conditions.py::TestApproveDraftCreateDocumentError` (Registry 409).
- ✅ `tests/orchestrator/test_race_conditions.py::TestStopDuplicateFlow`, `TestDuplicateDetectionInCreateDraft`.
- ✅ `tests/orchestrator/test_decide_edge_cases.py::TestDecideTerminalEdgeCases` (FSM-матрица).
- ✅ `tests/test_service_clients_registry.py::TestRegistryMockRealGap` (id=0 fix).
- ⚠️ **BUSINESS_KEY_DRIFT** — `specificity.md §3.11` явно: «`BUSINESS_KEY_DRIFT` не реализован». Тест будет xfail.
- ⚠️ Double `create_document` — защита в коде (`saga.compensate`), но **отдельного теста нет**.

**Тесты (раздел 5):**
- `tests/orchestrator/test_business_key_drift.py::TestBusinessKeyDrift` (xfail) — между preview и approve `validate/metadata` возвращает другой ключ → 409.
- `tests/orchestrator/test_approve_double_call.py::TestApproveDoubleCall` — concurrent approve для одного draft → одна запись в Registry, второй получает 409 или нет дубля документа.

---

## 6. Ошибки и аномалии данных

- ✅ `tests/orchestrator/test_drafts_boundaries.py` — MIME, empty, duplicates.
- ✅ `tests/orchestrator/test_drafts_crud.py` — 422 на пустом файле.
- ⚠️ **Preview-артефакты TTL 7 дней** — в коде нет явной очистки. Cleanup по TTL → `pipeline.task_steps` со старыми `preview_*`? **Тест отсутствует.**
- ⚠️ **Mock-real gap** — `tests/orchestrator/test_drafts_consistency.py::TestMockRealGap` уже есть, но не покрывает все расхождения полей (`id`/`draft_id`).

**Тесты (раздел 6):**
- `tests/orchestrator/test_orphan_data_cleanup.py::TestPreviewArtifactsTtl` — TaskStep `preview_*` старше 7 дней → фоновый job (отдельный scheduler) удаляет/архивирует.
- `tests/orchestrator/test_mock_real_alignment.py::TestAllResponseKeys` — параметризованный список всех endpoints, mock-ответ содержит все документированные поля.

---

## 7. Circuit Breaker / Retry-политики

- ✅ `tests/test_base_client.py::SimpleTestClient::test_call` — базовая обёртка.
- ⚠️ **`CircuitBreakerError` → mock fallback** в `app/services/base_client.py:188-202` (строки 188-202) — **не покрыто тестом**: открыт CB → метод возвращает `mock_response`, не 5xx.
- ⚠️ **Per-service CB (разные сервисы независимо)** — `app/services/base_client.py:81` создаёт CB per-сервис (`name=f"cb_{service_name}"`). Теста на изоляцию нет.

**Тесты (раздел 7):**
- `tests/test_base_client.py::TestCircuitBreakerOpen` — 5 ошибок подряд → 6-й вызов возвращает `mock_response` без сетевого запроса (verify `httpx.AsyncClient.request` не вызван).
- `tests/test_base_client.py::TestCircuitBreakerPerServiceIsolation` — `Registry` в OPEN, `OCR` продолжает работать (mock verify).
- `tests/test_base_client.py::TestConnectErrorFallback` — `httpx.ConnectError` (DNS/connection refused) → сразу mock, **без retry** (verify tenacity не вызван).

---

## 8. Saga-компенсация

- ✅ `tests/unit/test_saga_compensation.py::TestSagaCoordinator::test_compensate_registry_creation` (P1).
- ✅ `test_double_post_drafts_idempotent` и др. (вспомогательные).
- ⚠️ **`rag_index` → `delete_from_vector_index`** компенсация — есть в коде, но **отдельный тест на это** отсутствует.
- ⚠️ **Идемпотентность самой компенсации** (если упала на полпути, повторный запуск compensate не дублирует DELETE) — нет.

**Тесты (раздел 8):**
- `tests/unit/test_saga_compensation.py::TestCompensateRagIndex` — запись чанков, fail task, saga → DELETE `rag.document_chunks` для `document_id`.
- `tests/unit/test_saga_compensation.py::TestCompensationIdempotency` — повторный `compensate` для уже скомпенсированной задачи → не вызывает DELETE повторно (или вызывает, но без эффекта).

---

## 9. Health, мониторинг, трассировка

- ✅ `tests/test_health.py::TestHealthEndpoint`, `TestHealthLivenessReadiness` — health/live/ready.
- ⚠️ **`/system/health` возвращает захардкоженный `services_status`** (`app/api/v1/endpoints/health.py:22-50`): **никогда не показывает degraded**, даже если downstream упал. Это **расхождение docs↔code**: документ говорит «degraded при ошибке», код всегда `ok`.
- ⚠️ **`/health/ready` docstring обещает `Checks database connectivity`**, но в коде — никакого `SELECT 1`, только импорт.
- ⚠️ **OTEL spans** — `setup_otel` есть, тестов на наличие span'ов нет.

**Тесты (раздел 9):**
- `tests/test_health.py::TestSystemHealthAggregate` — параметризованный: для каждого downstream (RAG, OCR, Registry) — mock raises → `services_status[svc] != "ok"`, итог `degraded`.
- `tests/test_health.py::TestHealthReadyDbCheck` — реальный `Depends(get_db)` + mock `engine.begin()` raises → ответ содержит `"database": "offline"`.
- `tests/test_health.py::TestOtelSpansEmitted` — вызов любого endpoint → в exporter'е появился span с `service.name="orchestrator"`.

---

## 10. Инфра-краши извне

- ⚠️ Auth Service `MissingGreenlet` — внешняя зона, но в `app/api/deps/` нет проверки `X-User-ID is None` после обрыва Gateway. Тест отсутствует.

**Тесты (раздел 10):**
- `tests/api/v1/test_internal_call_user_id_missing.py::TestUserIdMissing` — internal-call без `X-User-ID` (Gateway down) → 401/403, не 500.

---

## 11. Специфичные аномалии (specificity)

- ✅ `tests/test_config.py::test_default_mock_mode`, `test_default_service_urls`.
- ✅ `tests/test_service_clients_registry.py::TestRegistryMockRealGap::test_get_draft_id_zero_no_draft_id_after_fix` (id=0).
- ⚠️ `DATABASE_URL` без default — **код падает при старте**, тест не покрывает сообщение ошибки и exit code.
- ⚠️ Сериализация JSONB для SQLite vs PG — поведение SQLite в `tests/unit/test_pipeline_repository.py` есть, но не параметризовано (не показано, что в PG будет так же).
- ❌ `approvals` Action `confirm` — `specificity.md §3.11`: «не реализован в коде». Тестов нет (xfail не нужен — фича отсутствует).

**Тесты (раздел 11):**
- `tests/test_config.py::TestDatabaseUrlRequired` — unset `DATABASE_URL` → `ValidationError`, не молчаливый SQLite.
- `tests/unit/test_pipeline_repository.py::TestJsonbSerialization` — параметризация SQLite/PG (skip PG в CI).

---

## 12. Longpoll-цикл (P1/P2) — критичный P0

- ✅ `tests/test_drafts.py::test_preview_status_with_longpoll`, `test_preview_status_longpoll_zero`, `test_preview_status_invalid_longpoll` (422 при >60).
- ✅ `tests/test_documents_api.py::TestDocumentStatus::test_status_supports_longpoll_param`.
- ⚠️ **`_wait_for_preview` (drafts.py:800-856)** — polling-loop с `asyncio.sleep(1.0)`. **Не покрыты**:
  - обрыв клиента mid-poll (cancelled task);
  - накопление longpoll'ов на один draft (concurrency limit);
  - поведение при term-сигнале (graceful);
  - сравнение с upstream longpoll endpoint'ом (RAG, Registry) — разные источники истины.
- ⚠️ Longpoll на терминальном статусе → немедленный ответ — частично в `get_preview_status` (early return), но **теста нет**.

**Тесты (раздел 12):**
- `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_returns_immediately_on_terminal` — task `failed` + `longpoll=15` → ответ < 1с.
- `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_client_cancellation` — открыть longpoll в Task, через 0.5с отменить task; verify сервер не падает, connection cleanup.
- `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_concurrent_limit` — N=10 одновременных longpoll на один draft → не блокируют друг друга, нет resource leak.
- `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_returns_current_progress_on_timeout` — step всё `running` после 1с polling → ответ `processing` (не ждёт 15с впустую).
- `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_status_idempotent` — повторный longpoll после `completed` → мгновенно, без повторного poll.
- `tests/integration/test_draft_to_document_flow.py::TestLongpollAfterRestart` — longpoll во время рестарта → после восстановления клиент получает прогресс (не 502).

---

## 13. Celery-надёжность — критичный P0

- ✅ `tests/unit/test_celery_tasks_all.py` — 10 pipeline-задач + happy/failure.
- ✅ `TestCleanupStaleTasks::test_happy_path`.
- ⚠️ **visibility timeout / redelivery (at-least-once)** — `task_acks_late=True` в `app/celery_app.py:62`. **Нет теста**: задача выполнена до ack, имитация crash → задача redelivered → должна выполниться повторно **без дублей** (idempotency: UNIQUE, ON CONFLICT).
- ⚠️ **Poisoned message** — нет `max_retries` на уровне Celery-task, нет DLX. Теста нет.
- ⚠️ **OOM-kill worker'а** — нет теста (требует cgroup/signal).
- ⚠️ **Revoked tasks** — `task.revoke()` не покрыт.
- ⚠️ **`_run_async` утечка** — `app/tasks/scheduler.py:14-19` создаёт `new_event_loop()` per-call, закрывает в `finally`. Тест на корректное закрытие loop'а при исключении отсутствует.

**Тесты (раздел 13):**
- `tests/unit/test_celery_redelivery.py::TestCeleryRedeliveryIdempotent` — имитация Celery redelivery (вызвать `.run()` дважды с одинаковым task_id) → verify `task_id` не создаёт дублей, step-progress checkpoint, UNIQUE-констрейнты держат.
- `tests/unit/test_celery_redelivery.py::TestPoisonedMessage` — задача всегда raises → после N retry → task `failed` + `error_code=POISONED_MESSAGE`, **не** бесконечный retry.
- `tests/unit/test_celery_redelivery.py::TestRunAsyncClosesEventLoop` — `_run_async(coro_that_raises)` → loop закрыт, `loop.is_closed() == True`, нет warning `unclosed event loop`.
- `tests/unit/test_celery_redelivery.py::TestTaskRevokedMidExecution` — Celery `revoke(task_id)` + проверка in-flight step корректно завершается (graceful stop).
- `tests/integration/test_redis_unavailable.py::TestRedisBrokerDown` — Redis mock raises → publish task → task помечена в `pending`, не теряется; после восстановления Redis — выполняется.

---

## 14. Advisory lock lifecycle (P2I-7) — критичный P0

- ✅ `tests/unit/test_pipeline_repository.py::TestTaskRepository::test_task_lock_unlock`.
- ✅ `tests/unit/test_celery_tasks_all.py::TestRunRagIndexStep::test_lock_held_skips`.
- ⚠️ **ВНИМАНИЕ: docs говорят `pg_advisory_xact_lock` (guide.md §P2I-7), код использует in-DB row-level lock через `locked_by` / `locked_at`** (`app/repositories/pipeline.py:101-119`). Это **другая семантика**: 
  - нет `pg_advisory_xact_lock` → lock не держится на уровне PG-сессии;
  - в коде `lock_task` (`pipeline.py:101-109`) делает `get_task_for_update` (row lock) + запись `locked_by`/`locked_at`.
- ⚠️ **Holder процесса упал → lock не auto-release** (нет `pg_advisory_unlock` / нет try/finally в Celery task) — lock висит, пока `unlock_task` явно не вызван. **Тест: holder упал, новый worker не может залочить → должен ли ждать таймаут или прерываться.**
- ⚠️ **Lock TTL/watchdog** — нет: `locked_at` не сравнивается с `now()` в `lock_task`. Старый lock не освобождается автоматически.
- ⚠️ **Reprocess при занятом lock** — `TestRunRagIndexStep::test_lock_held_skips` уже есть.

**Тесты (раздел 14):**
- `tests/unit/test_pipeline_repository.py::TestLockHolderCrashed` — task.locked_by=worker-1, locked_at=now-10min; вызвать `lock_task` worker-2 → успешно (lock «протух», но **в коде это не обрабатывается** — должно или fail, или автозахват. Тест зафиксирует текущее поведение).
- `tests/unit/test_pipeline_repository.py::TestLockReleasedOnTaskError` — step raises → Celery task снимает lock в `finally`/`on_step_failed` → verify `unlock_task` вызван.
- `tests/unit/test_pipeline_repository.py::TestLockStaleTimeout` — параметризованный `lock_age_seconds` — при `> MAX_JOB_RUNNING_TIME` Scheduler снимает lock (требует реализации watchdog в `cleanup_stale_tasks`).
- `tests/unit/test_pipeline_repository.py::TestRaceDoubleLock` — два concurrent `lock_task` для одного `task_id` → только один succeed, второй получает `None` или `locked_by != self`.

---

## 15. Backpressure / ограничение входа — P1 (нужен новый код)

- ❌ **Реализации нет**: rate-limit, semaphore на POST /drafts, лимит concurrent uploads.
- ❌ Тестов нет (только после реализации).

**После реализации — тесты:**
- `tests/api/v1/test_backpressure.py::TestRateLimitOnDraftUpload` — 1000 одновременных POST → 429/503, не 500.
- `tests/api/v1/test_backpressure.py::TestQueueOverflow` — Celery queue full → 503 с `Retry-After`.

---

## 16. Реконнект service clients (httpx-pool) — P1

- ✅ `tests/test_base_client.py::SimpleTestClient::test_call`.
- ⚠️ **Connection pool exhaustion** — `app/services/base_client.py:65-79` создаёт httpx-pool (50 connections, 100 keepalive). **Тест на exhaustion** отсутствует.
- ⚠️ **Stale connections** (keepalive на упавший сервис) — нет теста.
- ⚠️ **connect vs read timeout** — `app/services/base_client.py:62-69` задаёт отдельно. Тест на различие: connect-refused не retry, read-timeout retry.

**Тесты (раздел 16):**
- `tests/test_base_client.py::TestConnectVsReadTimeout` — `httpx.ConnectError` (refused) → 1 попытка; `httpx.ReadTimeout` → N попыток (verify `tenacity`).
- `tests/test_base_client.py::TestPoolExhaustion` — 51-й одновременный запрос в пул (50) → `httpx.PoolTimeout` → mock fallback.
- `tests/test_base_client.py::TestStaleConnectionReuse` — keepalive к упавшему сервису → 1 retry, восстановление, не блокировка.

---

## 17. Транзакционность БД — P0

- ✅ `tests/unit/test_pipeline_repository.py` — атомарные операции.
- ⚠️ **`create_task` + `create_task_step` атомарны?** (`app/repositories/pipeline.py:27-47` + `create_task_step`) — это два вызова в одной `AsyncSession`, но **нет explicit `BEGIN`/`COMMIT`**. Поведение зависит от session-фабрики.
- ⚠️ **Compensating write для orphan step** — нет.

**Тесты (раздел 17):**
- `tests/unit/test_pipeline_repository.py::TestAtomicTaskCreation` — `create_task` + `create_task_step` в одной транзакции: rollback первой → вторая не зафиксирована.
- `tests/unit/test_pipeline_repository.py::TestOrphanStepDetection` — task_step без parent task → scheduler job cleanup.

---

## 18. OOM / resource limits — P1

- ➖ Chaos-уровень. Требует OOM-killer simulation (через `resource.setrlimit` или cgroup). **Не критично для unit-тестов, рекомендуется в отдельном `tests/chaos/`**.

---

## 19. Reprocess retry counter — P1

- ⚠️ В коде нет max_attempts на `POST /documents/{id}/reprocess` — пользователь может спамить бесконечно.

**Тесты (раздел 19):**
- `tests/orchestrator/test_reprocess_limit.py::TestReprocessMaxAttempts` — 5 reprocess на одном документе → 6-й → 409 `REPROCESS_LIMIT_EXCEEDED` (после реализации).
- `tests/orchestrator/test_reprocess_limit.py::TestReprocessCounterInDb` — счётчик в `pipeline.tasks.reprocess_count` инкрементируется.

---

## 20. Cleanup orphaned — P1

- ✅ `tests/unit/test_celery_tasks_all.py::TestCleanupStaleTasks::test_happy_path`.
- ⚠️ **MinIO-orphan** (БД-удаление, MinIO остался) — теста нет.
- ⚠️ **Preview-артефакты TTL** — теста нет (см. §6).

**Тесты (раздел 20):**
- `tests/orchestrator/test_orphan_data_cleanup.py::TestOrphanMinioCleanup` — `pipeline.tasks` удалён, MinIO-объект остался → cleanup-job (отдельный) удаляет.
- `tests/orchestrator/test_orphan_data_cleanup.py::TestDiscardedDraftsGc` — `discarded` drafts старше 30 дней → job cleanup.

---

## 21. SLO / метрики — P2

- ⚠️ OTEL spans есть, но кастомных метрик (queue depth, retry count, p99) не измерено.

**Тесты (раздел 21):**
- `tests/test_metrics.py::TestOtelRetryCountMetric` — после N retry, в metrics — `orchestrator.pipeline.retry.count` инкремент.
- `tests/test_metrics.py::TestOtelQueueDepthMetric` — Celery queue depth периодически экспортируется.

---

## 22. Сводная карта «сбой → код → UI» — P1

- ✅ `tests/orchestrator/test_documents_status.py` — структура ответов.
- ⚠️ **Полный coverage** всех кодов из `pipeline1-orchestrator_details.md §13` — отсутствует (часть кодов задокументирована, но не возвращается).

**Тесты (раздел 22):**
- `tests/orchestrator/test_error_codes_full.py::TestAllErrorCodesMatrix` — параметризованная матрица (HTTP, code, условие) — вызывать каждый endpoint с условиями → проверить точный код.

---

## 23. Env-конфиги — P1

- ✅ `tests/test_config.py`.
- ⚠️ **PARSER_ENABLED=false + OCR_ENABLED=false** одновременно — теста нет.
- ⚠️ **PARSER_FALLBACK_TO_OCR=false** — поведение при недоступности Parser.

**Тесты (раздел 23):**
- `tests/test_config.py::TestAllServicesDisabled` — `PARSER_ENABLED=false` + `OCR_ENABLED=false` + `PARSER_FALLBACK_TO_OCR=false` → `POST /preview` возвращает понятную ошибку `NO_AVAILABLE_ENGINES`, не падает.

---

## 24. Clock drift — P2

- ➖ Требует mock `datetime.now()` в `cleanup_stale_tasks`. **Можно сделать параметризацией `freezegun` или mock datetime.**

**Тесты (раздел 24):**
- `tests/unit/test_schedulers.py::TestClockDrift` — task с `updated_at` = now-49ч, системные часы перевели вперёд на 2ч → absolute timeout triggers корректно (требует явной работы с БД-time, не app-time).

---

## 25. Тестирование отказоустойчивости — целый раздел P2

Предлагаемые сценарии chaos-уровня (в `tests/chaos/`):
- Убить downstream-сервис mid-call → verify 5xx, не 500; CB открывается после 5 ошибок.
- Убить worker mid-step → verify задача redelivered, идемпотентна.
- Заполнить очередь Celery до лимита → 503 на новых POST /preview.
- Исчерпать FD (ulimit) → service client корректно отдаёт mock fallback, не crash.

---

## 26. Cache invalidation — P2

- ⚠️ `_IDEMPOTENCY_CACHE` (in-memory) — нет TTL-проверки в `tests/`. Тест на TTL отсутствует.

**Тесты (раздел 26):**
- `tests/orchestrator/test_idempotency_ttl.py::TestIdempotencyCacheTtl` — запись в `_IDEMPOTENCY_CACHE` с `created_at = now-2h` → фоновый cleanup или при следующем запросе → запись удалена, новый запрос создаёт draft.

---

## 27. Граничные — P2

- ⚠️ **Timeout cascade** (Gateway 30с < downstream 60с) — не покрыт.
- ⚠️ **FSM-guard на кривой `status`** в БД — `DraftFSM.can_transition` уже ловит (returns False при ValueError), но тест на «незнакомый статус в БД» отсутствует.
- ⚠️ **Горячие миграции БД** — coverage не на уровне unit-тестов.

**Тесты (раздел 27):**
- `tests/test_drafts.py::TestUnknownDraftStatus` — patch `registry.drafts.status = "WAT?"` → `decide` отклоняет с 500/4xx, не падает.
- `tests/api/v1/test_drafts.py::TestTimeoutCascade` — Gateway timeout 0.1с (через mock), downstream отвечает за 1с → клиент получает 502.
- `tests/unit/test_fsm.py::TestFsmCorruptState` — `validate_transition("WAT?", "approved")` → ValueError, не падает.

---

## Сводный список НОВЫХ тестов (приоритет)

### P0 (P0-критичные, 19 тестов)

1. `tests/orchestrator/test_parser_ocr_fallback.py` — OCR-fallback вместо retry.
2. `tests/test_health.py::TestHealthReadyDbDown` — БД недоступна в `/health/ready`.
3. `tests/test_health.py::TestSystemHealthAggregate` — degraded при упавшем downstream.
4. `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_returns_immediately_on_terminal`.
5. `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_client_cancellation`.
6. `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_concurrent_limit`.
7. `tests/test_drafts.py::TestLongpollEdgeCases::test_longpoll_returns_current_progress_on_timeout`.
8. `tests/integration/test_draft_to_document_flow.py::TestLongpollAfterRestart`.
9. `tests/unit/test_celery_redelivery.py::TestCeleryRedeliveryIdempotent` — at-least-once.
10. `tests/unit/test_celery_redelivery.py::TestPoisonedMessage` — DLX.
11. `tests/unit/test_celery_redelivery.py::TestRunAsyncClosesEventLoop` — утечка loop'а.
12. `tests/unit/test_celery_redelivery.py::TestTaskRevokedMidExecution`.
13. `tests/unit/test_pipeline_repository.py::TestLockHolderCrashed`.
14. `tests/unit/test_pipeline_repository.py::TestLockReleasedOnTaskError`.
15. `tests/unit/test_pipeline_repository.py::TestRaceDoubleLock`.
16. `tests/unit/test_pipeline_repository.py::TestAtomicTaskCreation`.
17. `tests/unit/test_schedulers.py::TestStalePendingTimeout`.
18. `tests/unit/test_schedulers.py::TestAbsoluteTimeout`.
19. `tests/unit/test_schedulers.py::TestStaleRunningJob`.

### P1 (10 тестов)

20. `tests/test_base_client.py::TestCircuitBreakerOpen` — CB открыт → mock fallback.
21. `tests/test_base_client.py::TestCircuitBreakerPerServiceIsolation`.
22. `tests/test_base_client.py::TestConnectErrorFallback` — без retry на connect.
23. `tests/test_base_client.py::TestConnectVsReadTimeout`.
24. `tests/test_base_client.py::TestPoolExhaustion` — 51-й запрос.
25. `tests/test_base_client.py::TestStaleConnectionReuse`.
26. `tests/orchestrator/test_idempotency_persistence.py::TestIdempotencyCachePersistence` — in-memory не переживает рестарт (дефект/улучшение).
27. `tests/orchestrator/test_reprocess_cleanup_fail.py::TestReprocessCleanupFailed`.
28. `tests/orchestrator/test_registry_proxy_errors.py::TestRegistryProxyErrors`.
29. `tests/api/v1/test_internal_call_user_id_missing.py::TestUserIdMissing` — без `X-User-ID`.

### P2 (9 тестов, на будущее / после реализации фич)

30. `tests/unit/test_saga_compensation.py::TestCompensateRagIndex`.
31. `tests/unit/test_saga_compensation.py::TestCompensationIdempotency`.
32. `tests/orchestrator/test_orphan_data_cleanup.py::TestPreviewArtifactsTtl`.
33. `tests/orchestrator/test_orphan_data_cleanup.py::TestOrphanMinioCleanup`.
34. `tests/orchestrator/test_orphan_data_cleanup.py::TestDiscardedDraftsGc`.
35. `tests/orchestrator/test_idempotency_ttl.py::TestIdempotencyCacheTtl`.
36. `tests/test_drafts.py::TestUnknownDraftStatus`.
37. `tests/test_drafts.py::TestTimeoutCascade`.
38. `tests/test_config.py::TestAllServicesDisabled`.

---

## Найденные расхождения docs↔code (для `specificity.md` / `todo_fix_docs_vs_code.md`)

1. **`/health/ready`** не делает `SELECT 1` — обновлять docstring или реализовать.
2. **`/system/health`** всегда возвращает `ok` — нужно опрашивать downstream или хотя бы сделать `services_status` пустым dict'ом для тестирования.
3. **Idempotency-Key для `POST /preview`** — `specificity.md §3.11` говорит «не реализовано», код в `drafts.py:650-661` имеет реализацию. **Либо код, либо документ ошибается.**
4. **`pg_advisory_xact_lock` vs in-DB row-lock** — guide.md P2I-7 говорит advisory lock; код использует `locked_by`/`locked_at`. **Это не одно и то же.** Watchdog и TTL для in-DB lock отсутствуют.
5. **`auto_approve` / `validation` / `review_required` статусы** — `app/core/fsm.py::DraftState` enum содержит только 5 состояний (нет `validation`, `review_required`); `app/core/pipeline/orchestrator.py::_check_auto_approve` упоминает их в коде, но FSM-валидация не покрывает.
6. **CLEANUP_FAILED** для reprocess — документирован, но **в коде не возвращается как `409`** (`run_reprocess_step` обрабатывает, но не выдаёт явный код).
7. **`BUSINESS_KEY_DRIFT`** — задокументирован, не реализован.
8. **Сейчас `_IDEMPOTENCY_CACHE` — in-memory dict, не Redis**, как требует `specificity.md §3.10`.
