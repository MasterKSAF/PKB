# Todo — План разработки Orchestrator Service

> Создан: 19.06.2026 на основе task assignment от 19.06.2026

## Условные обозначения

- ✅ — Выполнено
- 🔴 — Блокирующе
- 🟠 — Серьёзно
- 🟡 — Важно
- 🔵 — Средне
- ⚪ — Косметика

---

## 1. Common API (сквозные задачи)

### CM-1 🟠 RBAC-матрица (search/registry), убрать checks
- [ ] Реализовать RBAC-матрицу для эндпоинтов search и registry
- [ ] Убрать mock checks в deps (сейчас всегда возвращается MOCK_USER)

### CM-2 🟠 Rate limiting (Nginx+Redis)
- [ ] Добавить интеграцию Redis для rate limiting
- [ ] Настроить лимиты на эндпоинты

### CM-3 🟠 IDOR: rate-limit + audit для идентификаторов
- [ ] Rate-limit на защиту от перебора draft_id, document_id
- [ ] Audit логирование доступа к идентификаторам

### CM-4 🔴 Service-to-service auth: сетевая изоляция
- [ ] Настроить Docker-сеть internal для вызовов между сервисами

### CM-5 🟠 Структурированное логирование + корреляционные заголовки
- [ ] ✅ Trace ID middleware реализован (X-Trace-ID, X-Request-ID)
- [ ] Добавить проброс X-User-ID, X-Draft-ID, X-Document-ID, X-Version-ID
- [ ] Добавить correlation ID во все downstream-вызовы

### CM-6 🟠 OTEL SDK + service_checker
- [ ] Добавить OpenTelemetry SDK в main.py
- [ ] Реализовать service_checker с exit-code 0/1/2

### CM-7 🟠 Специфичные коды ошибок (D24)
- [ ] Добавить коды 408: INDEX_TRIGGER_TIMEOUT, DECISION_TIMEOUT, PREVIEW_TRIGGER_TIMEOUT, LLM_GENERATION_TIMEOUT
- [ ] Привести error codes к единому справочнику

### DB-5 🟡 ON DELETE/ON UPDATE для всех FK
- [x] ✅ ON DELETE CASCADE добавлен для TaskStep.task_id и DraftNotification.task_id

### DB-11 🟡 uploaded_at → created_at, uploaded_by → created_by
- [ ] Переименовать поля в моделях БД

---

## 2. Orchestrator Service — API эндпоинты

### OR-1 🟠 Админка /tasks/* (read-only)
- [x] ✅ GET /tasks/{task_id}/status — реализован
- [x] ✅ GET /tasks — список задач с пагинацией + фильтры
- [x] ✅ GET /tasks/stats — статистика по задачам
- [ ] ⏳ Добавить эндпоинт списка шагов /tasks/{task_id}/steps

### OR-2 🟠 POST /drafts/{draft_id}/preview — идемпотентность 409
- [x] ✅ Добавить проверку: если preview уже запущен → 409 CONFLICT
- [x] ✅ Добавить error.code PREVIEW_ALREADY_RUNNING

### OR-3 🟡 PATCH /drafts/{id}/decide — metadata_overrides
- [x] ✅ Добавить поле metadata_overrides в DecideRequest
- [x] ✅ Передавать metadata_overrides в Registry при approve
- [x] ✅ Обновить схему DecideRequest

### OR-4 ⚪ uploaded_at/uploaded_by → created_at/created_by в versions
- [ ] ⏳ Переименовать в моделях (на уровне Orchestrator — относится к Task/TaskStep)

### OR-5 🔴 Передавать draft_id в Parser/OCR (обязательно)
- [x] ✅ Добавить draft_id в ParserProcessRequest, OcrProcessRequest
- [x] ✅ Обновить mock-ответы Parser/OCR клиентов
- [x] ✅ Передавать draft_id из create_draft → pipeline → Celery tasks

### OR-6 🟠 quality.notifications[] → pipeline.draft_notifications
- [x] ✅ Создать модель DraftNotification (task_id, draft_id, service, code, message, severity, created_at)
- [x] ✅ Создать таблицу pipeline.draft_notifications
- [x] ✅ Реализовать has_notifications, critical_count в TaskResponse
- [ ] ⏳ Перенести quality.notifications[] в draft_notifications (логика из Parser/OCR)

### OR-7 🟠 Добавить в GET /drafts/{id} поля document_id, version_id, is_new_document
- [x] ✅ DraftDetailResponse — добавлены version_id, is_new_document
- [x] ✅ DecideResponse — добавлены document_id, version_id, is_new_document
- [x] ✅ Получать данные из Registry



### OR-9 🟡 Обновить preview_metadata (8+ полей)
- [x] ✅ Расширить PreviewMetadata: +7 полей (source_type, era, jurisdiction, mks_oks_code, okstu_code, issuing_body, udk_code)
- [x] ✅ Обновить схему PreviewMetadata — теперь 12 полей
- [x] ✅ Синхронизирован DraftPreviewStatusResponse
- [ ] ⏳ Синхронизировать с Converter-Validator (CV-4)

### OR-10 🟠 Сетевая изоляция Docker-сети internal
- [ ] ⏳ Инфраструктурная задача — настройка Docker Compose

### OR-11 🔴 POST /drafts — единая точка входа
- [x] ✅ POST /drafts реализован (создание черновика)
- [x] ✅ Accept-Encoding header для mime_type пробрасывается в pipeline
- [ ] ⏳ Явно deprecate POST /documents в readme.md

### OR-12 🔴 PATCH /drafts/{draft_id}/decide — approve/reject + внутренние действия
- [x] ✅ approve/reject — реализованы
- [x] ✅ Добавлены proceed (продолжить), stop_duplicate (дубликат), force_new_version (новая версия)
- [x] ✅ Разделение external/internal actions
- [x] ✅ _check_auto_approve — реальная проверка (метаданные + дубликаты)
- [x] ✅ DecideRequest — action валидируется (400 если неизвестное)

### OR-13 🟠 approve → Registry создаёт document_id
- [x] ✅ approve_draft вызывает Registry.create_document() перед full phase
- [x] ✅ document_id, version_id возвращаются в DecideResponse
- [x] ✅ document_id сохраняется в Task.document_id для registry step

### OR-14 🟠 Ветвление: OCR vs Parser по MIME-типу
- [x] ✅ Исправлена логика: image/* → OCR, application/pdf → Parser
- [x] ✅ В POST /drafts mime_type передаётся из File.content_type
- [x] ✅ В start_preview mime_type берётся из Registry (draft metadata)
- [x] ✅ PDF больше не идёт в OCR по умолчанию

---

## 3. Database / Модели

### DB-23 🟠 Новая таблица pipeline.tasks
- [ ] ✅ Task модель уже существует
- [ ] ✅ TaskStep модель уже существует
- [ ] Проверить соответствие спецификации DB-23/DB-24

### DB-24 🟠 Новая таблица pipeline.task_steps
- [ ] ✅ TaskStep уже существует

### DB-6 🟡 Soft-delete: deleted_at
- [ ] Добавить deleted_at TIMESTAMPTZ в модели (если нужно)

### DB-26 🟡 draft_id FK в registry.documents
- [ ] (Относится к БД Registry — не входит в Orchestrator)

---

## 4. Сервис-клиенты

### OR-5/PS-3/OC-4 — draft_id в вызовах Parser/OCR
- [x] ✅ ParserProcessRequest: добавлен draft_id, mode, max_pages
- [x] ✅ OcrProcessRequest: изменён (file_key, draft_id, mode) вместо (file_id, pages)
- [x] ✅ ParserServiceClient: unified process() метод
- [x] ✅ OCRServiceClient: unified process() метод вместо process_document
- [x] ✅ pipeline_formation.py: draft_id во всех step-функциях

### PS-5/OC-8 — Объединить preview и process
- [x] ✅ Parser: /parser/process?mode=preview|full
- [x] ✅ OCR: /ocr/process?mode=preview|full
- [x] ✅ Mock-ответы обновлены

---

## 5. Тесты

### T-1 🔴 Unit-тесты assess_quality()
- [ ] Создать tests/shared/test_quality.py
- [ ] Тесты для функции оценки качества (пороги <0.6 / <0.85)

### T-4 🟠 Запись notifications[] в pipeline.draft_notifications
- [ ] tests/orchestrator/test_issues_recording.py

### T-5 🔴 Тест draft_id (400/404/валидный)
- [ ] tests/orchestrator/test_draft_id_propagation.py
- [ ] Проверка что draft_id передаётся в Parser/OCR

### T-7 🟠 Цепочка draft → document → version
- [ ] tests/integration/test_draft_to_version.py

### T-11 🟠 Корреляционные заголовки
- [ ] tests/integration/test_correlation.py

### T-12 🟡 health/ready vs health/live
- [ ] tests/integration/test_health.py
- [ ] Разделить health check на liveness и readiness

### T-13 🟡 Алерты (6 правил)
- [ ] tests/monitoring/test_alerts.py

### T-14 🟠 service_checker
- [ ] tests/observability/test_service_checker.py

### T-15 🟠 OTEL → SigNoz
- [ ] tests/observability/test_otel_export.py

---

## 6. Очистка и документация

### ⚪ Удалить устаревшие эндпоинты /documents
- [ ] Удалить или явно deprecate POST /documents
- [ ] Документация: /drafts — единая точка входа

### ⚪ Очистить API router
- [ ] Удалить monitor router если не используется (GW-12)
- [ ] Актуализировать таблицу маршрутизации

### 📖 Документация
- [ ] Обновить readme.md с новыми эндпоинтами
- [ ] Актуализировать orchestrator_service_api.md с изменениями
- [ ] Зафиксировать архитектурные решения в specificity.md
- [ ] Создать guide.md с ориентирами по разработке

---

## Выполнено (этап 19.06.2026)

### Критические (🔴)
- [x] OR-5 — draft_id передаётся в Parser/OCR ✅
- [x] OR-11 — POST /drafts единая точка входа (mime_type пробрасывается) ✅
- [x] OR-12 — approve/reject + proceed/stop_duplicate/force_new_version ✅
- [x] OR-13 — approve → Registry.create_document() ✅

### Серьёзные (🟠)
- [x] OR-1 — GET /tasks (список), GET /tasks/stats ✅
- [x] OR-2 — Идемпотентность preview (409 PREVIEW_ALREADY_RUNNING) ✅
- [x] OR-7 — version_id, is_new_document в DraftDetailResponse ✅
- [x] OR-14 — MIME-ветвление исправлено ✅
- [x] OR-6 — Модель DraftNotification + has_notifications/critical_count ✅

### Важные (🟡)
- [x] OR-3 — metadata_overrides в DecideRequest ✅
- [x] OR-9 — PreviewMetadata расширен до 12 полей ✅
- [x] DB-5 — ON DELETE CASCADE для FK ✅

### Сервис-клиенты
- [x] PS-5/OC-8 — /parser/process и /ocr/process unified (mode=preview|full) ✅
- [x] OR-5/PS-3/OC-4 — draft_id во всех клиентах и задачах ✅

### Тесты
- [x] 352 passed (все тесты) ✅

## Осталось (будущие этапы)

1. **🟠 OR-8** — OTEL SDK в main.py
2. **🟠 CM-6** — service_checker
3. **🟡 OR-6** — Логика quality.notifications из Parser/OCR
4. **🔴 T-1, T-5, T-7** — Новые тесты
5. **🟡 CM-7** — Коды ошибок (D24)
6. **🟠 CM-1** — RBAC-матрица
7. **🟠 CM-2/CM-3** — Rate limiting + IDOR
8. **🟠 OR-10** — Docker network internal
9. **⚪ OR-4** — uploaded_at → created_at
10. **📖** — Актуализация readme.md и API docsэтапа (что делать сейчас)

1. **🔴 OR-5** — draft_id в Parser/OCR (блокирует pipeline)
2. **🔴 OR-12** — approve/reject + внутренние действия
3. **🔴 OR-13** — Registry создаёт document_id
4. **🔴 OR-11** — POST /drafts единая точка входа
5. **🟠 OR-1** — Админка /tasks/* (read-only)
6. **🟠 OR-2** — Идемпотентность preview
7. **🟠 OR-7** — document_id/version_id/is_new_document в GET /drafts/{id}
8. **🟠 OR-14** — MIME-тип в POST /drafts
9. **🟡 OR-9** — Preview metadata (8 полей)
10. **🟠 OR-6** — notifications
11. **🟠 OR-8** — OTEL SDK
12. **🟡 OR-3** — metadata_overrides
13. **🔴 T-1, T-5, T-7** — Критические тесты

---

## Выполненные задачи (предыдущие итерации)

### ✅ Валидация данных на границах сервисов (предыдущая задача)

**Что сделано:**

1. **JSON serialization guard в `base_client.call()`** ✅
   - Файл: `app/services/base_client.py`
   - `json.dumps()` проверка для всех `json` kwargs — защита для ВСЕХ 5 клиентов
   - Срабатывает ДО ветвления mock/real — ошибка не уходит никуда

2. **Pydantic request_model в `base_client.call()`** ✅
   - Опциональный параметр `request_model: Type[BaseModel]`
   - `model_validate()` → `model_dump()` — структурная валидация до отправки
   - Ошибка: `TypeError("... Pydantic validation: ...")`

3. **Pydantic request schemas для всех клиентов** ✅
   - Файл: `app/schemas/requests.py` — 8 схем
   - CreateDraftRequest, UpdateDraftStatusRequest, CheckUniquenessRequest
   - OcrProcessRequest, ParserPreviewRequest, ParserProcessRequest
   - RagIndexRequest, RagSearchRequest, RagGenerateRequest

4. **Тесты** ✅ — TestServiceClientDataValidation (4 теста), 353 passed

5. **Зафиксировано в specificity.md** ✅ — п. 1.5, п. 3.9

## Текущий статус (19.06.2026)

- **Все тесты:** 353 passed
- **API эндпоинты:** /drafts, /documents, /tasks, /search, /health, /monitor
- **Pipeline:** Preview + Full фазы реализованы
- **FSM:** DraftState + TaskStatus + TaskStage
- **Trace:** contextvars-based trace ID
- **Service clients:** 6 клиентов (Registry, Parser, OCR, Converter, RAG, base)
- **DB:** SQLite (dev) / PostgreSQL (prod target)
