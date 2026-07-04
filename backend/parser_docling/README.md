# parser_docling

Утилита парсинга PDF через **Docling** с пост-обработкой.  
Выдаёт JSON в структуре, совместимой с `JsonStandardizer` (`parser_service`).

## Структура проекта

```
parser_docling/
├── src/             # библиотечный код (docling_mapper, md_to_json, quality_metrics и др.)
├── scripts/         # CLI-утилиты (run_range, evaluate_quality, compare_json и др.)
├── data/            # результаты парсинга (JSON)
├── docs/            # документация (README, SUMMARY, TASK_MD_CONVERTER и др.)
├── archive/         # устаревший код (main, pdfium_mapper, layout_analyzer и др.)
├── pdf/             # тестовые PDF-файлы
└── requirements.txt
```

## Быстрый старт

```bash
cd backend/parser_docling

# Парсинг PDF с диапазоном страниц
python scripts/run_range.py --start 1 --end 50 -o data/output.json [--mode json|md]

# Оценка качества
python scripts/evaluate_quality.py data/output.json pdf/2-020101-174-1.pdf

# Сравнение с ODO
python scripts/compare_json.py data/output_docling.json data/odo_50.json
```

## Подробнее

см. [docs/README.md](docs/README.md)
