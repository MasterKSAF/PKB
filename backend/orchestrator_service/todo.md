# Todo: комплексные тесты — State Machine, Consistency, Saga, Boundary

## Статус: ✅ ВЫПОЛНЕНО

### 1. State Machine Violations — матрица [действие × stage]
  - `tests/orchestrator/test_drafts_state_machine.py`
  - 30 комбинаций + 10 terminal-статусов = **40 тестов**

### 2. Mock-real gap — draft_id=0, ключи id/draft_id
  - `tests/test_service_clients_registry.py::TestRegistryMockRealGap` — **3 теста**
  - `tests/orchestrator/test_drafts_consistency.py::TestMockRealGap` — **3 теста** (1 xfail)
  - Найден баг: `data.get("id") or data.get("draft_id")` — 0 is falsy

### 3. Data consistency — после approve
  - `tests/orchestrator/test_drafts_consistency.py::TestApproveConsistency` — **2 теста** (1 xfail)
  - Найден баг: approve_draft не вызывает `registry.update_draft_status(document_id=...)`

### 4. Boundary conditions
  - `tests/orchestrator/test_drafts_consistency.py::TestBoundaryConditions` — **6 тестов**
  - file_size boundary, metadata=null, title="", page_size=0

### 5. Saga compensation
  - `tests/unit/test_saga_compensation.py` — **8 тестов**
  - Компенсация registry_creation, stateless шаги, reverse order, on_step_failed → Saga

### 6. Idempotency
  - `tests/orchestrator/test_drafts_consistency.py::TestIdempotency` — **3 теста**
  - Двойной POST /drafts с одним Idempotency-Key → 200 + тот же draft_id (**РЕАЛИЗОВАНО**)
  - Разные ключи → разные draft_id
  - Двойной POST /preview → 409 PREVIEW_ALREADY_RUNNING

### Production-фикс
- **Idempotency-Key** для POST /drafts — добавлен in-memory кэш с TTL 1ч
- Файл: `app/api/v1/endpoints/drafts.py`

### Итог
- **+62 новых теста** (40 + 12 + 8 + 3)
- **+1 production фикс** (Idempotency-Key)
- **2 xfail** — документированные баги
- **466 passed, 2 xfailed**
- **Найдено 2 бага:**
  1. `data.get("id") or data.get("draft_id")` — 0 is falsy
  2. `approve_draft` не синхронизирует document_id с Registry
