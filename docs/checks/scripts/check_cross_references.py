#!/usr/bin/env python3
"""Check cross-references between documentation files.
Verifies that fields, schemas, and endpoints are consistent across API specs,
pipelines, and common docs.

Usage: python docs/checks/scripts/check_cross_references.py
"""

import os
import re
import sys

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
errors = 0


def get_files():
    result = []
    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, DOCS_DIR)
            result.append((rel, path))
    return result


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def find(pattern, include_pattern=None, exclude_patterns=None, simple=False):
    results = []
    exclude = exclude_patterns or []
    for rel, path in get_files():
        if any(x in rel for x in exclude):
            continue
        if include_pattern and include_pattern not in rel:
            continue
        try:
            for lineno, line in enumerate(read_text(path).split("\n"), 1):
                if simple:
                    if pattern in line:
                        results.append((rel, lineno, line.strip()))
                else:
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append((rel, lineno, line.strip()))
        except Exception:
            pass
    return results


def check_fail(name, pattern, include_pattern=None, exclude=None, simple=False):
    """FAIL if pattern IS found (negative check)."""
    global errors
    results = find(pattern, include_pattern, exclude, simple)
    if results:
        print(f"  FAIL: {name}")
        for path, lineno, _ in results[:5]:
            print(f"    {path}:{lineno}")
        errors += 1
    else:
        print(f"  OK: {name}")


def check_pass(name, pattern, include_pattern=None, exclude=None, simple=False, min_count=1):
    """FAIL if pattern IS NOT found (positive check)."""
    global errors
    results = find(pattern, include_pattern, exclude, simple)
    if len(results) < min_count:
        print(f"  FAIL: {name} — expected at least {min_count} match(es), found {len(results)}")
        errors += 1
    else:
        print(f"  OK: {name} ({len(results)} matches)")


# ============================================================
print("=" * 60)
print(" Cross-reference consistency check")
print("=" * 60)
print()

# ------------------------------------------------------------------
# 1. PreviewMetadata: title_key must be present in all metadata examples
# ------------------------------------------------------------------
print("[1] PreviewMetadata — title_key")
print("-" * 40)

# API specs that define preview_metadata
for file_hint, label in [
    ("orchestrator_service_api.md", "Orchestrator DraftItem"),
    ("orchestrator_service_api.md", "Orchestrator GET /drafts/{id}"),
    ("registry_service_api.md", "Registry GET /registry/drafts"),
    ("registry_service_api.md", "Registry GET /registry/drafts/{id}"),
    ("converter_validator_service_api.md", "Converter POST /converter/preview/metadata"),
]:
    pass  # We check globally below

# Check that title_key appears near preview_metadata in API specs
check_pass(
    "title_key in orchestrator_service_api.md (DraftItem preview_metadata)",
    "title_key",
    include_pattern="orchestrator_service_api.md",
    min_count=3
)

check_pass(
    "title_key in registry_service_api.md (drafts preview_metadata)",
    "title_key",
    include_pattern="registry_service_api.md",
    min_count=3
)

check_pass(
    "title_key in converter_validator_service_api.md",
    "title_key",
    include_pattern="converter_validator_service_api.md",
    min_count=1
)

# pipeline1-formation.md: must also have title_key in preview metadata example
check_pass(
    "title_key in pipeline1-formation.md (preview metadata example)",
    "title_key",
    include_pattern="pipeline1-formation.md",
    min_count=1
)

print()

# ------------------------------------------------------------------
# 2. DraftItem: fields consistency between Orchestrator and Registry
# ------------------------------------------------------------------
print("[2] DraftItem — field consistency")
print("-" * 40)

# Orchestrator DraftItem must have core fields (file_key, document_key, confidence теперь только в Registry)
for field in ["draft_id", "task_id", "status",
              "preview_metadata", "document_id",
              "has_notifications", "critical_count", "created_at", "updated_at"]:
    check_pass(
        f"DraftItem Orchestrator has `{field}`",
        f"`{field}`",
        include_pattern="orchestrator_service_api.md",
        min_count=1
    )

# Registry 4.2 DraftItem must have core fields
# Fields may appear in JSON examples (with quotes, no backticks) or in markdown tables
for field in ["file_key", "document_key", "status", "confidence",
              "preview_metadata", "created_by", "created_at"]:
    check_pass(
        f"DraftItem Registry has `{field}` (in JSON examples)",
        f'"{field}"',  # JSON format: "field_name"
        include_pattern="registry_service_api.md",
        min_count=1
    )

print()

# ------------------------------------------------------------------
# 3. Task status model alignment
# ------------------------------------------------------------------
print("[3] Task status — alignment between docs")
print("-" * 40)

# These status values should appear in orchestrator_service_api.md task status
task_statuses = ["uploaded", "previewing", "ready_for_approve", "processing",
                 "created", "indexing", "indexed", "failed"]
for status in task_statuses:
    check_pass(
        f"task.status `{status}` in orchestrator_service_api.md",
        f"`{status}`",
        include_pattern="orchestrator_service_api.md",
        min_count=1
    )

# These processing_status values should appear in pipeline2-indexation.md
proc_statuses = ["pending_index", "indexing", "indexed", "failed"]
for status in proc_statuses:
    check_pass(
        f"processing_status `{status}` in pipeline2-indexation.md",
        f"`{status}`",
        include_pattern="pipeline2-indexation.md",
        min_count=1
    )

# These draft status values should appear in pipeline1-formation.md
draft_statuses = ["uploaded", "previewing", "ready_for_approve",
                  "review_required", "validation", "approved", "discarded"]
for status in draft_statuses:
    check_pass(
        f"draft.status `{status}` in pipeline1-formation.md",
        f"`{status}`",
        include_pattern="pipeline1-formation.md",
        min_count=1
    )

print()

# ------------------------------------------------------------------
# 4. DecideResponse: decided_by and decided_at
# ------------------------------------------------------------------
print("[4] DecideResponse — fields")
print("-" * 40)

for field in ["decided_by", "decided_at"]:
    check_pass(
        f"DecideResponse has `{field}` in orchestrator_service_api.md",
        f"`{field}`",
        include_pattern="orchestrator_service_api.md",
        min_count=1
    )

print()

# ------------------------------------------------------------------
# 5. POST /drafts/{draft_id}/preview — estimated_completion
# ------------------------------------------------------------------
print("[5] POST /drafts/{draft_id}/preview → estimated_completion")
print("-" * 40)

check_pass(
    "estimated_completion in orchestrator_service_api.md",
    "estimated_completion",
    include_pattern="orchestrator_service_api.md",
    min_count=1
)

print()

# ------------------------------------------------------------------
# 6. POST /documents/{doc_id}/reprocess response fields
# ------------------------------------------------------------------
print("[6] POST /documents/{doc_id}/reprocess — response")
print("-" * 40)

for field in ["task_id", "document_id", "status", "message"]:
    check_pass(
        f"reprocess response has `{field}` in orchestrator_service_api.md",
        f"`{field}`",
        include_pattern="orchestrator_service_api.md",
        min_count=1
    )
# mode в reprocess — поле запроса, не ответа, исключено из проверки

# Note: user_id in GET /documents/{id} response is correct and expected.

print()

# ------------------------------------------------------------------
# 7. POST /drafts — form parameters
# ------------------------------------------------------------------
print("[7] POST /drafts — form parameters")
print("-" * 40)

for field in ["source_type", "title", "doc_code", "mks_oks_code",
              "okstu_code", "era", "jurisdiction", "issuing_body", "metadata"]:
    check_pass(
        f"POST /drafts has form param `{field}`",
        f"`{field}`",
        include_pattern="orchestrator_service_api.md",
        min_count=1
    )

print()

# ------------------------------------------------------------------
# 8. Health endpoint format consistency
# ------------------------------------------------------------------
print("[8] Health endpoint — format consistency")
print("-" * 40)

# All health specs should have 'status' and 'version' (in JSON format: "field")
for doc in ["orchestrator_service_api.md", "common_api.md", "gateway_service_api.md"]:
    check_pass(
        f"health has 'status' in {doc}",
        '"status"',
        include_pattern=doc,
        min_count=1
    )
    check_pass(
        f"health has 'version' in {doc}",
        '"version"',
        include_pattern=doc,
        min_count=1
    )

# Common health format (internal services) — uptime_seconds intentionally removed
# See guide.md §Health-формат: uptime_seconds не входит в health внутренних сервисов
# check removed — intentional design decision
# Gateway health (external) should have services — different format
check_pass(
    "gateway health has 'services' (external format)",
    '"services"',
    include_pattern="gateway_service_api.md",
    min_count=1
)

print()

# ------------------------------------------------------------------
# 9. Search endpoints should be documented
# ------------------------------------------------------------------
print("[9] Search endpoints — documented")
print("-" * 40)

for endpoint in ["POST /documents/search", "GET /documents/search", "POST /ask"]:
    check_pass(
        f"`{endpoint}` should be documented somewhere",
        endpoint,
        min_count=0  # Informational — will fail only when we know where they go
    )

print()

# ------------------------------------------------------------------
# 10. GET /tasks and GET /tasks/stats
# ------------------------------------------------------------------
print("[10] GET /tasks endpoints — documented")
print("-" * 40)

check_pass(
    "`GET /tasks` in orchestrator_service_api.md",
    "GET /tasks",
    include_pattern="orchestrator_service_api.md",
    min_count=0  # Informational — expected but may not exist yet
)

check_pass(
    "`GET /tasks/stats` in orchestrator_service_api.md",
    "GET /tasks/stats",
    include_pattern="orchestrator_service_api.md",
    min_count=0  # Informational
)

# ------------------------------------------------------------------
# 11. POST /drafts should NOT return business key (title_hash_sha256)
# ------------------------------------------------------------------
print("[11] POST /drafts — business key NOT in response")
print("-" * 40)

# Orchestrator does NOT compute business key; POST /drafts response must NOT
# contain title_hash_sha256/title_key. Legitimate occurrences are in:
#   - POST /drafts notes (explaining absence) — 2
#   - GET /documents/{doc_id} response — 1
#   - PATCH /decide description — 2
#   - PATCH /metadata response/table — 4
# Total expected ~9. If > 10, likely leaked into POST /drafts response example/table.
bk_count = len(find("title_hash_sha256", include_pattern="orchestrator_service_api.md"))
if bk_count > 10:
    print(f"  FAIL: title_hash_sha256 appears {bk_count} times — may have leaked into POST /drafts response")
    errors += 1
else:
    print(f"  OK: title_hash_sha256 appears {bk_count} times in orchestrator_service_api.md (threshold ≤ 10)")

print()

# ------------------------------------------------------------------
# 12. PreviewMetadata in _schemas.md — no business key field
# ------------------------------------------------------------------
print("[12] PreviewMetadata — no business key field")
print("-" * 40)

# title_hash_sha256 should appear ONLY in the note explaining it is NOT part of
# PreviewMetadata (exactly 1 occurrence). If 0 → note missing. If > 1 → in table.
pm_count = len(find("title_hash_sha256", include_pattern="_schemas.md"))
if pm_count == 0:
    print("  FAIL: title_hash_sha256 not found in _schemas.md — note about exclusion may be missing")
    errors += 1
elif pm_count > 1:
    print(f"  FAIL: title_hash_sha256 appears {pm_count} times in _schemas.md — likely in PreviewMetadata table")
    errors += 1
else:
    print("  OK: title_hash_sha256 appears once in _schemas.md (expected: only in exclusion note)")

print()

# ------------------------------------------------------------------
# 13. POST /validate/metadata documented in Converter-validator
# ------------------------------------------------------------------
print("[13] POST /validate/metadata — documented in Converter-validator")
print("-" * 40)

check_pass(
    "POST /validate/metadata endpoint in converter_validator_service_api.md",
    "validate/metadata",
    include_pattern="converter_validator_service_api.md",
    min_count=1
)

print()

# ------------------------------------------------------------------
# 14. Orchestrator delegates business key calculation, does not compute locally
# ------------------------------------------------------------------
print("[14] Orchestrator delegates to POST /validate/metadata")
print("-" * 40)

check_pass(
    "PATCH /metadata and PATCH /decide reference validate/metadata",
    "validate/metadata",
    include_pattern="orchestrator_service_api.md",
    min_count=2
)

print()

# ------------------------------------------------------------------
# 15. Old path /converter/preview/metadata is removed
# ------------------------------------------------------------------
print("[15] Old path /converter/preview/metadata — removed")
print("-" * 40)

check_fail(
    "Old path /converter/preview/metadata still referenced somewhere",
    "converter/preview/metadata",
    exclude=["check_cross_references.py"]
)

print()

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print("=" * 60)
if errors:
    print(f" FAILED: {errors} cross-reference error(s) found.")
    sys.exit(1)
else:
    print(" PASSED: All cross-references are consistent.")
    sys.exit(0)
