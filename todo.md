# План: починить full_ocr pipeline

## Итог

### Сделано
1. [x] **pipeline_formation.py**: retry-логика — _notify_step_failed только при `self.request.retries >= self.max_retries`
2. [x] **steps.py (parser)**: ParseStep — обрезание PDF до `max_pages` перед парсингом, с корректным `preview_not_supported`
3. [x] **docker-compose.yml**: --reload для uvicorn orchestrator + parser, develop.watch
4. [x] Тесты: актуализированы под новую логику ParseStep (удалён TruncatePdfStep)

### Проверено
- Upload → Preview → Approve → full pipeline (full_ocr → full_converter → registry → rag_index) → COMPLETED ✅
- Preview не зависает на парсере (PDF обрезается до 3 страниц перед CLI)

### Осталось
- `pipeline_indexation.py` — та же проблема retry-логики (не касается full_ocr)
