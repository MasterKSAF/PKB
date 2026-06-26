# API Coverage Report

**Generated:** 2026-06-26 10:04:47 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 8082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| [Registry Service](#registry) | 8084 | ✅ | ✅ | 50 | 50 | 0 | 0 | ✅ |
| [Converter-Validator Service](#converter-validator) | 8086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| [Parser Service](#parser) | 8087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| [Orchestrator Service](#orchestrator) | 8081 | ✅ | ✅ | 35 | 22 | <span style="color:red;font-weight:bold">3</span> | <span style="color:red;font-weight:bold">10</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Query Service](#query) | 8083 | ✅ | ✅ | 27 | 27 | 0 | 0 | ✅ |
| [RAG Builder Service](#rag-builder) | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| [RAG Search Service](#rag-search) | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| [Gateway Service](#gateway) | 8080 | ✅ | — | 77 | 49 | <span style="color:red;font-weight:bold">15</span> | <span style="color:red;font-weight:bold">13</span> | <span style="color:red;font-weight:bold">❌</span> |
| [TEI (Embeddings)](#tei) | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | **6/6** | **229** | **188** | <span style="color:red;font-weight:bold">18</span> | <span style="color:red;font-weight:bold">23</span> | <span style="color:red;font-weight:bold">❌</span> |

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
| 1 | POST | `/auth/token` | ✅ OK | 200 | 267ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 15ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 249ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 9ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 15ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 20ms |
</details>

<details>
<summary><b>ADMIN</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 259ms |
| 2 | POST | `/admin/roles` | ✅ OK | 409 | 18ms |
| 3 | GET | `/admin/users` | ✅ OK | 200 | 21ms |
| 4 | POST | `/admin/users` | ✅ OK | 201 | 246ms |
| 5 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 19ms |
| 6 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 40ms |
| 7 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 36ms |
| 8 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 33ms |
| 9 | GET | `/admin/roles` | ✅ OK | 200 | 15ms |
| 10 | POST | `/admin/roles` | ✅ OK | 201 | 23ms |
| 11 | GET | `/admin/audit` | ✅ OK | 200 | 21ms |
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
| 1 | POST | `/internal/auth/validate` | ✅ OK | 200 | 20ms |
</details>

---

### registry

**Registry Service** (port 8084)

**Ping:** ✅ Alive

> ⚠️ ⚠️ Registry не поддерживает trailing slash — эндпоинты /classifiers, /documents, /terminology без / в конце.

> ⚠️ ⚠️ PATCH /documents/{id}/status — internal API (только Orchestrator), checker ожидает 403.

> ⚠️ ⚠️ PATCH /drafts/{id}/metadata — internal API (только Orchestrator), checker ожидает 404.

**Total:** 50 | **Passed:** 50 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers` | ✅ OK | 201 | 34ms |
| 2 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 26ms |
| 3 | GET | `/registry/classifiers` | ✅ OK | 200 | 15ms |
| 4 | GET | `/registry/classifiers/tree` | ✅ OK | 200 | 13ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 50ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 17ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 16ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 31ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 7ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 15ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 31ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 16ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 14ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents` | ✅ OK | 201 | 61ms |
| 2 | GET | `/registry/documents` | ✅ OK | 200 | 26ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 14ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 34ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 403 | 8ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 16ms |
| 7 | GET | `/registry/documents/{doc_id}/succession` | ✅ OK | 200 | 19ms |
| 8 | GET | `/registry/documents/export` | ✅ OK | 200 | 15ms |
| 9 | POST | `/registry/documents/import` | ✅ OK | 422 | 6ms |
| 10 | GET | `/registry/search` | ✅ OK | 200 | 43ms |
| 11 | GET | `/registry/documents/{doc_id}/sections` | ✅ OK | 200 | 23ms |
| 12 | POST | `/registry/documents/check-uniqueness` | ✅ OK | 200 | 18ms |
| 13 | PATCH | `/registry/documents/{doc_id}` | ✅ OK | 200 | 33ms |
| 14 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 16ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology` | ✅ OK | 201 | 23ms |
| 2 | GET | `/registry/terminology` | ✅ OK | 200 | 17ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 9ms |
| 4 | GET | `/registry/terminology/normalize` | ✅ OK | 200 | 10ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 14ms |
| 6 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 17ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 422 | 11ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories` | ✅ OK | 200 | 12ms |
| 2 | POST | `/registry/categories` | ✅ OK | 201 | 24ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 13ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 17ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 17ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/drafts` | ✅ OK | 201 | 24ms |
| 2 | GET | `/registry/drafts` | ✅ OK | 200 | 14ms |
| 3 | GET | `/registry/drafts/{draft_id}` | ✅ OK | 200 | 8ms |
| 4 | GET | `/registry/drafts/{draft_id}/preview` | ✅ OK | 200 | 9ms |
| 5 | PATCH | `/registry/drafts/{draft_id}/status` | ✅ OK | 200 | 16ms |
| 6 | DELETE | `/registry/drafts/{draft_id}` | ✅ OK | 200 | 21ms |
| 7 | PATCH | `/registry/drafts/{draft_id}/metadata` | ✅ OK | 404 | 14ms |
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
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 21ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 14ms |
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
| 1 | GET | `/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>CONVERTER</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/converter/preview` | ✅ OK | 200 | 16ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 75ms |
</details>

<details>
<summary><b>VALIDATE</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/metadata` | ✅ OK | 200 | 10ms |
| 2 | POST | `/validate/document` | ✅ OK | 200 | 38ms |
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
| 1 | POST | `/parser/process` | ✅ OK | 202 | 22ms |
| 2 | POST | `/parser/process` | ✅ OK | 202 | 14ms |
| 3 | GET | `/parser/process/{task_id}/status` | ✅ OK | 200 | 18ms |
| 4 | GET | `/parser/process/{task_id}/result` | ✅ OK | 409 | 17ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 35ms |
</details>

---

### orchestrator

**Orchestrator Service** (port 8081)

**Ping:** ✅ Alive

**Total:** 35 | **Passed:** 22 | **Failed:** <span style="color:red;font-weight:bold">3</span> | **Skipped:** <span style="color:red;font-weight:bold">10</span>

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 252ms |
</details>

<details>
<summary><b>DRAFTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ❌ Error: HTTP 500 | 500 | 73ms |
| 2 | POST | `/drafts/` | ❌ Error: HTTP 500 | 500 | 88ms |
| 3 | GET | `/drafts/` | ✅ OK | 405 | 2ms |
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
| 1 | GET | `/monitor/metrics` | ✅ OK | 404 | 2ms |
</details>

<details>
<summary><b>TASKS</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/` | ✅ OK | 200 | 31ms |
| 2 | GET | `/tasks/{task_id}/status` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 3 | GET | `/tasks/{task_id}/steps` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | GET | `/tasks/stats` | ✅ OK | 200 | 22ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/` | ✅ OK | 404 | 3ms |
| 2 | GET | `/documents/queue` | ❌ Error: HTTP 200 | 200 | 16ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 404 | 5ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 404 | 2ms |
| 5 | GET | `/documents/{doc_id}/status` | ✅ OK | 404 | 3ms |
| 6 | GET | `/documents/{doc_id}/file` | ✅ OK | 404 | 4ms |
| 7 | GET | `/documents/{doc_id}/versions` | ✅ OK | 404 | 3ms |
| 8 | POST | `/documents/{doc_id}/versions` | ✅ OK | 404 | 3ms |
| 9 | GET | `/documents/{doc_id}/history` | ✅ OK | 404 | 2ms |
| 10 | POST | `/documents/{doc_id}/reprocess` | ✅ OK | 202 | 769ms |
| 11 | GET | `/documents/{doc_id}/tasks` | ✅ OK | 200 | 149ms |
| 12 | GET | `/documents/{doc_id}/errors` | ✅ OK | 404 | 3ms |
| 13 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 404 | 3ms |
</details>

<details>
<summary><b>PAGES</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/{doc_id}/pages` | ✅ OK | 404 | 3ms |
| 2 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 404 | 2ms |
| 3 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 404 | 2ms |
| 4 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 404 | 5ms |
</details>

---

### query

**Query Service** (port 8083)

**Ping:** ✅ Alive

> ⚠️ ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

**Total:** 27 | **Passed:** 27 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>CHAT</b> (23 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/projects` | ✅ OK | 201 | 18ms |
| 2 | POST | `/chat/sessions` | ✅ OK | 201 | 21ms |
| 3 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 30ms |
| 4 | POST | `/chat/projects` | ✅ OK | 201 | 10ms |
| 5 | GET | `/chat/projects` | ✅ OK | 200 | 18ms |
| 6 | GET | `/chat/projects/{project_id}` | ✅ OK | 200 | 12ms |
| 7 | PUT | `/chat/projects/{project_id}` | ✅ OK | 200 | 17ms |
| 8 | POST | `/chat/sessions` | ✅ OK | 201 | 21ms |
| 9 | GET | `/chat/sessions` | ✅ OK | 200 | 20ms |
| 10 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 12ms |
| 11 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 200 | 18ms |
| 12 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 46ms |
| 13 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 200 | 25ms |
| 14 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 13ms |
| 15 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 200 | 61ms |
| 16 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 17ms |
| 17 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 200 | 11ms |
| 18 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 200 | 67ms |
| 19 | POST | `/chat/feedback` | ✅ OK | 200 | 19ms |
| 20 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 200 | 30ms |
| 21 | GET | `/chat/history` | ✅ OK | 200 | 55ms |
| 22 | GET | `/chat/history/export` | ✅ OK | 200 | 5ms |
| 23 | DELETE | `/chat/projects/{project_id}` | ✅ OK | 204 | 22ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 38ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 12ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 15ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 8ms |
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
| 1 | POST | `/auth/token` | ✅ OK | 200 | 335ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 36ms |
</details>

<details>
<summary><b>RAG</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ✅ OK | 202 | 43ms |
| 2 | POST | `/rag/build` | ✅ OK | 202 | 15ms |
| 3 | DELETE | `/rag/build/{doc_id}` | ✅ OK | 200 | 12ms |
| 4 | GET | `/rag/build/{doc_id}/status` | ✅ OK | 200 | 10ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 7ms |
</details>

---

### rag-search

**RAG Search Service** (port 8091)

**Ping:** ✅ Alive

**Total:** 2 | **Passed:** 2 | **Failed:** 0 | **Skipped:** 0

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
| 1 | POST | `/rag/search` | ✅ OK | 200 | 722ms |
</details>

---

### gateway

**Gateway Service** (port 8080)

**Ping:** ✅ Alive

**Total:** 77 | **Passed:** 49 | **Failed:** <span style="color:red;font-weight:bold">15</span> | **Skipped:** <span style="color:red;font-weight:bold">13</span>

<details>
<summary><b>AUTH</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ❌ Error: HTTP 401 | 401 | 302ms |
| 2 | POST | `/auth/token` | ❌ Error: HTTP 401 | 401 | 236ms |
| 3 | GET | `/auth/me` | ❌ Error: HTTP 401 | 401 | 9ms |
| 4 | POST | `/auth/refresh` | ⏭️ Skipped: Не все переменные контекста доступны для тела запроса | 0 | 0ms |
| 5 | POST | `/auth/revoke` | ⏭️ Skipped: Не все переменные контекста доступны для тела запроса | 0 | 0ms |
</details>

<details>
<summary><b>ADMIN</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ❌ Error: HTTP 401 | 401 | 4ms |
| 2 | GET | `/admin/users` | ❌ Error: HTTP 401 | 401 | 7ms |
| 3 | POST | `/admin/users` | ❌ Error: HTTP 401 | 401 | 4ms |
| 4 | GET | `/admin/users/{user_id}` | ⏭️ Skipped: Нет в контексте: user_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | PATCH | `/admin/users/{user_id}` | ⏭️ Skipped: Нет в контексте: user_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | DELETE | `/admin/users/{user_id}` | ⏭️ Skipped: Нет в контексте: user_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | GET | `/admin/roles` | ❌ Error: HTTP 401 | 401 | 4ms |
| 8 | POST | `/admin/roles` | ❌ Error: HTTP 401 | 401 | 3ms |
| 9 | GET | `/admin/audit` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>CHAT</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/projects` | ✅ OK | 201 | 18ms |
| 2 | POST | `/chat/sessions` | ✅ OK | 201 | 16ms |
| 3 | POST | `/chat/sessions` | ✅ OK | 201 | 17ms |
| 4 | GET | `/chat/sessions` | ✅ OK | 200 | 16ms |
| 5 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 10ms |
| 6 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 28ms |
| 7 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 21ms |
| 8 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 22ms |
| 9 | GET | `/chat/history` | ✅ OK | 200 | 30ms |
| 10 | GET | `/chat/history/export` | ✅ OK | 200 | 15ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers/` | ✅ OK | 201 | 32ms |
| 2 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 14ms |
| 3 | GET | `/registry/classifiers/` | ✅ OK | 200 | 11ms |
| 4 | POST | `/registry/classifiers/` | ✅ OK | 201 | 17ms |
| 5 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 11ms |
| 6 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 17ms |
| 7 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 22ms |
| 8 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 20ms |
| 9 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 25ms |
| 10 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 10ms |
| 11 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 25ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 29ms |
| 13 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 25ms |
| 14 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 17ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories/` | ✅ OK | 200 | 12ms |
| 2 | POST | `/registry/categories/` | ✅ OK | 201 | 27ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 17ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 19ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 18ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/terminology/` | ✅ OK | 200 | 21ms |
| 2 | POST | `/registry/terminology/` | ❌ Error: HTTP 422 | 422 | 16ms |
| 3 | GET | `/registry/terminology/{term_id}` | ⏭️ Skipped: Нет в контексте: term_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | PUT | `/registry/terminology/{term_id}` | ⏭️ Skipped: Нет в контексте: term_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | DELETE | `/registry/terminology/{term_id}` | ⏭️ Skipped: Нет в контексте: term_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 12ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 422 | 13ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/documents/` | ✅ OK | 200 | 22ms |
| 2 | POST | `/registry/documents/` | ✅ OK | 201 | 23ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 13ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 28ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ❌ Error: HTTP 403 | 403 | 18ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 13ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 15ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 24ms |
| 9 | GET | `/registry/documents/export` | ✅ OK | 200 | 16ms |
| 10 | POST | `/registry/documents/import` | ✅ OK | 422 | 9ms |
| 11 | GET | `/documents/` | ❌ Error: Поле 'items' обязательно, но не найдено в ответе | 200 | 17ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ✅ OK | 200 | 14ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 25ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 15ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ❌ Error: HTTP 422 | 422 | 109ms |
| 2 | GET | `/drafts/` | ✅ OK | 200 | 16ms |
| 3 | GET | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | DELETE | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | PATCH | `/drafts/{draft_id}/decide` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | POST | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | GET | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>FILES</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/files/1` | ❌ Error: HTTP 410 | 410 | 6ms |
</details>

<details>
<summary><b>TEXT</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 10ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ❌ Error: HTTP 404 | 404 | 9ms |
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
| 1 | GET | `/` | ✅ OK | 200 | 2ms |
</details>

<details>
<summary><b>EMBED</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/embed` | ✅ OK | 200 | 12ms |
</details>

---

## 🔗 Context Variables

_No context variables extracted._

## 📖 Legend

- **✅ Passed** — 2xx/3xx, либо 4xx/5xx с валидным JSON (эндпоинт существует)

- **❌ Failed** — 4xx/5xx без JSON, ошибка подключения, или все не-health эндпоинты вернули 404 (сервис не существует)

- **⏭️ Skipped** — эндпоинт пропущен (сервис не отвечает, нет ID в контексте)

- **Ping** — проверка health-эндпоинта на порту сервиса

- **Mode** — 🔬 Real (Docker)

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

_Report generated by `api_coverage_test.py` at 2026-06-26 10:04:47 UTC_
