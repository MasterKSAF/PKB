# Quality assessment issues

## Bug 1: `assess_document_quality()` checks `block["page"]` but blocks have `"page number"`

File: `backend/parser_service/app/services/pipeline/quality_assessment.py:47-49`

```python
for b in blocks:
    p = b.get("page", 1)  # WRONG: should also check "page number"
```

Fix: `p = b.get("page number", b.get("page", 1))`

## Bug 2: Detailed quality not in output

`AssessQualityStep` stores rich quality to `ctx.final_json["quality"]`, 
but initial `content.quality` (from parser) has only `per_page`, `confidence`, `notifications`.

The detailed assessment fields (`verdict`, `block_types`, `mean_chars_per_block`, etc.)
may not be available in the document API response if only `content.quality` is returned.

## Fix plan
Fix Bug 1 → corrects the false needs_ocr verdict.
