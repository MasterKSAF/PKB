import fitz, os, json, sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'H:\Projects\PKB_neuroassistant_develop\data\pdf_check\2-020101-174-20.pdf'
doc = fitz.open(pdf_path)
print(f'PDF: {os.path.basename(pdf_path)}, pages: {doc.page_count}')
print()

output_dir = r'H:\Projects\PKB_neuroassistant_develop\data\pdf_check\debug_output'
os.makedirs(output_dir, exist_ok=True)

# Накапливаем все текстовые блоки для JSON
all_blocks = []

for i in range(doc.page_count):
    page = doc[i]
    blocks = page.get_text('dict', sort=True)['blocks']
    print(f'=== Page {i+1} === ({len(blocks)} blocks)')
    
    for b in blocks:
        bbox = b['bbox']
        block_info = {
            'page': i + 1,
            'type': 'text' if b['type'] == 0 else 'image',
            'bbox': [round(x, 1) for x in bbox],
        }
        
        if b['type'] == 0:  # text
            lines = b['lines']
            text = ' '.join(''.join(s['text'] for s in l['spans']) for l in lines)
            block_info['content'] = text[:200]
            all_blocks.append(block_info)
            
            has_ris = 'рис' in text.lower()[:10]
            prefix = '[RIS]' if has_ris else '     '
            y_center = round((bbox[1] + bbox[3]) / 2)
            safe_text = text[:120].encode('utf-8', errors='replace').decode('utf-8')
            print(f'  {prefix} TEXT bbox=({bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f}) y_center={y_center}: {safe_text}')
        elif b['type'] == 1:  # image
            w = b.get('width', 0)
            h = b.get('height', 0)
            block_info['width'] = w
            block_info['height'] = h
            all_blocks.append(block_info)
            print(f'  [IMG] IMAGE bbox=({bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f}) size={w}x{h}')

# Save debug JSON
with open(os.path.join(output_dir, 'fitz_blocks.json'), 'w', encoding='utf-8') as f:
    json.dump(all_blocks, f, indent=2, ensure_ascii=False)
print(f'\nJSON saved to {output_dir}/fitz_blocks.json')

# Annotate PDF with bounding boxes
output_pdf = os.path.join(output_dir, 'annotated.pdf')
for i in range(doc.page_count):
    page = doc[i]
    blocks = page.get_text('dict', sort=True)['blocks']
    
    for b in blocks:
        rect = fitz.Rect(b['bbox'])
        
        if b['type'] == 0:
            text = ''.join(''.join(s['text'] for s in l['spans']) for l in b['lines'])
            is_ris = 'рис' in text.lower()[:10]
            color = (1, 0, 0) if is_ris else (0, 0, 1)
            annot = page.add_rect_annot(rect)
            annot.set_colors(stroke=color)
            annot.set_opacity(0.5)
            annot.update()
            label = 'RIS' if is_ris else 'T'
            page.insert_text(fitz.Point(rect.x0, rect.y0 - 2), label, fontsize=6, color=color)
        elif b['type'] == 1:
            annot = page.add_rect_annot(rect)
            annot.set_colors(stroke=(0, 1, 0))
            annot.set_opacity(0.5)
            annot.update()
            page.insert_text(fitz.Point(rect.x0, rect.y0 - 2), 'IMG', fontsize=6, color=(0, 1, 0))

doc.save(output_pdf)
doc.close()
print(f'Annotated PDF saved to {output_pdf}')
