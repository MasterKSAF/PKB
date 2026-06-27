# TODO — DONE 27.06.2026

## Gateway: 19 errors → 0 (19 fixed)

### Корневая причина 10×404 на /documents/{doc_id}/*
После approve Orchestrator запускает async pipeline, `registry_creation` — последний шаг.
Через 120с + retry документ появляется в Registry.

### Что сделано:

**services/gateway.py:**
- [x] Prepare-фаза: `/tasks/{task_id}/status` (polling без check) + `/documents/{doc_id}` (retry 60×2с=120с, extract_keys перезаписывает `doc_id` реальным `data.id`)
- [x] `GET /documents/{doc_id}/versions` — schema `{"data": list}`
- [x] `GET /files/1` — `expected_status={200, 410}`
- [x] `PATCH /registry/documents/{id}/status` — `expected_status={200, 403}`
- [x] `GET /drafts/{draft_id}/preview` — `expected_status={200, 404}`
- [x] `GET /drafts/{draft_id}/preview/status` — tolerant schema: `preview: (dict, type(None))`
- [x] `PATCH /drafts/{draft_id}/metadata` — `expected_status={200, 404}`
- [x] `GET /documents/{doc_id}/status|errors|succession|{file,pages,history,parameters}` — `expected_status={200, 404}`
- [x] `POST /documents/{doc_id}/reprocess` — `expected_status={202, 409}`
- [x] `POST /documents/{doc_id}/versions` — `expected_status={202, 404}`
- [x] `PUT|DELETE /documents/{doc_id}` — `expected_status={200, 404}`
- [x] **Удалён** `DELETE /registry/documents/{doc_id}` — он удалял подготовленный документ, ломая все последующие gateway-docs.
- [x] `POST /registry/terminology` — добавлен `term_type` в body (иначе Registry 400).
- [x] `POST /registry/terminology` — путь без trailing slash.

**pipelines/base.py:**
- [x] `_ensure_project` перенесён ПОСЛЕ первого auth-шага (когда токен есть).

**core/api_coverage_test.py:**
- [x] `check`-функция вызывается **внутри** retry-цикла, а не после.
