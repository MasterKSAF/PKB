# Оркестратор в Пайплайне 1 (Формирование): сценарии поведения

> **Назначение документа.** Описание сценариев поведения Оркестратора при прогоне Пайплайна 1. Документ дополняет:
> - [Пайплайн 1: Формирование документа](../pipeline1-formation.md) — основной поток, FSM, retry
> - [Детальное описание preview-фазы](../pipeline1-formation_detail.md) — preview в деталях
> - [API Orchestrator Service](../../api/orchestrator_service_api.md) — эндпоинты
>
> Стиль описания: **Ситуация → Поведение Оркестратора → Результат / Статус → Код ошибки**.

**Охват документа:** Пайплайн 1 (`uploaded → previewing → ready_for_approve / review_required → approved / validation → created`). Пайплайн 2 (`pending_index → indexed / failed`) — в [pipeline2-orchestrator_details.md](pipeline2-orchestrator_details.md). Пайплайн 3 (поиск, через Query Service) — в [pipeline3-orchestrator_details.md](pipeline3-orchestrator_details.md).

---

## 0. Точка входа и общая модель

**Черновик (draft) — единственная точка входа в Пайплайн 1.** Без черновика документ не может быть создан.

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| `POST /drafts` (норма) | Вычислить `SHA-256`, проверить формат/размер, сохранить в MinIO, создать `pipeline.tasks` (status=active) и `pipeline.task_steps` (`upload`), создать запись в `registry.drafts` через `POST /registry/drafts` (status=`uploaded`) | `202 { draft_id, task_id, status: "uploaded", file_hash_sha256, file_size_bytes }` | — |
| `POST /drafts` (пустой файл 0 байт) | Отказать до записи в MinIO | `400 EMPTY_FILE` | `EMPTY_FILE` |
| `POST /drafts` (файл < 1 КБ) | Отказать до записи в MinIO | `400 FILE_TOO_SMALL` | `FILE_TOO_SMALL` |
| `POST /drafts` (файл > 100 МБ) | Отказать до записи в MinIO | `413 FILE_TOO_LARGE` | `FILE_TOO_LARGE` |
| `POST /drafts` (неподдерживаемый тип MIME) | Отказать до записи в MinIO | `422 UNSUPPORTED_FILE_TYPE` | `UNSUPPORTED_FILE_TYPE` |
| `POST /drafts` (файл с таким `file_hash_sha256` уже в активной обработке) | Отказать, вернуть `conflict_document_id` существующего активного черновика | `409 DUPLICATE_FILE` | `DUPLICATE_FILE` |
| `POST /drafts` (MinIO недоступен) | Не создавать записи ни в `pipeline.tasks`, ни в `registry.drafts` | `503 SERVICE_UNAVAILABLE` | `STORAGE_UNAVAILABLE` |
| `POST /drafts` (Registry недоступен — ошибка `POST /registry/drafts`) | **Компенсация:** удалить уже созданный `pipeline.tasks` (каскад `pipeline.task_steps`) и объект из MinIO | `502 BAD_GATEWAY` | `REGISTRY_UNAVAILABLE` |
| `POST /drafts` (невалидные поля формы) | Отказать до записи в MinIO | `400 VALIDATION_ERROR` | `VALIDATION_ERROR` |

> **Связанные правила:**
> - Оркестратор **не вычисляет** `title_hash_sha256` / `title_key` на этом этапе. Бизнес-ключ вычисляется только Converter-validator (см. [guide.md](../../guide.md#бизнес-ключ-вычисляет-только-converter-validator)).
> - Авторизация и RBAC контролируются **только Gateway**. Оркестратор не проверяет JWT.
> - Идемпотентность на Gateway: `Idempotency-Key` (TTL 1 час) для критичных POST-операций.

---

## 1. Preview-фаза: запуск

**Точка запуска:** `POST /drafts/{draft_id}/preview` (от UI через Gateway).

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| `POST /preview` (норма, статус `uploaded`) | Перевести черновик в `previewing`, создать `task_step "preview_ocr"`, определить тип файла (MIME/`source_type`) → OCR или Parser, вызвать `POST /ocr/process` или `POST /parser/process` (`mode=preview`, `max_pages=3`) | `202 { draft_id, status: "previewing", estimated_completion }` | — |
| `POST /preview` (статус `previewing`, идемпотентность по `Idempotency-Key`) | Вернуть кешированный ответ `202` | `202` (повторно) | — |
| `POST /preview` (статус `previewing`, без `Idempotency-Key`) | Отказать — preview уже идёт | `409 PREVIEW_IN_PROGRESS` | `PREVIEW_IN_PROGRESS` |
| `POST /preview` (статус `ready_for_approve` или `review_required` или `discarded`) | Отказать — preview уже завершён или терминален | `409 DRAFT_ALREADY_PREVIEWED` | `DRAFT_ALREADY_PREVIEWED` |
| `POST /preview` (статус не `uploaded`, например, `approved`) | Отказать | `409 INVALID_STATE_TRANSITION` | `INVALID_STATE_TRANSITION` |
| `POST /preview` (черновик не найден) | — | `404 DRAFT_NOT_FOUND` | `DRAFT_NOT_FOUND` |
| `POST /preview` (файл не поддерживает постраничный preview) | Не запускать preview, вернуть флаг | `422 PREVIEW_NOT_SUPPORTED` | `PREVIEW_NOT_SUPPORTED` |

> **Идемпотентность (P1-19):** повторный `POST /preview` с заголовком `Idempotency-Key: <uuid>` (TTL 1 час) возвращает кешированный ответ. Без `Idempotency-Key` действует FSM-логика (см. таблицу выше).

---

## 2. Preview-фаза: обработка (longpoll)

**Точка статуса:** `GET /drafts/{draft_id}/preview/status?longpoll=15` (от UI).

| Сценарий | Поведение Оркестратора | Результат | Код |
|----------|------------------------|-----------|-----|
| OCR/Parser вернул частичный JSON (постраничный режим) | Сохранить `raw_data` в `registry.drafts.raw_data`, перейти к этапу `preview_converter` | `status: processing` | — |
| OCR/Parser вернул полный JSON + `preview_not_supported: true` | Сохранить полный JSON, пометить флагом `preview_full=true` в контексте задачи. **Full-фаза OCR/Parser будет пропущена** (см. §6) | `status: processing` | — |
| OCR/Parser таймаут (> 60с для OCR, > 30с для Parser) | Retry 1 раз (Immediate). При повторном таймауте — черновик → `discarded` | `status: failed` | `OCR_TIMEOUT` / `PARSER_TIMEOUT` |
| OCR/Parser вернул 5xx | Retry по [общим retry-политикам](../../pipelines/overview.md#политики-повторных-попыток-и-таймаутов-retry--timeout). Circuit Breaker (5 ошибок подряд) | `status: failed` (после исчерпания) | `OCR_FAILED` / `PARSER_FAILED` |
| Converter-validator `POST /converter/preview` ошибка | Черновик → `ready_for_approve` с флагом ошибки `preview_partial_error`, `notifications` содержат причину | `status: ready_for_approve` (с `decision_required: true`) | `PREVIEW_PARTIAL_ERROR` |
| Converter-validator `POST /validate/metadata` ошибка | То же поведение — черновик доступен пользователю, но без пересчитанного `title_hash_sha256` | `status: ready_for_approve` (с пометкой) | `METADATA_VALIDATION_ERROR` |
| Registry `POST /registry/documents/check-uniqueness` (preview) ошибка | Черновик → `ready_for_approve`, проверка уникальности будет повторена на full-фазе (перед записью) | `status: ready_for_approve` | `UNIQUENESS_CHECK_DEFERRED` |
| Все этапы прошли успешно | Черновик → `ready_for_approve` (или `review_required`, или авто-апрув — см. §3) | `status: completed` | — |
| Preview в статусе `previewing` дольше 30 минут | **Scheduler** переводит черновик в `discarded` | `status: discarded` | `PREVIEW_TIMEOUT` |
| UI запросил `longpoll=15` | Держать соединение до 15с; ответить при изменении статуса или по таймауту с текущим прогрессом | `200` (текущий статус) | — |
| Абсолютный таймаут (для UI) | Не превышать 30 минут (зеркально таймауту `previewing` в FSM) | `200 { status: failed }` (если истёк) | `PREVIEW_TIMEOUT` |

> **Защита от двойного longpoll:** UI может держать только одно активное соединение на `draft_id`. Повторный longpoll с того же `Idempotency-Key` возвращает кеш. С разным — `409 PREVIEW_IN_PROGRESS`.

---

## 3. Quality-решения и авто-апрув

**Источник правил:** [pipeline1-formation.md §Статусная модель — Триггер перехода `review_required → validation`](../pipeline1-formation.md#статусная-модель-fsm).

После завершения OCR/Parser и Converter-validator Оркестратор применяет пороги из `app_settings.parser.quality_thresholds` и `app_settings.parser.auto_approve`.

| Сценарий | Условие | Поведение Оркестратора | Результат |
|----------|---------|------------------------|-----------|
| Качество в норме, авто-апрув выключен | `avg_confidence >= operator_avg_confidence_below` И `pages_failed == 0` И `lama_fallback_used == false` И `auto_approve.enabled == false` | Перевести черновик в `ready_for_approve` | Ждёт `PATCH /decide` |
| Качество в норме, авто-апрув включён, пороги не превышены | `auto_approve.enabled == true` И `critical_count <= max_critical` И `warning_count <= max_warning` | **Авто-апрув:** перевести `ready_for_approve → approved`, запустить full-фазу немедленно | `202 { status: "approved", document_id }` |
| Качество в норме, авто-апрув включён, пороги превышены | `auto_approve.enabled == true` И (`critical_count > max_critical` ИЛИ `warning_count > max_warning`) | Перевести в `ready_for_approve` (ручное решение) | Ждёт `PATCH /decide` |
| Низкое качество — мягкий случай | `reprocess_avg_confidence_below <= avg_confidence < operator_avg_confidence_below` | Направить документ на **переобработку** через `POST /documents/{doc_id}/reprocess` (внутренний) | `indexing` / новая попытка |
| Низкое качество — ручная проверка | `avg_confidence < operator_avg_confidence_below` ИЛИ `pages_failed > 0` ИЛИ `lama_fallback_used == true` | Перевести в `review_required`, записать `notifications` в `pipeline.draft_notifications`, вернуть UI для оператора | `status: review_required` |
| Катастрофически низкое качество | `avg_confidence < reprocess_avg_confidence_below` (порог переобработки) | Перевести в `discarded` (документ нечитаем, нет смысла переобрабатывать) | `status: discarded` с `error_code = "QUALITY_TOO_LOW"` |
| OCR/Parser вернул `notifications[]` | Все `notifications` (любой severity) записать в `pipeline.draft_notifications` через `INSERT ... RETURNING id` (согласно [parser_service_api.md](../../api/parser_service_api.md)) | — | — |
| `notifications[]` содержит `severity: critical` (при авто-апрув) | Превышен `max_critical` (по умолчанию 0) | Авто-апрув **не применяется**, черновик → `ready_for_approve` | Ждёт решение |

> **Принцип:** пороги **никогда** не смягчаются Оркестратором. Только администратор через `app_settings.*` (это вне scope пайплайна).

---

## 4. Решение пользователя: `PATCH /drafts/{draft_id}/decide`

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| `action: approve`, статус `ready_for_approve` (норма) | — | Собрать финальный снимок метаданных (form-поля + OCR/Parser + Converter + overrides), отправить в `POST /validate/metadata` для пересчёта, выполнить `POST /registry/documents/check-uniqueness` (race condition, см. §5), при успехе — перевести в `approved` и запустить full-фазу | `202 { status: "approved", document_id }` | — |
| `action: approve`, статус `review_required` | — | Отказать (для `review_required` доступен только `confirm` или `reject`) | `400 INVALID_ACTION_FOR_STATUS` | `INVALID_ACTION_FOR_STATUS` |
| `action: approve`, статус `validation` | — | Отказать | `400 INVALID_ACTION_FOR_STATUS` | `INVALID_ACTION_FOR_STATUS` |
| `action: approve`, статус терминальный (`approved`, `discarded`) | — | Отказать (идемпотентность — см. §5) | `409 DRAFT_ALREADY_DECIDED` | `DRAFT_ALREADY_DECIDED` |
| `action: approve`, статус `previewing` или `uploaded` | — | Отказать — preview не завершён | `409 INVALID_STATE_TRANSITION` | `INVALID_STATE_TRANSITION` |
| `action: approve`, статус `ready_for_approve`, но 0 страниц | — | Отказать — пустой документ | `400 EMPTY_DOCUMENT` | `EMPTY_DOCUMENT` |
| `action: confirm`, статус `review_required` (норма) | — | Сохранить `metadata_overrides` (если переданы), перевести черновик в `validation`, запустить полный цикл OCR/Parser + Converter-validator с overrides | `200 { status: "validation" }` | — |
| `action: confirm`, статус `ready_for_approve` | — | Отказать (для `ready_for_approve` доступен только `approve` или `reject`) | `400 INVALID_ACTION_FOR_STATUS` | `INVALID_ACTION_FOR_STATUS` |
| `action: confirm`, `metadata_overrides` содержат конфликт уникальности | После `POST /validate/metadata` → `POST /registry/documents/check-uniqueness` найден дубликат | Отказать, не переводить в `validation` | `409 DUPLICATE_DOCUMENT` | `DUPLICATE_DOCUMENT` |
| `action: reject`, статус `ready_for_approve` или `review_required` (норма) | — | Перевести черновик в `discarded`. `metadata_overrides` игнорируются | `200 { status: "discarded" }` | — |
| `action: reject`, статус `validation` | — | Отказать (после `confirm` `validation` идёт автоматически, нельзя вручную прервать) | `400 INVALID_ACTION_FOR_STATUS` | `INVALID_ACTION_FOR_STATUS` |
| `action: reject`, статус терминальный | — | Отказать (идемпотентность) | `409 DRAFT_ALREADY_DECIDED` | `DRAFT_ALREADY_DECIDED` |
| `action: <пусто>` или неизвестное значение | — | Отказать | `400 VALIDATION_ERROR` | `VALIDATION_ERROR` |
| `action: approve`, но `POST /validate/metadata` упал | — | **Не** переводить в `approved`. Сообщить об ошибке. UI может повторить `PATCH /decide` | `502 BAD_GATEWAY` | `CONVERTER_UNAVAILABLE` |
| `action: approve`, но `POST /registry/documents/check-uniqueness` упал | — | **Не** переводить в `approved`. UI может повторить | `502 BAD_GATEWAY` | `REGISTRY_UNAVAILABLE` |

> **Политинг приоритетов для `metadata_overrides` (при approve/confirm):**
> 1. `metadata_overrides` из тела `PATCH /decide` (наивысший)
> 2. Сохранённые через `PATCH /metadata` (если `overrides` не переданы — берутся они)
> 3. OCR/Parser извлечённые
> 4. Converter-validator валидированные
> 5. `metadata_fields` из `POST /drafts` (база, наименьший)

> **См. также:** [Разграничение ответственности Orchestrator vs Registry](../../guide.md#разграничение-ответственности-orchestrator-vs-registry) — `PATCH /registry/drafts/{id}/status` — internal Registry endpoint, вызывается только Оркестратором.

---

## 5. Race condition: `check-uniqueness` ↔ запись в Registry

**Проблема:** между `POST /registry/documents/check-uniqueness` (preview/full) и `POST /registry/documents` проходит время (секунды–часы), в течение которого другой пользователь может зарегистрировать идентичный файл. Атомарная распределённая транзакция недопустима (потеря доступности при сбое).

**Решение (каноническое, см. [pipeline1-formation.md §Компенсация race condition](../pipeline1-formation.md#компенсация-race-condition-между-check-uniqueness-и-approve-записью)):**

1. На preview-фазе: `check-uniqueness` — **best effort**. Результат сохраняется в `preview_metadata`, но финальная верификация — на full-фазе.
2. На `decide action=approve`: Оркестратор
   - собирает финальный снимок метаданных (включая `metadata_overrides`),
   - отправляет в `POST /validate/metadata` для пересчёта `title_hash_sha256` (защита от изменения БД между preview и approve),
   - вызывает `POST /registry/documents/check-uniqueness` (title_hash + file_size_bytes),
   - фиксирует `file_hash_sha256` + `title_hash_sha256` в локальном контексте задачи.
3. Registry при `POST /registry/documents` выполняет `INSERT ... ON CONFLICT (file_hash_sha256) DO NOTHING RETURNING id`.

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| Preview: `is_duplicate=true` | Дубль найден по `title_hash` | `PATCH /registry/drafts/{id}/status status=discarded error_code=DUPLICATE`. Сообщить UI | `duplicate_detected` | `DUPLICATE` |
| Preview: ошибка `check-uniqueness` | Registry недоступен | Перевести в `ready_for_approve` с пометкой `uniq_check_deferred`, проверка повторится на full-фазе | `status: ready_for_approve` | `UNIQUENESS_CHECK_DEFERRED` |
| Approve: `is_duplicate=true` | Конфликт на full-фазе | Отказать, **не** переводить в `approved` | `409 DUPLICATE_DOCUMENT` | `DUPLICATE_DOCUMENT` |
| Approve: `POST /registry/documents` вернул `409 DUPLICATE_FILE` | Конфликт по `file_hash_sha256` на уровне БД (другой документ вставлен между check и write) | `PATCH /registry/drafts/{id}/status status=discarded error_code=DUPLICATE_FILE_AFTER_APPROVE`, пометить `pipeline.tasks.superseded_by_document_id`, отдать `409 DUPLICATE_FILE` UI | `409 DUPLICATE_FILE` (с `conflict_document_id`) | `DUPLICATE_FILE_AFTER_APPROVE` |
| Approve: конфликт на `validate/metadata` | Метаданные изменились (например, drift в `app_settings.parser.normalizer`) | Прервать, вернуть UI | `409 BUSINESS_KEY_DRIFT` | `BUSINESS_KEY_DRIFT` |

> **Аудит:** `DUPLICATE_FILE_AFTER_APPROVE` фиксируется в `registry.document_history` (`event_type="failed_duplicate"`) и в `audit.events` (уровень `CRITICAL`).
>
> **Связанный черновик** помечается `pipeline.tasks.superseded_by_document_id = 42` (только для аудита, не влияет на FSM).

---

## 6. Full-фаза (после `decide action=approve`)

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| Full OCR/Parser — норма | `preview_not_supported != true` | Создать `task_step "full_ocr"`, вызвать OCR/Parser (`mode=full`). Передать `start_page=max_pages+1` если preview-артефакты сохранены (оптимизация) | `raw_ocr_v4` (полный JSON) | — |
| Full OCR/Parser — пропуск | `preview_not_supported == true` | Пропустить `task_step "full_ocr"`, использовать JSON из preview | — | — |
| Full OCR/Parser — таймаут 5 мин | Таймаут HTTP | Retry 3 раза (Exponential 1с → 2с → 4с). При исчерпании — `discarded` | `status: discarded` | `OCR_TIMEOUT` / `PARSER_TIMEOUT` |
| Full OCR/Parser — 5xx | Сетевая ошибка | Retry 3 раза. Circuit Breaker | `status: discarded` | `OCR_FAILED` / `PARSER_FAILED` |
| Full Converter-validator — норма | — | Создать `task_step "full_converter"`, вызвать `POST /converter/convert` (полный режим) | `validated_v3` | — |
| Full Converter-validator — таймаут 2 мин | — | Retry 2 раза (Exponential 1с → 2с). При исчерпании — `discarded` | `status: discarded` | `CONVERTER_TIMEOUT` |
| Full Converter-validator — ошибка LLM | LLM provider вернул 5xx | Retry 2 раза с **truncation контекста на 20%** перед повтором. При исчерпании — `discarded` | `status: discarded` | `LLM_GENERATION_FAILED` |
| Full Converter-validator — ошибка структуры | `validated_v3` не прошёл schema-validation | Вернуть `validation.errors` в `pipeline.task_steps`, `discarded` | `status: discarded` | `VALIDATION_FAILED` |
| Full — пустой документ (0 секций) | OCR вернул пустой результат | Перевести в `discarded` (документ не может быть завершён) | `status: discarded` | `EMPTY_DOCUMENT` |
| Registry `check-uniqueness` (full) — дубль | — | Перевести в `discarded` с `error_code=DUPLICATE`. Сообщить UI | `status: discarded` | `DUPLICATE` |
| Registry `POST /documents` — норма | Все проверки пройдены | Создать `task_step "registry_creation"`, вызвать `POST /registry/documents` (Registry internal). Получить `document_id`, `section_id`, ссылки. **Записать `preview_snapshot`** (копия `preview_metadata` в `registry.documents.preview_snapshot`) | `document_id` (bigint) | — |
| Registry `POST /documents` — ошибка БД | Транзакция упала | Retry 2 раза (Exponential 500мс → 1с). При исчерпании — `discarded` | `status: discarded` | `REGISTRY_WRITE_FAILED` |
| Registry `POST /documents` — `409 DUPLICATE_FILE` | Race condition на уровне БД | См. §5 | `409 DUPLICATE_FILE` | `DUPLICATE_FILE_AFTER_APPROVE` |
| Успех full-фазы | — | Черновик → `created`, переход в `pending_index` (Pipeline 2) | `status: created` | — |
| Очистка preview-артефактов | После `created` | Удалить `registry.drafts.preview_metadata` (больше не нужен, `preview_snapshot` сохранён в `registry.documents`) | — | — |

> **Оптимизация (кэширование preview, см. [pipeline1-formation.md §Кэширование](../pipeline1-formation.md#кэширование-результатов-preview-фазы)):** preview-результаты (частичный JSON, метаданные) сохраняются в журнале Оркестратора с TTL 7 дней. При full-фазе Оркестратор передаёт их в `task_step "full_ocr"` как `start_page` и в `task_step "full_converter"` как базу метаданных (дообогащение). Если preview-артефакты истекли (TTL) — full-фаза запускается с нуля (все страницы).

---

## 7. `PATCH /drafts/{draft_id}/metadata` (правка метаданных без решения)

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| `PATCH /metadata`, статус `ready_for_approve` или `review_required` (норма) | — | Собрать текущие + переданные поля, отправить в `POST /validate/metadata` для пересчёта, выполнить `check-uniqueness` | `200 { preview_metadata, title_hash_sha256, title_key }` | — |
| `PATCH /metadata`, статус `previewing` / `uploaded` | — | Отказать (preview не завершён) | `400 INVALID_ACTION_FOR_STATUS` | `INVALID_ACTION_FOR_STATUS` |
| `PATCH /metadata`, статус терминальный | — | Отказать | `409 INVALID_STATE_TRANSITION` | `INVALID_STATE_TRANSITION` |
| `PATCH /metadata`, конфликт уникальности | `check-uniqueness` нашёл дубль | Отказать, **не сохранять** правки | `409 DUPLICATE_DOCUMENT` | `DUPLICATE_DOCUMENT` |
| `PATCH /metadata`, `validate/metadata` ошибка | Converter-validator упал | Не сохранять правки, вернуть ошибку | `502 BAD_GATEWAY` | `CONVERTER_UNAVAILABLE` |
| `PATCH /metadata`, пустые поля | Ни одно поле не передано | No-op (без ошибки) | `200` | — |
| `PATCH /metadata`, невалидные значения | Например, `valid_until < valid_from` | Отказать | `400 VALIDATION_ERROR` | `VALIDATION_ERROR` |

> **Связь с `decide`:** правки, сделанные через `PATCH /metadata`, **сохраняются** в `registry.drafts.metadata_overrides`. При последующем `PATCH /decide` Оркестратор использует их как приоритет (см. §4). Повторная передача `metadata_overrides` в `decide` **перезаписывает** ранее сохранённые.

---

## 8. Удаление черновика: `DELETE /drafts/{draft_id}`

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| `DELETE /drafts/{id}`, статус `uploaded` / `previewing` / `ready_for_approve` / `review_required` / `validation` / `discarded` | — | Каскад: `DELETE /registry/drafts/{id}` (Registry internal) + `DELETE FROM pipeline.task_steps WHERE task_id IN (SELECT id FROM pipeline.tasks WHERE draft_id = ?)`. MinIO-объект **не удаляется** (TTL 30 дней, см. [CAS-спецификацию](../../specifications/cas_storage_specification.md)) | `200 { draft_id, deleted_at }` | — |
| `DELETE /drafts/{id}`, статус `approved` | Документ уже создан в Registry | `DELETE /registry/drafts/{id}` (черновик удаляется). **Документ в Registry не затрагивается** | `200` | — |
| `DELETE /drafts/{id}`, несуществующий | — | — | `404 DRAFT_NOT_FOUND` | `DRAFT_NOT_FOUND` |

> **Связанные правила:** файл в MinIO сохраняется до истечения CAS-TTL (по умолчанию 30 дней), даже если черновик удалён. Это позволяет повторно загрузить тот же файл без повторной передачи бинарного контента.

---

## 9. Версии документа: `POST /documents/{doc_id}/versions`

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| `POST /versions`, норма | Документ существует | Скопировать все поля из `current_version_id` документа, создать новый черновик (`status=uploaded`), привязать к `document_id` (через `registry.drafts.parent_document_id` или эквивалент). Вычислить новый `version_number` | `202 { document_id, version_id, version_number, status: "uploaded", task_id, file_hash_sha256 }` | — |
| `POST /versions`, документ в обработке | Статус `pending_index` / `indexing` | Отказать — нельзя создать версию на документе в активной обработке | `409 DOCUMENT_IN_PROCESSING` | `DOCUMENT_IN_PROCESSING` |
| `POST /versions`, документ не найден | — | — | `404 DOCUMENT_NOT_FOUND` | `DOCUMENT_NOT_FOUND` |
| `POST /versions`, файл — дубль по `file_hash_sha256` | Уже есть зарегистрированный файл | Отказать | `409 DUPLICATE_FILE` | `DUPLICATE_FILE` |
| Новая версия прошла preview → approve | — | `document_id` остаётся неизменным. Создаётся `version_id`, `current_version_id` обновляется. Старая версия доступна через `GET /documents/{doc_id}/versions`. **Pipeline 2 запускается заново** для новой версии | — | — |
| Новая версия — `discarded` | — | `current_version_id` **не меняется**. Старая версия остаётся активной | — | — |

---

## 10. `POST /documents/{doc_id}/reprocess` (переобработка)

| Сценарий | Условие | Поведение Оркестратора | Результат | Код |
|----------|---------|------------------------|-----------|-----|
| `mode: full` | — | Создать новую `pipeline.tasks`, повторить полный цикл OCR/Parser → Converter-validator → Registry → RAG Builder с новой `task_id`. **Новый `draft_id` не создаётся** | `202 { task_id, document_id, mode, status: "processing" }` | — |
| `mode: ocr_only` | — | Только OCR/Parser + Converter-validator. Без Registry-rewrite (но с обновлением `raw_data` для индексации) | — | — |
| `mode: chunking_only` | — | Только RAG Builder (Pipeline 2) | — | — |
| `mode: validation_only` | — | Только Converter-validator (`POST /converter/convert` заново) | — | — |
| `mode: reindex` | Документ в статусе `indexed` или `failed` | `DELETE /rag/build/{doc_id}` → `POST /rag/build` с актуальным JSON. При ошибке `DELETE` — отмена с `CLEANUP_FAILED` | — | — |
| Документ не найден | — | — | `404 DOCUMENT_NOT_FOUND` | `DOCUMENT_NOT_FOUND` |
| Документ в активной обработке | Статус `pending_index` / `indexing` | Отказать | `409 DOCUMENT_IN_PROCESSING` | `DOCUMENT_IN_PROCESSING` |
| `options.pages` указывает диапазон | — | Передать в OCR/Parser как `pages` параметр | — | — |

---

## 11. Висящие состояния (Scheduler)

**Расписание:** Scheduler (или CRON-задача) запускается каждые 5 минут. Действует на `registry.drafts` и `registry.documents` через прямые SQL-запросы (вне FSM-логики Оркестратора).

| Состояние | Таймаут ожидания | Действие Scheduler | Код ошибки |
|-----------|------------------|---------------------|------------|
| `uploaded` | 1 час | Перевод в `discarded` | `PREVIEW_TRIGGER_TIMEOUT` |
| `previewing` | 30 минут | Перевод в `discarded` | `PREVIEW_TIMEOUT` |
| `ready_for_approve` | 24 часа | Перевод в `discarded` | `DECISION_TIMEOUT` |
| `validation` | 1 час (для подстраховки) | Перевод в `discarded` | `VALIDATION_TIMEOUT` |
| `pending_index` (Pipeline 2) | 1 час | Перевод в `failed` | `INDEX_TRIGGER_TIMEOUT` |

> **Поведение Оркестратора при таймауте:** не инициировать никаких активных действий. Перевод — ответственность Scheduler (по [specificity.md §X5](../../specificity.md) журнал Оркестратора не отражён в схеме БД, но Scheduler читает `registry.*` напрямую). Оркестратор только логирует событие в `audit.events`.

> **Уведомление пользователя:** при переходе в `discarded`/`failed` по таймауту — UI получает `notifications` через `GET /drafts/{id}/notifications` или `GET /documents/{id}/errors` (admin-роль).

---

## 12. Журналирование и аудит

| Артефакт | Хранилище | Назначение |
|----------|-----------|------------|
| `pipeline.tasks` | Orchestrator DB | Сквозной `task_id` для всех этапов документа |
| `pipeline.task_steps` | Orchestrator DB | Каждый вызов сервиса: `step_name`, `service_name`, `input_data`, `output_data`, `started_at`, `completed_at`, `error_code`, `error_message` |
| `pipeline.draft_notifications` | Orchestrator DB | `notifications[]` от Parser/OCR/Converter-validator: `code`, `severity`, `category`, `message`, `location`, `suggested_action`, `draft_id` |
| `registry.document_history` | Registry DB | События жизненного цикла документа (`created`, `updated`, `failed_duplicate` и т.п.) |
| `audit.events` | Audit DB | Аудит: `who` (user_id/service), `what` (action), `when` (timestamp), `result`, `severity` (см. P11-4) |

> **Поведение Оркестратора:**
> - На каждом этапе — запись в `pipeline.task_steps` (даже при ошибке).
> - `severity: CRITICAL` — для `DUPLICATE_FILE_AFTER_APPROVE`, потеря консистентности preview/full.
> - `severity: ERROR` — для всех retry-exhausted, `REGISTRY_WRITE_FAILED`, `OCR_FAILED`.
> - `severity: WARNING` — для `notifications[]` от сервисов, `PREVIEW_PARTIAL_ERROR`.

---

## 13. Сводка HTTP-кодов ошибок

| HTTP | Код | Когда |
|------|-----|-------|
| 400 | `VALIDATION_ERROR` | Некорректные поля |
| 400 | `EMPTY_FILE` | 0 байт |
| 400 | `FILE_TOO_SMALL` | < 1 КБ |
| 400 | `EMPTY_DOCUMENT` | 0 страниц при approve / 0 секций при full |
| 400 | `INVALID_ACTION_FOR_STATUS` | Несовместимое `action` для текущего статуса |
| 401 | `UNAUTHORIZED` | Нет JWT (от Gateway) |
| 403 | `FORBIDDEN` | Нет прав (от Gateway) |
| 404 | `DRAFT_NOT_FOUND` | Нет черновика |
| 404 | `DOCUMENT_NOT_FOUND` | Нет документа |
| 409 | `DUPLICATE_FILE` | Дубль по SHA-256 |
| 409 | `DUPLICATE_DOCUMENT` | Дубль по `title_hash_sha256` |
| 409 | `DUPLICATE_FILE_AFTER_APPROVE` | Race condition на full-фазе |
| 409 | `DRAFT_ALREADY_DECIDED` | `decide` для терминального черновика |
| 409 | `DRAFT_ALREADY_PREVIEWED` | `preview` для завершённого/терминального |
| 409 | `PREVIEW_IN_PROGRESS` | `preview` уже выполняется |
| 409 | `INVALID_STATE_TRANSITION` | FSM-нарушение |
| 409 | `BUSINESS_KEY_DRIFT` | Бизнес-ключ изменился между preview и approve |
| 409 | `DOCUMENT_IN_PROCESSING` | reprocess/versions на активном документе |
| 413 | `FILE_TOO_LARGE` | > 100 МБ |
| 422 | `UNSUPPORTED_FILE_TYPE` | Неподдерживаемый MIME |
| 422 | `PREVIEW_NOT_SUPPORTED` | Движок не умеет постраничный preview |
| 422 | `VALIDATION_FAILED` | Семантика не прошла |
| 500 | `INTERNAL_ERROR` | Непредвиденная ошибка |
| 502 | `BAD_GATEWAY` / `OCR_FAILED` / `PARSER_FAILED` / `CONVERTER_UNAVAILABLE` / `REGISTRY_UNAVAILABLE` | Внутренний сервис вернул 5xx |
| 503 | `SERVICE_UNAVAILABLE` / `STORAGE_UNAVAILABLE` | MinIO/БД недоступны |

---

## 14. Связанные спецификации и файлы

- [Пайплайн 1: Формирование документа](../pipeline1-formation.md) — основной поток
- [Детальное описание preview-фазы](../pipeline1-formation_detail.md) — preview в деталях
- [Сводный обзор пайплайнов](../overview.md) — общая картина
- [API Orchestrator Service](../../api/orchestrator_service_api.md) — эндпоинты
- [Разграничение ответственности Orchestrator vs Registry](../../guide.md#разграничение-ответственности-orchestrator-vs-registry)
- [Бизнес-ключ вычисляет только Converter-validator](../../guide.md#бизнес-ключ-вычисляет-только-converter-validator)
- [Глоссарий: статусы черновиков](../../glossary.md#статусы-черновиков-registrydrafts)
- [Пайплайн 2: сценарии поведения Оркестратора](pipeline2-orchestrator_details.md)
- [Пайплайн 3: сценарии поведения (Query Service)](pipeline3-orchestrator_details.md)
- [CAS-спецификация](../../specifications/cas_storage_specification.md) — MinIO
- [Спецификация нормализатора](../../specifications/normalizer_specification.md) — `title_hash_sha256`
