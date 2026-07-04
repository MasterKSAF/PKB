"""
CLI-утилита парсинга PDF через Docling или pypdfium2.
На выходе — JSON в структуре JsonStandardizer (как у opendataloader).

Использование:
    python main.py path/to/file.pdf [-o output.json] [--max-pages N] [--engine docling|pdfium]
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Parse PDF and output standard JSON")
    parser.add_argument("pdf_path", type=str, help="Path to PDF file")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Output JSON file (default: stdout)")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Parse only first N pages")
    parser.add_argument("--engine", type=str, default="pdfium",
                        choices=["docling", "pdfium"],
                        help="Parsing engine: docling (if works) or pdfium (default)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {pdf_path} with {args.engine}...", file=sys.stderr)

    if args.engine == "docling":
        from docling_mapper import convert_docling_to_standard
        result = convert_docling_to_standard(str(pdf_path), max_pages=args.max_pages)
    else:
        from pdfium_mapper import convert_to_standard
        result = convert_to_standard(str(pdf_path), max_pages=args.max_pages)

    json_str = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(json_str, encoding="utf-8")
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
