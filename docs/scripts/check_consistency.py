#!/usr/bin/env python3
"""Check documentation consistency.
Run before committing changes to docs/.
"""

import os
import re
import sys

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = 0


def find(pattern, exclude_patterns=None, simple=False):
    """Search for pattern in .md files, excluding paths matching exclude_patterns."""
    results = []
    exclude = exclude_patterns or []

    for root, dirs, files in os.walk(DOCS_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, DOCS_DIR)

            # skip excluded
            if any(x in rel for x in exclude):
                continue

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for lineno, line in enumerate(fh, 1):
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


print("=" * 50)
print(" Documentation consistency check")
print("=" * 50)
print()

# 1. IDOR
print("1. IDOR references")
check("IDOR found", "IDOR", exclude=["check_rule", "check_consistency", "todo", "README"])

# 2. Redis + rate limiting
print("2. Redis + rate limiting")
check(
    "Redis in rate limiting",
    r"redis.*rate|rate.*redis|limit_req.*[Rr]edis",
    exclude=["check_consistency", "todo", "README"],
    skip_lines=["не зависит от Redis"],
)

# 3. post-deploy
print("3. service_checker - post-deploy (dev-only)")
check("post-deploy found", r"post.deploy", exclude=["check_consistency", "todo", "README"])

# 4. IP mask in logs
print("4. IP masking in logs")
check("IP masked", r"IP.*xxx|xxx.*IP")

# 5. Removed task IDs
print("5. Removed task IDs referenced")
for task in ["CM-1", "CM-3", "DB-5"]:
    check(
        f"  {task} referenced outside tasks file",
        task,
        exclude=["6.dev_tasks_17_06", "todo", "check_consistency"],
        simple=True,
    )

# 6. OTEL only in Gateway (should be in all services)
print("6. OTEL only in Gateway (should be all services)")
check(
    'OTEL only in Gateway',
    r"OTEL.*tolko.*Gateway|tolko.*Gateway.*OTEL|tolko v Gateway|OTEL.*only.*gateway",
    exclude=["todo", "README"],
)

print()
print("=" * 50)
if errors:
    print(f"ERRORS: {errors} - fix before commit")
    sys.exit(1)
else:
    print("ERRORS: 0 - documentation is consistent")
print("=" * 50)
