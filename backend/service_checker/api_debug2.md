# API Coverage Report

**Generated:** 2026-06-10 08:34:37 UTC

**Mode:** 🔬 Real (Docker)

**Based on:** `docs/api/*.md`

---

## 📊 Summary

| Service | Port | Ping | Endpoints | ✅ Passed | ❌ Failed | ⏭️ Skipped | Status |
|---------|:----:|:----:|:---------:|:---------:|:---------:|:----------:|:------:|
| [Auth Service](#auth) | 8082 | ✅ | 18 | 18 | 0 | 0 | ✅ |
| [Registry Service](#registry) | 8084 | ✅ | 35 | 30 | <span style="color:red;font-weight:bold">5</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |
| **Total** | | **2/2** | **53** | **48** | <span style="color:red;font-weight:bold">5</span> | 0 | <span style="color:red;font-weight:bold">❌</span> |

## 🔍 Details by Service

### auth

**Auth Service** (port 8082)

**Ping:** ✅ Alive

**Total:** 18 | **Passed:** 18 | **Failed:** 0 | **Skipped:** 0

<details>
<summary><b>AUTH</b> (6 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/auth/token` | ✅ OK | 401 | 4ms |
| 2 | GET | `/auth/me` | ✅ OK | 404 | 3ms |
| 3 | POST | `/auth/token` | ✅ OK | 401 | 4ms |
| 4 | GET | `/auth/me` | ✅ OK | 404 | 1ms |
| 5 | POST | `/auth/refresh` | ✅ OK | 401 | 3ms |
| 6 | POST | `/auth/revoke` | ✅ OK | 401 | 5ms |
</details>

<details>
<summary><b>HEALTH</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 404 | 2ms |
| 2 | GET | `/system/health` | ✅ OK | 404 | 1ms |
</details>

<details>
<summary><b>ADMIN</b> (9 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/admin/users` | ✅ OK | 404 | 2ms |
| 2 | POST | `/admin/users` | ✅ OK | 404 | 1ms |
| 3 | GET | `/admin/users/{user_id}` | ✅ OK | 404 | 1ms |
| 4 | PUT | `/admin/users/{user_id}` | ✅ OK | 404 | 2ms |
| 5 | PATCH | `/admin/users/{user_id}` | ✅ OK | 404 | 2ms |
| 6 | DELETE | `/admin/users/{user_id}` | ✅ OK | 404 | 1ms |
| 7 | GET | `/admin/roles` | ✅ OK | 404 | 1ms |
| 8 | POST | `/admin/roles` | ✅ OK | 404 | 1ms |
| 9 | GET | `/admin/audit` | ✅ OK | 404 | 1ms |
</details>

<details>
<summary><b>INTERNAL</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/internal/auth/validate` | ✅ OK | 404 | 1ms |
</details>

---

### registry

**Registry Service** (port 8084)

**Ping:** ✅ Alive

**Total:** 35 | **Passed:** 30 | **Failed:** <span style="color:red;font-weight:bold">5</span> | **Skipped:** 0

<details>
<summary><b>CLASSIFIERS</b> (13 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/classifiers` | ✅ OK | 307 | 1ms |
| 2 | POST | `/registry/classifiers` | ✅ OK | 307 | 1ms |
| 3 | GET | `/registry/classifiers` | ✅ OK | 307 | 1ms |
| 4 | GET | `/registry/classifiers/tree` | ✅ OK | 422 | 1ms |
| 5 | GET | `/registry/classifiers/{classifier_code}` | ✅ OK | 422 | 2ms |
| 6 | PUT | `/registry/classifiers/{classifier_code}` | ✅ OK | 422 | 2ms |
| 7 | PATCH | `/registry/classifiers/{classifier_code}` | ✅ OK | 422 | 4ms |
| 8 | DELETE | `/registry/classifiers/{classifier_code}` | ✅ OK | 422 | 3ms |
| 9 | POST | `/registry/classifiers/import` | ✅ OK | 422 | 3ms |
| 10 | GET | `/registry/classifiers/pending` | ❌ Error: HTTP 500 | 500 | 5ms |
| 11 | POST | `/registry/classifiers/pending/{pending_id}/accept` | ✅ OK | 404 | 6ms |
| 12 | POST | `/registry/classifiers/pending/{pending_id}/reject` | ✅ OK | 404 | 5ms |
| 13 | POST | `/registry/classifiers/validate` | ❌ Error: HTTP 500 | 500 | 7ms |
</details>

<details>
<summary><b>DOCUMENTS</b> (11 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/documents` | ✅ OK | 307 | 1ms |
| 2 | POST | `/registry/documents` | ✅ OK | 307 | 1ms |
| 3 | GET | `/registry/documents` | ✅ OK | 307 | 1ms |
| 4 | GET | `/registry/documents/{doc_id}` | ✅ OK | 404 | 3ms |
| 5 | PUT | `/registry/documents/{doc_id}` | ✅ OK | 404 | 7ms |
| 6 | PATCH | `/registry/documents/{doc_id}/status` | ✅ OK | 404 | 6ms |
| 7 | GET | `/registry/documents/{doc_id}/history` | ✅ OK | 404 | 4ms |
| 8 | GET | `/registry/documents/{doc_id}/succession` | ✅ OK | 404 | 4ms |
| 9 | DELETE | `/registry/documents/{doc_id}` | ✅ OK | 404 | 5ms |
| 10 | GET | `/registry/documents/export` | ❌ Error: HTTP 500 | 500 | 5ms |
| 11 | POST | `/registry/documents/import` | ✅ OK | 422 | 3ms |
</details>

<details>
<summary><b>TERMINOLOGY</b> (8 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | POST | `/registry/terminology` | ✅ OK | 307 | 1ms |
| 2 | POST | `/registry/terminology` | ✅ OK | 307 | 1ms |
| 3 | GET | `/registry/terminology` | ✅ OK | 307 | 1ms |
| 4 | GET | `/registry/terminology/{term_id}` | ✅ OK | 404 | 3ms |
| 5 | GET | `/registry/terminology/normalize` | ❌ Error: HTTP 500 | 500 | 5ms |
| 6 | PUT | `/registry/terminology/{term_id}` | ✅ OK | 404 | 3ms |
| 7 | DELETE | `/registry/terminology/{term_id}` | ✅ OK | 404 | 3ms |
| 8 | POST | `/registry/terminology/import` | ✅ OK | 422 | 1ms |
</details>

<details>
<summary><b>HEALTH</b> (1 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/health` | ✅ OK | 200 | 2ms |
</details>

<details>
<summary><b>COMMON</b> (2 эндпоинтов)</summary>

| # | Method | Path | Status | Code | Time |
|---|--------|------|--------|:----:|:----:|
| 1 | GET | `/registry/stats` | ✅ OK | 200 | 7ms |
| 2 | GET | `/registry/enums` | ❌ Error: HTTP 500 | 500 | 4ms |
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

_Report generated by `api_coverage_test.py` at 2026-06-10 08:34:37 UTC_
