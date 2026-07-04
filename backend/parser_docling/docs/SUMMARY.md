# parser_docling — архитектура и метрики

## Текущее состояние (2026-07)

### ✅ Работает

| Компонента | Описание |
|---|---|
| **Pipeline** | `DocumentConverter` / `StandardPdfPipeline.execute()` с батчами по 5 стр. |
| **Enrich (DoclingDocument)** | Добавляет колонтитулы, подписи, пропущенные строки через PyMuPDF |
| **MD-конвейер** | `enrich` → `export_to_markdown()` → `md_to_json()` (основной, `--mode md`) |
| **Группировка списков** | Короткие параграфы (≤120 символов, ≥3) группируются в list-блоки |
| **Bbox списков** | Каждый item хранит свой bbox; block-level bbox — объединение всех |
| **Подписи изображений** | После `<!-- image -->` захватывается строка с Рис./Fig./Таблица как image.content |
| **Оценка качества** | `evaluate_quality.py` с flattening list-блоков для корректной сортировки |
| **Сравнение с ODO** | `compare_json.py` — метрики и расхождения |

### 📊 Метрики (327 страниц)

| Метрика | Docling (MD) | ODO |
|---|---|---|
| **Precision** | **0.996** | 0.828 |
| **Recall** | **0.989** | 0.620 |
| **F1** | **0.993** | 0.709 |
| Jaccard | **0.985** | — |
| Text similarity | **0.831** | — |

### 📦 Блоки (327 страниц)

| Тип | Docling (MD) | ODO |
|---|---|---|
| paragraph | 1 342 | — |
| heading | 459 | — |
| table | 323 | — |
| list | 166 (779 items) | — |
| image | 7 | — |
| **Всего** | **2 297** | — |

### 🏗 Архитектура

```
scripts/run_range.py --mode md
  → src/docling_mapper.py
      → convert_via_docling_md()
          → DocumentConverter (батчи по 5 стр., generate_picture_images=True)
          → enrich_docling_document() — PyMuPDF: добавляет пропущенные строки
          → export_to_markdown() — compact_tables, ImageRefMode.REFERENCED
          → src/md_to_json.py
              → split_markdown_blocks() — парсинг MD в блоки
              → _looks_like_list_item() — эвристика списков
              → md_to_document_json() — сборка финального JSON
          → bbox matching: _match_bbox() / _merge_bbox()
```

### 🔧 Тестовый сценарий

**Полный прогон:**
```bash
python scripts/run_range.py --start 1 --end 327 -o data/output_full.json --mode md --quiet
# ~11 мин
```

**Оценка:**
```bash
python scripts/evaluate_quality.py data/output_full.json pdf/2-020101-174-1.pdf
# F1 ≥ 0.99, Jaccard ≥ 0.97
```

**Локальная проверка списков:**
```bash
python scripts/run_range.py --start 11 --end 11 -o data/test_lists.json --mode md --quiet
# Стр. 11 — 63 элемента списка сокращений → 1 list-блок
```

**Проверка изображений:**
```bash
python scripts/run_range.py --start 6 --end 7 -o data/test_images.json --mode md --quiet
# 2 image с подписями Рис. 1.1.1-1 и Рис. 1.1.1-2
```

**Сравнение структур:**
```bash
python scripts/compare_json.py data/output_50.json data/odo_50.json
```

### ⚠️ Известные особенности

1. **Quality confidence (0.75)**
   - Эвристика не учитывает enrich — confidence занижен
   - Реальный F1 = 0.993
   - При оценке полагаться на evaluate_quality.py, не на confidence

2. **Изображения**
   - Docling находит только 7 из 9 (пропускает мелкие иконки стр. 17)
   - Подписи встроены в image.content, нет отдельных caption-блоков

3. **Заголовки**
   - 459 заголовков (ODO ~29) — Docling классифицирует многие bold-строки как heading
   - Это может быть избыточно, но не теряет данных

4. **Списки**
   - Группируются только строки ≤120 символов, ≥3 штук
   - Единичные короткие строки остаются параграфами
   - Эвристика `_looks_like_list_item()` требует ` - ` или заглавную аббревиатуру

5. **Таблицы**
   - Поддерживаются pipe-таблицы с многострочными ячейками
   - Bbox восстанавливается по ключу `('__table__', page_no)`

### 📦 Зависимости

```
docling-slim docling-core docling-parse
PyMuPDF (fitz)
pypdfium2
```

Установка:
```bash
python -m pip install docling-slim PyMuPDF pypdfium2
```
