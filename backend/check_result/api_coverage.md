# API Coverage Report

**Generated:** 2026-06-27 15:34:47 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 18082 | ✅ | ✅ | 19 | 19 | 0 | 0 | ✅ |
| [Registry Service](#registry) | 18084 | ✅ | ✅ | 50 | 50 | 0 | 0 | ✅ |
| [Converter-Validator Service](#converter-validator) | 18086 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| [Parser Service](#parser) | 18087 | ✅ | — | 5 | 5 | 0 | 0 | ✅ |
| [Orchestrator Service](#orchestrator) | 18081 | ✅ | ✅ | 35 | 35 | 0 | 0 | ✅ |
| [Query Service](#query) | 18083 | ✅ | ✅ | 27 | 27 | 0 | 0 | ✅ |
| [RAG Builder Service](#rag-builder) | 18090 | ✅ | ✅ | 7 | 7 | 0 | 0 | ✅ |
| [RAG Search Service](#rag-search) | 18091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| [Gateway Service](#gateway) | 18080 | ✅ | — | 101 | 101 | 0 | 0 | ✅ |
| [TEI (Embeddings)](#tei) | 18092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | **6/6** | **253** | **253** | 0 | 0 | ✅ |

## 🔍 Details by Service

### auth

**Auth Service** (port 18082)

**Ping:** ✅ Alive

> ⚠️ PATCH /admin/users/{id}: docs ожидает audit_log_id, но сервис его не возвращает

**Total:** 19 | **Passed:** 19 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 260ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 13ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 237ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 9ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 14ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 24ms |
</details>

<details>
<summary><b>ADMIN</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 271ms |
| 2 | POST | `/admin/roles` | ✅ OK | 409 | 22ms |
| 3 | GET | `/admin/users` | ✅ OK | 200 | 20ms |
| 4 | POST | `/admin/users` | ✅ OK | 201 | 249ms |
| 5 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 13ms |
| 6 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 33ms |
| 7 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 31ms |
| 8 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 32ms |
| 9 | GET | `/admin/roles` | ✅ OK | 200 | 15ms |
| 10 | POST | `/admin/roles` | ✅ OK | 201 | 25ms |
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
| 1 | POST | `/internal/auth/validate` | ✅ OK | 200 | 22ms |
</details>

---

### registry

**Registry Service** (port 18084)

**Ping:** ✅ Alive

> ⚠️ ⚠️ PATCH /documents/{id}/status — internal API (только Orchestrator), checker ожидает 403.

> ⚠️ ⚠️ PATCH /drafts/{id}/metadata — internal API (только Orchestrator), checker ожидает 404.

**Total:** 50 | **Passed:** 50 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers` | ✅ OK | 201 | 37ms |
| 2 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 36ms |
| 3 | GET | `/registry/classifiers` | ✅ OK | 200 | 22ms |
| 4 | GET | `/registry/classifiers/tree` | ✅ OK | 200 | 71ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 16ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 23ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 19ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 24ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 400 | 13ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 16ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 33ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 21ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 14ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents` | ✅ OK | 201 | 62ms |
| 2 | GET | `/registry/documents` | ✅ OK | 200 | 89ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 14ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 32ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 403 | 13ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 23ms |
| 7 | GET | `/registry/documents/{doc_id}/succession` | ✅ OK | 200 | 18ms |
| 8 | GET | `/registry/documents/export` | ✅ OK | 200 | 15ms |
| 9 | POST | `/registry/documents/import` | ✅ OK | 400 | 13ms |
| 10 | GET | `/registry/search` | ✅ OK | 200 | 21ms |
| 11 | GET | `/registry/documents/{doc_id}/sections` | ✅ OK | 200 | 32ms |
| 12 | POST | `/registry/documents/check-uniqueness` | ✅ OK | 200 | 14ms |
| 13 | PATCH | `/registry/documents/{doc_id}` | ✅ OK | 200 | 33ms |
| 14 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 24ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology` | ✅ OK | 201 | 22ms |
| 2 | GET | `/registry/terminology` | ✅ OK | 200 | 17ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 13ms |
| 4 | GET | `/registry/terminology/normalize` | ✅ OK | 200 | 15ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 20ms |
| 6 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 21ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 400 | 8ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories` | ✅ OK | 200 | 13ms |
| 2 | POST | `/registry/categories` | ✅ OK | 201 | 23ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 13ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 31ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 16ms |
</details>

<details>
<summary><b>DRAFTS</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/drafts` | ✅ OK | 201 | 20ms |
| 2 | GET | `/registry/drafts` | ✅ OK | 200 | 15ms |
| 3 | GET | `/registry/drafts/{draft_id}` | ✅ OK | 200 | 10ms |
| 4 | GET | `/registry/drafts/{draft_id}/preview` | ✅ OK | 200 | 17ms |
| 5 | PATCH | `/registry/drafts/{draft_id}/status` | ✅ OK | 200 | 18ms |
| 6 | DELETE | `/registry/drafts/{draft_id}` | ✅ OK | 200 | 23ms |
| 7 | PATCH | `/registry/drafts/{draft_id}/metadata` | ✅ OK | 404 | 13ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ✅ OK | 200 | 19ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 20ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 12ms |
</details>

---

### converter-validator

**Converter-Validator Service** (port 18086)

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
| 1 | POST | `/converter/preview` | ✅ OK | 200 | 13ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 84ms |
</details>

<details>
<summary><b>VALIDATE</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/metadata` | ✅ OK | 200 | 13ms |
| 2 | POST | `/validate/document` | ✅ OK | 200 | 40ms |
</details>

---

### parser

**Parser Service** (port 18087)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 5 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>PARSER</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/parser/process` | ✅ OK | 202 | 21ms |
| 2 | POST | `/parser/process` | ✅ OK | 202 | 25ms |
| 3 | GET | `/parser/process/{task_id}/status` | ✅ OK | 200 | 27ms |
| 4 | GET | `/parser/process/{task_id}/result` | ✅ OK | 409 | 24ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 75ms |
</details>

---

### orchestrator

**Orchestrator Service** (port 18081)

**Ping:** ✅ Alive

**Total:** 35 | **Passed:** 35 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 275ms |
</details>

<details>
<summary><b>DRAFTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts` | ✅ OK | 202 | 630ms |
| 2 | POST | `/drafts` | ✅ OK | 202 | 620ms |
| 3 | GET | `/drafts/` | ✅ OK | 405 | 8ms |
| 4 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 156ms |
| 5 | GET | `/drafts/{draft_id}/tasks` | ✅ OK | 200 | 86ms |
| 6 | DELETE | `/drafts/{draft_id}` | ✅ OK | 204 | 130ms |
| 7 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 200 | 530ms |
| 8 | PATCH | `/drafts/{draft_id}/metadata` | ✅ OK | 404 | 125ms |
| 9 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 75ms |
| 10 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 121ms |
| 11 | GET | `/drafts/{draft_id}/preview/status` | ✅ OK | 200 | 161ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/system/health` | ✅ OK | 200 | 8ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ✅ OK | 404 | 7ms |
</details>

<details>
<summary><b>TASKS</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/` | ✅ OK | 200 | 115ms |
| 2 | GET | `/tasks/{task_id}/status` | ✅ OK | 200 | 152ms |
| 3 | GET | `/tasks/{task_id}/steps` | ✅ OK | 200 | 70ms |
| 4 | GET | `/tasks/stats` | ✅ OK | 200 | 81ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/` | ✅ OK | 404 | 5ms |
| 2 | GET | `/documents/queue` | ✅ OK | 200 | 86ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 404 | 4ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 404 | 5ms |
| 5 | GET | `/documents/{doc_id}/status` | ✅ OK | 404 | 4ms |
| 6 | GET | `/documents/{doc_id}/file` | ✅ OK | 404 | 7ms |
| 7 | GET | `/documents/{doc_id}/versions` | ✅ OK | 404 | 4ms |
| 8 | POST | `/documents/{doc_id}/versions` | ✅ OK | 404 | 6ms |
| 9 | GET | `/documents/{doc_id}/history` | ✅ OK | 404 | 7ms |
| 10 | POST | `/documents/{doc_id}/reprocess` | ✅ OK | 202 | 170ms |
| 11 | GET | `/documents/{doc_id}/tasks` | ✅ OK | 200 | 72ms |
| 12 | GET | `/documents/{doc_id}/errors` | ✅ OK | 404 | 8ms |
| 13 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 404 | 4ms |
</details>

<details>
<summary><b>PAGES</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/{doc_id}/pages` | ✅ OK | 404 | 11ms |
| 2 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 404 | 13ms |
| 3 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 404 | 4ms |
| 4 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 404 | 4ms |
</details>

---

### query

**Query Service** (port 18083)

**Ping:** ✅ Alive

> ⚠️ ⚠️ POST /chat/feedback: rating:int + rating_status:string (QS-10). Ранее был rating:string без rating_status.

**Total:** 27 | **Passed:** 27 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>CHAT</b> (23 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/projects` | ✅ OK | 201 | 34ms |
| 2 | POST | `/chat/sessions` | ✅ OK | 201 | 48ms |
| 3 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 63ms |
| 4 | POST | `/chat/projects` | ✅ OK | 201 | 15ms |
| 5 | GET | `/chat/projects` | ✅ OK | 200 | 64ms |
| 6 | GET | `/chat/projects/{project_id}` | ✅ OK | 200 | 31ms |
| 7 | PUT | `/chat/projects/{project_id}` | ✅ OK | 200 | 33ms |
| 8 | POST | `/chat/sessions` | ✅ OK | 201 | 25ms |
| 9 | GET | `/chat/sessions` | ✅ OK | 200 | 19ms |
| 10 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 14ms |
| 11 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 200 | 16ms |
| 12 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 18ms |
| 13 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 200 | 89ms |
| 14 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 79ms |
| 15 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 200 | 95ms |
| 16 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 72ms |
| 17 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 200 | 15ms |
| 18 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 200 | 27ms |
| 19 | POST | `/chat/feedback` | ✅ OK | 200 | 26ms |
| 20 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 200 | 88ms |
| 21 | GET | `/chat/history` | ✅ OK | 200 | 21ms |
| 22 | GET | `/chat/history/export` | ✅ OK | 200 | 12ms |
| 23 | DELETE | `/chat/projects/{project_id}` | ✅ OK | 204 | 33ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 244ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 24ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 13ms |
</details>

---

### rag-builder

**RAG Builder Service** (port 18090)

**Ping:** ✅ Alive

**Total:** 7 | **Passed:** 7 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 297ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 43ms |
</details>

<details>
<summary><b>RAG</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ✅ OK | 202 | 236ms |
| 2 | POST | `/rag/build` | ✅ OK | 202 | 78ms |
| 3 | DELETE | `/rag/build/{doc_id}` | ✅ OK | 200 | 18ms |
| 4 | GET | `/rag/build/{doc_id}/status` | ✅ OK | 200 | 10ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 8ms |
</details>

---

### rag-search

**RAG Search Service** (port 18091)

**Ping:** ✅ Alive

**Total:** 2 | **Passed:** 2 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 8ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 12ms |
</details>

---

### gateway

**Gateway Service** (port 18080)

**Ping:** ✅ Alive

**Total:** 101 | **Passed:** 101 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 362ms |
| 2 | POST | `/auth/token` | ✅ OK | 200 | 284ms |
| 3 | GET | `/auth/me` | ✅ OK | 200 | 80ms |
| 4 | POST | `/auth/refresh` | ✅ OK | 200 | 38ms |
| 5 | POST | `/auth/revoke` | ✅ OK | 200 | 47ms |
</details>

<details>
<summary><b>ADMIN</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 296ms |
| 2 | GET | `/admin/users` | ✅ OK | 200 | 32ms |
| 3 | POST | `/admin/users` | ✅ OK | 409 | 36ms |
| 4 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 35ms |
| 5 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 70ms |
| 6 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 53ms |
| 7 | GET | `/admin/roles` | ✅ OK | 200 | 36ms |
| 8 | POST | `/admin/roles` | ✅ OK | 409 | 28ms |
| 9 | GET | `/admin/audit` | ✅ OK | 200 | 28ms |
</details>

<details>
<summary><b>CHAT</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/projects` | ✅ OK | 201 | 45ms |
| 2 | POST | `/chat/sessions` | ✅ OK | 201 | 31ms |
| 3 | POST | `/chat/sessions` | ✅ OK | 201 | 24ms |
| 4 | GET | `/chat/sessions` | ✅ OK | 200 | 21ms |
| 5 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 16ms |
| 6 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 23ms |
| 7 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 65ms |
| 8 | POST | `/chat/sessions/{session_id}/messages/search` | ✅ OK | 200 | 40ms |
| 9 | GET | `/chat/history` | ✅ OK | 200 | 47ms |
| 10 | GET | `/chat/history/export` | ✅ OK | 200 | 18ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (14 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers/` | ✅ OK | 201 | 44ms |
| 2 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 40ms |
| 3 | GET | `/registry/classifiers/` | ✅ OK | 200 | 29ms |
| 4 | POST | `/registry/classifiers/` | ✅ OK | 201 | 33ms |
| 5 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 110ms |
| 6 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 52ms |
| 7 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 42ms |
| 8 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 65ms |
| 9 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 54ms |
| 10 | POST | `/registry/classifiers/import` | ✅ OK | 400 | 31ms |
| 11 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 53ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 65ms |
| 13 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 52ms |
| 14 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 49ms |
</details>

<details>
<summary><b>DRAFTS</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts` | ✅ OK | 202 | 582ms |
| 2 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 200 | 289ms |
| 3 | GET | `/drafts/` | ✅ OK | 200 | 41ms |
| 4 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 93ms |
| 5 | DELETE | `/drafts/{draft_id}` | ✅ OK | 204 | 111ms |
| 6 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 63ms |
| 7 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 18ms |
| 8 | GET | `/drafts/{draft_id}/preview/status` | ✅ OK | 200 | 5167ms |
| 9 | PATCH | `/drafts/{draft_id}/metadata` | ✅ OK | 404 | 55ms |
| 10 | GET | `/drafts/{draft_id}/tasks` | ✅ OK | 200 | 52ms |
</details>

<details>
<summary><b>TASKS</b> (3 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/{task_id}/status` | ✅ OK | 200 | 106ms |
| 2 | GET | `/tasks/{task_id}/status` | ✅ OK | 200 | 49ms |
| 3 | GET | `/tasks/{task_id}/steps` | ✅ OK | 200 | 58ms |
</details>

<details>
<summary><b>GATEWAY-DOCS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 32ms |
| 2 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 39ms |
| 3 | PUT | `/documents/{doc_id}` | ✅ OK | 200 | 52ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 200 | 45ms |
| 5 | GET | `/documents/{doc_id}/file` | ✅ OK | 404 | 52ms |
| 6 | GET | `/documents/{doc_id}/pages` | ✅ OK | 404 | 45ms |
| 7 | GET | `/documents/{doc_id}/history` | ✅ OK | 404 | 40ms |
| 8 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 404 | 37ms |
| 9 | GET | `/documents/{doc_id}/versions` | ✅ OK | 200 | 48ms |
| 10 | GET | `/documents/{doc_id}/succession` | ✅ OK | 404 | 37ms |
| 11 | GET | `/documents/export` | ✅ OK | 200 | 43ms |
| 12 | POST | `/documents/import` | ✅ OK | 400 | 27ms |
| 13 | POST | `/documents/check-uniqueness` | ✅ OK | 200 | 40ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 6ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 62ms |
</details>

<details>
<summary><b>MONITOR</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/monitor/metrics` | ✅ OK | 200 | 21ms |
</details>

<details>
<summary><b>CATEGORIES</b> (5 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/categories/` | ✅ OK | 200 | 48ms |
| 2 | POST | `/registry/categories/` | ✅ OK | 201 | 53ms |
| 3 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 34ms |
| 4 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 58ms |
| 5 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 43ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/terminology/` | ✅ OK | 200 | 32ms |
| 2 | POST | `/registry/terminology` | ✅ OK | 201 | 46ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 42ms |
| 4 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 50ms |
| 5 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 36ms |
| 6 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 39ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 400 | 39ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (16 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/documents/` | ✅ OK | 200 | 49ms |
| 2 | POST | `/registry/documents/` | ✅ OK | 201 | 54ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 43ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 51ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 403 | 68ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 42ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 50ms |
| 8 | GET | `/registry/documents/export` | ✅ OK | 200 | 48ms |
| 9 | POST | `/registry/documents/import` | ✅ OK | 400 | 37ms |
| 10 | GET | `/documents/` | ✅ OK | 200 | 22ms |
| 11 | GET | `/documents/queue` | ✅ OK | 200 | 17ms |
| 12 | GET | `/documents/{doc_id}/status` | ✅ OK | 404 | 32ms |
| 13 | GET | `/documents/{doc_id}/errors` | ✅ OK | 404 | 14ms |
| 14 | POST | `/documents/{doc_id}/reprocess` | ✅ OK | 409 | 56ms |
| 15 | POST | `/documents/{doc_id}/versions` | ✅ OK | 404 | 21ms |
| 16 | GET | `/documents/{doc_id}/tasks` | ✅ OK | 200 | 51ms |
</details>

<details>
<summary><b>SEARCH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/search` | ✅ OK | 200 | 57ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 47ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 47ms |
</details>

<details>
<summary><b>FILES</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/files/1` | ✅ OK | 410 | 2ms |
</details>

<details>
<summary><b>TEXT</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 18ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 35ms |
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
| 1 | POST | `/embed` | ✅ OK | 200 | 3ms |
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

_Report generated by `api_coverage_test.py` at 2026-06-27 15:34:47 UTC_
