# parser_docling — итоги и задание для нового разработчика

## Что это

Утилита парсинга PDF через Docling + enrich (PyMuPDF). Выдаёт JSON в структуре, идентичной parser_service (opendataloader). Может заменить ODO.

## Текущее состояние

### ✅ Работает

| Компонента | Описание |
|---|---|
| **Pipeline** | `StandardPdfPipeline.execute()` с батчами по 5 стр. (чтобы избежать `std::bad_alloc`) |
| **Enrich (таблицы)** | Заполняет пустые блоки (таблицы с битым bbox) через PyMuPDF |
| **Колонтитулы** | Добавляет строки из PDF, которые Docling отфильтровал (название документа, номера страниц) |
| **Конвертация координат** | Docling (BOTTOMLEFT) → Screen (PyMuPDF) |
| **Оценка качества** | `evaluate_quality.py` — Precision/Recall/F1 через сырой PDF |
| **Сравнение с ODO** | `compare_json.py` — сравнение метрик и расхождений |
| **CLI** | `run_range.py --start N --end M -o file.json [--quiet]` |

### 📊 Метрики (50 страниц)

| Метрика | Docling (+enrich) | ODO |
|---|---|---|
| **Precision** | **0.993** | 0.828 |
| **Recall** | **0.996** | 0.620 |
| **F1** | **0.995** | 0.709 |
| Text similarity | 0.811 | 0.639 |
| Эвристический confidence | 0.750 | 0.646 |
| Проблемных страниц (sim < 0.5) | 0 | 16 |
| Время | ~57 сек / 50 стр | через API |

### 🏗 Архитектура

```
run_range.py (CLI)
  → docling_mapper.py
      → _try_pipeline()            — StandardPdfPipeline, батчи по 5 стр.
      → _docling_doc_to_raw()      — DoclingDocument → kids (raw JSON)
      → _enrich_empty_blocks()     — PyMuPDF:
          1. Заполняет пустые блоки (конвертация BOTTOMLEFT→Screen)
          2. Добавляет строки из PDF, пропущенные Docling
  → quality_metrics.py             — эвристический confidence
```

### 🔧 Инструменты

| Скрипт | Назначение |
|---|---|
| `run_range.py --start N --end M -o f.json [--quiet]` | Парсинг диапазона страниц |
| `evaluate_quality.py docling.json pdf [--max-pages N]` | Оценка Precision/Recall/F1 |
| `compare_json.py docling.json odo.json` | Сравнение Docling vs ODO |
| `run_via_api.py pdf_path` | Загрузка в API parser_service |

## Задание новому разработчику

### 1. Чистка кода

Удалить неиспользуемые файлы (проверить, что нигде не импортируются):
- `layout_analyzer.py`
- `pdfium_mapper.py`
- `main.py` (заменён на `run_range.py`)
- `test_clean_pipeline.py`, `test_direct_pipeline.py` (отладочные)
- `compare_50.py` (заменён на `compare_json.py`)

Из `docling_mapper.py` убрать:
- `_merge_pages` (больше не используется)
- `_build_via_parse` (не используется)
- `from layout_analyzer import parse_pdf as layout_parse` (не используется)

### 2. Полный прогон (327 стр.)

```bash
python run_range.py --start 1 --end 327 -o output_full.json --quiet
```

Ожидаемое время: ~6-7 минут.
После прогона:
```bash
python evaluate_quality.py output_full.json pdf/2-020101-174-1.pdf
```

### 3. DocumentConverter

`DocumentConverter` работает на диапазонах ≤5 страниц, но на больших падает с `std::bad_alloc`. Причина: он передаёт все страницы одним батчем в `pipeline.execute()`. 

Возможные решения:
- Дождаться исправления в `docling` (версия >2.109)
- Сделать ручную батчевую обёртку (как сейчас с `StandardPdfPipeline`)
- Использовать `DocumentConverter` только для малых PDF (<10 стр.)

### 4. Извлечение изображений

Сейчас блоки `type=image` имеют только `image_key` и пустой `content`. Нужно:
- В `_docling_doc_to_raw` при встрече `PictureItem` вызывать `item.get_image(doc)` → PIL Image
- Сохранять в папку `{pdf_stem}_images/`
- В JSON писать путь к файлу вместо `image_key`
- Учитывать `generate_picture_images = True` в `PdfPipelineOptions`

### 5. Оценка эвристики (quality_metrics.py)

Эвристика (0.75) занижена относительно реального F1 (0.995). Причины:
- Штрафует за короткие строки (колонтитулы, номера страниц)
- Не учитывает, что таблицы с битым bbox были обогащены

Варианты:
- Доработать weights для учёта колонтитулов
- Или использовать `evaluate_quality.py` как основную метрику

### 6. Зависимости

Установлены (hand-made):
```
docling-slim, docling-core, docling-parse, pypdfium2
opencv-python-headless, rtree, beautifulsoup4, python-pptx
PyMuPDF (fitz)
```

Проблема: полный `docling` не устанавливается — `pylatexenc` требует сборки C. Используется `docling-slim`.

При установке на новую машину:
```bash
python -m pip install docling-slim pypdfium2 PyMuPDF opencv-python-headless rtree beautifulsoup4 python-pptx
```
