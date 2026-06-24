# Recheck — анализ ошибок в service_checker

## Найденные ошибки и их причины

### 1. Orchestrator: POST /api/v1/drafts/ → HTTP 500 (блокирует 8 пайплайнов)
- **Симптом**: Все пайплайны с созданием черновика падают с 500
- **Корень в orchestrator-логах**: 
  - `POST /registry/documents/check-uniqueness` → **422** (Unprocessable Content)
  - `POST /registry/drafts` → **422**
  - Orchestrator возвращает `"Ошибка при создании черновика в Registry"`
- **Причина**: **Проблема в orchestrator service** — он отправляет неверные данные в Registry. 
  Registry при прямом вызове из API Coverage работает (POST /registry/drafts → 201, check-uniqueness → 200).
- **Чекер не может исправить** — проблема взаимодействия orchestrator → registry.

### 2. Gateway: 36 failed, 34 skipped — все с HTTP 401 ✅ ИСПРАВЛЕНО
- **Симптом**: Все endpoint'ы Gateway возвращают 401. Даже POST /auth/token → 401
- **Корень**: В Docker (supervisord.conf) запущен **Mock Gateway** (`mocks.gateway:app`), не реальный reverse-proxy (`gateway.main:app`).
  Mock Gateway использует seed users с паролем **`admin123`** (см. `mocks/common.py`), а чекер слал `Admin1234!` (TEST_CREDENTIALS).
- **Исправление**: В `services/gateway.py` всегда используем `GATEWAY_CREDENTIALS` (admin123).

### 3. Query Service: POST /chat/sessions → HTTP 500 + UniqueViolationError
- **Корень из query-err**: 
  - `UniqueViolationError: duplicate key value violates unique constraint "uq_chat_projects_user_code"`
  - Проект с code='PIPELINE' для user 'u-001' уже существует
  - Вместо 409 — 500 Internal Server Error
- **Причина**: **Проблема в query service** — не обрабатывает unique constraint правильно (должен 409).

### 4. RAG Builder: POST /api/v1/rag/build → HTTP 500 в pipeline
- **API Coverage**: POST /rag/build → 202 OK
- **Pipeline**: POST /rag/build с `{"document_id": N, "sections": [...]}` → 500
- **Причина**: Разные данные. В pipeline передаются section'ы, а в API coverage — только document_id.
  **Возможная проблема в чекере** — разница в данных. Но скорее проблема в RAG Builder сервисе.

### 5. DB: Отсутствуют схемы auth, pipeline и UNIQUE-индексы
- **Проблема в сервисах** — Alembic миграции не до конца применились.

### 6. OpenTelemetry UNAVAILABLE — во всех сервисах
- signoz-otel-collector:4317 недоступен. Контейнер не запущен.

## Сделано в чекере (service_checker)

### 1. Gateway credentials — ИСПРАВЛЕНА ОСНОВНАЯ ПРИЧИНА 401
- ✅ В Docker (supervisord.conf) запущен **Mock Gateway** (`mocks.gateway:app`) с seed-паролем `admin123`
- ✅ Чекер в `services/gateway.py` теперь всегда использует `GATEWAY_CREDENTIALS` (admin123) вместо `TEST_CREDENTIALS` (Admin1234!)
- ✅ Обновлены тесты `test_gateway_mode.py` — 570/570 passed

### 2. pipelines/base.py — `_ensure_project` (UniqueViolation)
- ✅ Уникальный code с timestamp (`PIPELINE_<ts>_<attempt>`) вместо фиксированного "PIPELINE"
- ✅ При 500 (UniqueViolation вместо 409) — логируем тело ответа и пробуем следующий attempt с другим code

### 3. pipelines/base.py — `run_step` (диагностика 500)
- ✅ При failed в error добавляется тело ответа (первые 200 символов): `| body: {...}`
- Теперь видно реальную причину 500, не только код

### 4. api_coverage_test.py — Gateway prepare diagnostics
- ✅ При неудачных prepare-шагах для Gateway выводится URL, тело запроса и последний ответ
