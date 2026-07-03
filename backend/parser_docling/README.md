# parser_docling

Утилита для парсинга PDF с помощью **Docling** (вместо OpenDataLoader).
JSON на выходе — в той же структуре, что и `JsonStandardizer` (`parser_service`).

## Использование

```bash
cd backend/parser_docling
python main.py path/to/document.pdf [-o output.json] [--max-pages N] [--engine docling|pdfium]
```

- `--engine docling` — Docling (через pipeline, при ошибке — fallback на raw parser)
- `--engine pdfium` — pypdfium2 (быстро, один блок на страницу)
- `--max-pages N` — ограничить число страниц

## Структура выхода

```json
{
  "document": {
    "source": {"file_name", "file_hash_sha256", "page_count", ...},
    "pages": [{"page", "width", "height"}, ...],
    "block": [{"number", "type", "page", "bbox", "content"/"rows"/"image_key", ...}, ...]
  },
  "quality": {"confidence", "pages_processed", ..., "per_page": [...]},
  "errors": [],
  "status": "completed",
  "metadata": {"total_pages", "has_tables"}
}
```

## Детали работы

### docling engine
1. Пытается `StandardPdfPipeline` (с таблицами, layout analysis)
2. При ошибке — fallback на `DoclingPdfParser` + сборка `DoclingDocument` вручную через `docling-core`
3. Маппинг → стандартный JSON

### pdfium engine
- `pypdfium2` — прямой рендеринг, без ML, текст одним блоком на страницу
- Быстро, подходит для любых PDF

## Сравнение с opendataloader

1. `python main.py doc.pdf -o docling.json --engine docling`
2. Запустить parser_service (opendataloader) → opendataloader.json
3. Сравнить блоки, таблицы, качество
