import fitz, json, os

pdf_path = r'H:\Projects\PKB_neuroassistant_develop\data\pdf_check\2-020101-174-20.pdf'
doc = fitz.open(pdf_path)

for pno in [23, 24, 25, 38]:
    page = doc[pno - 1]
    blocks = page.get_text('dict', sort=True)['blocks']
    imgs = page.get_images()
    text = page.get_text()
    print(f'=== PyMuPDF: Page {pno} === (blocks={len(blocks)}, get_images={len(imgs)})')
    for b in blocks:
        if b['type'] == 1:
            r = b['bbox']
            w, h = b.get('width', 0), b.get('height', 0)
            print(f'  IMG bbox=({r[0]:.0f},{r[1]:.0f},{r[2]:.0f},{r[3]:.0f}) w={w} h={h}')
    # Show text lines containing "рис"
    for line in text.split('\n'):
        if 'рис' in line.lower()[:15]:
            print(f'  CAPTION: {line.strip()[:120]}')
    print()

# Also check page 23 for image specifically
print('=== Checking page 23 raw images ===')
page23 = doc[22]
for img in page23.get_images(full=True):
    xref = img[0]
    base = fitz.Pixmap(doc, xref)
    print(f'  xref={xref}, w={base.width}, h={base.height}, n={base.n}')

doc.close()
