# Plan of work

1. **auth_routes.py** — POST /auth/revoke
   - Add `token: str = ""` to `RevokeRequest`
   - Use `req.refresh_token or req.token` in `revoke`

2. **registry_routes.py** — Import endpoints (classifiers, documents, terminology)
   - Add `Union` import
   - POST /classifiers/import: accept `Union[List[ClassifierCreate], dict]`, extract from `data`/`classifiers` keys
   - POST /documents/import: accept `Union[List[RegistryDocCreate], dict]`, extract from `data`/`documents` keys
   - POST /terminology/import: accept `Union[List[TermCreate], dict]`, extract from `data`/`terms` keys

3. **orch_routes.py** — PATCH /drafts/{id}/decide
   - Add `decision: str = ""` to `DecideRequest`
   - Use `req.action or req.decision` in `decide_draft`

4. **orch_routes.py** — POST /documents/{id}/versions
   - Accept JSON body with `file_key` or multipart with UploadFile

5. **orch_routes.py** — GET /drafts
   - Make `document_key` optional with default `""`
   - If empty, return all drafts

6. **orch_routes.py** — GET /documents/search
   - Make `q` optional with default `""`
   - Handle empty `q` with empty results

7. **orch_routes.py** — POST /drafts
   - Accept `title`, `doc_code`, `source_type` from JSON body directly

✅ All 7 changes implemented.
✅ 453 tests passed.

Note on #7: `create_draft` JSON branch already accepted `title`, `doc_code`, `source_type` from body — no change needed.

Test updates:
- `test_gateway_fails.py`: updated `test_revoke_missing_token` and `test_search_without_q` (behaviour changed from 422→200)
- `test_tz_coverage.py`: updated `test_search_without_query` and `test_list_drafts_requires_document_key` (behaviour changed from 422→200)
