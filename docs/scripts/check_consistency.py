#!/usr/bin/env python3
"""Check documentation consistency.
Run before committing changes to docs/.
Usage: python docs/scripts/check_consistency.py
"""

import os
import re
import sys

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def find(pattern, exclude_patterns=None, simple=False):
    results = []
    exclude = exclude_patterns or []
    for rel, path in get_files():
        if any(x in rel for x in exclude):
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


def check(name, pattern, exclude=None, simple=False, skip_lines=None):
    global errors
    results = find(pattern, exclude, simple)
    if skip_lines:
        results = [r for r in results if not any(s in r[2] for s in skip_lines)]
    if results:
        print(f"  FAIL: {name}")
        for path, lineno, _ in results[:5]:
            print(f"    {path}:{lineno}")
        errors += 1
    else:
        print(f"  OK: {name}")


def extract_headings(text):
    anchors = {}
    for line in text.split("\n"):
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            heading = m.group(1).strip()
            anchor = heading.lower()
            anchor = re.sub(r"[^a-z0-9а-я\-\s]", "", anchor)
            anchor = re.sub(r"\s+", "-", anchor).strip("-")
            anchors[anchor] = heading
    return anchors


def get_task_ids():
    tasks_path = os.path.join(DOCS_DIR, "6.dev_tasks_17_06.md")
    if not os.path.exists(tasks_path):
        return set()
    text = read_text(tasks_path)
    ids = re.findall(r"\b(CM|GW|OR|DB|RG|QS|RS|PS|OC|CV|RB|AU|P1F|P2I|P3S|T)-\d+", text)
    return set(ids)


# ============================================================
print("=" * 60)
print(" Documentation consistency check")
print("=" * 60)
print()

# 1-6. Original checks
print("1. IDOR references")
check("IDOR found", "IDOR", exclude=["check_rule", "check_consistency", "todo", "README"])

print("2. Redis + rate limiting")
check("Redis in rate limiting", r"redis.*rate|rate.*redis|limit_req.*[Rr]edis",
      exclude=["check_consistency", "todo", "README"], skip_lines=["не зависит от Redis"])

print("3. service_checker - post-deploy (dev-only)")
check("post-deploy found", r"post.deploy", exclude=["check_consistency", "todo", "README"])

print("4. IP masking in logs")
check("IP masked", r"IP.*xxx|xxx.*IP")

print("5. Removed task IDs referenced")
for task in ["CM-1", "CM-3", "DB-5"]:
    check(f"  {task} referenced outside tasks file", task,
          exclude=["6.dev_tasks_17_06", "todo", "check_consistency"], simple=True)

print("6. OTEL only in Gateway (should be all services)")
check("OTEL only in Gateway", r"OTEL.*tolko.*Gateway|tolko.*Gateway.*OTEL|tolko v Gateway|OTEL.*only.*gateway",
      exclude=["todo", "README"])

# 7. Anchor links to common_api.md
print("7. Anchor links to common_api.md (check anchors exist)")
common_path = os.path.join(DOCS_DIR, "api", "common_api.md")
if os.path.exists(common_path):
    common_text = read_text(common_path)
    common_anchors = extract_headings(common_text)
    anchor_errors = 0
    for rel, path in get_files():
        if rel.startswith("api/common_api.md"):
            continue
        try:
            text = read_text(path)
            for m in re.finditer(r"common_api\.md#([^\s\"\'\)\]>]+)", text):
                anchor = m.group(1)
                if anchor not in common_anchors:
                    print(f"  BROKEN LINK: {rel} -> common_api.md#{anchor}")
                    anchor_errors += 1
                    errors += 1
        except Exception:
            pass
    if anchor_errors == 0:
        print("  OK: all anchors found")
else:
    print("  SKIP: common_api.md not found")

# 8. Task-ID validation
print("8. Task-ID validation")
task_ids = get_task_ids()
if task_ids:
    missing = 0
    for rel, path in get_files():
        if "6.dev_tasks_17_06" in rel or "todo" in rel or "check_consistency" in rel:
            continue
        text = read_text(path)
        for m in re.finditer(r"\b(CM|GW|OR|DB|RG|QS|RS|PS|OC|CV|RB|AU)-\d+", text):
            tid = m.group(0)
            if tid not in task_ids:
                print(f"  MISSING TASK: {rel} references {tid} not in task file")
                missing += 1
                errors += 1
    if missing == 0:
        print("  OK: all task IDs exist")
else:
    print("  SKIP: cannot read tasks file")

# ============================================================
print()
print("=" * 60)
if errors:
    print(f"ERRORS: {errors} - fix before commit")
    sys.exit(1)
else:
    print("ERRORS: 0 - documentation is consistent")
print("=" * 60)
