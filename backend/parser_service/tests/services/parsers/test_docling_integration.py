"""
Интеграционный тест DoclingParser.
Сверяет извлечение изображений и текста с raw-содержимым PDF (fitz).
Парсинг docling — батчами по 5 страниц (для избежания std::bad_alloc).
"""
import os, sys, time, re, json, tempfile
from pathlib import Path
from typing import Dict, List, Tuple
from io import BytesIO

os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_SECRET_KEY", "test")
os.environ.setdefault("MINIO_BUCKET", "test")
os.environ.setdefault("MINIO_IMAGE_BUCKET", "test")
os.environ.setdefault("USE_MOCK_PARSER", "False")
os.environ.setdefault("DOCLING_DO_OCR", "False")
os.environ.setdefault("DOCLING_TABLE_STRUCTURE", "True")
os.environ.setdefault("LOG_LEVEL", "WARNING")

_PARSER_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_PARSER_ROOT))

from app.services.parsers.docling.docling_mapper import convert_via_docling_md


def raw_page_info(pdf_path: str) -> List[dict]:
    """Raw-информация о страницах через fitz."""
    import fitz
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        page = doc[i]
        imgs = page.get_images()
        text = page.get_text() or ""
        tokens = set(re.findall(r'[а-яёА-ЯЁa-zA-Z0-9]+', text.lower()))
        pages.append({
            "page": i + 1,
            "has_images": len(imgs) > 0,
            "num_images": len(imgs),
            "tokens": tokens,
        })
    doc.close()
    return pages


def run(pdf_path: str, max_pages: int = 5) -> dict:
    """Парсит PDF батчами и сверяет с raw."""
    # 1. Raw информация
    raw = raw_page_info(pdf_path)
    raw_pages = raw[:max_pages]

    # 2. Парсинг docling (convert_via_docling_md уже делает батчи по 5)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        result = convert_via_docling_md(
            pdf_path=pdf_path, max_pages=max_pages, page_start=1,
            images_dir=os.path.join(tmp, "images"),
        )
    elapsed = time.time() - t0

    # 3. Собираем image_key по страницам из docling
    blocks = result.get("content", {}).get("document", {}).get("block", [])
    img_dir = os.path.join(tempfile.gettempdir(), "docling_images_temp")
    # (изображения уже сохранены внутри convert_via_docling_md, но во временной директории,
    #  которая удалена. Но image_key в JSON остался — проверим его наличие)

    doc_img_pages = {}
    for b in blocks:
        if b.get("type") != "image":
            continue
        pno = b.get("page number", 1)
        ikey = b.get("image_key", "")
        doc_img_pages.setdefault(pno, []).append(ikey)

    # 4. Сверка изображений
    img_report = []
    for rp in raw_pages:
        pno = rp["page"]
        if rp["has_images"]:
            doc_imgs = doc_img_pages.get(pno, [])
            with_key = [k for k in doc_imgs if k]
            img_report.append({
                "page": pno,
                "raw_count": rp["num_images"],
                "docling_count": len(doc_imgs),
                "with_key": len(with_key),
                "status": "OK" if with_key else "MISS",
            })
        elif pno in doc_img_pages:
            img_report.append({
                "page": pno,
                "raw_count": 0,
                "docling_count": len(doc_img_pages[pno]),
                "with_key": len([k for k in doc_img_pages[pno] if k]),
                "status": "EXTRA",
            })

    # 5. Сверка текста (токены)
    doc_tokens = set()
    for b in blocks:
        t = b.get("type", "")
        c = b.get("content", "") or ""
        if t in ("paragraph", "heading"):
            doc_tokens.update(re.findall(r'[а-яёА-ЯЁa-zA-Z0-9]+', c.lower()))
        elif t == "list":
            for item in b.get("items", []):
                ic = item.get("content", "") if isinstance(item, dict) else str(item)
                doc_tokens.update(re.findall(r'[а-яёА-ЯЁa-zA-Z0-9]+', ic.lower()))

    raw_tokens = set()
    for rp in raw_pages:
        raw_tokens.update(rp["tokens"])

    common = doc_tokens & raw_tokens

    return {
        "pdf": Path(pdf_path).name,
        "pages": max_pages,
        "time_s": round(elapsed, 1),
        "time_per_page": round(elapsed / max_pages, 2),
        "blocks": len(blocks),
        "images": {
            "report": img_report,
            "total_raw": sum(rp["num_images"] for rp in raw_pages if rp["has_images"]),
            "total_docling": len(doc_img_pages),
            "found": len(img_report),
            "missed": len([r for r in img_report if r["status"] == "MISS"]),
        },
        "text": {
            "raw_tokens": len(raw_tokens),
            "docling_tokens": len(doc_tokens),
            "common_tokens": len(common),
            "recall_pct": round(len(common) / len(raw_tokens) * 100, 1) if raw_tokens else 0,
        },
    }


def test_all_pages():
    """Полный тест всех страниц PDF (батчи по 5 страниц внутри docling)."""
    pdf = str(_PARSER_ROOT / "pdf" / "2-020101-013.pdf")
    
    import fitz
    doc = fitz.open(pdf)
    total = len(doc)
    doc.close()

    # Парсим весь PDF батчами (docling сам делает по 5 страниц внутри convert_via_docling_md)
    r = run(pdf, max_pages=total)
    
    print("=" * 60)
    print(f"  INTEGRATION TEST: {r['pdf']}")
    print(f"  Страниц: {r['pages']}, время: {r['time_s']}s ({r['time_per_page']}s/p)")
    print(f"  Блоков: {r['blocks']}")
    print("=" * 60)

    # Изображения
    print(f"\n  ИЗОБРАЖЕНИЯ (raw={r['images']['total_raw']}, docling={r['images']['total_docling']} страниц с img)")
    if r["images"]["report"]:
        print(f"  {'Стр':>4} {'Raw':>5} {'Doc':>5} {'Key':>5}  Статус")
        for ir in r["images"]["report"]:
            status_icon = "✓" if ir["status"] == "OK" else "✗ MISS" if ir["status"] == "MISS" else "⚠ EXTRA"
            print(f"  {ir['page']:4} {ir['raw_count']:5} {ir['docling_count']:5} {ir['with_key']:5}  {status_icon}")
    
    if r["images"]["missed"] > 0:
        print(f"\n  ✗ Пропущено страниц с изображениями: {r['images']['missed']}")
    else:
        print(f"\n  ✓ Все страницы с изображениями покрыты")

    # Текст
    t = r["text"]
    print(f"\n  ТЕКСТ: raw={t['raw_tokens']} токенов, docling={t['docling_tokens']}, recall={t['recall_pct']}%")
    status_t = "✓" if t["recall_pct"] >= 85 else "⚠" if t["recall_pct"] >= 60 else "✗"
    print(f"  {status_t} Token recall: {t['common_tokens']}/{t['raw_tokens']} = {t['recall_pct']}%")
    
    # Assert
    assert r["images"]["missed"] == 0, f"Пропущены страницы с картинками: {r['images']['missed']}"
    assert t["recall_pct"] >= 70, f"Низкий recall текста: {t['recall_pct']}%"
    assert r["time_per_page"] <= 30, f"Медленно: {r['time_per_page']}s/page"
    
    print(f"\n{'=' * 60}")
    print(f"  ✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    test_all_pages()
