# План: привести production-код в соответствие с документацией

**Источник расхождений:** `specificity.md` §3.11, `docs/pipelines/pipeline1-orchestrator_details.md`

## Приоритет 1 — Ошибки в кодах ответов

### 1.1 UNSUPPORTED_FILE_TYPE → 422 (не 400)

**Где:** `app/api/v1/endpoints/drafts.py:167-176`
**Документация:** `422 UNSUPPORTED_FILE_TYPE`
**Сейчас:** `400 BAD_REQUEST` с текстом "Неподдерживаемый формат файла"

**Что сделать:**
- Поменять `status.HTTP_400_BAD_REQUEST` → `status.HTTP_422_UNPROCESSABLE_ENTITY`
- Поменять `"code": "BAD_REQUEST"` → `"code": "UNSUPPORTED_FILE_TYPE"`

### 1.2 PREVIEW_IN_PROGRESS → PREVIEW_ALREADY_RUNNING

**Где:** `app/api/v1/endpoints/drafts.py:692`
**Документация:** `409 PREVIEW_IN_PROGRESS`
**Сейчас:** `409 PREVIEW_ALREADY_RUNNING`

**Что сделать:**
- Заменить `"code": "PREVIEW_ALREADY_RUNNING"` → `"code": "PREVIEW_IN_PROGRESS"`

### 1.3 DRAFT_ALREADY_DECIDED → TASK_ALREADY_TERMINAL

**Где:** `app/api/v1/endpoints/drafts.py:1012`
**Документация:** `409 DRAFT_ALREADY_DECIDED`
**Сейчас:** `409 TASK_ALREADY_TERMINAL`

**Что сделать:**
- Заменить `"code": "TASK_ALREADY_TERMINAL"` → `"code": "DRAFT_ALREADY_DECIDED"`

---

## Приоритет 2 — Недостающая валидация

### 2.1 FILE_TOO_SMALL (< 1 КБ)

**Где:** `app/api/v1/endpoints/drafts.py`, после `file_size == 0` (строка 266)
**Документация:** `400 FILE_TOO_SMALL` для файлов < 1 КБ

**Что сделать:**
- Добавить после проверки `file_size == 0`:
```python
if file_size < 1024:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": {
                "code": "FILE_TOO_SMALL",
                "message": "Размер файла менее 1 КБ",
                "details": {"min_size_bytes": 1024, "actual_size_bytes": file_size},
            }
        },
    )
```

### 2.2 DUPLICATE_FILE — блокировка при создании черновика

**Где:** `app/api/v1/endpoints/drafts.py:352-368`
**Документация:** Если `file_hash_sha256` уже в активной обработке → `409 DUPLICATE_FILE`

**Что сделать:**
- После `check_uniqueness` (строка 362), если `is_duplicate_file == True`:
  - Не создавать черновик
  - Вернуть `409 DUPLICATE_FILE`
  - Перед этим проверить, что существующий черновик активен (не discarded)

### 2.3 Пороги качества (auto-approve)

**Где:** `app/core/pipeline/orchestrator.py:_check_auto_approve` (строка 544)
**Документация:** §3, пороги `avg_confidence`, `max_critical`, `max_warning`, `operator_avg_confidence_below`, `reprocess_avg_confidence_below`

**Что сделать:**
- Расширить `PipelineConfig` в `app/core/config.py` новыми полями:
  - `AUTO_APPROVE_ENABLED: bool = False`
  - `AUTO_APPROVE_MAX_CRITICAL: int = 0`
  - `AUTO_APPROVE_MAX_WARNING: int = 2`
  - `QUALITY_OPERATOR_CONFIDENCE_BELOW: float = 0.8`
  - `QUALITY_REPROCESS_CONFIDENCE_BELOW: float = 0.5`
- Доработать `_check_auto_approve`: читать `quality_data` из step, проверять пороги
- Добавить логику для `review_required` при `avg_confidence < operator_avg_confidence_below`
- Добавить логику для discarded при `avg_confidence < reprocess_avg_confidence_below`

---

## Приоритет 3 — Новая функциональность

### 3.1 confirm action

**Где:** `app/api/v1/endpoints/drafts.py` + `PipelineOrchestrator`
**Документация:** §4, `action: confirm` для `review_required`

**Что сделать:**
- Добавить `"confirm"` в `ALL_ACTIONS`
- Создать `PipelineOrchestrator.confirm_draft()`:
  - Сохранить `metadata_overrides`
  - Перевести черновик в `validation`
  - Запустить полный цикл OCR/Parser + Converter-validator с overrides
- Добавить проверку в `decide_draft`: для `confirm` допускать только stage `review_required`

### 3.2 DUPLICATE_FILE_AFTER_APPROVE

**Где:** `app/core/pipeline/orchestrator.py:approve_draft`
**Документация:** §5, race condition между check-uniqueness и POST /documents

**Что сделать:**
- После `registry.create_document()`, если пришёл `409 DUPLICATE_FILE`:
  - Откатить: `PATCH /registry/drafts/{id}/status` → discarded
  - Записать `task.superseded_by_document_id` из ответа Registry
  - Вернуть `409 DUPLICATE_FILE_AFTER_APPROVE` с `conflict_document_id`

### 3.3 BUSINESS_KEY_DRIFT

**Где:** `app/core/pipeline/orchestrator.py:approve_draft`
**Документация:** §5, дрифт метаданных между preview и approve

**Что сделать:**
- После `POST /validate/metadata` на approve — сравнить `title_hash_sha256` с тем, что был на preview
- Если не совпадает → `409 BUSINESS_KEY_DRIFT`, прервать
- Если метаданные изменились настолько, что бизнес-ключ стал другим — прервать

### 3.4 Idempotency-Key для POST /preview

**Где:** `app/api/v1/endpoints/drafts.py:start_preview`
**Документация:** §1, P1-19

**Что сделать:**
- Добавить параметр `idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")`
- Реализовать in-memory кэш (аналогично `_IDEMPOTENCY_CACHE` для POST /drafts)
- TTL 1 час
- При повторном ключе → вернуть кэшированный 202

---

## Тесты

После каждого исправления:
1. Снять с тестов, которые проверяли "реальное" поведение, пометки
2. Обновить asserts под новые коды ошибок
3. Написать новые тесты на новую функциональность

Затрагиваемые тесты:
- `test_drafts_boundaries.py` — FILE_TOO_SMALL
- `test_preview_state_validation.py` — коды ошибок
- `test_decide_edge_cases.py` — confirm, коды ошибок
- `test_quality_auto_approve.py` — пороги качества
- `test_race_conditions.py` — DUPLICATE_FILE_AFTER_APPROVE
