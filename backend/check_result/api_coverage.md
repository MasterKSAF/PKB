# API Coverage Report

**Generated:** 2026-06-20 13:08:30 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 8082 | ✅ | ✅ | 18 | 17 | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [Registry Service](#registry) | 8084 | ✅ | ✅ | 34 | 32 | <span style="color:red;font-weight:bold">1</span> | <span style="color:red;font-weight:bold">1</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Converter-Validator Service](#converter-validator) | 8086 | ✅ | — | 5 | 3 | 0 | <span style="color:red;font-weight:bold">2</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Parser Service](#parser) | 8087 | ✅ | — | 5 | 1 | <span style="color:red;font-weight:bold">2</span> | <span style="color:red;font-weight:bold">2</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Orchestrator Service](#orchestrator) | 8081 | ✅ | ✅ | 22 | 9 | <span style="color:red;font-weight:bold">5</span> | <span style="color:red;font-weight:bold">8</span> | <span style="color:red;font-weight:bold">❌</span> |
| [Query Service](#query) | 8083 | ✅ | ✅ | 21 | 6 | <span style="color:red;font-weight:bold">4</span> | <span style="color:red;font-weight:bold">11</span> | <span style="color:red;font-weight:bold">❌</span> |
| [RAG Builder Service](#rag-builder) | 8090 | ✅ | ✅ | 9 | 5 | <span style="color:red;font-weight:bold">2</span> | <span style="color:red;font-weight:bold">2</span> | <span style="color:red;font-weight:bold">❌</span> |
| [RAG Search Service](#rag-search) | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| [Gateway Service](#gateway) | 8080 | ✅ | — | 76 | 4 | <span style="color:red;font-weight:bold">53</span> | <span style="color:red;font-weight:bold">19</span> | <span style="color:red;font-weight:bold">❌</span> |
| [TEI (Embeddings)](#tei) | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | **6/6** | **194** | **81** | <span style="color:red;font-weight:bold">68</span> | <span style="color:red;font-weight:bold">45</span> | <span style="color:red;font-weight:bold">❌</span> |

## 🔍 Details by Service

### auth

**Auth Service** (port 8082)

**Ping:** ✅ Alive

**Total:** 18 | **Passed:** 17 | **Failed:** <span style="color:red;font-weight:bold">1</span> | **Skipped:** 0

<details>
<summary><b>AUTH</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 251ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 11ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 237ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 8ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 16ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 21ms |
</details>

<details>
<summary><b>ADMIN</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 250ms |
| 2 | GET | `/admin/users` | ✅ OK | 200 | 17ms |
| 3 | POST | `/admin/users` | ✅ OK | 201 | 240ms |
| 4 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 11ms |
| 5 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 30ms |
| 6 | PATCH | `/admin/users/{user_id}` | ❌ Error: HTTP 400 | 400 | 13ms |
| 7 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 28ms |
| 8 | GET | `/admin/roles` | ✅ OK | 200 | 18ms |
| 9 | POST | `/admin/roles` | ✅ OK | 201 | 27ms |
| 10 | GET | `/admin/audit` | ✅ OK | 200 | 19ms |
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
| 1 | POST | `/internal/auth/validate` | ✅ OK | 200 | 15ms |
</details>

---

### registry

**Registry Service** (port 8084)

**Ping:** ✅ Alive

> ⚠️ ⚠️ Registry требует trailing slash на всех эндпоинтах /classifiers/, /documents/, /terminology/ (в т.ч. параметризованные). Документация — без /.

**Total:** 34 | **Passed:** 32 | **Failed:** <span style="color:red;font-weight:bold">1</span> | **Skipped:** <span style="color:red;font-weight:bold">1</span>

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers/` | ✅ OK | 201 | 28ms |
| 2 | GET | `/registry/classifiers/pending/` | ✅ OK | 200 | 19ms |
| 3 | GET | `/registry/classifiers/` | ✅ OK | 200 | 14ms |
| 4 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 8ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 10ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 15ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 15ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 25ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 9ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 13ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 24ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 16ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 11ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 47ms |
| 2 | GET | `/registry/documents/` | ✅ OK | 200 | 14ms |
| 3 | GET | `/registry/documents/{doc_id}` | ❌ Error: Поле 'data.current_version_id' обязательно, но не найдено в ответе | 200 | 10ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 21ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 200 | 20ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 12ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 8ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 18ms |
| 9 | GET | `/registry/documents/export` | ✅ OK | 200 | 10ms |
| 10 | POST | `/registry/documents/import` | ✅ OK | 422 | 8ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology/` | ✅ OK | 201 | 17ms |
| 2 | GET | `/registry/terminology/` | ✅ OK | 200 | 12ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 11ms |
| 4 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 8ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 15ms |
| 6 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 14ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 422 | 7ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ⏭️ Skipped: Сервис не обновлён — эндпоинт из задач 19.06.2026 | 404 | 2ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 19ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 9ms |
</details>

---

### converter-validator

**Converter-Validator Service** (port 8086)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 3 | **Failed:** 0 | **Skipped:** <span style="color:red;font-weight:bold">2</span>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 2ms |
</details>

<details>
<summary><b>CONVERTER</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/converter/preview` | ⏭️ Skipped: Сервис не обновлён — эндпоинт из задач 19.06.2026 | 404 | 1ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 94ms |
</details>

<details>
<summary><b>VALIDATE</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/metadata` | ⏭️ Skipped: Сервис не обновлён — эндпоинт из задач 19.06.2026 | 404 | 1ms |
| 2 | POST | `/validate/document` | ✅ OK | 200 | 46ms |
</details>

---

### parser

**Parser Service** (port 8087)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 1 | **Failed:** <span style="color:red;font-weight:bold">2</span> | **Skipped:** <span style="color:red;font-weight:bold">2</span>

<details>
<summary><b>PARSER</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/parser/process` | ❌ Error: HTTP 422 | 422 | 14ms |
| 2 | POST | `/parser/process` | ❌ Error: Поле 'preview_not_supported' обязательно, но не найдено в ответе | 202 | 37ms |
| 3 | GET | `/parser/process/{task_id}/status` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | GET | `/parser/process/{task_id}/result` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 2ms |
</details>

---

### orchestrator

**Orchestrator Service** (port 8081)

**Ping:** ✅ Alive

**Total:** 22 | **Passed:** 9 | **Failed:** <span style="color:red;font-weight:bold">5</span> | **Skipped:** <span style="color:red;font-weight:bold">8</span>

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 241ms |
</details>

<details>
<summary><b>DRAFTS</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ❌ Error: HTTP 422 | 422 | 17ms |
| 2 | POST | `/drafts/` | ❌ Error: HTTP 422 | 422 | 6ms |
| 3 | GET | `/drafts/` | ✅ OK | 200 | 68ms |
| 4 | GET | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | DELETE | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | PATCH | `/drafts/{draft_id}/decide` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | PATCH | `/drafts/{draft_id}/metadata` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 8 | GET | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 9 | POST | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 10 | GET | `/drafts/{draft_id}/preview/status` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/system/health` | ✅ OK | 200 | 10ms |
| 2 | GET | `/health` | ❌ Error: HTTP 404 | 404 | 2ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ❌ Error: HTTP 404 | 404 | 2ms |
</details>

<details>
<summary><b>TASKS</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/` | ❌ Error: Поле 'tasks' обязательно, но не найдено в ответе | 200 | 28ms |
| 2 | GET | `/tasks/{task_id}/status` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/` | ✅ OK | 200 | 14ms |
| 2 | GET | `/documents/queue` | ✅ OK | 200 | 5ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 6ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 200 | 4ms |
| 5 | GET | `/documents/{doc_id}/status` | ✅ OK | 200 | 5ms |
| 6 | GET | `/documents/{doc_id}/file` | ✅ OK | 200 | 4ms |
</details>

---

### query

**Query Service** (port 8083)

**Ping:** ✅ Alive

> ⚠️ ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

**Total:** 21 | **Passed:** 6 | **Failed:** <span style="color:red;font-weight:bold">4</span> | **Skipped:** <span style="color:red;font-weight:bold">11</span>

<details>
<summary><b>CHAT</b> (17 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ❌ Error: HTTP 500 | 500 | 66ms |
| 2 | POST | `/chat/sessions/{session_id}/messages` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 3 | POST | `/chat/sessions` | ❌ Error: HTTP 500 | 500 | 21ms |
| 4 | GET | `/chat/sessions` | ✅ OK | 200 | 12ms |
| 5 | GET | `/chat/sessions/{session_id}` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | PUT | `/chat/sessions/{session_id}` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | POST | `/chat/sessions/{session_id}/messages` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 8 | GET | `/chat/sessions/{session_id}/messages/last` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 9 | GET | `/chat/sessions/{session_id}/messages` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 10 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ⏭️ Skipped: Нет в контексте: session_id, message_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 11 | POST | `/chat/sessions/{session_id}/messages/search` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 12 | POST | `/chat/sessions/{session_id}/context` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 13 | POST | `/chat/sessions/{session_id}/export` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 14 | POST | `/chat/feedback` | ❌ Error: HTTP 500 | 500 | 70ms |
| 15 | DELETE | `/chat/sessions/{session_id}` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 16 | GET | `/chat/history` | ✅ OK | 200 | 16ms |
| 17 | GET | `/chat/history/export` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 7ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ❌ Error: Поле 'enrichment_skipped' обязательно, но не найдено в ответе | 200 | 9ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 6ms |
</details>

---

### rag-builder

**RAG Builder Service** (port 8090)

**Ping:** ✅ Alive

**Total:** 9 | **Passed:** 5 | **Failed:** <span style="color:red;font-weight:bold">2</span> | **Skipped:** <span style="color:red;font-weight:bold">2</span>

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 421ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 15ms |
</details>

<details>
<summary><b>RAG</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ❌ Error: HTTP 500 | 500 | 98ms |
| 2 | POST | `/rag/build` | ❌ Error: HTTP 500 | 500 | 15ms |
| 3 | DELETE | `/rag/build/{doc_id}` | ✅ OK | 200 | 10ms |
| 4 | POST | `/rag/build/{doc_id}/reprocess` | ⏭️ Skipped: Сервис не обновлён — эндпоинт из задач 19.06.2026 | 404 | 3ms |
| 5 | GET | `/rag/build/{doc_id}/status` | ✅ OK | 200 | 7ms |
| 6 | GET | `/rag/build/{doc_id}/integrity` | ⏭️ Skipped: Сервис не обновлён — эндпоинт из задач 19.06.2026 | 404 | 4ms |
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

**Total:** 2 | **Passed:** 2 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 1186ms |
</details>

---

### gateway

**Gateway Service** (port 8080)

**Ping:** ✅ Alive

**Total:** 76 | **Passed:** 4 | **Failed:** <span style="color:red;font-weight:bold">53</span> | **Skipped:** <span style="color:red;font-weight:bold">19</span>

<details>
<summary><b>AUTH</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 338ms |
| 2 | POST | `/auth/token` | ❌ Error: HTTP 401 | 401 | 13ms |
| 3 | GET | `/auth/me` | ❌ Error: HTTP 401 | 401 | 6ms |
| 4 | POST | `/auth/refresh` | ❌ Error: HTTP 401 | 401 | 8ms |
| 5 | POST | `/auth/revoke` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>HEALTH</b> (3 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 5ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 5ms |
| 3 | GET | `/gateway/health` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>ADMIN</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/admin/users` | ❌ Error: HTTP 401 | 401 | 2ms |
| 2 | POST | `/admin/users` | ❌ Error: HTTP 401 | 401 | 2ms |
| 3 | GET | `/admin/users/{user_id}` | ❌ Error: HTTP 401 | 401 | 4ms |
| 4 | PATCH | `/admin/users/{user_id}` | ❌ Error: HTTP 401 | 401 | 4ms |
| 5 | DELETE | `/admin/users/{user_id}` | ❌ Error: HTTP 401 | 401 | 3ms |
| 6 | GET | `/admin/roles` | ❌ Error: HTTP 401 | 401 | 3ms |
| 7 | POST | `/admin/roles` | ❌ Error: HTTP 401 | 401 | 4ms |
| 8 | GET | `/admin/audit` | ❌ Error: HTTP 401 | 401 | 4ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (12 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/classifiers/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 2 | POST | `/registry/classifiers/` | ❌ Error: HTTP 401 | 401 | 2ms |
| 3 | GET | `/registry/classifiers/tree/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 4 | GET | `/registry/classifiers/{classifier_code}` | ⏭️ Skipped: Нет в контексте: classifier_code. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | PUT | `/registry/classifiers/{classifier_code}` | ⏭️ Skipped: Нет в контексте: classifier_code. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | PATCH | `/registry/classifiers/{classifier_code}` | ⏭️ Skipped: Нет в контексте: classifier_code. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | DELETE | `/registry/classifiers/{classifier_code}` | ⏭️ Skipped: Нет в контексте: classifier_code. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 8 | POST | `/registry/classifiers/import` | ❌ Error: HTTP 401 | 401 | 5ms |
| 9 | GET | `/registry/classifiers/pending` | ❌ Error: HTTP 401 | 401 | 3ms |
| 10 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ⏭️ Skipped: Нет в контексте: pending_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ⏭️ Skipped: Нет в контексте: pending_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 12 | POST | `/registry/classifiers/validate` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 2 | POST | `/registry/categories/` | ❌ Error: HTTP 401 | 401 | 4ms |
| 3 | GET | `/registry/categories/{category_id}` | ❌ Error: HTTP 401 | 401 | 3ms |
| 4 | PUT | `/registry/categories/{category_id}` | ❌ Error: HTTP 401 | 401 | 3ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ❌ Error: HTTP 401 | 401 | 2ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/terminology/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 2 | POST | `/registry/terminology/` | ❌ Error: HTTP 401 | 401 | 6ms |
| 3 | GET | `/registry/terminology/{term_id}` | ⏭️ Skipped: Нет в контексте: term_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | PUT | `/registry/terminology/{term_id}` | ⏭️ Skipped: Нет в контексте: term_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | DELETE | `/registry/terminology/{term_id}` | ⏭️ Skipped: Нет в контексте: term_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | GET | `/registry/terminology/normalize/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 7 | POST | `/registry/terminology/import` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/documents/` | ❌ Error: HTTP 401 | 401 | 4ms |
| 2 | POST | `/registry/documents/` | ❌ Error: HTTP 401 | 401 | 4ms |
| 3 | GET | `/registry/documents/{doc_id}` | ❌ Error: HTTP 401 | 401 | 3ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ❌ Error: HTTP 401 | 401 | 2ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ❌ Error: HTTP 401 | 401 | 3ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ❌ Error: HTTP 401 | 401 | 5ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ❌ Error: HTTP 401 | 401 | 2ms |
| 9 | GET | `/registry/documents/export` | ❌ Error: HTTP 401 | 401 | 3ms |
| 10 | POST | `/registry/documents/import` | ❌ Error: HTTP 401 | 401 | 3ms |
| 11 | GET | `/documents/` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ❌ Error: HTTP 401 | 401 | 4ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ❌ Error: HTTP 401 | 401 | 3ms |
| 2 | GET | `/registry/enums` | ❌ Error: HTTP 401 | 401 | 2ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ❌ Error: HTTP 401 | 401 | 3ms |
| 2 | GET | `/drafts/` | ❌ Error: HTTP 401 | 401 | 5ms |
| 3 | GET | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | DELETE | `/drafts/{draft_id}` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | PATCH | `/drafts/{draft_id}/decide` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | POST | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | GET | `/drafts/{draft_id}/preview` | ⏭️ Skipped: Нет в контексте: draft_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>ANALYSE</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/analyse/start` | ❌ Error: HTTP 401 | 401 | 2ms |
| 2 | GET | `/analyse/{task_id}/status` | ⏭️ Skipped: Нет в контексте: task_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
</details>

<details>
<summary><b>MERIDIAN</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/meridian/status` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>FILES</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/files/{file_id}` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>EXTERNAL</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/external/integrations` | ❌ Error: HTTP 401 | 401 | 4ms |
</details>

<details>
<summary><b>CHAT</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ❌ Error: HTTP 401 | 401 | 3ms |
| 2 | GET | `/chat/sessions` | ❌ Error: HTTP 401 | 401 | 3ms |
| 3 | GET | `/chat/sessions/{session_id}` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 4 | POST | `/chat/sessions/{session_id}/messages` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 5 | GET | `/chat/sessions/{session_id}/messages` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 6 | POST | `/chat/sessions/{session_id}/messages/search` | ⏭️ Skipped: Нет в контексте: session_id. Требуется предварительный вызов создающего эндпоинта. | 0 | 0ms |
| 7 | GET | `/chat/history` | ❌ Error: HTTP 401 | 401 | 5ms |
| 8 | GET | `/chat/history/export` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>TEXT</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ❌ Error: HTTP 401 | 401 | 3ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ❌ Error: HTTP 401 | 401 | 4ms |
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
| 1 | POST | `/embed` | ✅ OK | 200 | 17ms |
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

_Report generated by `api_coverage_test.py` at 2026-06-20 13:08:30 UTC_
