"""
Расширенное сравнение JSON: Docling vs ODO.
Оценивает:
  - Базовые метрики (блоки, заголовки, таблицы, изображения)
  - Quality confidence
  - Расхождение структуры (типы блоков по страницам)
  - Совпадение содержания (текст блоков)
  - Bbox deviation
"""
import json
import sys
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher


def load_json(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def group_blocks_by_page(blocks: list) -> dict:
    pages = {}
    for b in blocks:
        p = b.get('page', b.get('page number', 0))
        pages.setdefault(p, []).append(b)
    return pages


def text_similarity(a: str, b: str) -> float:
    """Сходство текста 0..1."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def compare_blocks(doc_blocks: list, odo_blocks: list) -> dict:
    """
    Сравнивает блоки двух парсеров.
    Возвращает метрики расхождения.
    """
    # Типы блоков
    doc_types = Counter(b.get('type') for b in doc_blocks)
    odo_types = Counter(b.get('type') for b in odo_blocks)

    all_types = set(doc_types.keys()) | set(odo_types.keys())
    type_diff = {}
    for t in sorted(all_types):
        type_diff[t] = {
            'docling': doc_types.get(t, 0),
            'odo': odo_types.get(t, 0),
            'delta': doc_types.get(t, 0) - odo_types.get(t, 0),
        }

    # Группируем по страницам
    doc_pages = group_blocks_by_page(doc_blocks)
    odo_pages = group_blocks_by_page(odo_blocks)

    all_pages = sorted(set(doc_pages.keys()) | set(odo_pages.keys()))
    page_type_match = 0
    page_type_total = 0
    page_text_matches = []

    for p in all_pages:
        d_blocks = doc_pages.get(p, [])
        o_blocks = odo_pages.get(p, [])

        # Сравнение количества блоков по типам на странице
        d_types = Counter(b.get('type') for b in d_blocks)
        o_types = Counter(b.get('type') for b in o_blocks)

        for t in all_types:
            page_type_total += 1
            if d_types.get(t, 0) == o_types.get(t, 0):
                page_type_match += 1

        # Сравнение текстового содержания
        d_texts = [b.get('content', '') for b in d_blocks if b.get('content')]
        o_texts = [b.get('content', '') for b in o_blocks if b.get('content')]

        if d_texts and o_texts:
            # Best-match каждой строки
            match_scores = []
            for dt in d_texts:
                best = max(text_similarity(dt, ot) for ot in o_texts) if o_texts else 0
                match_scores.append(best)
            for ot in o_texts:
                best = max(text_similarity(ot, dt) for dt in d_texts) if d_texts else 0
                match_scores.append(best)

            avg_match = sum(match_scores) / len(match_scores) if match_scores else 0
            page_text_matches.append(avg_match)

    text_match_avg = sum(page_text_matches) / len(page_text_matches) if page_text_matches else 0
    type_match_ratio = page_type_match / page_type_total if page_type_total > 0 else 0

    return {
        'type_counts': type_diff,
        'type_match_by_page': round(type_match_ratio * 100, 1),
        'text_similarity_avg': round(text_match_avg * 100, 1),
        'pages_docling': len(doc_pages),
        'pages_odo': len(odo_pages),
    }


def compare_header_levels(doc_blocks, odo_blocks):
    """Сравнение уровней заголовков."""
    d_headings = [(b.get('page'), b.get('content', ''), b.get('heading_level'))
                  for b in doc_blocks if b.get('type') == 'heading']
    o_headings = [(b.get('page'), b.get('content', ''), b.get('heading_level'))
                  for b in odo_blocks if b.get('type') == 'heading']

    # Поиск совпадающих заголовков
    matched = 0
    level_diff = 0
    for dp, dc, dl in d_headings:
        for op, oc, ol in o_headings:
            if dp == op and text_similarity(dc, oc) > 0.8:
                matched += 1
                if dl != ol:
                    level_diff += 1
                break

    return {
        'docling_headings': len(d_headings),
        'odo_headings': len(o_headings),
        'matched_headings': matched,
        'level_mismatch': level_diff,
    }


def compare_quality(doc_q, odo_q):
    """Сравнение quality confidence."""
    return {
        'docling_confidence': doc_q.get('confidence', 0),
        'odo_confidence': odo_q.get('confidence', 0),
        'delta': round(doc_q.get('confidence', 0) - odo_q.get('confidence', 0), 3),
        'docling_pages': doc_q.get('pages_processed', 0),
        'odo_pages': odo_q.get('pages_processed', 0),
    }


def main():
    doc_path = 'output_50.json'
    odo_path = 'odo_50.json'

    if len(sys.argv) >= 3:
        doc_path = sys.argv[1]
        odo_path = sys.argv[2]
    elif len(sys.argv) == 2:
        doc_path = sys.argv[1]

    doc = load_json(doc_path)
    odo = load_json(odo_path)

    d_doc = doc['document']
    d_odo = odo['document']

    print("=" * 60)
    print("СРАВНЕНИЕ JSON: Docling vs ODO")
    print("=" * 60)

    # 1. Базовые метрики
    d_blocks = d_doc['block']
    o_blocks = d_odo['block']

    print(f"\n{'Метрика':40s} {'Docling':>10s} {'ODO':>10s} {'Δ':>8s}")
    print("-" * 70)

    metrics = [
        ('Всего блоков', len(d_blocks), len(o_blocks)),
        ('Заголовки (heading)', sum(1 for b in d_blocks if b['type']=='heading'),
         sum(1 for b in o_blocks if b['type']=='heading')),
        ('Параграфы', sum(1 for b in d_blocks if b['type']=='paragraph'),
         sum(1 for b in o_blocks if b['type']=='paragraph')),
        ('Таблицы', sum(1 for b in d_blocks if b['type']=='table'),
         sum(1 for b in o_blocks if b['type']=='table')),
        ('Изображения', sum(1 for b in d_blocks if b['type']=='image'),
         sum(1 for b in o_blocks if b['type']=='image')),
        ('Списки', sum(1 for b in d_blocks if b['type']=='list'),
         sum(1 for b in o_blocks if b['type']=='list')),
    ]

    for name, d_val, o_val in metrics:
        delta = d_val - o_val
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"{name:40s} {d_val:>10d} {o_val:>10d} {delta_str:>8s}")

    # 2. Quality
    q_comp = compare_quality(doc['quality'], odo['quality'])
    print(f"\n{'Quality confidence':40s} {q_comp['docling_confidence']:>10.3f} {q_comp['odo_confidence']:>10.3f} {q_comp['delta']:>+8.3f}")

    # 3. Заголовки
    h_comp = compare_header_levels(d_blocks, o_blocks)
    print(f"\n--- Заголовки ---")
    print(f"  Docling заголовков:   {h_comp['docling_headings']}")
    print(f"  ODO заголовков:       {h_comp['odo_headings']}")
    print(f"  Совпало (text>80%):   {h_comp['matched_headings']}")
    print(f"  Разный уровень:       {h_comp['level_mismatch']}")

    # 4. Расхождение структуры
    b_comp = compare_blocks(d_blocks, o_blocks)
    print(f"\n--- Расхождение структуры ---")
    print(f"  Совпадение типов блоков по страницам: {b_comp['type_match_by_page']:.1f}%")
    print(f"  Среднее сходство текста:              {b_comp['text_similarity_avg']:.1f}%")
    print(f"  Страниц с блоками (Docling):          {b_comp['pages_docling']}")
    print(f"  Страниц с блоками (ODO):              {b_comp['pages_odo']}")

    # 5. Детально по типам
    print(f"\n--- Типы блоков ---")
    print(f"{'Тип':25s} {'Docling':>8s} {'ODO':>8s} {'Δ':>8s}")
    print("-" * 50)
    for t, v in sorted(b_comp['type_counts'].items()):
        delta = v['docling'] - v['odo']
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"{t:25s} {v['docling']:>8d} {v['odo']:>8d} {delta_str:>8s}")


if __name__ == '__main__':
    main()
