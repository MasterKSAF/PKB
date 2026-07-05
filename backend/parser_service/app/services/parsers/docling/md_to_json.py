"""
Конвертер Markdown → JSON (структура opendataloader).

Принимает Markdown от Docling export_to_markdown() и преобразует
в стандартный JSON с блоками (heading, paragraph, table, image).

Не использует LLM — только регулярки и грамматика Markdown.
"""
import re
import json
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from collections import OrderedDict


# ============================================================
# 1. Парсинг Markdown-блоков
# ============================================================

BLOCK_TYPES = OrderedDict([
    ('heading', re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)),
    ('table', re.compile(r'^\|.+\|[\s\S]*?^\|.+\|(?:\n\n|\Z)', re.MULTILINE)),
    ('image', re.compile(r'^<!--\s*image\s*-->$', re.MULTILINE)),
    ('image_md', re.compile(r'^!\[.*?\]\(.*?\)$', re.MULTILINE)),
    ('code_block', re.compile(r'^```.*?\n[\s\S]*?^```$', re.MULTILINE)),
    ('horizontal_rule', re.compile(r'^---+\s*$', re.MULTILINE)),
])


def _is_list_marker(line: str) -> Optional[str]:
    """
    Проверяет, является ли строка началом списка.
    Возвращает маркер с типом: 'bullet', 'numbered.dot', 'numbered.num', или None.
    """
    stripped = line.lstrip()
    # Маркированный список: -, *, +
    if re.match(r'^[-*+]\s+', stripped):
        rest = re.sub(r'^[-*+]\s+', '', stripped)
        # Если после маркера идёт .1 .2 и т.д. — это нумерованный список
        if re.match(r'^\.?\d', rest):
            indent = len(line) - len(stripped)
            return f'numbered:{indent}'
        indent = len(line) - len(stripped)
        return f'bullet:{indent}'
    # Нумерованный список с точки: .1, .2, .2.1
    if re.match(r'^\.\d+(\.\d+)*\s+', stripped):
        indent = len(line) - len(stripped)
        return f'numbered.dot:{indent}'
    # Нумерованный список с цифры: 1., 1.2.3, 2.2.1, (а)
    if re.match(r'^(\d+[\.\)]|\([а-яa-z]\))\s+', stripped):
        indent = len(line) - len(stripped)
        return f'numbered.num:{indent}'
    return None


def _detect_list_type(marker: str) -> str:
    return 'bullet' if marker.startswith('bullet') else 'numbered'


def _extract_list_content(line: str) -> str:
    """Извлекает содержимое элемента списка, удаляя маркер."""
    stripped = line.lstrip()
    # bullet: '- текст' или '- .1 текст'
    if re.match(r'^[-*+]\s+', stripped):
        return re.sub(r'^[-*+]\s+', '', stripped).strip()
    # numbered: '.1 текст', '.2.1 текст', '1. текст', '(а) текст'
    # Для dotted (.1, .2.1) — сохраняем префикс, т.к. ODO хранит его в content
    return stripped


def split_markdown_blocks(md_text: str) -> List[Dict[str, Any]]:
    """
    Разбивает Markdown-текст на блоки.
    Возвращает список: [{'type': 'heading', 'level': 2, 'text': '...'}, ...]
    """
    blocks = []
    # Разбиваем на строки для построчного парсинга
    lines = md_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Пустая строка — пропускаем
        if not line.strip():
            i += 1
            continue
        
        # Heading: ## text
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            level = len(hm.group(1))
            text = hm.group(2).strip()
            blocks.append({'type': 'heading', 'level': level, 'text': text})
            i += 1
            continue
        
        # Image placeholder: <!-- image -->  +  caption со следующей строки
        if re.match(r'^<!--\s*image\s*-->$', line.strip()):
            caption = ''
            # Проверяем следующую непустую строку — это caption?
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                next_line = lines[j].strip()
                # Caption: строка с ключевыми словами подписи (Рис., Fig., Таблица, Table)
                if (next_line and not next_line.startswith('#') and not next_line.startswith('|')
                        and not next_line.startswith('<!--')
                        and not next_line.startswith('![')
                        and re.match(r'^(Рис\.|Fig\.|Таблица|Table|Иллюстрация|Illustration)', next_line)):
                    caption = next_line
                    # Пропускаем строку caption в основном цикле
                    # Помечаем, что строку нужно пропустить
                    lines[j] = ''  # очищаем, чтобы основной цикл её пропустил
            blocks.append({'type': 'image', 'text': caption or ''})
            i += 1
            continue
        
        # Image MD: ![alt](path)
        if re.match(r'^!\[.*?\]\(.*?\)$', line.strip()):
            alt_match = re.search(r'\[(.*?)\]', line)
            alt = alt_match.group(1) if alt_match else ''
            blocks.append({'type': 'image', 'text': alt})
            i += 1
            continue
        
        # Table: | ... | (с поддержкой многострочных ячеек)
        if line.startswith('|'):
            table_rows = []
            # Собираем все строки таблицы, включая продолжения
            while i < len(lines):
                current = lines[i]
                stripped = current.strip()
                if not stripped:
                    break
                if not stripped.startswith('|'):
                    # Если предыдущая строка не закрыта '|', это продолжение ячейки
                    if table_rows and not table_rows[-1].strip().endswith('|'):
                        table_rows[-1] = table_rows[-1].strip() + ' ' + stripped
                        i += 1
                        continue
                    break
                # Проверяем, не является ли строка частью другой конструкции (---)
                if re.match(r'^-{3,}\s*$', stripped.strip('|')):
                    break
                table_rows.append(stripped)
                i += 1
            blocks.append({'type': 'table', 'rows': table_rows})
            continue
        
        # Horizontal rule
        if re.match(r'^---+\s*$', line.strip()):
            i += 1
            continue
        
        # Code block
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            blocks.append({'type': 'code', 'text': '\n'.join(code_lines)})
            continue
        
        # List: маркированный или нумерованный
        list_marker = _is_list_marker(line)
        if list_marker:
            list_type = _detect_list_type(list_marker)
            # Определяем стиль первого элемента: dot-prefix (.1) или digit-prefix (1.2)
            first_stripped = line.lstrip()
            first_after_marker = re.sub(r'^[-*+]\s+', '', first_stripped) if re.match(r'^[-*+]\s+', first_stripped) else first_stripped
            list_has_dot_prefix = first_after_marker.startswith('.')
            items = []
            while i < len(lines):
                l = lines[i]
                
                # Пустая строка в списке — пропускаем (может быть между .1 и .2)
                if not l.strip():
                    i += 1
                    continue
                
                # Если строка — заголовок, таблица, image — конец списка
                if re.match(r'^#{1,6}\s', l):
                    break
                if l.strip().startswith('|'):
                    break
                if re.match(r'^<!--\s*image\s*-->$', l.strip()):
                    break
                if re.match(r'^-{3,}\s*$', l.strip()):
                    i += 1
                    continue
                
                marker = _is_list_marker(l)
                if marker and _detect_list_type(marker) == list_type:
                    stripped_now = l.lstrip()
                    # Определяем стиль номера ПОСЛЕ удаления маркера (- , *)
                    text_after_marker = re.sub(r'^[-*+]\s+', '', stripped_now) if re.match(r'^[-*+]\s+', stripped_now) else stripped_now
                    is_dot_item = text_after_marker.startswith('.')
                    # Смена стиля: были подпункты (.1), а это новый пункт (1.2)
                    if list_has_dot_prefix and not is_dot_item:
                        break
                    # Смена стиля: были пункты (1.2), а это подпункт (.1)
                    if not list_has_dot_prefix and is_dot_item:
                        break
                    
                    content = _extract_list_content(l)
                    items.append(content)
                    i += 1
                elif marker:
                    # Другой тип списка — выходим, обработаем на следующей итерации
                    break
                elif not l[0].isspace():
                    # Строка без отступа и без маркера (напр. параграф) — конец списка
                    break
                else:
                    # Строка с отступом — продолжение элемента
                    if items:
                        items[-1] = items[-1] + ' ' + l.strip()
                    i += 1
            if items:
                blocks.append({'type': 'list', 'list_type': list_type, 'items': items})
            continue
        
        # Paragraph: всё остальное до пустой строки или заголовка
        para_lines = []
        while i < len(lines):
            l = lines[i]
            if not l.strip():
                break
            # Не захватываем заголовки
            if re.match(r'^#{1,6}\s', l):
                break
            # Не захватываем таблицы (строка начинается с |)
            if l.strip().startswith('|'):
                break
            if re.match(r'^<!--\s*image\s*-->$', l.strip()):
                break
            # Не захватываем списки
            if _is_list_marker(l):
                break
            # Пропускаем разделители ---
            if re.match(r'^-{3,}\s*$', l.strip()):
                i += 1
                continue
            para_lines.append(l)
            i += 1
        
        if para_lines:
            text = ' '.join(l.strip() for l in para_lines if l.strip())
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                blocks.append({'type': 'paragraph', 'text': text})
            continue
        
        i += 1
    
    return blocks


# ============================================================
# 2. Парсинг таблицы
# ============================================================

def parse_table(rows: List[str]) -> Dict[str, Any]:
    """
    Парсит pipe-таблицу Markdown в структурированный JSON.
    
    Вход:
        rows = ['| № | Описание | Штамп |', '|---|---|---|', '| .1 | Чертеж | О |']
    
    Выход:
        {'type': 'table', 'rows': [{'cells': [...]}, ...], 
         'number of rows': N, 'number of columns': M}
    """
    if len(rows) < 2:
        return {'type': 'table', 'rows': [], 'number of rows': 0, 'number of columns': 0}
    
    # Отделяем заголовок от данных
    # Строка 0: заголовок
    # Строка 1: разделитель (| --- | --- |)
    # Строка 2+: данные
    
    header_row = rows[0]
    data_rows = rows[2:] if len(rows) > 2 else []
    
    def split_cells(row: str) -> List[str]:
        """Разбивает строку таблицы на ячейки."""
        row = row.strip()
        if row.startswith('|'):
            row = row[1:]
        if row.endswith('|'):
            row = row[:-1]
        cells = []
        current = ''
        for ch in row:
            if ch == '|':
                cells.append(current.strip())
                current = ''
            else:
                current += ch
        cells.append(current.strip())
        return cells
    
    headers = split_cells(header_row)
    num_cols = len(headers)
    
    result_rows = []
    for ri, rdata in enumerate(data_rows):
        cells = split_cells(rdata)
        # Дополняем до num_cols, если строк меньше
        while len(cells) < num_cols:
            cells.append('')
        cell_objects = []
        for ci, cell_text in enumerate(cells[:num_cols]):
            cell_objects.append({
                'row number': ri + 1,
                'column number': ci + 1,
                'row span': 1,
                'column span': 1,
                'page number': 1,
                'bounding box': [0, 0, 0, 0],
                'kids': [{'content': cell_text.strip(), 'font': {}}],
            })
        result_rows.append({
            'type': 'table row',
            'row number': ri + 1,
            'cells': cell_objects,
        })
    
    return {
        'type': 'table',
        'number of rows': len(result_rows),
        'number of columns': num_cols,
        'rows': result_rows,
        'content': ' | '.join(headers),  # первая строка как content
    }


# ============================================================
# 3. MD → JSON converter
# ============================================================

def _looks_like_list_item(text: str) -> bool:
    """Проверяет, похож ли короткий параграф на элемент перечисления.
    Критерии: начинается с заглавной/аббревиатуры или содержит " - " / " — "."""
    t = text.strip()
    if not t or len(t) > 100:
        return False
    # Начинается с аббревиатуры (заглавные буквы) и содержит разделитель
    if re.match(r'^[А-ЯA-Z]{2,}\s+[-—]', t):
        return True
    if re.match(r'^[А-ЯA-Z][а-яa-z]+\s+[-—]', t):
        return True
    # Содержит " - " или " — " (типично для списков определений)
    if ' - ' in t or ' — ' in t:
        return True
    # Начинается с римской цифры, буквы с точкой: I., II., а), б)
    if re.match(r'^[IVXLCM]+\..', t):
        return True
    if re.match(r'^[а-яa-z]\)', t):
        return True
    # Очень короткая строка (3-10 символов) из заглавных букв — аббревиатура
    if 2 <= len(t) <= 10 and re.match(r'^[А-ЯA-Z][А-ЯA-Z0-9]+$', t):
        return True
    return False


def md_to_json_blocks(md_text: str, page_number: int = 1) -> List[Dict[str, Any]]:
    """
    Конвертирует Markdown страницы в список блоков opendataloader-формата.
    """
    raw_blocks = split_markdown_blocks(md_text)
    result = []
    
    # Буфер для группировки коротких параграфов в список
    list_buffer = []
    
    def flush_list():
        nonlocal list_buffer
        if len(list_buffer) >= 3:
            all_short = all(len(b['text']) <= 120 for b in list_buffer)
            # Хотя бы один элемент содержит " - " или это заглавная аббревиатура
            has_list_like = any(_looks_like_list_item(b['text']) for b in list_buffer)
            if all_short and has_list_like:
                result.append({
                    'type': 'list',
                    'page number': page_number,
                    'list_type': 'bullet',
                    'content': '\n'.join(b['text'] for b in list_buffer),
                    'items': [{'content': b['text']} for b in list_buffer],
                    'bounding box': [0, 0, 0, 0],
                })
                list_buffer = []
                return
        # Если не подошло — сбрасываем как обычные параграфы
        for b in list_buffer:
            result.append({
                'type': 'paragraph',
                'page number': page_number,
                'content': b['text'],
                'bounding box': [0, 0, 0, 0],
            })
        list_buffer = []
    
    for bi, block in enumerate(raw_blocks):
        bt = block['type']
        text = block.get('text', '')
        
        # Пропускаем пустые блоки-разделители внутри потенциального списка
        is_empty_block = bt in ('list', 'horizontal_rule') and not text.strip()
        if is_empty_block and list_buffer:
            continue
        
        if bt == 'heading':
            flush_list()
            result.append({
                'type': 'heading',
                'page number': page_number,
                'heading level': block['level'],
                'content': text,
                'bounding box': [0, 0, 0, 0],
            })
        
        elif bt == 'list':
            flush_list()
            items = block.get('items', [])
            result.append({
                'type': 'list',
                'page number': page_number,
                'list_type': block.get('list_type', 'bullet'),
                'content': '\n'.join(items),
                'items': [{'content': item} for item in items],
                'bounding box': [0, 0, 0, 0],
            })
        
        elif bt == 'paragraph':
            # Короткий параграф (≤120) — в буфер, если буфер уже начат
            # или это первый похожий на элемент списка
            is_short = len(text) <= 120
            is_listy = _looks_like_list_item(text)
            if is_short and (list_buffer or is_listy):
                list_buffer.append(block)
            else:
                flush_list()
                result.append({
                    'type': 'paragraph',
                    'page number': page_number,
                    'content': text,
                    'bounding box': [0, 0, 0, 0],
                })
        
        elif bt == 'table':
            flush_list()
            parsed = parse_table(block['rows'])
            parsed['page number'] = page_number
            parsed['bounding box'] = [0, 0, 0, 0]
            result.append(parsed)
        
        elif bt == 'image':
            flush_list()
            result.append({
                'type': 'image',
                'page number': page_number,
                'content': block['text'] or '',
                'image_key': '',
                'bounding box': [0, 0, 0, 0],
            })
        
        elif bt == 'code':
            flush_list()
            # Код как параграф (в MD структура кода не критична)
            result.append({
                'type': 'paragraph',
                'page number': page_number,
                'content': block['text'],
                'bounding box': [0, 0, 0, 0],
            })
    
    flush_list()
    return result


def md_to_document_json(page_mds: List[Tuple[int, str]], 
                         file_name: str = 'document.pdf') -> Dict[str, Any]:
    """
    Конвертирует список (page_number, md_text) в полный JSON документа.
    
    Args:
        page_mds: список пар (номер_страницы, markdown_текст)
        file_name: имя файла
    
    Returns:
        JSON в структуре opendataloader
    """
    all_blocks = []
    total_pages = len(page_mds)
    has_tables = False
    
    for pno, md_text in page_mds:
        blocks = md_to_json_blocks(md_text, pno)
        for b in blocks:
            if b.get('type') == 'table':
                has_tables = True
        all_blocks.extend(blocks)
    
    # Подсчитываем блоки по типам
    type_counts = {}
    for b in all_blocks:
        t = b.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    
    document = {
        'source': {
            'file_name': file_name,
            'file_hash_sha256': '',
            'page_count': total_pages,
        },
        'pages': [{'page': i + 1, 'width': 595.0, 'height': 842.0} 
                  for i in range(total_pages)],
        'block': all_blocks,
    }
    
    return {
        'content': {
            'document': document,
            'quality': {
                'confidence': 0.75,
                'pages_processed': total_pages,
                'per_page': [],
            },
            'errors': [],
            'status': 'completed',
            'metadata': {
                'total_pages': total_pages,
                'has_tables': has_tables,
            },
        }
    }


# ============================================================
# 4. CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Convert Docling Markdown to JSON (opendataloader format)')
    parser.add_argument('input_md', help='Path to Markdown file (or - for stdin)')
    parser.add_argument('-o', '--output', default=None, help='Output JSON path')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages')
    parser.add_argument('--file-name', default='document.pdf', help='Original file name')
    args = parser.parse_args()
    
    if args.input_md == '-':
        md_text = sys.stdin.read()
    else:
        with open(args.input_md, encoding='utf-8') as f:
            md_text = f.read()
    
    # Если текст не разбит по страницам, считаем одной страницей
    page_mds = [(1, md_text)] if args.pages == 1 else [
        (i + 1, md_text) for i in range(args.pages)
    ]
    
    result = md_to_document_json(page_mds, args.file_name)
    
    output = args.output or (Path(args.input_md).stem + '_from_md.json' 
                             if args.input_md != '-' else 'output_from_md.json')
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Статистика
    blocks = result['content']['document']['block']
    type_counts = {}
    for b in blocks:
        t = b.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print(f'Converted {len(blocks)} blocks from MD to JSON', flush=True)
    print(f'Types: {type_counts}', flush=True)
    print(f'Saved to {output}', flush=True)


if __name__ == '__main__':
    import argparse
    main()
