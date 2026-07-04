"""
Layout analysis поверх DoclingPdfParser.
Группирует строки → параграфы/заголовки/списки/таблицы.
Определяет структуру документа без ML-пайплайна.
"""
import logging
import sys
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# Пороги для группировки
LINE_GAP_THRESHOLD = 3.0        # если расстояние между строками < 3pt — это одна строка
PARAGRAPH_GAP_MULTIPLIER = 1.5  # если пробел >= среднего * multiplier — разрыв параграфа
HEADING_FONT_MULTIPLIER = 1.2   # если font_size > среднего * multiplier — заголовок
BOLD_KEYWORDS = ("Bold", "Heavy", "Black", "Demi")  # признаки жирности


# ---------------------------------------------------------------------------
# Структуры данных
# ---------------------------------------------------------------------------
class TextLine:
    """Одна строка текста."""
    def __init__(self, words: list, page_no: int):
        self.words = words
        self.page_no = page_no
        self.text = " ".join(wc.text for wc in words).strip()

        # BoundingRect имеет CoordOrigin.BOTTOMLEFT
        # верхняя граница = max(r_y1, r_y3), нижняя = min(r_y0, r_y1)
        y_top = max(max(w.rect.r_y1, w.rect.r_y3) for w in words)   # max Y = верх
        y_bot = min(min(w.rect.r_y0, w.rect.r_y1) for w in words)  # min Y = низ
        x0 = min(w.rect.r_x0 for w in words)
        x1 = max(w.rect.r_x2 for w in words)

        # Конвертируем в [x0, y0, x1, y1] где y0=верх, y1=низ (стандартный экранный)
        page_h = 842.0  # A4 высота
        self.bbox = [round(x0, 1), round(page_h - y_top, 1),
                     round(x1, 1), round(page_h - y_bot, 1)]

        # Шрифт
        self.font_name = words[0].font_name if words else ""
        # Размер шрифта — берём из разницы Y
        self.font_size = round(abs(y_top - y_bot), 1)
        self.is_bold = any(k in self.font_name for k in BOLD_KEYWORDS)

        # Оригинальные Y для сортировки
        self._y_order = y_top  # чем больше, тем выше на странице

    @property
    def y_center(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2


def _build_text_lines(page, page_no: int) -> List[TextLine]:
    """Группирует word_cells страницы в строки текста."""
    words = list(page.word_cells) if hasattr(page, 'word_cells') and page.word_cells else []
    if not words:
        return []

    # Сортируем слова сверху вниз: чем больше Y (BOTTOMLEFT), тем выше
    words_sorted = sorted(words, key=lambda w: (-w.rect.r_y1, w.rect.r_x0))

    lines = []
    current = []
    last_y = None
    for wc in words_sorted:
        y_top = max(wc.rect.r_y1, wc.rect.r_y3)  # верхняя граница в BOTTOMLEFT
        if last_y is not None and abs(y_top - last_y) > LINE_GAP_THRESHOLD:
            if current:
                lines.append(TextLine(current, page_no))
            current = []
        current.append(wc)
        last_y = y_top
    if current:
        lines.append(TextLine(current, page_no))

    return lines


def _group_lines_to_paragraphs(lines: List[TextLine]) -> List[Dict[str, Any]]:
    """Группирует строки в параграфы/заголовки."""
    if not lines:
        return []

    # Средний размер шрифта и расстояние между строками
    font_sizes = [l.font_size for l in lines if l.font_size > 0]
    avg_font = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0

    gaps = []
    for i in range(1, len(lines)):
        gap = lines[i].bbox[1] - lines[i-1].bbox[3]  # y0_current - y1_prev
        if gap > 0:
            gaps.append(gap)
    avg_gap = sum(gaps) / len(gaps) if gaps else 10.0
    if avg_gap < 1:
        avg_gap = 10.0

    blocks = []
    current_group = [lines[0]]

    for i in range(1, len(lines)):
        prev = lines[i - 1]
        curr = lines[i]
        gap = curr.bbox[1] - prev.bbox[3]
        # Новый параграф если разрыв большой
        is_new_paragraph = gap > avg_gap * PARAGRAPH_GAP_MULTIPLIER
        # Или если меняется шрифт кардинально
        is_font_change = (prev.is_bold != curr.is_bold or
                          abs(prev.font_size - curr.font_size) > 2.0)

        if is_new_paragraph or is_font_change:
            blocks.append(_make_block(current_group, avg_font))
            current_group = [curr]
        else:
            current_group.append(curr)

    if current_group:
        blocks.append(_make_block(current_group, avg_font))

    return blocks


def _make_block(lines: List[TextLine], avg_font: float) -> Dict[str, Any]:
    """Из группы строк → блок в формате opendataloader."""
    page_no = lines[0].page_no
    text = " ".join(l.text for l in lines).strip()

    # bbox объединённый
    x0 = min(l.bbox[0] for l in lines)
    y0 = min(l.bbox[1] for l in lines)   # верх
    x1 = max(l.bbox[2] for l in lines)
    y1 = max(l.bbox[3] for l in lines)   # низ
    bbox = [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)]

    # Определяем тип блока
    max_font = max(l.font_size for l in lines)
    any_bold = any(l.is_bold for l in lines)

    block_type = "paragraph"
    heading_level = None
    numbering_style = None
    list_items = None

    # Определяем заголовки: крупный шрифт (>1.4× среднего) или bold + крупный
    if max_font >= avg_font * 1.4:
        block_type = "heading"
        if max_font >= avg_font * 2.0:
            heading_level = 1
        else:
            heading_level = 2
    elif any_bold and max_font >= avg_font * 1.15:
        block_type = "heading"
        heading_level = 2

    # Проверка на список
    first_line = lines[0].text.strip()
    if first_line and first_line[0] in ("•", "–", "-", "*"):
        block_type = "list"
        numbering_style = "bullet"
        list_items = []
        for l in lines:
            t = l.text.strip()
            if t and len(t) > 2:
                item_text = t[1:].strip() if t[0] in ("•", "–", "-", "*") else t
                list_items.append({
                    "type": "paragraph",
                    "page": page_no,
                    "bounding box": l.bbox,
                    "content": item_text,
                    "font": {"size": l.font_size, "bold": l.is_bold},
                })
    elif first_line and first_line[0].isdigit():
        idx = 0
        while idx < len(first_line) and first_line[idx].isdigit():
            idx += 1
        if idx > 0 and idx < len(first_line) and first_line[idx] in (".", ")", ": "):
            block_type = "list"
            numbering_style = "numbering"
            list_items = []
            for j, l in enumerate(lines):
                t = l.text.strip()
                prefix_len = 0
                while prefix_len < len(t) and (t[prefix_len].isdigit() or t[prefix_len] in (".", ")", " ")):
                    prefix_len += 1
                item_text = t[prefix_len:].strip() if prefix_len > 0 else t
                list_items.append({
                    "type": "paragraph",
                    "page": page_no,
                    "bounding box": l.bbox,
                    "content": item_text,
                    "font": {"size": l.font_size, "bold": l.is_bold},
                })

    block = {
        "type": block_type,
        "page number": page_no,
        "bounding box": bbox,
        "content": text,
        "font size": max_font,
        "font": lines[0].font_name,
    }
    if heading_level:
        block["heading level"] = heading_level
    if numbering_style:
        block["numbering style"] = numbering_style
    if list_items:
        block["list items"] = list_items

    return block


def _detect_tables(page, page_no: int) -> List[Dict[str, Any]]:
    """Эвристика: если на странице есть слова с регулярной сеткой X — таблица."""
    words = list(page.word_cells) if hasattr(page, 'word_cells') and page.word_cells else []
    if len(words) < 10:
        return []

    # Группируем по Y (строкам таблицы)
    line_groups = defaultdict(list)
    for w in words:
        # Округляем Y до ближайших 3pt
        y_key = round(w.rect.r_y3 / 3) * 3
        line_groups[y_key].append(w)

    table_candidates = []
    for y_key, group in line_groups.items():
        if len(group) < 3:
            continue
        # Проверяем по X — если минимум 2 чётких колонки
        x_positions = sorted(set(round(w.rect.r_x0 / 5) * 5 for w in group))
        if len(x_positions) >= 3:
            table_candidates.append(group)

    if len(table_candidates) < 3:
        return []

    # Строим таблицу (упрощённо)
    rows = []
    for group in table_candidates:
        sorted_cells = sorted(group, key=lambda w: w.rect.r_x0)
        row_text = " | ".join(wc.text for wc in sorted_cells)
        rows.append(row_text)

    if not rows:
        return []

    bbox = [0, 0, 0, 0]
    return [{
        "type": "table",
        "page number": page_no,
        "bounding box": bbox,
        "number of rows": len(rows),
        "number of columns": max(len(g) for g in table_candidates),
        "content": "\n".join(rows),
    }]


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------
def parse_pdf(pdf_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    """Парсит PDF с layout analysis, возвращает raw JSON в формате opendataloader."""
    from docling_parse.pdf_parser import DoclingPdfParser

    parser = DoclingPdfParser(loglevel="error")
    pdf_doc = parser.load(pdf_path, lazy=True)
    total = pdf_doc.number_of_pages()
    limit = min(max_pages or total, total)

    file_name = Path(pdf_path).name
    file_bytes = Path(pdf_path).read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    all_kids = []
    table_counter = 0

    for page_idx in range(limit):
        page = pdf_doc.get_page(page_idx + 1)
        page_no = page_idx + 1
        words_count = len(page.word_cells) if hasattr(page, 'word_cells') and page.word_cells else 0
        if words_count == 0:
            continue

        # Текстовые блоки (параграфы, заголовки, списки)
        lines = _build_text_lines(page, page_no)
        blocks = _group_lines_to_paragraphs(lines)

        # Таблицы (эвристика)
        tables = _detect_tables(page, page_no)
        for t in tables:
            table_counter += 1
            all_kids.append(t)

        all_kids.extend(blocks)

        if (page_idx + 1) % 10 == 0:
            print(f"  Parsed {page_idx + 1}/{limit} pages", file=sys.stderr, flush=True)

    raw = {
        "file name": file_name,
        "file_hash_sha256": file_hash,
        "number of pages": limit,
        "kids": all_kids,
    }
    return raw
