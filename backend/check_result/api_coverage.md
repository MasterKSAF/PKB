# API Coverage Report

**Generated:** 2026-06-22 14:59:18 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

📋 **Logs:** [errors.md](errors.md)

---

## 📊 Summary

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 8082 | ✅ | — | 19 | 19 | 0 | 0 | ✅ |
| [Registry Service](#registry) | 8084 | ✅ | — | 50 | 33 | <span style="color:red;font-weight:bold">9</span> | <span style="color:red;font-weight:bold">8</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Converter-Validator Service](#converter-validator) | 8086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| [Parser Service](#parser) | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| [Orchestrator Service](#orchestrator) | 8081 | ✅ | — | 34 | 20 | <span style="color:red;font-weight:bold">4</span> | <span style="color:red;font-weight:bold">10</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Query Service](#query) | 8083 | ✅ | — | 26 | 24 | <span style="color:red;font-weight:bold">2</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [RAG Builder Service](#rag-builder) | 8090 | ✅ | — | 7 | 7 | 0 | 0 | ✅ |
| [RAG Search Service](#rag-search) | 8091 | ✅ | — | 2 | 1 | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [Gateway Service](#gateway) | 8080 | ✅ | — | 72 | 72 | 0 | 0 | ✅ |
| [TEI (Embeddings)](#tei) | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | **6/6** | **222** | **188** | <span style="color:red;font-weight:bold">16</span> | <span style="color:red;font-weight:bold">18</span> | <span style="color:red;font-weight:bold">❌</span> |

## 🔍 Details by Service

### auth

**Auth Service** (port 8082)

**Ping:** ✅ Alive

> ⚠️ PATCH /admin/users/{id}: docs ожидает audit_log_id, но сервис его не возвращает

**Total:** 19 | **Passed:** 19 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 237ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 8ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 240ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 7ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 12ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 16ms |
</details>

<details>
<summary><b>ADMIN</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 248ms |
| 2 | POST | `/admin/roles` | ✅ OK | 409 | 8ms |
| 3 | GET | `/admin/users` | ✅ OK | 200 | 13ms |
| 4 | POST | `/admin/users` | ✅ OK | 409 | 11ms |
| 5 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 12ms |
| 6 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 30ms |
| 7 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 30ms |
| 8 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 27ms |
| 9 | GET | `/admin/roles` | ✅ OK | 200 | 9ms |
| 10 | POST | `/admin/roles` | ✅ OK | 409 | 9ms |
| 11 | GET | `/admin/audit` | ✅ OK | 200 | 8ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 2ms |
</details>

<details>
<summary><b>INTERNAL</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/internal/auth/validate` | ✅ OK | 200 | 6ms |
</details>

---

### registry

**Registry Service** (port 8084)

**Ping:** ✅ Alive

> ⚠️ ⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.

**Total:** 50 | **Passed:** 33 | **Failed:** <span style="color:red;font-weight:bold">9</span> | **Skipped:** <span style="color:red;font-weight:bold">8</span>

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers/` | ✅ OK | 201 | 11ms |
| 2 | GET | `/registry/classifiers/pending/` | ✅ OK | 200 | 21ms |
| 3 | GET | `/registry/classifiers/` | ✅ OK | 200 | 8ms |
| 4 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 8ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 6ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 14ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 15ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 15ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 6ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 24ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 22ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 14ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 13ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 31ms |
| 2 | GET | `/registry/documents/` | ✅ OK | 200 | 7ms |
| 3 | GET | `/registry/documents/{doc_id}` | ❌ Error: Поле 'data.current_version_id' обязательно, но не найдено в ответе | 200 | 7ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 21ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 200 | 14ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 12ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 7ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 14ms |
| 9 | GET | `/registry/documents/export` | ✅ OK | 200 | 9ms |
| 10 | POST | `/registry/documents/import` | ✅ OK | 422 | 8ms |
| 11 | GET | `/registry/documents/search/` | ❌ Error: HTTP 404 | 404 | 6ms |
| 12 | GET | `/registry/documents/{doc_id}/sections/` | ❌ Error: HTTP 404 | 404 | 8ms |
| 13 | POST | `/registry/documents/check-uniqueness/` | ✅ OK | 200 | 8ms |
| 14 | PATCH | `/registry/documents/{doc_id}/` | ❌ Error: HTTP 404 | 404 | 11ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology/` | ✅ OK | 201 | 12ms |
| 2 | GET | `/registry/terminology/` | ✅ OK | 200 | 7ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 7ms |
| 4 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 9ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 16ms |
| 6 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 12ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 422 | 9ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories/` | ❌ Error: HTTP 404 | 404 | 1ms |
| 2 | POST | `/registry/categories/` | ❌ Error: HTTP 404 | 404 | 1ms |
| 3 | GET | `/registry/categories/{category_id}` | ⏭️ Skipped: Нет в контексте: category_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | PUT | `/registry/categories/{category_id}` | ⏭️ Skipped: Нет в контексте: category_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ⏭️ Skipped: Нет в контексте: category_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/drafts/` | ❌ Error: HTTP 404 | 404 | 1ms |
| 2 | GET | `/registry/drafts/` | ❌ Error: HTTP 404 | 404 | 2ms |
| 3 | GET | `/registry/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | GET | `/registry/drafts/{draft_id}/preview/` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | PATCH | `/registry/drafts/{draft_id}/status` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | DELETE | `/registry/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | PATCH | `/registry/drafts/{draft_id}/metadata` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ❌ Error: HTTP 404 | 404 | 3ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 15ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 8ms |
</details>

---

### converter-validator

**Converter-Validator Service** (port 8086)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 5 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 1ms |
</details>

<details>
<summary><b>CONVERTER</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/converter/preview` | ✅ OK | 200 | 1ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 35ms |
</details>

<details>
<summary><b>VALIDATE</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/metadata` | ✅ OK | 200 | 1ms |
| 2 | POST | `/validate/document` | ✅ OK | 200 | 39ms |
</details>

---

### parser

**Parser Service** (port 8087)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 5 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>PARSER</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/parser/process` | ✅ OK | 202 | 40ms |
| 2 | POST | `/parser/process` | ✅ OK | 202 | 3ms |
| 3 | GET | `/parser/process/{task_id}/status` | ✅ OK | 200 | 6ms |
| 4 | GET | `/parser/process/{task_id}/result` | ✅ OK | 409 | 2ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
</details>

---

### orchestrator

**Orchestrator Service** (port 8081)

**Ping:** ✅ Alive

**Total:** 34 | **Passed:** 20 | **Failed:** <span style="color:red;font-weight:bold">4</span> | **Skipped:** <span style="color:red;font-weight:bold">10</span>

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 314ms |
</details>

<details>
<summary><b>DRAFTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ❌ Error: HTTP 500 | 500 | 117ms |
| 2 | POST | `/drafts/` | ❌ Error: HTTP 500 | 500 | 164ms |
| 3 | GET | `/drafts/` | ✅ OK | 200 | 86ms |
| 4 | GET | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | GET | `/drafts/{draft_id}/tasks` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | DELETE | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | PATCH | `/drafts/{draft_id}/decide` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 8 | PATCH | `/drafts/{draft_id}/metadata` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 9 | GET | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 10 | POST | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 11 | GET | `/drafts/{draft_id}/preview/status` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/system/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ❌ Error: HTTP 404 | 404 | 2ms |
</details>

<details>
<summary><b>TASKS</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/` | ✅ OK | 200 | 61ms |
| 2 | GET | `/tasks/{task_id}/status` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 3 | GET | `/tasks/{task_id}/steps` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | GET | `/tasks/stats` | ✅ OK | 200 | 12ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (12 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/` | ✅ OK | 200 | 4ms |
| 2 | GET | `/documents/queue` | ✅ OK | 200 | 3ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 6ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 200 | 4ms |
| 5 | GET | `/documents/{doc_id}/status` | ✅ OK | 200 | 3ms |
| 6 | GET | `/documents/{doc_id}/file` | ✅ OK | 200 | 2ms |
| 7 | GET | `/documents/{doc_id}/versions` | ✅ OK | 200 | 50ms |
| 8 | POST | `/documents/{doc_id}/versions` | ✅ OK; ⚠️ Поле 'version_id' ожидалось int, получен str = fb4dd06a-3a58-45bc-8ed5-f3248d6feaad | 202 | 5ms |
| 9 | GET | `/documents/{doc_id}/history` | ✅ OK | 200 | 2ms |
| 10 | POST | `/documents/{doc_id}/reprocess` | ❌ Error: HTTP 500 | 500 | 23ms |
| 11 | GET | `/documents/{doc_id}/errors` | ✅ OK | 200 | 4ms |
| 12 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 200 | 2ms |
</details>

<details>
<summary><b>PAGES</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/{doc_id}/pages` | ✅ OK | 200 | 2ms |
| 2 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 200 | 2ms |
| 3 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 200 | 2ms |
| 4 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 200 | 3ms |
</details>

---

### query

**Query Service** (port 8083)

**Ping:** ✅ Alive

> ⚠️ ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

**Total:** 26 | **Passed:** 24 | **Failed:** <span style="color:red;font-weight:bold">2</span> | **Skipped:** 0

<details>
<summary><b>CHAT</b> (22 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ✅ OK | 201 | 59ms |
| 2 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 17ms |
| 3 | POST | `/chat/projects` | ❌ Error: HTTP 500 | 500 | 83ms |
| 4 | GET | `/chat/projects` | ✅ OK | 200 | 8ms |
| 5 | GET | `/chat/projects/{project_id}` | ✅ OK | 200 | 5ms |
| 6 | PUT | `/chat/projects/{project_id}` | ✅ OK | 200 | 13ms |
| 7 | DELETE | `/chat/projects/{project_id}` | ✅ OK | 204 | 53ms |
| 8 | POST | `/chat/sessions` | ❌ Error: HTTP 500 | 500 | 36ms |
| 9 | GET | `/chat/sessions` | ✅ OK | 200 | 10ms |
| 10 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 51ms |
| 11 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 200 | 11ms |
| 12 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 15ms |
| 13 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 200 | 10ms |
| 14 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 10ms |
| 15 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 200 | 12ms |
| 16 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 9ms |
| 17 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 200 | 33ms |
| 18 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 200 | 11ms |
| 19 | POST | `/chat/feedback` | ✅ OK | 200 | 11ms |
| 20 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 200 | 16ms |
| 21 | GET | `/chat/history` | ✅ OK | 200 | 11ms |
| 22 | GET | `/chat/history/export` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 5ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 43ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 3ms |
</details>

---

### rag-builder

**RAG Builder Service** (port 8090)

**Ping:** ✅ Alive

**Total:** 7 | **Passed:** 7 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 500ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 19ms |
</details>

<details>
<summary><b>RAG</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ✅ OK | 201 | 48ms |
| 2 | POST | `/rag/build` | ✅ OK | 201 | 16ms |
| 3 | DELETE | `/rag/build/{doc_id}` | ✅ OK | 200 | 12ms |
| 4 | GET | `/rag/build/{doc_id}/status` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 5ms |
</details>

---

### rag-search

**RAG Search Service** (port 8091)

**Ping:** ✅ Alive

**Total:** 2 | **Passed:** 1 | **Failed:** <span style="color:red;font-weight:bold">1</span> | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ❌ Error: HTTP 500 | 500 | 3383ms |
</details>

---

### gateway

**Gateway Service** (port 8080)

**Ping:** ✅ Alive

**Total:** 72 | **Passed:** 72 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 4ms |
| 2 | POST | `/auth/token` | ✅ OK | 200 | 6ms |
| 3 | GET | `/auth/me` | ✅ OK | 200 | 4ms |
| 4 | POST | `/auth/refresh` | ✅ OK | 200 | 4ms |
| 5 | POST | `/auth/revoke` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>ADMIN</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/admin/users` | ✅ OK | 200 | 5ms |
| 2 | POST | `/admin/users` | ✅ OK | 409 | 4ms |
| 3 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 6ms |
| 4 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 5ms |
| 5 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 3ms |
| 6 | GET | `/admin/roles` | ✅ OK | 200 | 4ms |
| 7 | POST | `/admin/roles` | ✅ OK | 201 | 8ms |
| 8 | GET | `/admin/audit` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (12 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/classifiers/` | ✅ OK | 200 | 4ms |
| 2 | POST | `/registry/classifiers/` | ✅ OK | 201 | 6ms |
| 3 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 4ms |
| 4 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 4ms |
| 5 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 6ms |
| 6 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 5ms |
| 7 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 6ms |
| 8 | POST | `/registry/classifiers/import` | ✅ OK | 400 | 5ms |
| 9 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 3ms |
| 10 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 4ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 6ms |
| 12 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories/` | ✅ OK | 200 | 6ms |
| 2 | POST | `/registry/categories/` | ✅ OK | 201 | 5ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 3ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 5ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/terminology/` | ✅ OK | 200 | 5ms |
| 2 | POST | `/registry/terminology/` | ✅ OK | 201 | 6ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 3ms |
| 4 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 4ms |
| 5 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 4ms |
| 6 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 6ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 400 | 6ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/documents/` | ✅ OK | 200 | 6ms |
| 2 | POST | `/registry/documents/` | ✅ OK | 201 | 4ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 3ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 6ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 200 | 6ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 4ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 5ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 4ms |
| 9 | GET | `/registry/documents/export` | ✅ OK | 200 | 3ms |
| 10 | POST | `/registry/documents/import` | ✅ OK | 400 | 6ms |
| 11 | GET | `/documents/` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 4ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ✅ OK | 202 | 6ms |
| 2 | GET | `/drafts/` | ✅ OK | 200 | 4ms |
| 3 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 3ms |
| 4 | DELETE | `/drafts/{draft_id}` | ✅ OK | 200 | 5ms |
| 5 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 409 | 7ms |
| 6 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 409 | 3ms |
| 7 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>FILES</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/files/{file_id}` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>CHAT</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ✅ OK | 201 | 5ms |
| 2 | GET | `/chat/sessions` | ✅ OK | 200 | 4ms |
| 3 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 5ms |
| 4 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 7ms |
| 5 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 4ms |
| 6 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 4ms |
| 7 | GET | `/chat/history` | ✅ OK | 200 | 3ms |
| 8 | GET | `/chat/history/export` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>TEXT</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 6ms |
</details>

---

### tei

**TEI (Embeddings)** (port 18092)

**Ping:** ✅ Alive

**Total:** 2 | **Passed:** 2 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/` | ✅ OK | 200 | 1ms |
</details>

<details>
<summary><b>EMBED</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/embed` | ✅ OK | 200 | 13ms |
</details>

---

## 🔗 Context Variables

_No context variables extracted._

## 📖 Legend

- **✅ Passed** — 2xx/3xx, либо 4xx/5xx с валидным JSON (эндпоинт существует)

- **❌ Failed** — 4xx/5xx без JSON, ошибка подключения, или все не-health эндпоинты вернули 404 (сервис не существует)

- **⏭️ Skipped** — эндпоинт пропущен (сервис не отвечает, нет ID в контексте)

- **Ping** — проверка health-эндпоинта на порту сервиса

- **Mode** — Real (Docker): проверяются только запущенные в Docker сервисы

- ⏸️ **Analyse Service** — временно не тестируется (нет контейнера)


## 🔗 Dependency Map

| Сервис | Зависит от |
|--------|-----------|
| `converter_validator` | registry |
| `gateway` | auth, orchestrator, query, registry |
| `orchestrator` | auth, registry, query, converter_validator, parser, ocr, rag_search |
| `query` | registry |
| `rag_builder` | registry |
| `rag_search` | registry |

---

_Report generated by `api_coverage_test.py` at 2026-06-22 14:59:18 UTC_
