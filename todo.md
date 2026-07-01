# Todo — Тестирование загрузки PDF и трассировка Registry → Orchestrator → RAG Builder

## Статус тестов на 01.07

### Выполнено
- [x] 1. test_dup_check для 2-020101-004.pdf — **дубль детектируется** (HTTP 409) ✅
- [x] 2. test_dup_check для gost_22786-77.pdf — **дубль детектируется** (HTTP 409) ✅
- [x] 3. test_universal_pdf_loader для 2-020101-004.pdf — pipeline **FAILED** на registry_creation
- [x] 4. test_universal_pdf_loader для gost_22786-77.pdf — pipeline **FAILED** на registry_creation
- [x] 5. Трассировка Registry → Orchestrator → RAG Builder — локализованы 2 корневые причины
- [x] 6. Актуализирована specificity.md (D1 удалена, R6 добавлен)

### Результаты трассировки

**Поток:** Registry (save + gen IDs) → orchestrator reads → RAG Builder

**Где обрывается:**
```
Upload → Preview → Approve → full_ocr → full_converter → 🔥 registry_creation (400) → ✗ rag_index
```

**Шаги до обрыва:**
- ✅ Upload → draft_id создан (Registry)
- ✅ Preview → завершён (OCR + converter)
- ✅ Approve → document_id создан (Registry) — через не-pipeline endpoint
- ✅ full_ocr → завершён
- ✅ full_converter → завершён, конвертер отдал document + metadata
- ❌ **registry_creation** — POST /registry/documents → 400 Bad Request

**2 корневые причины (обе активны):**

1. **`_find_doc_code()` не покрывает формат `2-020101-004`** — regex чертежей ждёт буквенный префикс
2. **`run_registry_step` перезатирает metadata** — `document_data["metadata"] = response_metadata` (без doc_code)

### Исправлено (01.07)
- [x] `_DRAWING_NUM_CODE_RE` — новый regex для цифровых номеров чертежей `2-020101-004`
- [x] `run_registry_step` — merge metadata вместо overwrite, + fallback doc_code из title при пустом

### Остаётся (R5 — предсуществующее)
- Registry. 0 sections — `create_pipeline_document` создаёт второй документ вместо обновления первого
- Документы дублируются: approve создаёт doc с хешом, pipeline создаёт второй с корректным doc_code
- Cекции доходят до RAG Builder через fallback в `_on_full_step_completed`

### Что дальше
- [ ] R5: `run_registry_step` или `create_pipeline_document` — обновлять существующий документ, а не создавать новый
