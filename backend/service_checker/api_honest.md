# API Coverage Report

**Generated:** 2026-06-10 09:12:01 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Ping | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 8082 | ✅ | 18 | 4 | <span style="color:red;font-weight:bold">14</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [Registry Service](#registry) | 8084 | ✅ | 35 | 14 | <span style="color:red;font-weight:bold">21</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [Converter-Validator Service](#converter-validator) | 8086 | ✅ | 4 | 3 | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [RAG Builder Service](#rag-builder) | 8090 | ✅ | 5 | 0 | <span style="color:red;font-weight:bold">5</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| [RAG Search Service](#rag-search) | 8091 | ✅ | 2 | 1 | <span style="color:red;font-weight:bold">1</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| **Total** | | **5/5** | **64** | **22** | <span style="color:red;font-weight:bold">42</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |

## 🔍 Details by Service

### auth

**Auth Service** (port 8082)

**Ping:** ✅ Alive

**Total:** 18 | **Passed:** 4 | **Failed:** <span style="color:red;font-weight:bold">14</span> | **Skipped:** 0

<details>
<summary><b>AUTH</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 200 | 245ms |
| 2 | GET | `/auth/me` | ❌ Error: HTTP 404 | 404 | 2ms |
| 3 | POST | `/auth/token` | ✅ OK | 200 | 237ms |
| 4 | GET | `/auth/me` | ❌ Error: HTTP 404 | 404 | 2ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 200 | 12ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 200 | 17ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ❌ Error: HTTP 404 | 404 | 1ms |
| 2 | GET | `/system/health` | ❌ Error: HTTP 404 | 404 | 1ms |
</details>

<details>
<summary><b>ADMIN</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/admin/users` | ❌ Error: HTTP 404 | 404 | 3ms |
| 2 | POST | `/admin/users` | ❌ Error: HTTP 404 | 404 | 2ms |
| 3 | GET | `/admin/users/{user_id}` | ❌ Error: HTTP 404 | 404 | 2ms |
| 4 | PUT | `/admin/users/{user_id}` | ❌ Error: HTTP 404 | 404 | 1ms |
| 5 | PATCH | `/admin/users/{user_id}` | ❌ Error: HTTP 404 | 404 | 1ms |
| 6 | DELETE | `/admin/users/{user_id}` | ❌ Error: HTTP 404 | 404 | 1ms |
| 7 | GET | `/admin/roles` | ❌ Error: HTTP 404 | 404 | 1ms |
| 8 | POST | `/admin/roles` | ❌ Error: HTTP 404 | 404 | 1ms |
| 9 | GET | `/admin/audit` | ❌ Error: HTTP 404 | 404 | 1ms |
</details>

<details>
<summary><b>INTERNAL</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/internal/auth/validate` | ❌ Error: HTTP 404 | 404 | 1ms |
</details>

---

### registry

**Registry Service** (port 8084)

**Ping:** ✅ Alive

**Total:** 35 | **Passed:** 14 | **Failed:** <span style="color:red;font-weight:bold">21</span> | **Skipped:** 0

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers` | ✅ OK | 307 | 3ms |
| 2 | POST | `/registry/classifiers` | ✅ OK | 307 | 1ms |
| 3 | GET | `/registry/classifiers` | ✅ OK | 307 | 1ms |
| 4 | GET | `/registry/classifiers/tree` | ❌ Error: HTTP 422 | 422 | 5ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ❌ Error: HTTP 422 | 422 | 8ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ❌ Error: HTTP 422 | 422 | 5ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ❌ Error: HTTP 422 | 422 | 6ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ❌ Error: HTTP 422 | 422 | 5ms |
| 9 | POST | `/registry/classifiers/import` | ❌ Error: HTTP 422 | 422 | 5ms |
| 10 | GET | `/registry/classifiers/pending` | ✅ OK | 200 | 5ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ❌ Error: HTTP 404 | 404 | 6ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ❌ Error: HTTP 404 | 404 | 7ms |
| 13 | POST | `/registry/classifiers/validate` | ✅ OK | 200 | 6ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents` | ✅ OK | 307 | 2ms |
| 2 | POST | `/registry/documents` | ✅ OK | 307 | 1ms |
| 3 | GET | `/registry/documents` | ✅ OK | 307 | 1ms |
| 4 | GET | `/registry/documents/{doc_id}` | ❌ Error: HTTP 404 | 404 | 5ms |
| 5 | PUT | `/registry/documents/{doc_id}` | ❌ Error: HTTP 404 | 404 | 7ms |
| 6 | PATCH | `/registry/documents/{doc_id}/status` | ❌ Error: HTTP 404 | 404 | 7ms |
| 7 | GET | `/registry/documents/{doc_id}/history` | ❌ Error: HTTP 404 | 404 | 5ms |
| 8 | GET | `/registry/documents/{doc_id}/succession` | ❌ Error: HTTP 404 | 404 | 6ms |
| 9 | DELETE | `/registry/documents/{doc_id}` | ❌ Error: HTTP 404 | 404 | 10ms |
| 10 | GET | `/registry/documents/export` | ❌ Error: Невалидный JSON: Expecting value: line 1 column 1 (char 0) | 200 | 6ms |
| 11 | POST | `/registry/documents/import` | ❌ Error: HTTP 422 | 422 | 5ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology` | ✅ OK | 307 | 3ms |
| 2 | POST | `/registry/terminology` | ✅ OK | 307 | 1ms |
| 3 | GET | `/registry/terminology` | ✅ OK | 307 | 1ms |
| 4 | GET | `/registry/terminology/{term_id}` | ❌ Error: HTTP 404 | 404 | 7ms |
| 5 | GET | `/registry/terminology/normalize` | ❌ Error: Поле 'raw_term' обязательно, но не найдено в ответе; Поле 'normalized_value' обязательно, но не найдено в ответе | 200 | 7ms |
| 6 | PUT | `/registry/terminology/{term_id}` | ❌ Error: HTTP 404 | 404 | 7ms |
| 7 | DELETE | `/registry/terminology/{term_id}` | ❌ Error: HTTP 404 | 404 | 7ms |
| 8 | POST | `/registry/terminology/import` | ❌ Error: HTTP 422 | 422 | 4ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 8ms |
| 2 | GET | `/registry/enums` | ✅ OK | 200 | 5ms |
</details>

---

### converter-validator

**Converter-Validator Service** (port 8086)

**Ping:** ✅ Alive

**Total:** 4 | **Passed:** 3 | **Failed:** <span style="color:red;font-weight:bold">1</span> | **Skipped:** 0

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ❌ Error: HTTP 404 | 404 | 1ms |
</details>

<details>
<summary><b>CONVERTER</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/converter/preview/metadata` | ✅ OK | 200 | 1ms |
| 2 | POST | `/converter/convert` | ✅ OK | 200 | 52ms |
</details>

<details>
<summary><b>VALIDATE</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/validate/document` | ✅ OK | 200 | 51ms |
</details>

---

### rag-builder

**RAG Builder Service** (port 8090)

**Ping:** ✅ Alive

**Total:** 5 | **Passed:** 0 | **Failed:** <span style="color:red;font-weight:bold">5</span> | **Skipped:** 0

<details>
<summary><b>RAG</b> (4 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/build` | ❌ Error: HTTP 422 | 422 | 4ms |
| 2 | POST | `/rag/build` | ❌ Error: HTTP 422 | 422 | 3ms |
| 3 | DELETE | `/rag/build/{doc_id}` | ❌ Error: HTTP 422 | 422 | 4ms |
| 4 | GET | `/rag/build/{doc_id}/status` | ❌ Error: HTTP 422 | 422 | 3ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ❌ Error: HTTP 404 | 404 | 3ms |
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
| 1 | GET | `/health` | ✅ OK | 200 | 4ms |
</details>

<details>
<summary><b>RAG</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/rag/search` | ❌ Error: HTTP 500 | 500 | 3044ms |
</details>

---

## 🔗 Context Variables

| Variable | Value |
|----------|-------|
| `access_token` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTZkODAzNTY0ZGJlYyIsInJvbGVzIjpbInN5c3RlbV9hZG1pbiJdLCJwZXJtaXNzaW9ucyI6WyJhdWRpdDpyZWFkIiwiZG9jdW1lbnRzOnJlYWQiLCJkb2N1bWVudHM6d3JpdGUiLCJyb2xlczptYW5hZ2UiLCJzZWFyY2giLCJ1c2VyczptYW5hZ2UiXSwiaWF0IjoxNzgxMDgyNzE4LCJleHAiOjE3ODEwODYzMTgsInR5cGUiOiJhY2Nlc3MifQ.ca5irtdsNhPaJTpsVHVQILwMj77TxkMPjUYCuMbuqu0` |
| `refresh_token` | `p0dSNP4Z4Nwa32yNQQqU1E0W3ptRLVOBLluc_xDcXXc9r1G3xn8CqAhF3DwilsT2` |
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

_Report generated by `api_coverage_test.py` at 2026-06-10 09:12:01 UTC_
