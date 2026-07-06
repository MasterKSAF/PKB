# Аудит `orchestrator_service` — качество процессинга задач

Аудит охватывает: алгоритмы планирования/диспетчеризации пайплайна, обработку шагов, отказоустойчивость (таймауты, retry, fallback, soft/hard kill), конкурентность и блокировки, транзакционную консистентность, дублирование кода и покрытие тестами.

Анализ выполнен по коду на диске (символы получены через `codegraph_explore` + точечные чтения ключевых мест). Линии указаны на момент аудита.

---

## 1. Краткая оценка

| Измерение | Оценка | Комментарий |
|---|---|---|
| Архитектура диспетчеризации | Средне | Понятная FSM-структура (upload → preview → decision → full → registry → indexation), но смешаны слои: оркестратор ходит в Celery и внешние сервисы напрямую, а Celery-задачи дергают оркестратор — циркулярная связь. |
| Алгоритмы очереди | Ниже среднего | FIFO + лимит слотов, но проверка лимита не атомарна с постановкой в `active` → возможен перебор лимита (`MAX_CONCURRENT_TASKS`). |
| Retry/fallback | Средне | Логика есть, но расходится между Celery-retry и orchestrator-retry → двойные/несогласованные retry-счетчики, дублирующиеся `TaskStep`. |
| Отказоустойчивость | Ниже среднего | Много таймаутов, но `cleanup_stale_tasks` помечает шаги `failed` БЕЗ вызова `on_step_failed` → задача «зависает» до абсолютного 48h-таймаута. |
| Блокировки | Средне | `FOR UPDATE` используется, но избыточно: любой `update_task_status` берёт row-lock даже на read-only обновления прогресса. |
| Транзакции | Слабо | Внешние сайд-эффекты (Registry, RAG) выполняются до commit БД → нет outbox, возможна рассинхронизация БД и внешних сервисов. |
| Покрытие тестами | Ниже среднего | `_notify_step_*`, `BackgroundTaskPoller`, `DraftTaskItem` не покрыты; репозиторий `get_stale_running_steps_for_hard_kill` дублирован (тест не ловит). |

---

## 2. Архитектура — недочёты

### 2.1. Циркулярная связка «Оркестратор ↔ Celery-задачи»
`PipelineOrchestrator._enqueue_celery_tasks` напрямую дёргает `run_parser_preview_step.delay(...)` из `app.tasks.pipeline_formation`, а Celery-задачи через `_notify_step_completed/_notify_step_failed` снова зовут `PipelineOrchestrator.on_step_*`. Это создаёт двустороннюю жёсткую зависимость `core ← tasks`, мешает тестировать оркестратор изолированно и затрудняет замену транспорта (например, на стримы/очереди без Celery).

**Рекомендация:** ввести `StepDispatcher`/`StepQueue` интерфейс в `core/`, оркестратор зависит от абстракции; Celery-задачи — её реализация. Уведомления в оркестратор подавать через единый `notify_step_outcome()` utan импорта Celery из модуля оркестратора.

### 2.2. `on_step_completed` нарушает SRP и длинный
Метод одновременно: находит шаг, помечает completed, считает прогресс, диспетчит converter, ветвит «preview → full», зовёт `_drain_queue`. Сложно тестировать, легко регрессить. Линии `app/core/pipeline/orchestrator.py:445…558`.

**Рекомендация:** разнести на `_complete_step`, `_advance_pipeline`, `_maybe_drain_queue`; `_on_preview_completed`/`_on_full_step_completed` делать pure, без реэнтрабельных side-effect-ов.

### 2.3. Файл `orchestrator.py` ~2000+ строк
`app/core/pipeline/orchestrator.py` содержит и FSM-flow, и хелс-чеки, и cleanup, и approver/drener логику.

**Рекомендация:** по `.rules §3.2` декомпозировать: `pipeline/orchestrator.py`, `pipeline/dispatcher.py`, `pipeline/health.py`, `pipeline/cleanup.py`, `pipeline/approver.py`.

### 2.4. Гибрид двух polling-механизмов
Есть параллельные механизмы ожидания внешних задач: `BackgroundTaskPoller` (asyncio-цикл в FastAPI lifespan) и Celery-task-stepping. Для parser/rag_builder задачи «fire-and-forget» с external-task записью + poller, для OCR/converter — синхронные внутри Celery-таска. Две модели вносят когнитивный шум и неодинаковые пути восстановления.

**Рекомендация:** унифицировать: либо всё через external_tasks + poller, либо всё через Celery-chord. Текущий «mix» усложняет и так же страдает от утечек (см. §4).

---

## 3. Алгоритмы — недочёты

### 3.1. Неатомарная проверка лимита одновременных задач (`_has_free_slot`)
В `start_pipeline` (оркестратор `~384`) и `_on_*_completed` → `_drain_queue` шаги:
1. `count_active_tasks()` считается → проверка `< MAX_CONCURRENT_TASKS`.
2. Только потом задача переводится в `active` и диспатчится.

Между шагами 1 и 2 нет транзакции/блокировки, поэтому при параллельных `POST /drafts`/`approve_draft` несколько запросов одновременно увидят «есть слот» и все станут `active` → **лимит `MAX_CONCURRENT_TASKS` будет превышен**.

`count_active_tasks` тоже счётает только задачи со статусом `active` И pending/running-шагом (`pipeline.py:28-56`) — то есть факт «слот занят» фиксируется **только когда шаг уже стартанул**, а не когда задача стала `active`. Это удлиняет окно гонки.

**Рекомендация:** делать «reserve → dispatch» атомарно:
- либо одной транзакцией с `SELECT count(*) FOR UPDATE` на gesamten счётчике (или advisory lock),
- либо вести явный счётчик `active_slot_count` в отдельной строке-счётчике и обновлять его `UPDATE ... SET x=x+1 RETURNING`,
- либо распределять очередность через `SKIP LOCKED` при диспатче и не проверять «slot free» предварительно.

### 3.2. `get_next_queued_task` корректен, но `_drain_queue` вызывает `update_task_status(status=ACTIVE)` безусловно
Хорошо, что `get_next_queued_task` использует `FOR UPDATE SKIP LOCKED` (`pipeline.py:544`). Но затем `_drain_queue` (`orchestrator.py ~234`) делает `update_task_status(status=ACTIVE)` — это второй `get_task_for_update` и второй row-lock на ту же строку. Избыточно и нагружает БД.

**Рекомендация:** переводить в `active` в той же trx, что и `SKIP LOCKED`-выборка, либо передавать выбранную строку в `update_task_status` без повторного `with_for_update`.

### 3.3. Прогресс считается по числу завершённых шагов во множестве дублирующихся шагов
`orchestrator.py:530-533`:
```python
total_steps = task.total_steps or 3
completed_steps = sum(1 for s in steps if s.status == "completed")
progress = min(int((completed_steps / total_steps) * 100), 99)
```
При retry/fallback создаются дубликаты `preview_ocr` (Parser→OCR) — `completed_steps` растёт по числу **всех** завершённых строк, а не уникальных логических шагов. После fallback получает 2 завершённых `preview_ocr`-строки → прогресс пересчитывается некорректно.

**Рекомендация:** считать completed по уникальным `step_name` (uses `_find_best_step` уже существует — переиспользовать).

### 3.4. `on_step_completed` ищет `current_step` сначала по `running`, затем по `pending` (`orchestrator.py:479-509`)
Логика «skip if already-completed idempotent callback» корректна, но смешана с «fallback current_step». Если приходит дублированный Celery-retry event после уже выполненного шага — онällt идёт в `elif current_step.status == "completed"` и тоже уходит в `dispatch _on_preview_completed` повторно? Нет, оно выходит из блока, но **после блока** продолжается:
- `_start_converter_preview` (только если `step_name == "preview_ocr" && output_data`),
- `_on_preview_completed` (только если `step_name == "preview_converter"`),
- `_drain_queue`.

То есть **повторный `preview_converter` callback повторно триггерит `_on_preview_completed`** → повторный OCR fallback / повторная `RegistryServiceClient.update_draft_status`. Это риск двойных сайд-эффектов на дублированных Celery-доставках (а `task_acks_late=True` делает их вероятными).

**Рекомендация:** в `on_step_completed` после «step already completed» сразу `return` без следующей диспетчеризации.

### 3.5. Хардкод «Parser-first» вне FSM
`start_pipeline` сначала пытает Parser, fallback по событию. Это строго зашитая последовательность в коде (`orchestrator.py:312-330`), альтернатив нет (например, тип-документа → предпочтение OCR). Алгоритм негибкий.

**Рекомендация:** вынести `choose_preview_engine(draft, metadata)` в стратегию, конфигурируемую.

### 3.6. `_on_preview_completed` очень разветвлён
Метод делает слишком много: save notifications, check converter, OCR fallback, preview_not_supported ветка с auto_approve/discarded/review_required, наличие critical notifications. Имеет смысл вынести в `PreviewDecisionEngine` класс, который возвращает одно из действий, а оркестратор только исполняет. Это упростит тестирование (и процентов покроется).

---

## 4. Отказоустойчивость — недочёты

### 4.1. 🔴 BUG: Converter-tasks зыворят `_notify_step_failed` на КАЖДОМ retry
`run_converter_preview_step` (`pipeline_formation.py:205-208`) и `run_converter_full_step` (`pipeline_formation.py:433-436`) вызывают `_notify_step_failed` БЕЗ предусловия `self.request.retries >= self.max_retries`, в отличие от OCR/Parser (`if self.request.retries >= self.max_retries`).

Следствие:
- Каждая неудачная попытка (а их до 3) зовёт `on_step_failed` → `set_task_error` инкрементирует `task.retry_count` трижды за один Celery-task.
- Может триггерить `use_ocr_fallback`/`MAX_STEP_RETRIES` преждевременно — задача фейлится/фолбэкается раньше, чем Celery-retry реально испробует все попытки.
- Создаются **дублирующие** `TaskStep` строки (см. §6.2).

**Рекомендация:** унифицировать: либо всегда notify-on-last-attempt, либо notify-on-every и убрать счётчик из `set_task_error` (дублирование).

### 4.2. 🔴 BUG: `cleanup_stale_tasks` помечает шаги failed, но не запускает `on_step_failed`
`cleanup_stale_tasks` (`orchestrator.py:1984-2113`) для hard-kill шагов зовёт только `fail_task_step` (меняет статус строки `TaskStep`), но не вызывает `on_step_failed` orchestrator-a. Аналогично для `SERVICE_DEAD`, `PENDING_TIMEOUT`, `VALIDATING_TIMEOUT`.

Следствие: step-строка failed, **но task остаётся `active`** со всеми running/pending-шагами вокруг. Retry/fallback/компенсация не запускаются. Задача «зависает» и «висит» до срабатывания `get_absolute_timeout_tasks` (по умолчанию 48ч). Это массовый источник «зависших» пайплайнов.

**Рекомендация:** для hard-kill/timeout-step'ов после `fail_task_step` вызывать `on_step_failed(task_id, step.step_name, error_code, error_message)` (или явно запускать compensation). Дополнительно: в `cleanup_stale_tasks` для найденных «stale running tasks» тоже обязательно `unlock_task` (теперь lock остаётся, и `_has_free_slot`/`get_next_queued_task` не считает такую задачу queued).

### 4.3. Дубликат метода `get_stale_running_steps_for_hard_kill`
`app/repositories/pipeline.py:231-251` и `:253-273` — два idентичных определения подряд. Второе перекрывает первое (Python сохраняет последнее). Мёрдж-артефакт. Это не ошибка поведения, но:
- «dead code», который вводит в заблуждение при чтении,
- указывает на отсутствие линтера/CI-проверки дубликатов,
- проверок нет: дублирование не покрыто тестами.

**Рекомендация:** удалить одно определение; добавить CI-правило (ruff `--select F811` или `flake8 --select=F811`).

### 4.4. `_check_service_health` последовательный без суммарного таймаута
`orchestrator.py ~1968-1972` перебирает три URL (`/health`, `/api/v1/health`, base) с одинаковыми настройками клиента. Если сервис «полумёртвый» (принимает соединение, не отвечает), три попытки × read-timeout последовательно блокируют cleanup-цикл. cleanup запускается каждые 5 минут — шаг проверки может не уложиться.

**Рекомендация:**短发 timeout (например, 2s) на health-check; не повторять три URL'а последовательно при сетевых ошибках (только при 404).

### 4.5. `integrity_check` scheduler течёт соединения
`scheduler.py:51-89`: `client = RAGBuilderClient(); ...; await client.close()`. `close()` вызывается ВНЕ `try/finally`. Если `client.check_index(doc_id)` выбрасывает — `close()` не вызывается, соединение утекает (`httpx.AsyncClient` удерживается до GC).

На каждом цикле по `get_recently_indexed_tasks(max_hours=24)`can быть десятки-сотни задач → десятки утечек.

**Рекомендация:** обернуть в `try/finally` (как в `_check_parser_status`).

### 4.6. Adapter `_run_async` создаёт новый event-loop на каждый вызов
`_run_async` (`scheduler.py`, `pipeline_formation.py`) создаёт и закрывает новый event-loop на каждый Celery-вызов и на каждый `_notify_step_*`. Это нагружает ресурсы, и **важно**: если внутри одного Celery-task'а `_run_async(_do_xxx())` succeeded, а последующий `_run_async(_notify_step_completed(...))` падает — в новой петле state теряется, а Celery-task уходит в retry → **повторное выполнение внешнего запроса** (например, повторный submit в Parser) → дублирующийся внешний task_id.

**Рекомендация:** один event-loop на Celery-task, единый `with`-контекст, notify — отдельно с retry-идемпотентностью.

### 4.7. BackgroundTaskPoller non-deterministic на двойной обработке
`_poll_once` выбирает pending в одной сессии и зовёт `_process_task`, затем `db.commit()`. Внутри `_handle_parser_completed` зовётся `process_parser_full_result` → `_notify_step_completed` → **отдельная** `get_db_context` со своим commit. Затем `repo.delete(task.id)` коммитится во внешней сессии. Если внешний commit падает после коммита внутреннего — запись `external_tasks` остаётся, на следующем цикле тот же external_task повторно обрабатывается → повторно `_notify_step_completed`. Для `on_step_completed` шаг уже completed → дубль маловероятен (см. §3.4 issues), но для `process_rag_index_result` нет идемпотентности — повтор может дублировать индекс.

**Рекомендация:** для external_tasks нужен unique-key по `(external_service, external_task_id, step_name)` + UPSERT/lock; либо `_handle_*_completed` делать в той же транзакции, что и `repo.delete`.

### 4.8. BackgroundTaskPollerRUN без backoff'а при пустых циклах
`POLL_INTERVAL = 3s` фиксировано. Если внешних задач нет — все равно каждые 3с селект. Это жилково при простой нагрузке.

**Рекомендация:** адаптивный интервал (например, экспоненциальный backoff при N пустых циклах进行治疗, или `EXISTS`-check перед full query).

### 4.9. `start_poller` может создать только одну инстанцию в процессе
Глобальный `_poller_task` singleton. В multi-worker развертывании (uvicorn `--workers N` или несколько процессов FastAPI) `poller` запускается в **каждом** worker'е → параллельный опрос одних и тех же `external_tasks`. С `SELECT FOR UPDATE SKIP LOCKED` (если он есть в `get_pending_tasks` — нужно проверить) это можно решить, но текущий poller-lock'ит по строке только в момент `_process_task`, поэтому между select и process — гонка. Нужна явная distributed-lock (или запуск poller-а в одном процессе).

**Рекомендация:** запускать poller в отдельном процессе (один экземпляр) либо вести `external_tasks` через `SELECT FOR UPDATE SKIP LOCKED`事先, помечая записи в flightом.

### 4.10. `_run_ocr_fallback` создаёт дублирующийся `preview_ocr`-шаг
`orchestrator.py:560-628`. После Parser-фолбэка строка «preview_ocr Parser Service failed» остаётся, плюс создаётся новая «preview_ocr OCR Service pending» —TreeView **несколько** строк с одним `step_name` в одной задаче. Это работает, пока `on_step_completed` ищет по `running`/`pending`, но:
- `_find_best_step` выбирает `completed > running > pending` — после завершения OCR-фолбэка возникает **две completed-строки** `preview_ocr`, и `progress` их обеих посчитает (см. §3.3).
- `notifications` `save_notifications` печётся из "`preview_step.output_data`" — выбирая лучшую, может взять Parser-вывод вместо OCR (или наоборот), недетерминированно.
- История шагов нечитаема в UI.

**Рекомендация:** для OCR-fallback переиспользовать ту же строку (`UPDATE ... SET service_name=... status='pending'`) или вводить другой `step_name` (например, `preview_ocr_fallback`), не дублируя стоpону.

### 4.11. Нет circuit breaker-а для внешних сервисов
При падении сервиса (например, OCR timeout) asyncio-retry (`app/services/base_client.py:320`) повторяет `MAX_RETRIES+1` раз на каждый запрос. Все параллельные задачи пинают упавший сервис → cascading failure. Нет никакого circuit breaker-а (ни health-based skip, ни mark-service-down).

Рекомендация: использовать `_check_service_health` при диспатче: если сервис DEAD — очередь задач ставится на паузу (с retry-again каждые N секунд), а не каждая задачаIndependently дёргает упавший сервис.

---

## 5. Конкурентность и блокировки — недочёты

### 5.1. Избыточный `FOR UPDATE` в `update_task_status`
`pipeline.py:102-130` для **любого** обновления (даже только `progress_percent`) зовёт `get_task_for_update` (row-lock). На каждый step-completion задача получает 1 `complete_task_step` (block на `TaskStep`) + 2-3 `update_task_status` (block на `Task`). Под нагрузкой это lock-contention и deadlock-risk.

**Рекомендация:** разделять: `update_progress` (без block), `update_status_locked` (с block). Использовать `with_for_update` только когда реально нужно избежать lost-update на `status` (терминальные переходы).

### 5.2. `_has_free_slot` использует обычный `count`, не блокирует
Контр-источник §3.1 — счёт «active задач со pending/running шагом» не берёт блокировки; гонка между параллельными `start_pipeline`/`_drain_queue`. Что ещё хуже, drain-цикл и REST-API стартуют задачи параллельно → бывет, drain_queue забирает slot после старта API時に API-стрart взял slot, но drain_queue выбрал queued-задачу и тоже сделал `status=ACTIVE` → лимит переполнен.

**Рекомендация:** slot-counter с advisory lock (`pg_advisory_xact_lock`), либо `UPDATE...RETURNING` на счётчике слотов (см. §3.1).

### 5.3. `set_task_error` инкрементирует `retry_count` и не под защищаемым блоком от расхождений с Celery-retry
`pipeline.py:348-359`: `task.retry_count = task.retry_count + 1`. Этот же retry_count сравнивается с `MAX_STEP_RETRIES` в `on_step_failed` (`orchestrator.py:1887`). Но converter tasks зовут `_notify_step_failed` на каждой попытке — retry_count инкрементится **за одну Celery-задачу** многократно (см. §4.1). Расхождение между двумя retry-механизмами (Celery `max_retries` vs repository `retry_count`) → поведение зависит от того, какой путь сработает первым.

**Рекомендация:** один retry-источник правды. Например, только Celery-retry управляет step-задачей, а orchestrator-retry (`on_step_failed` recreate pending step) включается только когда Celery maxed-out (notify-on-last-attempt).

### 5.4. Lock release несогласован
`unlock_task` зовётся из `on_step_failed` в ветке «retries exhausted» и в «NO_AVAILABLE_ENGINES» — но в ветке `use_ocr_fallback` и в elif-ветке retry (`orchestrator.py:1887-1910`) **lock не освобождается**. Это OK, если задача ещё активна и step-retry ещё будет, но если блокирующий worker упал (process crashed) — `release_stale_locks` поднимет его только через `MAX_JOB_RUNNING_TIME` (~ час по умолчанию).

**Рекомендация:** рестарт worker должен самостоятельно освободить свои locks при старте (через `worker_id`-фильтр), не ждать 1h.

### 5.5. `get_stale_validation_tasks` лишний раз compare against `started_at` без проверки `is not None`
`pipeline.py:322`: `Task.started_at < threshold`. Если `started_at IS NULL` (задача в очереди никогда не была active), сравнение даст `NULL` → в SQL исключается (правильно), но намерение читать сложнее. Не задерживает работу.

---

## 6. Транзакции/консистентность — недочёты

### 6.1. Внешние сайд-эффекты и БД-commit — нет outbox
В `on_step_completed` и в `_on_preview_completed` коммит транзакции происходит только на уровне `get_db_context` (в `_notify_step_completed`). ВНУТРИ оркестратора до коммита зовутся:
- `RegistryServiceClient.update_draft_status` (сеть, external state),
- `self.approve_draft(...)` → порождает новый Celery-task и з eigenen `Registry` againes.

Если БД-коммит упадёт (например, deadlock при `update_task_status`), external side-effect уже применён → состояние Registry/RAG расходится с локальной БД. **Нет outbox/no saga-anticompensation для draft-status**.

**Рекомендация:** outbox-таблица `outbox_events`; external calls делают outbox-записью, отдельный воркер executes и ack'ает.

### 6.2. `on_step_failed` создаёт **новый** `TaskStep` с тем же `step_name`
`orchestrator.py:1844-1855` (OCR fallback) и `:1898-1903` (retry) создают новый `TaskStep` row с тем же `step_name` и `step_index`. Это означает, что **одна задача может иметь несколько строк с одинаковым `step_name`**. Любой код, который делает `next(s for s in steps if s.step_name == X)` без явного учета статуса/service_name — получит недетерминированный выбор. Например:
- `on_step_completed` для converter-dispatch для fallback-dispatch.
- `progress` count по completed-шагам (§3.3).

Строки не удаляются (мягкое удаление через `deleted_at`, но никто его не проставляет). Накапливаются.

**Рекомендация:** на уровне БД — либо forbid separated rows (UNIQUE constraint on `(task_id, step_name)` — но это противоречит fallback-дизайну), либо сохранять history-таблицу `task_step_history`, а active представлять одну row с обновляемым `service_name`, `attempt_count`, `status`. По крайней мере, индекс/ограничение + сервисная логика.

### 6.3. `cleanup_stale_tasks` без commit в scheduler-task
`scheduler.py:31-37`: `_cleanup()` открывает `get_db_context`, вызывает `orchestrator.cleanup_stale_tasks()`. Этот метод зовёт `fail_task_step`/`update_task_status` (только `flush`, без commit). `get_db_context` авто-коммитит в конце, что спасает — но **сетевые `_check_service_health`-вызовы выполняются внутри открытой транзакции**, удлиняя транзакцию на длительное время, с row-locks уже взятыми (`with_for_update` на step-rows).

Если во время health-check掀ète транзакция длится десятки секунд — блокировки накапливаются**bd transaction. Если внутри cleanup упадёт одно — rollback **всех** cleanup-изменений, включая уже корректно помеченные шаги.

**Рекомендация:** батчевать cleanup по типам (soft-kill batch, hard-kill batch, validate-timeout), с commit после каждой группы; health-check вынести за транзакцию.

### 6.4. `parser_full`-subm walking: start_step + dispatch external
`_enqueue_celery_full_tasks` (`orchestrator.py:166-182`): `start_task_step(full_step.id)` (`FLUSH`) → `run_parser_full_step.delay(...)`. Celery-задача внутри `_submit_parser_full` пишет `external_tasks` через **отдельную** `get_db_context` (коммитится). Если `delay` успех, но Celery-сервер в момент выполнения ещё не залогировал — step застревает. Если же `delay` упал (Redis dead) — step уже `running`, но задача не диспатчена. Idempotent-dispatched-check отсутствует. Recovery через `cleanup_stale_tasks` hard-kill через 30 минут.

**Рекомендация:** отдельный outbox для задержки dispaytchцa, или поleast `task.started_at_within`-чек в `_enqueue_*`.

---

## 7. Покрытие тестами — недочёты

| Элемент | Что тестируется / не тестируется |
|---|---|
| `_notify_step_completed` / `_notify_step_failed` | ⚠️ Без тестов (no covering tests found). |
| `BackgroundTaskPoller` (`_check_parser_status`, `_handle_rag_builder_completed`) | ⚠️ Без тестов. |
| `run_converter_preview_step` / `run_converter_full_step` retry behaviour (§4.1) | ⃠ без специального теста «converter не делает notify на каждой попытке». |
| `DraftTaskItem` / `DraftTasksResponse` / `DocumentTasksResponse` | ⚠️ Без тестов. |
| `cleanup_stale_tasks` (orchestrator) | тесты на scheduler есть, но НЕ проверяют, что hard-killed шаги реально воскрешают on_step_failed/компенсацию (§4.2). |
| Дубликат `get_stale_running_steps_for_hard_kill` (§4.3) | тесты не ловят дубли (тесты вызывают метод по имени, оба возвращают одно и то же). |
| Race on `_has_free_slot` (§3.1) | нет конкурентных тестов. |

**Рекомендации:** добавить тест на «2 параллельных start_pipeline при `MAX_CONCURRENT_TASKS=1` — ровно одна задача active»; тест на «converterfailed при retries=0, retry_count на задаче не должен увеличиться» (ловит §4.1); тест на «cleanup hard-killed running step → `on_step_failed` вызвано ровно 1 раз» (ловит §4.2).

---

## 8. Прочее / мелочи

- `celery_app.conf.task_acks_late = True` хорошо для надёжности, но вместе с **неидемпотентным** `_run_async(_do_xxx())` (повторный OCR-запрос) — задачи пере.exec'аются при crash worker'а. Стоит дополнительно резко проверять идемпотентность внешних запросов (например, передавать `task_id` + draft_id и страничные лимиты, чтобы сервис кэшировал результат).
- `list_tasks` (`tasks.py:34`) не фильтрует по `pipeline_stage`, хотя это поле есть в схеме; фильтрация только по `draft_id`/`status`/`pipeline_type` — мелочь, но неполное API.
- `TaskStage`: где-то сравнивается строка `"decision"` напрямую (`orchestrator.py:240`), а не через `TaskStage.DECISION.value`. Магическая строка, риск опечатки.
- `mime_type` параметр в `start_pipeline` **не используется** — принимается, но нигде не применяется (это, скорее всего, задумано для выбора OCR/Parser-стратегии, см. §3.5).

---

## 9. Рекомендации — приоритезированный план

### 🔴 Critical (поведенческие баги)
1. **§4.1** Converter-tasks: добавить `if self.request.retries >= self.max_retries` перед `_notify_step_failed` в `run_converter_preview_step` и `run_converter_full_step`.
2. **§4.2** `cleanup_stale_tasks`: для hard-kill/timeout step'ов вызывать `on_step_failed` (а не только `fail_task_step`) — иначе задачи «зависают» до 48h.
3. **§4.3** Удалить дубликат `get_stale_running_steps_for_hard_kill` в `app/repositories/pipeline.py`. Добавить F811 в линтер.
4. **§3.4** В `on_step_completed` после «step already completed» делать `return`, чтобы не пере-dispatch'ить converter/preview.

### 🟠 High (отказоустойчивость / консистентность)
5. **§5.4** Restarting workers должны освобождать свои locks при запуске, не ждать `MAX_JOB_RUNNING_TIME`.
6. **§4.10** Реорганизовать OCR-fallback: либо UPDATE одной строки, либо использовать отдельный `step_name`, чтобы не плодить duplicate step rows.
7. **§6.3** Разбить `cleanup_stale_tasks` на фиксируемые пачки; вынести health-check'и из транзакции.
8. **§6.1** Внедрить outbox-таблицу для external side-effects (Registry, RAG); запуск через отдельный воркер.
9. **§4.5** `integrity_check` обернуть `client.close()` в `try/finally`.
10. **§3.1 / §5.2** Реализовать атомарный slot-counter или advisory-lock для `MAX_CONCURRENT_TASKS`.

### 🟡 Medium (architecture/readability)
11. **§2.1** Ввести `StepDispatcher` интерфейс, чтобы убрать циркулярную `core ← tasks` зависимость.
12. **§3.3** Прогресс — считать по unique `step_name`, не по строкам.
13. **§2.3** Декомпозировать `orchestrator.py` по `.rules §3.2`.
14. **§4.6** Один event-loop на Celery-task; ясная идемпотентность на повторе.
15. **§7** Покрыть тестами `_notify_step_*`, `BackgroundTaskPoller`, converter-retry-count.

### 🟢 Low (мелочи)
16. **§8** Использовать `TaskStage.DECISION.value` вместо литерала `"decision"` (`orchestrator.py:240`).
17. **§8** Реализовать `_choose_preview_engine(draft, metadata, mime_type)` (заодно использовать `mime_type`).
18. **§4.4** Здоровье-чек с коротким 2s-таймаутом; третий URL не пробовать при сетевых ошибках.
19. **§4.8/4.9** Адаптивный poll-interval; запускать poller в одном процессе или защищать внешние задачи `SKIP LOCKED` заранее.

---

## 10. Что осталось за рамками аудита

- Не анализировался код сервисов-клиентов (`ocr_client`, `parser_client`, `rag_client`, `registry_client`) на уровне retry/timeout — только по упоминаниям в `base_client`. Стоит отдельный аудит на корректность retry-policy, backoff и таймаутов.
- `SagaCoordinator.compensate` не входил в детальный разбор — нужен отдельный аудит на корректность компенсации по шагам.
- API-эндпоинты (`drafts.py`, `documents.py`, `tasks.py`) на валидацию/аутентификацию/обработку конфликтов — не детализировано.
- Конфигурация Celery broker/backend, prefetch, visibility timeout — не проверялась.
- миграции/индексы БД (`alembic`) на соответствие запросов (например, есть ли индекс на `TaskStep(task_id, status)` и `TaskStep.step_name`) — не проверялось; индексы критичны для `cleanup_stale_tasks` / poller'а при росте таблиц.
- Не проверялось, что `get_pending_tasks` в `ExternalTaskRepository` использует `FOR UPDATE SKIP LOCKED` (важно для §4.9).

---

> Аудит сделан по снимку кода на текущую дату. Все номера строк приблизительны — при рефакторинге ориентироваться на имена символов (`on_step_completed`, `on_step_failed`, `cleanup_stale_tasks`, `get_stale_running_steps_for_hard_kill`, `_has_free_slot`, `_drain_queue` и т.д.).