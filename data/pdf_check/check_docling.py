import json, sys
sys.path.insert(0, '/app')
from app.services.parsers.docling.docling_mapper import convert_via_docling_md

result = convert_via_docling_md('/tmp/test.pdf')
with open('/tmp/docling_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

blocks = result.get('content', {}).get('document', {}).get('block', [])
print(f'Total blocks: {len(blocks)}')

img_blocks = [b for b in blocks if b.get('type') == 'image']
cap_blocks = [b for b in blocks if b.get('content','').lower().startswith('рис')]
print(f'Image blocks: {len(img_blocks)}')
print(f'Caption blocks (Рис): {len(cap_blocks)}')

for b in cap_blocks:
    print(f'  Page {b.get("page number")}: {b["content"][:80]}  bbox={b.get("bounding box")}')

for b in img_blocks[:10]:
    print(f'  Page {b.get("page number")}: subtype={b.get("subtype","")}  size={b.get("width",0)}x{b.get("height",0)}  image_key={b.get("image_key","")[:60]}')

if len(img_blocks) > 10:
    print(f'  ... and {len(img_blocks)-10} more image blocks')

# Check per-page order
print('\nPer-page image positions:')
for pno in sorted(set(b.get('page number', 1) for b in blocks)):
    page_blocks = [b for b in blocks if b.get('page number') == pno]
    img_idx = [i for i, b in enumerate(page_blocks) if b.get('type') == 'image']
    if img_idx:
        print(f'  Page {pno}: {len(img_idx)} image(s) at indices {img_idx} out of {len(page_blocks)} blocks')

# Save annotated page showing image-key-to-page mapping
print('\nDone. Full JSON saved to /tmp/docling_result.json')
