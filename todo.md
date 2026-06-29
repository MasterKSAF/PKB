# Fix: обработка документов — завершено ✅

## Проблемы и исправления

### 1. ✅ Mock fallback при ConnectError
**Файл:** `backend/orchestrator_service/app/services/base_client.py`
- Убрал `return mock_response or {}` при ConnectError и CircuitBreakerError — теперь пробрасывает исключение
- Добавил ConnectError в список retryable ошибок (было исключено)
- После исчерпания retry — Celery-задача получает исключение и корректно обрабатывает (retry задачи через `on_step_failed`)

### 2. ✅ Embedding dimension mismatch
**Файл:** `backend/rag_builder_service/src/rag_builder/embeddings/service.py`
- Rag-builder теперь передаёт `dimensions=self.dim` в API запрос (как rag-search уже делал)
- Раньше dimensions не передавался → модель возвращала 4096, а сервис обрезал до 2048
- Теперь оба сервиса запрашивают 2048-мерные векторы напрямую

### 3. ✅ Registry 409 Conflict и статус документа
**Файлы:** 
- `backend/orchestrator_service/app/services/registry_client.py` — добавлен заголовок `X-Service-ID: orchestrator`
- `backend/orchestrator_service/app/core/pipeline/orchestrator.py` — после rag_index обновляется статус документа (`uploaded → validating`), а не статус черновика

### Результат E2E теста
- Pipeline: ✅ completed
- Search: ✅ 150 total_found, контент найден
- Registry: ✅ статус обновлён до "validating"

### Известное
- Тест `'ГОСТ 10054' NOT found` — ложное срабатывание: в тексте `ГОСТ\n10054-82` с переносом строки, ожидание `ГОСТ 10054` с пробелом (не зависит от кода)
