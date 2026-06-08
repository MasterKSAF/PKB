# API Coverage Report

**Generated:** 2026-06-08 05:54:33 UTC

**Mode:** 🔬 Real (полный)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Ping |
|---------|:----:|:---------:|:---------:|:---------:|:----------:|:----:|
| Analyse Service | 8089 | 6 | 0 | 0 | 6 | ❌ |
| Auth Service | 8082 | 16 | 15 | 1 | 0 | ✅ |
| Converter-Validator Service | 8086 | 4 | 4 | 0 | 0 | ✅ |
| Integration Service | 8085 | 7 | 7 | 0 | 0 | ✅ |
| OCR Service | 8088 | 5 | 0 | 0 | 5 | ❌ |
| Orchestrator Service | 8000 | 23 | 23 | 0 | 0 | ✅ |
| Parser Service | 8087 | 5 | 5 | 0 | 0 | ✅ |
| Query Service | 8083 | 18 | 17 | 1 | 0 | ✅ |
| RAG Builder Service | 8090 | 4 | 4 | 0 | 0 | ✅ |
| RAG Search Service | 8091 | 2 | 1 | 1 | 0 | ✅ |
| Registry Service | 8084 | 32 | 0 | 0 | 32 | ❌ |
| **Total** | | **122** | **76** | **3** | **43** | **8/11** |

## 🔍 Details by Service

### Analyse Service (port 8089)

**Ping:** ❌ Unreachable

**Total:** 6 | **Passed:** 0 | **Failed:** 0 | **Skipped:** 6

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

<details>
<summary><b>ANALYSE</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/analyse/compare` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 2 | GET | `/analyse/compare/{comparison_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 3 | POST | `/analyse/compare/batch` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 4 | POST | `/analyse/calculate` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 5 | POST | `/analyse/recommend` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

---

### Auth Service (port 8082)

**Ping:** ✅ Alive

**Total:** 16 | **Passed:** 15 | **Failed:** 1 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 404 | 1ms |
| 2 | GET | `/system/health` | ✅ OK | 404 | 1ms |
</details>

<details>
<summary><b>AUTH</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 225ms |
| 2 | GET | `/auth/me` | ❌ Error: Поле 'email' обязательно, но не найдено в ответе | 200 | 3ms |
| 3 | POST | `/auth/refresh` | ✅ OK | 200 | 3ms |
| 4 | POST | `/auth/revoke` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>ADMIN</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/admin/users` | ✅ OK | 403 | 12ms |
| 2 | POST | `/admin/users` | ✅ OK | 403 | 3ms |
| 3 | GET | `/admin/users/{user_id}` | ✅ OK | 403 | 3ms |
| 4 | PUT | `/admin/users/{user_id}` | ✅ OK | 403 | 3ms |
| 5 | PATCH | `/admin/users/{user_id}` | ✅ OK | 403 | 3ms |
| 6 | DELETE | `/admin/users/{user_id}` | ✅ OK | 403 | 2ms |
| 7 | GET | `/admin/roles` | ✅ OK | 403 | 2ms |
| 8 | POST | `/admin/roles` | ✅ OK | 403 | 4ms |
| 9 | GET | `/admin/audit` | ✅ OK | 403 | 6ms |
</details>

<details>
<summary><b>INTERNAL</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/internal/auth/validate` | ✅ OK | 200 | 6ms |
</details>

---

### Converter-Validator Service (port 8086)

**Ping:** ✅ Alive

**Total:** 4 | **Passed:** 4 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 404 | 2ms |
</details>

<details>
<summary><b>CONVERTER</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/converter/preview/metadata` | ✅ OK | 200 | 10ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 3415ms |
</details>

<details>
<summary><b>VALIDATE</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/document` | ✅ OK | 200 | 3330ms |
</details>

---

### Integration Service (port 8085)

**Ping:** ✅ Alive

**Total:** 7 | **Passed:** 7 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 404 | 1ms |
</details>

<details>
<summary><b>EXTERNAL</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/external/status` | ✅ OK | 200 | 11ms |
</details>

<details>
<summary><b>FILES</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/files/upload` | ✅ OK | 422 | 9ms |
| 2 | GET | `/files/{file_key}` | ✅ OK | 404 | 13ms |
| 3 | GET | `/files/{file_key}/info` | ✅ OK | 404 | 5ms |
| 4 | DELETE | `/files/{file_key}` | ✅ OK | 404 | 4ms |
</details>

<details>
<summary><b>MERIDIAN</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/meridian/export` | ✅ OK | 200 | 22ms |
</details>

---

### OCR Service (port 8088)

**Ping:** ❌ Unreachable

**Total:** 5 | **Passed:** 0 | **Failed:** 0 | **Skipped:** 5

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

<details>
<summary><b>OCR</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/ocr/process` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 2 | POST | `/ocr/preview` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 3 | GET | `/ocr/process/{task_id}/status` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 4 | GET | `/ocr/process/{task_id}/result` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

---

### Orchestrator Service (port 8000)

**Ping:** ✅ Alive

**Total:** 23 | **Passed:** 23 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>MONITOR</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/health` | ✅ OK | 404 | 2ms |
| 2 | GET | `/monitor/metrics` | ✅ OK | 200 | 12ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (18 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/documents` | ✅ OK | 307 | 4ms |
| 2 | GET | `/documents` | ✅ OK | 307 | 1ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 12ms |
| 4 | GET | `/documents/{doc_id}/status` | ✅ OK | 200 | 5ms |
| 5 | GET | `/documents/{doc_id}/file` | ✅ OK | 200 | 7ms |
| 6 | GET | `/documents/{doc_id}/history` | ✅ OK | 200 | 6ms |
| 7 | GET | `/documents/{doc_id}/errors` | ✅ OK | 200 | 5ms |
| 8 | GET | `/documents/{doc_id}/versions` | ✅ OK | 200 | 4ms |
| 9 | POST | `/documents/{doc_id}/versions` | ✅ OK | 422 | 4ms |
| 10 | POST | `/documents/{doc_id}/approve` | ✅ OK | 202 | 5ms |
| 11 | POST | `/documents/{doc_id}/reprocess` | ✅ OK | 202 | 18ms |
| 12 | DELETE | `/documents/{doc_id}` | ✅ OK | 200 | 4ms |
| 13 | GET | `/documents/queue` | ✅ OK | 200 | 3ms |
| 14 | GET | `/documents/{doc_id}/pages` | ✅ OK | 200 | 5ms |
| 15 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 422 | 7ms |
| 16 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 422 | 6ms |
| 17 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 422 | 5ms |
| 18 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>SEARCH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/documents/search` | ✅ OK | 200 | 12ms |
| 2 | GET | `/documents/search` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/system/health` | ✅ OK | 200 | 24ms |
</details>

---

### Parser Service (port 8087)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 5 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 404 | 3ms |
</details>

<details>
<summary><b>PARSER</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/parser/process` | ✅ OK | 422 | 11ms |
| 2 | POST | `/parser/preview` | ✅ OK | 422 | 9ms |
| 3 | GET | `/parser/process/{task_id}/status` | ✅ OK | 422 | 13ms |
| 4 | GET | `/parser/process/{task_id}/result` | ✅ OK | 422 | 11ms |
</details>

---

### Query Service (port 8083)

**Ping:** ✅ Alive

**Total:** 18 | **Passed:** 17 | **Failed:** 1 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 5ms |
| 2 | GET | `/system/health` | ✅ OK | 404 | 4ms |
</details>

<details>
<summary><b>CHAT</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ❌ Error: Поле 'session_id' ожидалось str, получен int = 1 | 201 | 43ms |
| 2 | GET | `/chat/sessions` | ✅ OK | 200 | 15ms |
| 3 | GET | `/chat/sessions/{session_id}` | ✅ OK | 422 | 7ms |
| 4 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 422 | 5ms |
| 5 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 422 | 4ms |
| 6 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 422 | 4ms |
| 7 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 422 | 3ms |
| 8 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 422 | 4ms |
| 9 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 422 | 5ms |
| 10 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 422 | 7ms |
| 11 | POST | `/chat/feedback` | ✅ OK | 422 | 4ms |
| 12 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 422 | 4ms |
| 13 | GET | `/chat/history` | ✅ OK | 200 | 11ms |
| 14 | GET | `/chat/history/export` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 10ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 4ms |
</details>

---

### RAG Builder Service (port 8090)

**Ping:** ✅ Alive

**Total:** 4 | **Passed:** 4 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 404 | 2ms |
</details>

<details>
<summary><b>RAG</b> (3 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ✅ OK | 422 | 15ms |
| 2 | DELETE | `/rag/build/{doc_id}` | ✅ OK | 422 | 8ms |
| 3 | GET | `/rag/build/{doc_id}/status` | ✅ OK | 422 | 6ms |
</details>

---

### RAG Search Service (port 8091)

**Ping:** ✅ Alive

**Total:** 2 | **Passed:** 1 | **Failed:** 1 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ❌ Error: HTTP 500 | 500 | 19ms |
</details>

---

### Registry Service (port 8084)

**Ping:** ❌ Unreachable

**Total:** 32 | **Passed:** 0 | **Failed:** 0 | **Skipped:** 32

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (12 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/classifiers` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 2 | GET | `/classifiers` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 3 | GET | `/classifiers/tree` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 4 | GET | `/classifiers/{classifier_code}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 5 | PUT | `/classifiers/{classifier_code}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 6 | PATCH | `/classifiers/{classifier_code}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 7 | DELETE | `/classifiers/{classifier_code}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 8 | POST | `/classifiers/import` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 9 | GET | `/classifiers/quarantine` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 10 | POST | `/classifiers/quarantine/{pending_id}/accept` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 11 | POST | `/classifiers/quarantine/{pending_id}/reject` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 12 | POST | `/classifiers/validate` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/terminology` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 2 | GET | `/terminology` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 3 | GET | `/terminology/{term_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 4 | GET | `/terminology/normalize` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 5 | PUT | `/terminology/{term_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 6 | DELETE | `/terminology/{term_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 7 | POST | `/terminology/import` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/documents` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 2 | GET | `/documents` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 3 | GET | `/documents/{doc_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 4 | PUT | `/documents/{doc_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 5 | PATCH | `/documents/{doc_id}/status` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 6 | GET | `/documents/{doc_id}/history` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 7 | GET | `/documents/{doc_id}/succession` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 8 | DELETE | `/documents/{doc_id}` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 9 | GET | `/documents/export` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 10 | POST | `/documents/import` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/stats` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
| 2 | GET | `/enums` | ⏭️ Skipped: Сервис не отвечает | 0 | 0ms |
</details>

---

## 🔗 Context Variables

| Variable | Value |
|----------|-------|
| `access_token` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTAwMiIsInR5cGUiOiJhY2Nlc3MiLCJleHAiOjE3ODA5MDE2NjR9.NGBZ_9QlO7uaQkPFk9BodL7ojCMZ5lipkyBU1yDq1oE` |
| `refresh_token` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTAwMiIsInR5cGUiOiJyZWZyZXNoIiwiZXhwIjoxNzgzNDkwMDY0LCJqdGkiOiJhMzdkYTlkNDAzZGU0MTg2OTVmZWRlNTI0YTM0MzBkZSJ9.hK1V453fOi-X0sGbiZoEWUE-IQGjSRQJzvxTtgOi3gE` |
| `session_id` | `1` |
## 📖 Legend

- **✅ Passed** — запрос выполнен, сервер вернул HTTP < 500

- **❌ Failed** — сервер вернул HTTP ≥ 500 или ошибка подключения

- **⏭️ Skipped** — эндпоинт пропущен (сервис не отвечает, нет ID в контексте)

- **Ping** — проверка health-эндпоинта на порту сервиса

- **Mode** — `real`: проверяются только сервисы этого режима


---

_Report generated by `api_coverage_test.py` at 2026-06-08 05:54:33 UTC_
