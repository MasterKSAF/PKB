# API Coverage Report

**Generated:** 2026-06-15 19:31:11 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Ping | CheckDb | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:-------:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 8082 | ✅ | ✅ | 18 | 18 | 0 | 0 | ✅ |
| [Registry Service](#registry) | 8084 | ✅ | ✅ | 33 | 33 | 0 | 0 | ✅ |
| [Converter-Validator Service](#converter-validator) | 8086 | ✅ | — | 4 | 4 | 0 | 0 | ✅ |
| [Parser Service](#parser) | 8087 | ✅ | — | 5 | 4 | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [Orchestrator Service](#orchestrator) | 8081 | ✅ | ✅ | 32 | 32 | 0 | 0 | ✅ |
| [Query Service](#query) | 8083 | ✅ | ✅ | 20 | 20 | 0 | 0 | ✅ |
| [RAG Builder Service](#rag-builder) | 8090 | ✅ | ❌ | 7 | 7 | 0 | 0 | ✅ |
| [RAG Search Service](#rag-search) | 8091 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| [Gateway Service](#gateway) | 8080 | ✅ | — | 120 | 120 | 0 | 0 | ✅ |
| [TEI (Embeddings)](#tei) | 8092 | ✅ | — | 2 | 2 | 0 | 0 | ✅ |
| **Total** | | **10/10** | **5/6** | **243** | **242** | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |

## 🔍 Details by Service

### auth

**Auth Service** (port 8082)

**Ping:** ✅ Alive

**Total:** 18 | **Passed:** 18 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 256ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 10ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 234ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 6ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 12ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 19ms |
</details>

<details>
<summary><b>ADMIN</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 248ms |
| 2 | GET | `/admin/users` | ✅ OK | 200 | 18ms |
| 3 | POST | `/admin/users` | ✅ OK | 201 | 239ms |
| 4 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 11ms |
| 5 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 33ms |
| 6 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 24ms |
| 7 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 34ms |
| 8 | GET | `/admin/roles` | ✅ OK | 200 | 23ms |
| 9 | POST | `/admin/roles` | ✅ OK | 201 | 23ms |
| 10 | GET | `/admin/audit` | ✅ OK | 200 | 16ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 1ms |
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

**Total:** 33 | **Passed:** 33 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers/` | ✅ OK | 201 | 27ms |
| 2 | GET | `/registry/classifiers/pending/` | ✅ OK | 200 | 17ms |
| 3 | GET | `/registry/classifiers/` | ✅ OK | 200 | 10ms |
| 4 | GET | `/registry/classifiers/tree/` | ✅ OK | 200 | 7ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 9ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 14ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 13ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 200 | 27ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 8ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 11ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 200 | 24ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 200 | 15ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 9ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 41ms |
| 2 | GET | `/registry/documents/` | ✅ OK | 200 | 13ms |
| 3 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 9ms |
| 4 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 21ms |
| 5 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 200 | 22ms |
| 6 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 15ms |
| 7 | GET | `/registry/documents/{doc_id}/succession/` | ✅ OK | 200 | 9ms |
| 8 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 16ms |
| 9 | GET | `/registry/documents/export` | ✅ OK | 200 | 14ms |
| 10 | POST | `/registry/documents/import` | ✅ OK | 422 | 7ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology/` | ✅ OK | 201 | 16ms |
| 2 | GET | `/registry/terminology/` | ✅ OK | 200 | 11ms |
| 3 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 10ms |
| 4 | GET | `/registry/terminology/normalize/` | ✅ OK | 200 | 7ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 14ms |
| 6 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 13ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 422 | 7ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 27ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 11ms |
</details>

---

### converter-validator

**Converter-Validator Service** (port 8086)

**Ping:** ✅ Alive

> ⚠️ ⚠️ Converter health на /health, а не /api/v1/health — сервис без префикса.

> ⚠️ ⚠️ task_id/version_id передаём как str — сервис требует str, docs API — int.

> ⚠️ ⚠️ document_id/validation_id принимаем как str — сервис возвращает UUID, docs — int.

**Total:** 4 | **Passed:** 4 | **Failed:** 0 | **Skipped:** 0

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
| 1 | POST | `/converter/preview/metadata` | ✅ OK | 200 | 12ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 84ms |
</details>

<details>
<summary><b>VALIDATE</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/document` | ✅ OK | 200 | 42ms |
</details>

---

### parser

**Parser Service** (port 8087)

**Ping:** ✅ Alive

> ⚠️ ⚠️ Реальная реализация расходится с docs: process требует version_id (docs: mode+file_key).

> ⚠️ ⚠️ Health Parser на /health, а не /api/v1/health — сервис не использует префикс.

**Total:** 5 | **Passed:** 4 | **Failed:** <span style="color:red;font-weight:bold">1</span> | **Skipped:** 0

<details>
<summary><b>PARSER</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/parser/process` | ✅ OK | 202 | 50ms |
| 2 | POST | `/parser/process` | ✅ OK | 202 | 5ms |
| 3 | GET | `/parser/process/{task_id}/status` | ✅ OK | 200 | 60ms |
| 4 | GET | `/parser/process/{task_id}/result` | ❌ Error: HTTP 500 | 500 | 14ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 3ms |
</details>

---

### orchestrator

**Orchestrator Service** (port 8081)

**Ping:** ✅ Alive

**Total:** 32 | **Passed:** 32 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 239ms |
</details>

<details>
<summary><b>DRAFTS</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts/` | ✅ OK | 202 | 431ms |
| 2 | POST | `/drafts/` | ✅ OK | 202 | 21ms |
| 3 | GET | `/drafts/` | ✅ OK | 200 | 5ms |
| 4 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 4ms |
| 5 | DELETE | `/drafts/{draft_id}` | ✅ OK | 204 | 4ms |
| 6 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 422 | 6ms |
| 7 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 6ms |
| 8 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 404 | 7ms |
| 9 | GET | `/drafts/{draft_id}/preview/status` | ✅ OK | 404 | 6ms |
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
| 1 | GET | `/monitor/metrics` | ✅ OK | 200 | 12ms |
</details>

<details>
<summary><b>TASKS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/{task_id}/status` | ✅ OK | 200 | 17ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (17 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents/` | ✅ OK | 200 | 12ms |
| 2 | GET | `/documents/queue` | ✅ OK | 200 | 5ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 5ms |
| 4 | DELETE | `/documents/{doc_id}` | ✅ OK | 200 | 5ms |
| 5 | GET | `/documents/{doc_id}/status` | ✅ OK | 200 | 5ms |
| 6 | GET | `/documents/{doc_id}/file` | ✅ OK | 200 | 4ms |
| 7 | GET | `/documents/{doc_id}/history` | ✅ OK | 200 | 5ms |
| 8 | GET | `/documents/{doc_id}/errors` | ✅ OK | 200 | 6ms |
| 9 | GET | `/documents/{doc_id}/versions` | ✅ OK | 200 | 6ms |
| 10 | POST | `/documents/{doc_id}/versions` | ✅ OK | 422 | 5ms |
| 11 | POST | `/documents/{doc_id}/approve` | ✅ OK | 202 | 6ms |
| 12 | POST | `/documents/{doc_id}/reprocess` | ✅ OK; ⚠️ Поле 'task_id' ожидалось int, получен str = task-repro-549b166d | 202 | 5ms |
| 13 | GET | `/documents/{doc_id}/pages` | ✅ OK | 200 | 4ms |
| 14 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 200 | 4ms |
| 15 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 200 | 4ms |
| 16 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 200 | 6ms |
| 17 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>SEARCH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/documents/search` | ✅ OK | 200 | 12ms |
| 2 | GET | `/documents/search` | ✅ OK | 200 | 3ms |
</details>

---

### query

**Query Service** (port 8083)

**Ping:** ✅ Alive

> ⚠️ ⚠️ POST /chat/feedback: docs требует rating:int + rating_status:string, но сервис принимает только rating:string (без rating_status). Docs новее реализации.

**Total:** 20 | **Passed:** 20 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>CHAT</b> (16 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ✅ OK | 201 | 34ms |
| 2 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 20ms |
| 3 | POST | `/chat/sessions` | ✅ OK | 201 | 7ms |
| 4 | GET | `/chat/sessions` | ✅ OK | 200 | 16ms |
| 5 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 8ms |
| 6 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 200 | 11ms |
| 7 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 202 | 12ms |
| 8 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 200 | 14ms |
| 9 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 8ms |
| 10 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 200 | 8ms |
| 11 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 200 | 5ms |
| 12 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 200 | 10ms |
| 13 | POST | `/chat/feedback` | ✅ OK | 200 | 11ms |
| 14 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 200 | 18ms |
| 15 | GET | `/chat/history` | ✅ OK | 200 | 11ms |
| 16 | GET | `/chat/history/export` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 36ms |
| 2 | GET | `/system/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 8ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 3ms |
</details>

---

### rag-builder

**RAG Builder Service** (port 8090)

**Ping:** ✅ Alive

> ⚠️ ⚠️ Документация не упоминает JWT, но RAG Builder требует bearer token. Исправлено: supervisord передаёт JWT_SECRET (RAG Builder) = JWT_SECRET_KEY (Auth).

> ⚠️ ⚠️ RAG Builder принимает document_id только как UUID (pydantic: uuid_type). int_to_uuid() конвертирует BIGINT в UUID строку.

> ⚠️ ⚠️ RAG Search падает с `operator does not exist: bigint = uuid` — внутренний SQL JOIN между registry.documents (BIGINT) и rag.document_chunks (UUID). НЕ связан с форматом входных данных.

> ⚠️ ⚠️ RAG Builder падал при старте: alembic migration 20260614_0002 не применилась — FK document_id UUID vs registry.documents.id BIGINT. Migration пропущена, таблица создана вручную с BIGINT document_id.

> ⚠️ ⚠️ Подключена заглушка docker/patch_rag_tables.py — при full-report/coverage/patch-rag проверяет и создаёт таблицы, если их нет.

**Total:** 7 | **Passed:** 7 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 232ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents/` | ✅ OK | 201 | 13ms |
</details>

<details>
<summary><b>RAG</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ✅ OK | 201 | 36ms |
| 2 | POST | `/rag/build` | ✅ OK | 201 | 11ms |
| 3 | DELETE | `/rag/build/{doc_id_uuid}` | ✅ OK | 200 | 11ms |
| 4 | GET | `/rag/build/{doc_id_uuid}/status` | ✅ OK | 200 | 6ms |
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
| 1 | GET | `/health` | ✅ OK | 200 | 3ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ✅ OK | 200 | 651ms |
</details>

---

### gateway

**Gateway Service** (port 8080)

**Ping:** ✅ Alive

> ⚠️ Gateway — отдельный mock-сервис, тестируется независимо от других сервисов.

> ⚠️ Эндпоинты и prepare определены строго по openapi.json mock'а.

**Total:** 120 | **Passed:** 120 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (7 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 12ms |
| 2 | GET | `/auth/me` | ✅ OK | 200 | 5ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 3ms |
| 4 | GET | `/auth/me` | ✅ OK | 200 | 3ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 5ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 5ms |
| 7 | POST | `/internal/auth/validate` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>CHAT</b> (22 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/chat/sessions` | ✅ OK | 201 | 9ms |
| 2 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 6ms |
| 3 | POST | `/chat/projects` | ✅ OK | 201 | 8ms |
| 4 | POST | `/chat/sessions` | ✅ OK | 201 | 6ms |
| 5 | GET | `/chat/sessions` | ✅ OK | 200 | 5ms |
| 6 | GET | `/chat/sessions/{session_id}` | ✅ OK | 200 | 5ms |
| 7 | PUT | `/chat/sessions/{session_id}` | ✅ OK | 200 | 5ms |
| 8 | GET | `/chat/history` | ✅ OK | 200 | 4ms |
| 9 | GET | `/chat/history/export` | ✅ OK | 200 | 4ms |
| 10 | POST | `/chat/projects` | ✅ OK | 201 | 3ms |
| 11 | GET | `/chat/projects` | ✅ OK | 200 | 4ms |
| 12 | GET | `/chat/projects/{project_id}` | ✅ OK | 200 | 5ms |
| 13 | PUT | `/chat/projects/{project_id}` | ✅ OK | 200 | 8ms |
| 14 | POST | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 5ms |
| 15 | GET | `/chat/sessions/{session_id}/messages` | ✅ OK | 200 | 5ms |
| 16 | GET | `/chat/sessions/{session_id}/messages/last` | ✅ OK | 200 | 5ms |
| 17 | GET | `/chat/sessions/{session_id}/messages/{message_id}` | ✅ OK | 200 | 4ms |
| 18 | POST | `/chat/sessions/{session_id}/context` | ✅ OK | 200 | 7ms |
| 19 | POST | `/chat/sessions/{session_id}/export` | ✅ OK | 200 | 8ms |
| 20 | POST | `/chat/feedback` | ✅ OK | 200 | 5ms |
| 21 | DELETE | `/chat/sessions/{session_id}` | ✅ OK | 200 | 5ms |
| 22 | DELETE | `/chat/projects/{project_id}` | ✅ OK | 204 | 7ms |
</details>

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers` | ✅ OK | 201 | 10ms |
| 2 | GET | `/registry/classifiers` | ✅ OK | 200 | 8ms |
| 3 | POST | `/registry/classifiers` | ✅ OK | 409 | 5ms |
| 4 | GET | `/registry/classifiers/tree` | ✅ OK | 200 | 5ms |
| 5 | GET | `/registry/classifiers/{code}` | ✅ OK | 200 | 4ms |
| 6 | PUT | `/registry/classifiers/{code}` | ✅ OK | 200 | 6ms |
| 7 | PATCH | `/registry/classifiers/{code}` | ✅ OK | 200 | 8ms |
| 8 | POST | `/registry/classifiers/import` | ✅ OK | 200 | 7ms |
| 9 | GET | `/registry/classifiers/quarantine` | ✅ OK | 200 | 4ms |
| 10 | POST | `/registry/classifiers/quarantine/{pending_id}/accept` | ✅ OK | 200 | 5ms |
| 11 | POST | `/registry/classifiers/quarantine/{pending_id}/reject` | ✅ OK | 200 | 6ms |
| 12 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 8ms |
| 13 | DELETE | `/registry/classifiers/{code}` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>REGISTRY_DOCUMENTS</b> (20 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents` | ✅ OK | 201 | 5ms |
| 2 | POST | `/registry/drafts` | ✅ OK | 201 | 5ms |
| 3 | GET | `/registry/documents` | ✅ OK | 200 | 5ms |
| 4 | POST | `/registry/documents` | ✅ OK | 201 | 4ms |
| 5 | GET | `/registry/documents/{doc_id}` | ✅ OK | 200 | 4ms |
| 6 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 200 | 5ms |
| 7 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 200 | 5ms |
| 8 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 200 | 4ms |
| 9 | GET | `/registry/documents/{doc_id}/succession` | ✅ OK | 200 | 4ms |
| 10 | GET | `/registry/documents/{doc_id}/sections` | ✅ OK | 200 | 4ms |
| 11 | GET | `/registry/documents/export` | ✅ OK | 200 | 4ms |
| 12 | POST | `/registry/documents/import` | ✅ OK | 200 | 5ms |
| 13 | POST | `/registry/documents/check-uniqueness` | ✅ OK | 200 | 5ms |
| 14 | POST | `/registry/drafts` | ✅ OK | 201 | 4ms |
| 15 | GET | `/registry/drafts` | ✅ OK | 200 | 4ms |
| 16 | GET | `/registry/drafts/{reg_draft_id}` | ✅ OK | 200 | 4ms |
| 17 | GET | `/registry/drafts/{reg_draft_id}/preview` | ✅ OK | 200 | 5ms |
| 18 | PATCH | `/registry/drafts/{reg_draft_id}/status` | ✅ OK | 200 | 5ms |
| 19 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 200 | 6ms |
| 20 | DELETE | `/registry/drafts/{reg_draft_id}` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology` | ✅ OK | 201 | 6ms |
| 2 | GET | `/registry/terminology` | ✅ OK | 200 | 5ms |
| 3 | POST | `/registry/terminology` | ✅ OK | 201 | 3ms |
| 4 | GET | `/registry/terminology/{term_id}` | ✅ OK | 200 | 4ms |
| 5 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 200 | 5ms |
| 6 | GET | `/registry/terminology/normalize` | ✅ OK | 200 | 5ms |
| 7 | POST | `/registry/terminology/import` | ✅ OK | 200 | 9ms |
| 8 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>CATEGORIES</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/categories` | ✅ OK | 201 | 5ms |
| 2 | GET | `/registry/categories` | ✅ OK | 200 | 4ms |
| 3 | POST | `/registry/categories` | ✅ OK | 201 | 4ms |
| 4 | GET | `/registry/categories/{category_id}` | ✅ OK | 200 | 6ms |
| 5 | PUT | `/registry/categories/{category_id}` | ✅ OK | 200 | 7ms |
| 6 | DELETE | `/registry/categories/{category_id}` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>ADMIN</b> (10 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/admin/users` | ✅ OK | 201 | 6ms |
| 2 | GET | `/admin/users` | ✅ OK | 200 | 6ms |
| 3 | POST | `/admin/users` | ✅ OK | 201 | 5ms |
| 4 | GET | `/admin/users/{user_id}` | ✅ OK | 200 | 5ms |
| 5 | PUT | `/admin/users/{user_id}` | ✅ OK | 200 | 5ms |
| 6 | PATCH | `/admin/users/{user_id}` | ✅ OK | 200 | 5ms |
| 7 | GET | `/admin/roles` | ✅ OK | 200 | 4ms |
| 8 | POST | `/admin/roles` | ✅ OK | 201 | 8ms |
| 9 | GET | `/admin/audit` | ✅ OK | 200 | 6ms |
| 10 | DELETE | `/admin/users/{user_id}` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>DRAFTS</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/drafts` | ✅ OK | 202 | 11ms |
| 2 | POST | `/drafts` | ✅ OK | 202 | 5ms |
| 3 | GET | `/drafts` | ✅ OK | 200 | 7ms |
| 4 | GET | `/drafts/{draft_id}` | ✅ OK | 200 | 5ms |
| 5 | PATCH | `/drafts/{draft_id}/decide` | ✅ OK | 409 | 7ms |
| 6 | GET | `/drafts/{draft_id}/preview` | ✅ OK | 200 | 5ms |
| 7 | POST | `/drafts/{draft_id}/preview` | ✅ OK | 202 | 5ms |
| 8 | GET | `/drafts/{draft_id}/preview/status` | ✅ OK | 200 | 4ms |
| 9 | DELETE | `/drafts/{draft_id}` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>HEALTH</b> (3 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 3ms |
| 2 | GET | `/monitor/health` | ✅ OK | 200 | 4ms |
| 3 | GET | `/monitor/metrics` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (17 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/documents` | ✅ OK | 200 | 7ms |
| 2 | GET | `/documents/queue` | ✅ OK | 200 | 5ms |
| 3 | GET | `/documents/{doc_id}` | ✅ OK | 200 | 5ms |
| 4 | GET | `/documents/{doc_id}/status` | ✅ OK | 200 | 5ms |
| 5 | GET | `/documents/{doc_id}/file` | ✅ OK | 200 | 4ms |
| 6 | GET | `/documents/{doc_id}/history` | ✅ OK | 200 | 4ms |
| 7 | GET | `/documents/{doc_id}/errors` | ✅ OK | 200 | 4ms |
| 8 | GET | `/documents/{doc_id}/versions` | ✅ OK | 200 | 4ms |
| 9 | POST | `/documents/{doc_id}/versions` | ✅ OK | 202 | 8ms |
| 10 | POST | `/documents/{doc_id}/approve` | ✅ OK | 202 | 6ms |
| 11 | POST | `/documents/{doc_id}/reprocess` | ✅ OK | 202 | 5ms |
| 12 | GET | `/documents/{doc_id}/pages` | ✅ OK | 200 | 5ms |
| 13 | GET | `/documents/{doc_id}/pages/{page_num}` | ✅ OK | 200 | 4ms |
| 14 | GET | `/documents/{doc_id}/pages/{page_num}/text` | ✅ OK | 200 | 4ms |
| 15 | GET | `/documents/{doc_id}/pages/{page_num}/preview` | ✅ OK | 200 | 4ms |
| 16 | GET | `/documents/{doc_id}/parameters` | ✅ OK | 200 | 4ms |
| 17 | DELETE | `/documents/{doc_id}` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>TASKS</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/tasks/{task_id}/status` | ✅ OK | 200 | 5ms |
</details>

<details>
<summary><b>TEXT</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/text/search` | ✅ OK | 200 | 5ms |
| 2 | POST | `/text/ask` | ✅ OK | 200 | 7ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/common/stats` | ✅ OK | 200 | 5ms |
| 2 | GET | `/registry/common/enums` | ✅ OK | 200 | 5ms |
</details>

---

### tei

**TEI (Embeddings)** (port 8092)

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
| 1 | POST | `/embed` | ✅ OK | 200 | 14ms |
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

_Report generated by `api_coverage_test.py` at 2026-06-15 19:31:11 UTC_
