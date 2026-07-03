"""
Оценка качества парсинга через сравнение с «сырым» текстом из PDF.
Извлекает текст через PyMuPDF (быстро, без ML).
Метрики:
  - Page-level Precision: доля блоков Docling, чей текст есть в сыром PDF
  - Page-level Recall: сколько символов сырого текста покрыто блоками Docling
  - Text similarity: сходство текста страницы (Docling vs raw)
"""
import json
import sys
import argparse
import re
from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict


# ============================================================
# 1. Извлечение «сырого» текста из PDF через PyMuPDF
# ============================================================

def extract_raw_text(pdf_path: str, max_pages: int = None) -> dict:
    """Извлекает весь текст страницы через PyMuPDF."""
    import fitz

    doc = fitz.open(pdf_path)
    total = len(doc)
    limit = min(max_pages or total, total)

    pages = {}
    for i in range(limit):
        page = doc[i]
        page_no = i + 1
        # Получаем весь текст страницы как есть
        raw_text = page.get_text('text')
        pages[page_no] = {
            'width': float(page.rect.width),
            'height': float(page.rect.height),
            'text': raw_text.strip(),
        }

    doc.close()
    return pages


# ============================================================
# 2. Нормализация и сравнение
# ============================================================

def norm(t: str) -> str:
    """Нормализация: нижний регистр, схлопнуть пробелы."""
    t = re.sub(r'[\s\u00a0]+', ' ', t)
    t = t.strip().lower()
    return t


def text_similarity(a: str, b: str) -> float:
    """SequenceMatcher по нормализованному тексту."""
    na, nb = norm(a), norm(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def words(s: str) -> set:
    """Множество слов из текста."""
    return set(re.findall(r'[а-яёa-z0-9]+', norm(s)))


def word_overlap_similarity(a: str, b: str) -> float:
    """
    Jaccard similarity по множеству слов.
    Нечувствительна к порядку — корректно оценивает страницы с таблицами,
    где SequenceMatcher даёт заниженную оценку из-за перестановки колонок.
    """
    wa = words(a)
    wb = words(b)
    if not wa and not wb:
        return 1.0
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def extract_block_text(block: dict) -> str:
    """
    Извлекает текст из блока, включая структурированные данные таблиц.
    Для таблиц с rows собирает текст построчно (ячейки через |).
    """
    text = block.get('content', '') or ''
    rows = block.get('rows', [])
    if rows:
        parts = []
        for r in rows:
            cells = r.get('cells', [])
            row_parts = []
            for c in cells:
                ct = ' '.join(k.get('content', '') for k in c.get('kids', []) if k.get('content', '').strip())
                if ct.strip():
                    row_parts.append(ct.strip())
            if row_parts:
                parts.append(' | '.join(row_parts))
        table_text = ' '.join(parts)
        if table_text:
            # Если нет плоского content, используем rows
            if not text.strip():
                text = table_text
            else:
                text = text + ' ' + table_text
    return text


def get_block_bbox(block: dict) -> list:
    """Возвращает bounding box блока: [x0, y0, x1, y1] (BOTTOMLEFT)."""
    bbox = block.get('bounding box', block.get('bbox', [0, 0, 0, 0]))
    if len(bbox) >= 4:
        return bbox
    return [0, 0, 0, 0]


def blocks_text_sorted(blocks: list, sort_key: str = 'original') -> str:
    """
    Собирает текст из блоков, отсортировав их по указанной стратегии.
    sort_key: 'original' — порядок Docling, 'asc' — BOTLEFT Y ascending,
              'desc' — BOTLEFT Y descending (screen ASC).
    """
    if sort_key == 'original':
        sorted_blocks = list(blocks)
    elif sort_key == 'asc':
        sorted_blocks = sorted(blocks, key=lambda b: get_block_bbox(b)[1])
    elif sort_key == 'desc':
        sorted_blocks = sorted(blocks, key=lambda b: -get_block_bbox(b)[1])
    else:
        sorted_blocks = list(blocks)
    return ' '.join(extract_block_text(b) for b in sorted_blocks)


# ============================================================
# 3. Оценка качества
# ============================================================

def evaluate(docling_blocks: list, raw_pages: dict) -> dict:
    """
    Оценка качества:
    - precision: доля блоков Docling, текст которых есть в сыром PDF (>60% overlap слов)
    - recall: доля слов сырого PDF, покрытых блоками Docling
    - И full-text similarity страницы
    """
    # Группируем блоки Docling по страницам
    doc_by_page = defaultdict(list)
    for b in docling_blocks:
        p = b.get('page', b.get('page number', 0))
        doc_by_page[p].append(b)

    all_pages = sorted(set(raw_pages.keys()) | set(doc_by_page.keys()))

    total_doc_blocks = 0
    total_matched_blocks = 0
    total_sim_sum = 0.0
    total_wosim_sum = 0.0
    total_sim_pages = 0
    per_page = {}

    for p in all_pages:
        d_blocks = doc_by_page.get(p, [])
        raw_text = raw_pages.get(p, {}).get('text', '')
        raw_words = words(raw_text)
        raw_word_count = len(raw_words)

        if not d_blocks and not raw_text:
            continue

        # --- Precision: блоки Docling (с учётом табличных rows) ---
        matched = 0
        doc_text_all = ''
        for b in d_blocks:
            b_text = extract_block_text(b)
            if not b_text.strip():
                continue
            doc_text_all += ' ' + norm(b_text)
            b_words = words(b_text)
            # Блок совпал, если >50% его слов есть в сыром тексте страницы
            if raw_words and b_words:
                overlap = len(b_words & raw_words)
                if overlap / max(len(b_words), 1) > 0.5:
                    matched += 1

        total_doc_blocks += len(d_blocks)
        total_matched_blocks += matched

        precision_p = matched / len(d_blocks) if d_blocks else 1.0

        # --- Recall: покрытие сырого текста ---
        doc_words = words(doc_text_all)
        if raw_words and doc_words:
            covered = len(raw_words & doc_words)
            recall_p = covered / raw_word_count
        else:
            covered = 0
            recall_p = 0.0 if raw_words else 1.0

        # --- Text similarity: макс по 3 стратегиям сортировки ---
        # Docling (BOTTOMLEFT) vs raw PDF (Screen) дают разный порядок блоков.
        # Пробуем: оригинальный порядок, BOTLEFT ASC, BOTLEFT DESC → берём макс.
        sort_strategies = ['original', 'asc', 'desc']
        sim_values = {}
        for sk in sort_strategies:
            text = blocks_text_sorted(d_blocks, sk)
            sim_values[sk] = text_similarity(text, raw_text)
        best_sk = max(sim_values, key=sim_values.get)
        sim = sim_values[best_sk]
        total_sim_sum += sim
        # --- Word overlap similarity (Jaccard, нечувствительна к порядку) ---
        full_text_doc = blocks_text_sorted(d_blocks, best_sk)
        wosim = word_overlap_similarity(full_text_doc, raw_text)
        total_wosim_sum += wosim
        total_sim_pages += 1

        per_page[p] = {
            'blocks': len(d_blocks),
            'precision': round(precision_p, 3),
            'recall': round(recall_p, 3),
            'text_similarity': round(sim, 3),
            'word_overlap_sim': round(wosim, 3),
            'sort_best': best_sk,
            'sort_asc': round(sim_values['asc'], 3),
            'sort_desc': round(sim_values['desc'], 3),
            'raw_chars': len(raw_text),
            'doc_chars': len(full_text_doc),
        }

    # Итог
    precision = total_matched_blocks / total_doc_blocks if total_doc_blocks > 0 else 0
    recall_avg = sum(pp['recall'] for pp in per_page.values()) / len(per_page) if per_page else 0
    avg_sim = total_sim_sum / total_sim_pages if total_sim_pages > 0 else 0
    avg_wosim = total_wosim_sum / total_sim_pages if total_sim_pages > 0 else 0
    f1 = 2 * precision * recall_avg / (precision + recall_avg) if (precision + recall_avg) > 0 else 0

    return {
        'total_docling_blocks': total_doc_blocks,
        'matched_blocks': total_matched_blocks,
        'precision': round(precision, 3),
        'recall_avg': round(recall_avg, 3),
        'f1': round(f1, 3),
        'avg_text_similarity': round(avg_sim, 3),
        'avg_word_overlap_sim': round(avg_wosim, 3),
        'per_page': per_page,
    }


# ============================================================
# 4. Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Evaluate Docling parsing quality against raw PDF text')
    parser.add_argument('docling_json', help='Path to Docling JSON output')
    parser.add_argument('pdf_path', help='Path to original PDF')
    parser.add_argument('--max-pages', type=int, default=None, help='Max pages')
    args = parser.parse_args()

    # Load Docling JSON
    with open(args.docling_json, encoding='utf-8') as f:
        data = json.load(f)

    content = data.get('content', data)
    doc_blocks = content.get('document', {}).get('block', [])
    if not doc_blocks:
        doc_blocks = content.get('kids', [])

    print(f"Docling blocks: {len(doc_blocks)}", flush=True)

    # Extract raw text
    print("Extracting raw text via PyMuPDF...", flush=True)
    raw_pages = extract_raw_text(args.pdf_path, args.max_pages)
    total_raw_chars = sum(len(p['text']) for p in raw_pages.values())
    print(f"Raw pages: {len(raw_pages)}, total chars: {total_raw_chars}", flush=True)

    # Evaluate
    result = evaluate(doc_blocks, raw_pages)

    print("\n" + "=" * 60)
    print("КАЧЕСТВО ПАРСИНГА: Docling vs сырой текст PDF")
    print("=" * 60)

    print(f"\n{'Метрика':50s} {'Значение':>10s}")
    print("-" * 62)
    print(f"{'Блоков Docling':50s} {result['total_docling_blocks']:>10d}")
    print(f"{'Из них совпало с PDF (precision)':50s} {result['matched_blocks']:>10d}")
    print(f"{'Precision (блоки найденные в PDF)':50s} {result['precision']:>10.3f}")
    print(f"{'Recall_avg (покрытие сырого текста)':50s} {result['recall_avg']:>10.3f}")
    print(f"{'F1':50s} {result['f1']:>10.3f}")
    print(f"{'Text similarity (SequenceMatcher)':50s} {result['avg_text_similarity']:>10.3f}")
    print(f"{'Word overlap similarity (Jaccard)':50s} {result['avg_word_overlap_sim']:>10.3f}")

    # Проблемные страницы по text_similarity
    low_pages = [(p, d) for p, d in result['per_page'].items()
                 if d['text_similarity'] < 0.5]
    print(f"\n--- Проблемные страницы (text_similarity < 0.5): {len(low_pages)} ---")
    for p, d in sorted(low_pages)[:15]:
        print(f"  P{p:3d}: P={d['precision']:.2f} R={d['recall']:.2f} "
              f"sim={d['text_similarity']:.2f} wosim={d['word_overlap_sim']:.2f} "
              f"sort={d['sort_best']} asc={d['sort_asc']:.2f} desc={d['sort_desc']:.2f} "
              f"doc={d['doc_chars']:5d} raw={d['raw_chars']:5d}")

    # Проблемные страницы по word_overlap
    low_wo = [(p, d) for p, d in result['per_page'].items()
              if d['word_overlap_sim'] < 0.7]
    if low_wo:
        print(f"\n--- Страницы с потерей данных (word_overlap < 0.7): {len(low_wo)} ---")
        for p, d in sorted(low_wo)[:10]:
            print(f"  P{p:3d}: wosim={d['word_overlap_sim']:.2f} missing={d['raw_chars']-d['doc_chars']:+d}")


if __name__ == '__main__':
    main()
