# Specificity — аномалии и трудные моменты

## ⚙ Особенности рабочего окружения

### G4. Diagnostics на сервере — docker логи недоступны

Gateway имеет встроенный diagnostics-модуль (`diagnostics.py`) с эндпоинтами:
- `GET /api/v1/system/diagnostics` — краткая сводка (публичный)
- `GET /api/v1/system/diagnostics?verbose=true` — полная (диски, порты, Docker, логи, dmesg)
- `GET /api/v1/system/diagnostics/{service}` — детально по сервису (name: query, auth, rag-search...)
- `GET /api/v1/system/diagnostics/system` — логи ядра (dmesg) и memory pressure

**Важно:** diagnostics вызывает `docker inspect`, `docker logs`, `docker ps` через subprocess внутри контейнера gateway. Раньше `run()` возвращал только stdout, stderr подавлялся — из-за этого ошибки docker не отображались. **Исправлено:** `run()` теперь возвращает stderr при ошибке, diagnostics показывает реальную причину (`error: no such object: pkb-query`, `Error response from daemon`).

**Что работает всегда (без docker):** dmesg, journalctl, memory pressure, df, free, ss — через `/host/proc`.

**Как диагностировать сервисы на сервере без SSH:**
1. `GET /api/v1/system/diagnostics?verbose=true` — увидеть OOM в dmesg
2. `GET /api/v1/system/diagnostics/{service}` — пытается взять docker logs, но если docker не работает — будет пусто
3. Нужен SSH на сервер для `docker logs pkb-query --tail 50`

### G5. Infinity OOM — диагностика и схема отказа (26.06)

**Симптом:** фронтенд: «Поиск временно недоступен».

**Схема отказа:**
```
infinity (7997) — OOM kill
  ↓
RAG search (8091) — timeout (зависит от infinity)
  ↓
query_service.pipeline.run_pipeline()
  → rag_client.search() 3 retries × 30s timeout → всё падает
  → запись в БД: status="failed", content="Поиск временно недоступен..."
```

**Диагностика (через gateway diagnostics):**
- `GET /api/v1/system/diagnostics?verbose=true` → dmesg показывает OOM kill infinity_emb
- `GET /api/v1/system/diagnostics/query` → пусто (docker не работает внутри контейнера)
- `GET /api/v1/system/diagnostics/system` → dmesg + memory pressure
- Прямые запросы к infinity:7997, rag-search:8091 → timeout (порты не открыты наружу)

**Причина:** infinity без `mem_limit` грузит `bge-reranker-v2-m3-ONNX` через optimum engine и жрёт ~30GB RAM. На сервере 32GB RAM + 4GB swap. Своп исчерпан, OOM убивает infinity, после перезапуска infinity снова забирает всю память и система в цикле OOM.

**Фикс (в docker-compose.yml):**
- `mem_limit: 8g`, `memswap_limit: 0` — не даёт infinity убить всю систему
- `--engine torch` вместо `--engine optimum` — optimum при загрузке ONNX создаёт временные буферы >10GB (см. [michaelfeil/infinity#579](https://github.com/michaelfeil/infinity/issues/579))
- `--model-id BAAI/bge-reranker-v2-m3` (PyTorch) вместо `onnx-community/bge-reranker-v2-m3-ONNX` — torch engine не загружает ONNX
- `--batch-size 1` — снижает пиковое потребление

**Выводы:**
- Diagnostics gateway не может читать docker logs (docker CLI отсутствует внутри контейнера gateway или не смонтирован сокет).
- Единственный источник диагностики без SSH — dmesg (через /host/proc) и health endpoints.
- При добавлении нового сервиса с потенциально высоким потреблением памяти — обязательно указывать `mem_limit`.
- При OOM одного сервиса валится вся цепочка downstream. Нужен Resilience: circuit breaker на rag_client.

### G6. FastAPI трейлинг-слеш — 307 redirect ломает прокси через Gateway

**Проблема:** Если роут FastAPI определён с `"/"` (слеш), а клиент шлёт запрос без слеша — FastAPI отвечает 307 с Location на внутренний Docker-hostname (напр. `http://orchestrator:8081/api/v1/drafts/`). Браузер не может резолвить Docker-имена и падает с `ERR_NAME_NOT_RESOLVED`.

**Где проявилось:** `POST /api/v1/drafts` в оркестраторе — роут был `@router.post("/")`, нужно `@router.post("")`.

**Фикс в Gateway (client.py):** перехват 3xx ответов и замена Location с внутреннего URL на Gateway (`proxy_request`).

**Профилактика:**
- Определять роуты без слеша — `@router.post("")`, а не `@router.post("/")`
- При добавлении нового сервиса проверить, не утекают ли внутренние URL наружу

### F4. Нечисловой draft_id в gatewayDraftId — 400 Bad Request

**Симптом:** `GET /api/v1/drafts/draft-{timestamp}-{random}/tasks → 400 (INVALID_DRAFT_ID)`.

**Причина:** `gatewayDraftId` получает нечисловое значение (локальный id `draft-{timestamp}-{random}`), когда сервер возвращает `draft_id` в нечисловом формате или через fallback-цепочку в `mapGatewayDraftRecordToUi`.

**Фикс (четыре уровня защиты):**
1. `mapGatewayDraftRecord` — `draft_id: data.draft_id ?? data.id` заменено на `draft_id: data.draft_id` (веб не подменяет id сервера)
2. `mapGatewayDraftRecordToUi` — санитизация `gatewayDraftId`: если не число → `""`
3. Все методы `draftsApi` (get, getPreview, startPreview, waitPreview, updateMetadata, decide, delete) — `requireNumericDraftId` бросает ошибку до отправки запроса
4. `draftTasksQuery.enabled` и `refreshGatewayDraftDetails` — проверка `/^\\d+$/` вместо `Boolean()`

**Вывод:** Любой новый метод API, принимающий `draftId`, должен валидировать числовой формат.

### F5. crypto.subtle недоступен в HTTP — падает загрузка черновиков

**Симптом:** `TypeError: Cannot read properties of undefined (reading 'digest')` при загрузке файла черновика на http://сервер:3300. В консоли нет ошибок API.

**Причина:** `crypto.subtle.digest()` (Web Crypto API) доступен только в **secure contexts** (HTTPS, localhost). На продакшене по HTTP `crypto.subtle` — `undefined`.

**Фикс:** `calculateFileSha256` в `http.ts` — проверка `crypto.subtle`; если его нет, хеш генерируется через `crypto.getRandomValues` (доступен всегда). Сервер сам вычисляет реальный хеш файла, локальный хеш нужен только для `documentKey`.

**Профилактика:** Любое использование `crypto.subtle` должно иметь fallback для HTTP.

### G7. Pipeline: preview status не приходит в completed (дублирующиеся шаги)

**Симптом:** `GET /drafts/{id}/preview/status` возвращает `"status":"processing"` даже когда preview выполнен.

**Причина:** `on_step_completed` вызывается дважды для `preview_converter` (из-за дублирующихся задач Celery). 
Создаются два шага с `step_name="preview_converter"` — один completed, второй pending. 
`_build_preview_status` проверяет `all(s.status == "completed" for s in preview_steps)` → всегда False.

**Где:** `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`, функция `_build_preview_status`.

**Статус:** не исправлено.

### G8. Pipeline: RAG-индексация не завершается после registry_creation

**Симптом:** шаг `rag_index` висит `pending`, pipeline падает в `failed`.

**Причина:** дублирующиеся шаги при создании в `approve_draft` (вызов дважды) или при retry/fallback в `on_step_failed`.

**Фикс (27.06):**
- `approve_draft` — проверка `existing_step_names` перед созданием шагов (не создавать если уже есть)
- `on_step_failed` — guard: не создавать pending шаг если уже есть pending с тем же step_name
- `_run_ocr_fallback` — guard: не создавать preview_ocr если уже есть pending
- `_build_preview_status` — группировка шагов по step_name, взятие лучшего статуса

**Где:** `backend/orchestrator_service/app/core/pipeline/orchestrator.py`, `backend/orchestrator_service/app/api/v1/endpoints/drafts.py`.

**Статус:** исправлено.

### G9. base_client.py — mock fallback при ConnectError удалён

**Проблема:** При `ConnectError` (сервис недоступен) `ServiceClient.call()` возвращал пустой `mock_response` вместо retry.
Celery-задача получала `{}` → конвертер падал с `MetadataExtractionFailedError`.

**Фикс (29.06):**
- ConnectError теперь retryable (tenacity)
- После исчерпания retry — исключение пробрасывается в Celery-задачу
- Аналогично для CircuitBreakerError

**Где:** `backend/orchestrator_service/app/services/base_client.py`.

### G10. Rag-builder: dimensions parameter для эмбеддингов

**Проблема:** Qwen3-Embedding-8B возвращает 4096-мерные векторы. Rag-builder не передавал `dimensions`, обрезал 4096→2048.
Rag-search передавал `dimensions=2048` и получал 2048 — несоответствие.

**Фикс (29.06):** Rag-builder также передаёт `dimensions=self.dim` в API.

**Где:** `backend/rag_builder_service/src/rag_builder/embeddings/service.py`.

### G11. Registry: заголовок X-Service-ID для обновления статуса документа

**Проблема:** Эндпоинт `PATCH /registry/documents/{id}/status` требует заголовок `X-Service-ID: orchestrator`.
`RegistryServiceClient.update_document_status` не передавал его → 403 Forbidden.
+ Статус `"active"` не входит в валидные переходы из `"uploaded"`.

**Фикс (29.06):**
- Добавлен заголовок `X-Service-ID: orchestrator` в `update_document_status`
- После rag_index статус меняется на `"validating"` (валидный переход `uploaded → validating`)

**Где:** `backend/orchestrator_service/app/services/registry_client.py`, `backend/orchestrator_service/app/core/pipeline/orchestrator.py`.

### G12. Сканированные PDF: 422 вместо OCR fallback

**Симптом:** Загрузка сканированного PDF (например `gost_22786-77.pdf`) → черновик DISCARDED
с ошибкой «Проверку черновика завершить не удалось».

**Причина:** Converter-validator не может извлечь doc_code/title из сканированного PDF
(нет текстового слоя) → `MetadataExtractionFailedError` → HTTP 422.
Оркестратор делает retry, затем retry exhausted → задача FAILED.
OCR fallback существовал только для падения Parser, не для Converter.

**Фикс (29.06):**
1. `converter.py` (endpoint `/preview`): перехват `MetadataExtractionFailedError`,
   возврат 200 OK с пустыми полями вместо 422.
2. `pipeline_formation.py` (`run_converter_preview_step`): если в ответе конвертера
   нет doc_code и title → `validated=False`.
3. `_on_preview_completed` видит `validated=False` + `used_parser=True` +
   `fallback_to_ocr=True` → запускает OCR fallback.

**Где:**
- `backend/converter_validator_service/app/api/v1/endpoints/converter.py`
- `backend/orchestrator_service/app/tasks/pipeline_formation.py`

### G13. Не-ГОСТ документы без doc_code падают в full_converter

**Симптом:** Циркулярное письмо (например `0A83D092-1D22-47AD-A6EF-0F06A8F11A6B_001.pdf`) —
full_converter возвращает 400 `VALIDATION_ERROR: doc_code is required`.

**Причина:** `compute_business_key` требует непустой doc_code. Для циркулярных писем
`extract_preview_metadata` не находит doc_code (нет ГОСТ-шаблона) → `""` → ошибка.
Preview-этап работает (там `MetadataExtractionFailedError` перехвачен), но
`validate_document` в full-конвертации вызывает `_compute_fingerprint` → `compute_business_key` → падает.

**Фикс (29.06):**
1. `metadata_extractor.py` — добавлен `_CIRCULAR_RE` для распознавания
   `ЦИРКУЛЯРНОЕ ПИСЬМО № 311-05-1950ц`
2. `document_validator.py` — `_compute_fingerprint`: try-except `MetadataValidationError`
   вокруг `compute_business_key`. При отсутствии doc_code/title создаётся fallback fingerprint
   из task_id:version_id.

**Где:**
- `backend/converter_validator_service/app/services/metadata_extractor.py`
- `backend/converter_validator_service/app/services/document_validator.py`

### B1. Циклический OCR fallback в preview — дублирование preview_ocr шагов

**Симптом:** `preview_ocr` шаги множатся (completed=5, pending=1), новые создаются каждый цикл.

**Механизм:**
1. Parser preview_ocr → completed
2. Converter preview (`_on_preview_completed`) → `validated=False` (НД без doc_code)
3. `_run_ocr_fallback` → создаёт `preview_ocr` (OCR), диспатчит
4. OCR preview_ocr → completed → снова Converter → validated=False → снова `_run_ocr_fallback`
5. **Бесконечный цикл:** guard в `_run_ocr_fallback` проверяет только `pending` шаги (`has_pending_ocr`),
   но НЕ проверяет `completed` OCR-шаги. Каждый раз после завершения OCR Converter падает → новый OCR.

**Где:** `PipelineOrchestrator._run_ocr_fallback()` (orchestrator.py:347–391).

**Фикс (30.06):** guard теперь проверяет `has_existing_ocr` — completed шаги OCR Service.

### B2. Pipeline full_phase: full_ocr (Parser) не завершается на больших PDF

**Симптом:** `full_ocr` висит `running` на PDF 249 страниц более 300с.
`full_converter`, `registry_creation`, `rag_index` — все `pending`, ждут full_ocr.

**Причина:** Parser full не может обработать большой PDF (таймаут/зависание).
Шаги стартуются последовательно: full_ocr → full_converter → registry → rag_index.
Если full_ocr не completed — цепочка не движется.

**Где:** `PipelineOrchestrator._on_full_step_completed()` (orchestrator.py:714–842).

**Фикс (30.06):**
- добавлен `RUNNING_STEP_TIMEOUT = 600с` (10 мин) в `PipelineConfig`
- `get_stale_running_steps()` в TaskRepository — ищет шаги running > N секунд
- `_check_service_health()` — HTTP health check сервиса (Parser, OCR, Converter, Registry, RAG)
- `cleanup_stale_tasks` проверяет stale running шаги: если сервис жив → warning (медленная обработка),
  если сервис мёртв → fail шага (SERVICE_DEAD)

### B3. RAG-индексация не стартует даже при доступных данных

**Симптом:** Данные в RAG Search уже есть (поиск находит doc_id=59), 
но pipeline висит на 99%, `rag_index` всегда `pending`.

**Причина:** rag_index стартуется только через цепочку:
`full_ocr completed → _on_full_step_completed → enqueue full_converter → 
full_converter completed → enqueue registry_creation → 
registry_creation completed → enqueue rag_index`

Если любой шаг в цепочке не завершён (B2: full_ocr running) — rag_index никогда не стартует.
При этом RAG Builder может получить данные другим путём (через auto-индексацию или 
параллельный процесс), поэтому данные в поиске есть, но pipeline не в курсе.

**Где:** `PipelineOrchestrator._on_full_step_completed()` (orchestrator.py:714–842).

### UTL. Универсальный тест загрузки PDF — data/tests/test_universal_pdf_loader.py

**Назначение:** Единый скрипт для загрузки любого PDF через Gateway, прохождения полного pipeline и верификации через RAG Search.

**Особенности:**
- Не использует service_checker — только корневой docker-compose (порт 8080)
- Текст для верификации берётся из Registry sections (**распарсенный конвертером/OCR PDF**, не PyPDF2)
- Если конвертер не смог парсить PDF (CID-шрифты, сканы) — sections пусты, тест выходит с exit 2
- Настройка через переменные окружения: `EXTRACT_FRAGMENTS`, `DOC_SOURCE_TYPE`, `DOC_TITLE`, `DOC_CODE`, `TEST_API_URL`
- Выходной код: 0 (успех), 1 (ошибка), 2 (низкая верификация или нет секций)

**Важно:** Для PDF с CID-шрифтами/закодированным текстом конвертер не создаёт секции. Тест корректно отражает это — верификация невозможна, т.к. текст не извлекается ни самим конвертером, ни OCR.

### D1. Детекция дублей — ИСПРАВЛЕНО (01.07)

Дубли детектятся: HTTP 409 с `DUPLICATE_FILE` на повторную загрузку.
Подтверждено на `2-020101-004.pdf` и `gost_22786-77.pdf`.

### — ✂ УДАЛЕНО: R6, R5. ИСПРАВЛЕНО 01.07 —

### S1. Search 500 — bbox строка вместо списка (30.06, НОВАЯ)

**Статус:** НЕ ИСПРАВЛЕНО

**Симптом:** `POST /api/v1/rag/search` → HTTP 500: `Input should be a valid list [type=list_type, input_value='[0.255, 0.595, 0.786, 0.631]', input_type=str]`

**Корневая причина:** Конвертер/парсер сериализует `bbox` как JSON-строку, Pydantic ожидает list.

**Где должно быть:**
- Конвертер должен передавать `bbox` как список чисел, а не строку
