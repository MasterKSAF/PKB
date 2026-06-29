# Fix dispatching full_ocr / OCR fallback in orchestrator

## Analysis findings

### Bugs identified:

1. **`_run_ocr_fallback` (line 349):** New OCR preview step is created with `status="pending"` but never started via `start_task_step`. When OCR task completes, `on_step_completed` finds a "pending" step and completes it directly (skipping "running" state). This breaks step lifecycle.

2. **`approve_draft` else branch (line 1197):** When `need_full_processing=False` (full preview mode or `full_completed=True`), the `full_converter` step is started but `run_converter_full_step.delay()` is NEVER called. The step stays `running` forever — no Celery task is dispatched to process it.

3. **`_run_ocr_fallback` missing import guard:** After creating the step, `.delay()` is called but if the local import or dispatch fails, there's no error handling.

### Plan:

- [x] Fix 1: `_run_ocr_fallback` — start the new OCR step after creation
- [x] Fix 2: `approve_draft` else branch — dispatch `run_converter_full_step.delay()` when skipping Parser/OCR
- [x] Review all dispatch sites for consistency
- [x] Run tests
