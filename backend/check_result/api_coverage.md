# API Coverage Report

**Generated:** 2026-06-23 14:03:13 UTC

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
| [Orchestrator Service](#orchestrator) | 8081 | ✅ | ✅ | 35 | 35 | 0 | 0 | ✅ |
| [Query Service](#query) | 8083 | ✅ | ✅ | 27 | 26 | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [RAG Builder Service](#rag-builder) | 8090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| [RAG Search Service](#rag-search) | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| [Gateway Service](#gateway) | 8080 | ✅ | — | 77 | 74 | 0 | <span style="color:red;font-weight:bold">3</span> | <span style="color:orange;font-weight:bold">⏭️</span> |
| [TEI (Embeddings)](#tei) | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | **6/6** | **229** | **225** | <span style="color:red;font-weight:bold">1</span> | <span style="color:red;font-weight:bold">3</span> | <span style="color:red;font-weight:bold">❌</span> |

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
| 1 | POST | `/auth/token` | ✅ OK | 200 | 248ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 7ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 240ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 8ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 15ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 17ms |
</details>

<details>
<summary><b>ADMIN</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 243ms |
| 2 | POST | `/admin/roles` | ✅ OK | 409 | 13ms |
| 3 | GET | `/admin/users` | ✅ OK | 200 | 19ms |
| 4 | POST | `/admin/users` | ✅ OK | 409 | 11ms |
| 5 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 10ms |
| 6 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 26ms |
| 7 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 30ms |
| 8 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 27ms |
| 9 | GET | `/admin/roles` | ✅ OK | 200 | 8ms |
| 10 | POST | `/admin/roles` | ✅ OK | 409 | 12ms |
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
| 1 | POST | `/internal/auth/validate` | ✅ OK | 200 | 7ms |
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
| 1 | POST | `/registry/classifiers` | ✅ OK | 201 | 13ms |
| 2 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 34ms |
| 3 | GET | `/registry/classifiers` | ✅ OK | 200 | 10ms |
| 4 | GET | `/registry/classifiers/tree` | ✅ OK | 200 | 5ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 8ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 11ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 10ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 15ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 4ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 69ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 15ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 16ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents` | ✅ OK | 201 | 34ms |
| 2 | GET | `/registry/documents` | ✅ OK | 200 | 15ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 11ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 42ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 403 | 11ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 13ms |
| 7 | GET | `/registry/documents/{doc_id}/succession` | ✅ OK | 200 | 21ms |
| 8 | GET | `/registry/documents/export` | ✅ OK | 200 | 22ms |
| 9 | POST | `/registry/documents/import` | ✅ OK | 422 | 6ms |
| 10 | GET | `/registry/search` | ✅ OK | 200 | 9ms |
| 11 | GET | `/registry/documents/{doc_id}/sections` | ✅ OK | 200 | 27ms |
| 12 | POST | `/registry/documents/check-uniqueness` | ✅ OK | 200 | 14ms |
| 13 | PATCH | `/registry/documents/{doc_id}` | ✅ OK | 200 | 38ms |
| 14 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 17ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology` | ✅ OK | 201 | 12ms |
| 2 | GET | `/registry/terminology` | ✅ OK | 200 | 6ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 9ms |
| 4 | GET | `/registry/terminology/normalize` | ✅ OK | 200 | 7ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 19ms |
| 6 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 13ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 422 | 6ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories` | ✅ OK | 200 | 11ms |
| 2 | POST | `/registry/categories` | ✅ OK | 201 | 18ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 9ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 19ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 14ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/drafts` | ✅ OK | 201 | 17ms |
| 2 | GET | `/registry/drafts` | ✅ OK | 200 | 14ms |
| 3 | GET | `/registry/drafts/{draft_id}` | ✅ OK | 200 | 13ms |
| 4 | GET | `/registry/drafts/{draft_id}/preview` | ✅ OK | 200 | 5ms |
| 5 | PATCH | `/registry/drafts/{draft_id}/status` | ✅ OK | 200 | 15ms |
| 6 | DELETE | `/registry/drafts/{draft_id}` | ✅ OK | 200 | 15ms |
| 7 | PATCH | `/registry/drafts/{draft_id}/metadata` | ✅ OK | 404 | 11ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ✅ OK | 200 | 8ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 17ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 10ms |
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
| 1 | GET | `/health` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>CONVERTER</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/converter/preview` | ✅ OK | 200 | 9ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 40ms |
</details>

<details>
<summary><b>VALIDATE</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/metadata` | ✅ OK | 200 | 2ms |
| 2 | POST | `/validate/document` | ✅ OK | 200 | 42ms |
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
| 1 | POST | `/parser/process` | ✅ OK | 202 | 45ms |
| 2 | POST | `/parser/process` | ✅ OK | 202 | 3ms |
| 3 | GET | `/parser/process/{task_id}/status` | ✅ OK | 200 | 4ms |
| 4 | GET | `/parser/process/{task_id}/result` | ✅ OK | 409 | 2ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 10ms |
</details>

---

### orchestrator

**Orchestrator Service** (port 8081)

**Ping:** ✅ Alive

**Total:** 35 | **Passed:** 35 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 336ms |
</details>

<details>
<summary><b>DRAFTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ✅ OK | 202 | 219ms |
| 2 | POST | `/drafts/` | ✅ OK | 202 | 269ms |
| 3 | GET | `/drafts/` | ✅ OK | 405 | 5ms |
| 4 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 91ms |
| 5 | GET | `/drafts/{draft_id}/tasks` | ✅ OK | 200 | 8ms |
| 6 | DELETE | `/drafts/{draft_id}` | ✅ OK | 204 | 98ms |
| 7 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 200 | 293ms |
| 8 | PATCH | `/drafts/{draft_id}/metadata` | ✅ OK | 404 | 96ms |
| 9 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 99ms |
| 10 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 109ms |
| 11 | GET | `/drafts/{draft_id}/preview/status` | ✅ OK | 200 | 92ms |
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
| 1 | GET | `/tasks/` | ✅ OK | 200 | 10ms |
| 2 | GET | `/tasks/{task_id}/status` | ✅ OK | 200 | 48ms |
| 3 | GET | `/tasks/{task_id}/steps` | ✅ OK | 200 | 14ms |
| 4 | GET | `/tasks/stats` | ✅ OK | 200 | 11ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/` | ✅ OK | 404 | 3ms |
| 2 | GET | `/documents/queue` | ✅ OK | 404 | 5ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 404 | 4ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 404 | 4ms |
| 5 | GET | `/documents/{doc_id}/status` | ✅ OK | 404 | 3ms |
| 6 | GET | `/documents/{doc_id}/file` | ✅ OK | 404 | 49ms |
| 7 | GET | `/documents/{doc_id}/versions` | ✅ OK | 404 | 4ms |
| 8 | POST | `/documents/{doc_id}/versions` | ✅ OK | 404 | 8ms |
| 9 | GET | `/documents/{doc_id}/history` | ✅ OK | 404 | 3ms |
| 10 | POST | `/documents/{doc_id}/reprocess` | ✅ OK | 409 | 6ms |
| 11 | GET | `/documents/{doc_id}/tasks` | ✅ OK | 200 | 5ms |
| 12 | GET | `/documents/{doc_id}/errors` | ✅ OK | 404 | 2ms |
| 13 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 404 | 4ms |
</details>

<details>
<summary><b>PAGES</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/{doc_id}/pages` | ✅ OK | 404 | 3ms |
| 2 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 404 | 3ms |
| 3 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 404 | 2ms |
| 4 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 404 | 2ms |
</details>

---

### query

**Query Service** (port 8083)

**Ping:** ✅ Alive

> ⚠️ ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

**Total:** 27 | **Passed:** 26 | **Failed:** <span style="color:red;font-weight:bold">1</span> | **Skipped:** 0

<details>
<summary><b>CHAT</b> (23 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/projects` | ✅ OK | 201 | 58ms |
| 2 | POST | `/chat/sessions` | ✅ OK | 201 | 14ms |
| 3 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 23ms |
| 4 | POST | `/chat/projects` | ❌ Error: HTTP 409 | 409 | 12ms |
| 5 | GET | `/chat/projects` | ✅ OK | 200 | 17ms |
| 6 | GET | `/chat/projects/{project_id}` | ✅ OK | 200 | 6ms |
| 7 | PUT | `/chat/projects/{project_id}` | ✅ OK | 200 | 13ms |
| 8 | POST | `/chat/sessions` | ✅ OK | 201 | 60ms |
| 9 | GET | `/chat/sessions` | ✅ OK | 200 | 104ms |
| 10 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 10ms |
| 11 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 200 | 12ms |
| 12 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 65ms |
| 13 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 200 | 11ms |
| 14 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 17ms |
| 15 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 200 | 11ms |
| 16 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 54ms |
| 17 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 200 | 6ms |
| 18 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 200 | 9ms |
| 19 | POST | `/chat/feedback` | ✅ OK | 200 | 14ms |
| 20 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 200 | 18ms |
| 21 | GET | `/chat/history` | ✅ OK | 200 | 56ms |
| 22 | GET | `/chat/history/export` | ✅ OK | 200 | 3ms |
| 23 | DELETE | `/chat/projects/{project_id}` | ✅ OK | 204 | 12ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 10ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 49ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 3ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 5ms |
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
| 1 | POST | `/auth/token` | ✅ OK | 200 | 315ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 22ms |
</details>

<details>
<summary><b>RAG</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ✅ OK | 202 | 21ms |
| 2 | POST | `/rag/build` | ✅ OK | 202 | 11ms |
| 3 | DELETE | `/rag/build/{doc_id}` | ✅ OK | 200 | 10ms |
| 4 | GET | `/rag/build/{doc_id}/status` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
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
| 1 | GET | `/health` | ✅ OK | 200 | 2ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 3318ms |
</details>

---

### gateway

**Gateway Service** (port 8080)

**Ping:** ✅ Alive

**Total:** 77 | **Passed:** 74 | **Failed:** 0 | **Skipped:** <span style="color:red;font-weight:bold">3</span>

<details>
<summary><b>AUTH</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 5ms |
| 2 | POST | `/auth/token` | ✅ OK | 200 | 6ms |
| 3 | GET | `/auth/me` | ✅ OK | 200 | 4ms |
| 4 | POST | `/auth/refresh` | ✅ OK | 200 | 6ms |
| 5 | POST | `/auth/revoke` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>ADMIN</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 409 | 4ms |
| 2 | GET | `/admin/users` | ✅ OK | 200 | 7ms |
| 3 | POST | `/admin/users` | ✅ OK | 409 | 7ms |
| 4 | GET | `/admin/users/{user_id}` | ⏭️ Skipped: Нет в контексте: user_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | PATCH | `/admin/users/{user_id}` | ⏭️ Skipped: Нет в контексте: user_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | DELETE | `/admin/users/{user_id}` | ⏭️ Skipped: Нет в контексте: user_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | GET | `/admin/roles` | ✅ OK | 200 | 4ms |
| 8 | POST | `/admin/roles` | ✅ OK | 201 | 5ms |
| 9 | GET | `/admin/audit` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>CHAT</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/projects` | ✅ OK | 201 | 11ms |
| 2 | POST | `/chat/sessions` | ✅ OK | 201 | 4ms |
| 3 | POST | `/chat/sessions` | ✅ OK | 201 | 8ms |
| 4 | GET | `/chat/sessions` | ✅ OK | 200 | 4ms |
| 5 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 5ms |
| 6 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 6ms |
| 7 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 5ms |
| 8 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 4ms |
| 9 | GET | `/chat/history` | ✅ OK | 200 | 4ms |
| 10 | GET | `/chat/history/export` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers/` | ✅ OK | 409 | 7ms |
| 2 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 5ms |
| 3 | GET | `/registry/classifiers/` | ✅ OK | 200 | 4ms |
| 4 | POST | `/registry/classifiers/` | ✅ OK | 201 | 4ms |
| 5 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 4ms |
| 6 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 4ms |
| 7 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 5ms |
| 8 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 5ms |
| 9 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 3ms |
| 10 | POST | `/registry/classifiers/import` | ✅ OK | 400 | 4ms |
| 11 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 8ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 6ms |
| 13 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 7ms |
| 14 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories/` | ✅ OK | 200 | 4ms |
| 2 | POST | `/registry/categories/` | ✅ OK | 201 | 5ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 4ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 7ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/terminology/` | ✅ OK | 200 | 5ms |
| 2 | POST | `/registry/terminology/` | ✅ OK | 201 | 4ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 6ms |
| 4 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 6ms |
| 5 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 3ms |
| 6 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 4ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 400 | 4ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/documents/` | ✅ OK | 200 | 4ms |
| 2 | POST | `/registry/documents/` | ✅ OK | 201 | 4ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 8ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 4ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 200 | 5ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 4ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 3ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 3ms |
| 9 | GET | `/registry/documents/export` | ✅ OK | 200 | 6ms |
| 10 | POST | `/registry/documents/import` | ✅ OK | 400 | 6ms |
| 11 | GET | `/documents/` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 4ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ✅ OK | 202 | 4ms |
| 2 | GET | `/drafts/` | ✅ OK | 200 | 4ms |
| 3 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 7ms |
| 4 | DELETE | `/drafts/{draft_id}` | ✅ OK | 200 | 3ms |
| 5 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 409 | 5ms |
| 6 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 409 | 4ms |
| 7 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>FILES</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/files/1` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>TEXT</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 5ms |
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

_Report generated by `api_coverage_test.py` at 2026-06-23 14:03:13 UTC_
