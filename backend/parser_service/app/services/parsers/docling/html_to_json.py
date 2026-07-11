import json
import re
import sys
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class _PageHtmlParser(HTMLParser):
    """
    SAX-парсер HTML-страницы от Docling export_to_html().
    Извлекает блоки: heading, paragraph, table, image, list.
    """
    def __init__(self):
        super().__init__()
        self.blocks: List[Dict[str, Any]] = []
        self._in_page = False
        self._page_depth = 0

        self._text_buf: List[str] = []
        self._current_tag: Optional[str] = None

        self._in_table = False
        self._table_rows: List[List[str]] = []
        self._current_row_cells: List[str] = []
        self._current_cell_text: List[str] = []
        self._table_has_th = False

        self._list_type: Optional[str] = None
        self._list_items: List[str] = []
        self._in_list_item = False

        self._in_figure = False
        self._figcaption = ''
        self._in_figcaption = False

    def _flush_text(self):
        text = ''.join(self._text_buf).strip()
        if text:
            if self._current_tag == 'p':
                self.blocks.append({'type': 'paragraph', 'text': text})
            elif self._current_tag and self._current_tag.startswith('h'):
                level = int(self._current_tag[1])
                self.blocks.append({'type': 'heading', 'level': level, 'text': text})
        self._text_buf = []
        self._current_tag = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'div' and attrs_dict.get('class') == 'page':
            self._in_page = True
            self._page_depth = 1
            return

        if not self._in_page:
            return

        if tag == 'div':
            self._page_depth += 1

        self._in_figcaption = False

        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._flush_text()
            self._current_tag = tag
            self._text_buf = []

        elif tag == 'p':
            self._flush_text()
            self._current_tag = 'p'
            self._text_buf = []

        elif tag == 'table':
            self._flush_text()
            self._in_table = True
            self._table_rows = []
            self._table_has_th = False

        elif tag == 'tr':
            if self._in_table:
                self._current_row_cells = []

        elif tag == 'th':
            if self._in_table:
                self._table_has_th = True
                self._current_cell_text = []

        elif tag == 'td':
            if self._in_table:
                self._current_cell_text = []

        elif tag == 'figure':
            self._flush_text()
            self._in_figure = True
            self._figcaption = ''
            self._in_figcaption = False

        elif tag == 'img':
            if self._in_figure:
                self._img_alt = attrs_dict.get('alt', '')

        elif tag == 'figcaption':
            self._in_figcaption = True

        elif tag in ('ul', 'ol'):
            self._flush_text()
            self._list_type = 'bullet' if tag == 'ul' else 'numbered'
            self._list_items = []

        elif tag == 'li':
            self._in_list_item = True
            self._list_items.append('')

    def handle_endtag(self, tag):
        if not self._in_page:
            return

        if tag == 'div':
            if self._page_depth <= 1:
                self._in_page = False
            self._page_depth -= 1
            return

        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            if self._current_tag == tag:
                self._flush_text()
            else:
                self._text_buf = []
                self._current_tag = None

        elif tag == 'p':
            if self._current_tag == 'p':
                self._flush_text()
            else:
                self._text_buf = []
                self._current_tag = None

        elif tag == 'table':
            if self._in_table:
                self._in_table = False
                if self._table_rows:
                    self.blocks.append({'type': 'table', 'rows': self._table_rows,
                                        'has_header': self._table_has_th})

        elif tag == 'tr':
            if self._in_table and self._current_row_cells:
                self._table_rows.append(self._current_row_cells)
                self._current_row_cells = []

        elif tag in ('td', 'th'):
            if self._in_table:
                cell_text = ''.join(self._current_cell_text).strip()
                self._current_row_cells.append(cell_text)
                self._current_cell_text = []

        elif tag == 'figure':
            if self._in_figure:
                self._in_figure = False
                caption = self._figcaption or ''
                self.blocks.append({'type': 'image', 'text': caption})

        elif tag == 'figcaption':
            self._in_figcaption = False

        elif tag in ('ul', 'ol'):
            if self._list_items:
                self.blocks.append({
                    'type': 'list',
                    'list_type': self._list_type,
                    'items': self._list_items,
                })
            self._list_items = []
            self._list_type = None

        elif tag == 'li':
            self._in_list_item = False

    def handle_data(self, data):
        if not self._in_page:
            return

        if self._in_table:
            self._current_cell_text.append(data)
        elif self._in_figcaption:
            self._figcaption += data
        elif self._in_list_item and self._list_items is not None:
            self._list_items[-1] += data
        elif self._current_tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._text_buf.append(data)


def parse_table_from_html(rows: List[List[str]], has_header: bool = True) -> Dict[str, Any]:
    """
    Парсит HTML-таблицу (список списков ячеек) в структурированный JSON.

    Args:
        rows: список строк, каждая строка — список ячеек
        has_header: True если первая строка — заголовок (<th>)
    """
    if not rows:
        return {
            'type': 'table',
            'number of rows': 0,
            'number of columns': 0,
            'rows': [],
            'content': '',
        }

    num_cols = max(len(r) for r in rows) if rows else 0
    data_start = 1 if has_header and len(rows) > 1 else 0
    header_cells = rows[0] if rows else []
    content = ' | '.join(header_cells)
    data_rows = rows[data_start:] if rows else []

    result_rows = []
    for ri, row_cells in enumerate(data_rows):
        cells = list(row_cells)
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
        'content': content,
    }


def html_to_json_blocks(page_html: str, page_number: int = 1) -> List[Dict[str, Any]]:
    """
    Конвертирует HTML страницы в список блоков opendataloader-формата.
    """
    parser = _PageHtmlParser()
    parser.feed(page_html)
    raw_blocks = parser.blocks

    result = []
    for block in raw_blocks:
        bt = block['type']

        if bt == 'heading':
            result.append({
                'type': 'heading',
                'page number': page_number,
                'heading level': block['level'],
                'content': block['text'],
                'bounding box': [0, 0, 0, 0],
            })

        elif bt == 'paragraph':
            result.append({
                'type': 'paragraph',
                'page number': page_number,
                'content': block['text'],
                'bounding box': [0, 0, 0, 0],
            })

        elif bt == 'list':
            items = block.get('items', [])
            result.append({
                'type': 'list',
                'page number': page_number,
                'list_type': block.get('list_type', 'bullet'),
                'content': '\n'.join(items),
                'items': [{'content': item} for item in items],
                'bounding box': [0, 0, 0, 0],
            })

        elif bt == 'table':
            parsed = parse_table_from_html(block['rows'], has_header=block.get('has_header', False))
            parsed['page number'] = page_number
            parsed['bounding box'] = [0, 0, 0, 0]
            result.append(parsed)

        elif bt == 'image':
            result.append({
                'type': 'image',
                'page number': page_number,
                'content': block['text'] or '',
                'image_key': '',
                'bounding box': [0, 0, 0, 0],
            })

    return result


def html_to_document_json(page_htmls: List[Tuple[int, str]],
                           file_name: str = 'document.pdf') -> Dict[str, Any]:
    """
    Конвертирует список (page_number, html_text) в полный JSON документа.

    Args:
        page_htmls: список пар (номер_страницы, HTML-текст)
        file_name: имя файла

    Returns:
        JSON в структуре opendataloader
    """
    all_blocks = []
    total_pages = len(page_htmls)
    has_tables = False

    for pno, html_text in page_htmls:
        blocks = html_to_json_blocks(html_text, pno)
        for b in blocks:
            if b.get('type') == 'table':
                has_tables = True
        all_blocks.extend(blocks)

    # Финальный фильтр: контент только из цифр/разделителей (без букв, без точки — коды классификации не трогать)
    all_blocks = [
        b for b in all_blocks
        if not re.match(r'^[\d\s\-—\/]+$', (b.get('content') or '').strip())
    ]

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


def main():
    parser = argparse.ArgumentParser(
        description='Convert Docling HTML to JSON (opendataloader format)')
    parser.add_argument('input_html', help='Path to HTML file (or - for stdin)')
    parser.add_argument('-o', '--output', default=None, help='Output JSON path')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages')
    parser.add_argument('--file-name', default='document.pdf', help='Original file name')
    args = parser.parse_args()

    if args.input_html == '-':
        html_text = sys.stdin.read()
    else:
        with open(args.input_html, encoding='utf-8') as f:
            html_text = f.read()

    page_htmls = [(1, html_text)] if args.pages == 1 else [
        (i + 1, html_text) for i in range(args.pages)
    ]

    result = html_to_document_json(page_htmls, args.file_name)

    output = args.output or (Path(args.input_html).stem + '_from_html.json'
                             if args.input_html != '-' else 'output_from_html.json')

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    blocks = result['content']['document']['block']
    type_counts = {}
    for b in blocks:
        t = b.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f'Converted {len(blocks)} blocks from HTML to JSON', flush=True)
    print(f'Types: {type_counts}', flush=True)
    print(f'Saved to {output}', flush=True)


if __name__ == '__main__':
    import argparse
    main()
