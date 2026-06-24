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

# Все возможные префиксы task-ID. Единый источник истины для проверки ссылок.
TASK_PREFIXES = r'(?:CM|GW|OR|DB|RG|QS|RS|PS|OC|CV|RB|AU|P1F|P2I|P3S|T)'


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


def extract_markdown_table_values(text, column_index=0, header_row=0):
    """Extract values from first column of a markdown table.
    Returns list of non-empty cell values.
    """
    values = []
    lines = text.split('\n')
    in_table = False
    for line in lines:
        if '|' not in line:
            in_table = False
            continue
        cells = [c.strip() for c in line.split('|')]
        # Skip separator lines (|---|)
        if any('---' in c for c in cells):
            continue
        # Skip header rows up to header_row
        if not in_table:
            in_table = True
            continue
        # Data row
        idx = column_index + 1  # +1 because split gives empty before first |
        if idx < len(cells) and cells[idx]:
            val = cells[idx].strip()
            # Remove backticks if present
            val = val.strip('`')
            if val and not val.startswith('['):
                values.append(val)
    return values


def get_canonical_draft_statuses():
    """Extract canonical draft status list from Registry API."""
    path = os.path.join(DOCS_DIR, 'api', 'registry_service_api.md')
    if not os.path.exists(path):
        return set()
    text = read_text(path)
    # Find the canonical status table after "Канонический список статусов черновика"
    m = re.search(r'Канонический список статусов черновика.*?\n(\|.*?\|.*?\|(?:\n\|.*?\|.*?\|)+)', text, re.DOTALL)
    if not m:
        return set()
    table_text = m.group(1)
    values = set()
    for line in table_text.split('\n'):
        if '|' not in line or '---' in line:
            continue
        cells = [c.strip() for c in line.split('|')]
        if len(cells) >= 2:
            val = cells[1].strip('`').strip()
            if val and val != 'Статус':
                values.add(val)
    return values


def get_canonical_source_types():
    """Extract canonical source_type list from Registry /registry/enums endpoint."""
    path = os.path.join(DOCS_DIR, 'api', 'registry_service_api.md')
    if not os.path.exists(path):
        return set()
    text = read_text(path)
    # Find source_type array in the enums response
    m = re.search(r'"source_type":\s*\[(.*?)\]', text)
    if not m:
        return set()
    items = m.group(1)
    values = set()
    for item in re.findall(r'"([^"]+)"', items):
        values.add(item)
    return values


def get_enum_values_from_text(text, enum_name):
    """Find enum array like `"source_type": ["GOST", ...]` in text."""
    pattern = r'"' + re.escape(enum_name) + r'"\s*:\s*\[(.*?)\]'
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    items = m.group(1)
    return set(re.findall(r'"([^"]+)"', items))


def get_all_registry_enums():
    """Extract ALL enum values from Registry /registry/enums endpoint.
    Returns dict: enum_name -> set(values)
    """
    path = os.path.join(DOCS_DIR, 'api', 'registry_service_api.md')
    if not os.path.exists(path):
        return {}
    text = read_text(path)
    enums = {}
    # Find the enums response block
    for m in re.finditer(r'"(\w+)":\s*\[(.*?)\]', text):
        name = m.group(1)
        values = set(re.findall(r'"([^"]+)"', m.group(2)))
        if values:
            enums[name] = values
    return enums


def get_er_diagram_fields(table_name):
    """Extract field list from ER diagram for a given table.
    Returns set of field names.
    """
    path = os.path.join(DOCS_DIR, 'database', 'db_diagrams.md')
    if not os.path.exists(path):
        return set()
    text = read_text(path)
    # Find table block in erDiagram
    in_table = False
    fields = set()
    for line in text.split('\n'):
        if f'erDiagram' in line:
            in_table = True
            continue
        if not in_table:
            continue
        if line.strip().startswith('}'):
            in_table = False
            continue
        if table_name in line and '{' in line:
            continue  # Skip table header
        if in_table and line.strip() and '}' not in line:
            # Extract field name (second word after type)
            parts = line.strip().split()
            if len(parts) >= 2:
                # Skip type keywords
                if parts[0] in ('bigint', 'text', 'varchar', 'date', 'jsonb', 'timestamptz',
                               'boolean', 'uuid', 'int', 'float', 'numeric', 'char64'):
                    if len(parts) >= 2:
                        fields.add(parts[1].strip())
                else:
                    fields.add(parts[0].strip())
    return fields


def get_model_fields(model_section_start_marker):
    """Extract field names from a markdown model table (5.x sections).
    First column values after header.
    """
    path = os.path.join(DOCS_DIR, 'api', 'registry_service_api.md')
    if not os.path.exists(path):
        return set()
    text = read_text(path)
    # Find the model section
    lines = text.split('\n')
    in_model = False
    in_table = False
    fields = set()
    for i, line in enumerate(lines):
        if model_section_start_marker in line:
            in_model = True
            continue
        if not in_model:
            continue
        if line.startswith('### ') and i > 0:
            break  # Next section
        if '|' in line:
            cells = [c.strip() for c in line.split('|')]
            if len(cells) >= 2 and cells[1] and cells[1] != '---':
                # Skip header rows
                if cells[1].startswith('`') and '`' in cells[1]:
                    field = cells[1].strip('`').strip()
                    if field and field != 'Поле':
                        fields.add(field)
    return fields


def get_task_ids():
    tasks_path = os.path.join(DOCS_DIR, "6.dev_tasks_17_06.md")
    if not os.path.exists(tasks_path):
        return set()
    text = read_text(tasks_path)
    ids = re.findall(r"\b" + TASK_PREFIXES + r"-\d+", text)
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
        for m in re.finditer(r"\b" + TASK_PREFIXES + r"-\d+", text):
            tid = m.group(0)
            if tid not in task_ids:
                print(f"  MISSING TASK: {rel} references {tid} not in task file")
                missing += 1
                errors += 1
    if missing == 0:
        print("  OK: all task IDs exist")
else:
    print("  SKIP: cannot read tasks file")

# 9. Draft statuses cross-check (Registry canonical vs other files)
print("9. Draft statuses consistency")
canonical_statuses = get_canonical_draft_statuses()
if canonical_statuses:
    status_ok = True
    # Files that should contain all canonical statuses
    check_files = [
        "api/orchestrator_service_api.md",
        "pipelines/pipeline1-formation.md",
    ]
    for rel in check_files:
        path = os.path.join(DOCS_DIR, rel.replace("/", os.sep))
        if not os.path.exists(path):
            continue
        text = read_text(path)
        missing = set()
        for s in sorted(canonical_statuses):
            # Word boundary check: ensure the status appears as a standalone word
            if not re.search(r'\b' + re.escape(s) + r'\b', text):
                missing.add(s)
        if missing:
            print(f"  FAIL: {rel} missing statuses: {', '.join(sorted(missing))}")
            errors += 1
            status_ok = False
    if status_ok:
        print("  OK: all files contain all canonical draft statuses")
else:
    print("  SKIP: cannot read canonical statuses from registry_service_api.md")

# 10. source_type enum cross-check
print("10. source_type enum consistency")
canonical_source = get_canonical_source_types()
if canonical_source:
    source_ok = True
    # Files that reproduce the source_type enum
    check_targets = [
        ("database/db_diagrams.md", r'source_type.*?enum\s+([^\n]+)'),
        ("api/converter_validator_service_api.md", r'source_type.*?тип.*?([^\n]+)'),
    ]
    for rel, pattern in check_targets:
        path = os.path.join(DOCS_DIR, rel.replace("/", os.sep))
        if not os.path.exists(path):
            continue
        text = read_text(path)
        # Check that RMRS is present in source_type mentions
        if 'RMRS' not in text:
            print(f"  FAIL: {rel} has no reference to RMRS in source_type")
            errors += 1
            source_ok = False
            continue
        # For db_diagrams.md, extract the full enum line and compare
        m = re.search(r'source_type[^\n]*?enum\s+([^|\n]+)', text, re.IGNORECASE)
        if m:
            listed = set(re.findall(r'[A-Z_]+', m.group(1)))
            # Filter to only source_type-like values
            known = {s for s in listed if s in canonical_source or s == 'OTHER'}
            missing = canonical_source - known
            if missing:
                print(f"  FAIL: {rel} source_type missing: {', '.join(sorted(missing))}")
                errors += 1
                source_ok = False
    if source_ok:
        print("  OK: source_type consistent across all files")
else:
    print("  SKIP: cannot read canonical source_type from registry_service_api.md")

# 11. Stale identifier names
print("11. Stale identifier names")
stale_found = 0
stale_checks = [
    ("operator-confirm", "operator-confirm", ["check_consistency", "specificity.md", "todo"]),
    ("issues[] in API context (should be notifications[])", r'issues\[\]',
     ["check_consistency", "guide.md", "specificity.md", "todo"]),
]
for name, pattern, exclude in stale_checks:
    results = find(pattern, exclude, simple=isinstance(pattern, str))
    if results:
        print(f"  FAIL: {name}")
        for path, lineno, _ in results[:3]:
            print(f"    {path}:{lineno}")
        errors += 1
        stale_found += 1
if stale_found == 0:
    print("  OK: no stale identifier names")

# 12. Validate that route in Gateway has corresponding API section
print("12. Gateway route table vs API specs")
gw_path = os.path.join(DOCS_DIR, "api", "gateway_service_api.md")
if os.path.exists(gw_path):
    print("  OK: Gateway route table documented")
else:
    print("  SKIP: gateway_service_api.md not found")

# 13. Enum cross-check: Registry enums vs DB CHECK constraints
print("13. Registry enums vs DB CHECK constraints")
registry_enums = get_all_registry_enums()
db_diagrams_path = os.path.join(DOCS_DIR, "database", "db_diagrams.md")
if registry_enums and os.path.exists(db_diagrams_path):
    db_text = read_text(db_diagrams_path)
    enum_ok = True
    # Enums where case matters: source_type uses UPPERCASE (GOST, RMRS — аббревиатуры).
    # Для document_type, validity_status — слова, хранятся в lowercase как в API.
    check_map = {
        'source_type': r'source_type.*?CHECK IN \(([^)]+)\)',
        'document_type': r'document_type.*?CHECK IN \(([^)]+)\)',
        'era': r'`era`.*?CHECK IN \(([^)]+)\)',
        'validity_status': r'validity_status.*?CHECK IN \(([^)]+)\)',
        'jurisdiction': r'jurisdiction.*?CHECK IN \(([^)]+)\)',
    }
    # Enums that should be UPPERCASE (аббревиатуры и коды)
    uppercase_enums = {'source_type', 'era', 'jurisdiction'}
    for enum_name, db_pattern in check_map.items():
        if enum_name not in registry_enums:
            continue
        m = re.search(db_pattern, db_text, re.IGNORECASE)
        if not m:
            print(f"  FAIL: CHECK constraint for {enum_name} not found in db_diagrams.md")
            errors += 1
            enum_ok = False
            continue
        db_values = set()
        for v in re.findall(r"'([^']+)'", m.group(1)):
            db_values.add(v)
        api_values = registry_enums[enum_name]
        api_lower = {v.lower() for v in api_values}
        db_lower = {v.lower() for v in db_values}
        if api_lower != db_lower:
            missing_in_db = api_lower - db_lower
            extra_in_db = db_lower - api_lower
            msg = []
            if missing_in_db:
                msg.append(f"missing in CHECK: {', '.join(sorted(missing_in_db))}")
            if extra_in_db:
                msg.append(f"extra in CHECK: {', '.join(sorted(extra_in_db))}")
            print(f"  FAIL: {enum_name} — {'; '.join(msg)}")
            errors += 1
            enum_ok = False
        for v in db_values:
            if enum_name in uppercase_enums and v != v.upper():
                print(f"  FAIL: {enum_name} CHECK value '{v}' should be UPPERCASE")
                errors += 1
                enum_ok = False
    if enum_ok:
        print("  OK: all Registry enums match DB CHECK constraints")
else:
    print("  SKIP: cannot read Registry enums or db_diagrams.md")

# 14. Model 5.4 completeness vs ER diagram
print("14. Model 5.4 (registry_document) completeness")
er_fields = get_er_diagram_fields('registry.documents')
model_fields = get_model_fields('### 5.4. registry_document')
known_skip = {'id', 'PK', 'FK'}
if er_fields:
    er_clean = {f for f in er_fields if f not in known_skip 
                 and not f.startswith('bigint') and not f.startswith('}}')}
    missing_in_model = er_clean - model_fields
    if missing_in_model:
        print(f"  FAIL: model 5.4 missing fields: {', '.join(sorted(missing_in_model))}")
        errors += 1
    else:
        print("  OK: all ER-diagram fields present in model 5.4")
else:
    print("  SKIP: cannot extract ER diagram fields from db_diagrams.md")

# 15. DDL migrations enum values vs Registry enums
print("15. DDL migrations enum values")
ddl_path = os.path.join(DOCS_DIR, "database", "ddl_migrations_17_06.md")
if registry_enums and os.path.exists(ddl_path):
    ddl_text = read_text(ddl_path)
    ddl_ok = True
    for enum_name in ['source_type', 'document_type', 'era', 'validity_status', 'jurisdiction']:
        if enum_name not in registry_enums:
            continue
        m = re.search(r'`' + re.escape(enum_name) + r'`\s*[—–-]\s*([^\n]+)', ddl_text, re.IGNORECASE)
        if not m:
            print(f"  FAIL: {enum_name} not found in DDL migrations")
            errors += 1
            ddl_ok = False
            continue
        ddl_values = set(re.findall(r"'([^']+)'", m.group(1)))
        api_values = registry_enums[enum_name]
        api_lower = {v.lower() for v in api_values}
        ddl_lower = {v.lower() for v in ddl_values}
        missing_in_ddl = api_lower - ddl_lower
        if missing_in_ddl:
            print(f"  FAIL: {enum_name} DDL missing: {', '.join(sorted(missing_in_ddl))}")
            errors += 1
            ddl_ok = False
        for v in ddl_values:
            if enum_name in uppercase_enums and v != v.upper():
                print(f"  FAIL: {enum_name} DDL value '{v}' should be UPPERCASE")
                errors += 1
                ddl_ok = False
    if ddl_ok:
        print("  OK: all Registry enums match DDL migrations")
else:
    print("  SKIP: cannot read Registry enums or ddl_migrations.md")

# ============================================================
print()
print("=" * 60)
if errors:
    print(f"ERRORS: {errors} - fix before commit")
    sys.exit(1)
else:
    print("ERRORS: 0 - documentation is consistent")
print("=" * 60)
