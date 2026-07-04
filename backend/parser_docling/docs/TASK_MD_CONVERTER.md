# Задача: Конвертер Markdown → JSON для замены ODO-формата

## Контекст

Сейчас у нас сложный конвейер:

```
PDF → Docling Pipeline → docling_to_raw_json() → enrich (JSON) → standardize → normalize → JSON
```

Он делает много лишнего: парсит DoclingDocument в ODO-формат, потом обогащает на уровне сырого JSON, потом стандартизирует.
Docling умеет экспортировать `export_to_markdown()` — на выходе чистый Markdown без дублей.

**Новый, более короткий конвейер:**

```
PDF → Docling Pipeline → enrich (DoclingDocument) → export_to_markdown(params) → md_to_json()
```

## Что уже сделано

`md_to_json.py` — прототип конвертера Markdown → JSON без LLM. Умеет:
- Парсить заголовки (`#`, `##`, ...) → `type: heading`
- Парсить параграфы → `type: paragraph`
- Парсить pipe-таблицы → `type: table` с `rows` и `cells`
- Распознавать `<!-- image -->` → `type: image`
- Собирать полный JSON в структуре opendataloader

## Важные находки по export_to_markdown()

### 1. `compact_tables=True` — чистая разметка таблиц

Без флага:
```
|   № | Описание документации                               | Штамп   | ТП   |
```

С флагом:
```
| № | Описание документации | Штамп | ТП | РД | ПДСП | Примечание |
| - | - | - | - | - | - | - |
| .1 | Чертежи... | С | ● | ● | ● | |
```

Корректная pipe-таблица, которая нормально парсится.

### 2. `image_mode=ImageRefMode.REFERENCED` — подписи к рисункам

Без флага:
```markdown
<!-- image -->
```

С флагом:
```markdown
<!-- image -->

Рис.3.2 Типовые сечения мидель-шпангоута нефтяного танкера ESP
```

Caption-текст, ассоциированный с `PictureItem`, автоматически включается в MD.

### 3. `doc.add_text()` — можно вставлять пропущенные элементы

`DoclingDocument.add_text()` и `add_picture()` существуют и работают.
Можно добавить колонтитулы/подписи через PyMuPDF прямо в документ до export.

### 4. `traverse_pictures=True` — включает обработку изображений

Без этого флага PictureItem могут не обрабатываться.

## Рекомендуемый конвейер

```python
from docling_core.types.doc.base import ImageRefMode, DocItemLabel

# 1. Pipeline (как сейчас)
doc = pipeline.execute(in_doc)

# 2. Enrich на уровне DoclingDocument (через PyMuPDF)
#    Находит строки, пропущенные Docling (колонтитулы, подписи)
#    и добавляет их через doc.add_text() с правильным label
import fitz
pdf = fitz.open(pdf_path)
for pno in all_pages:
    missing_lines = find_missing_lines(doc, pdf, pno)
    for text, bbox in missing_lines:
        # Конвертация bbox: Screen → BOTTOMLEFT
        prov = docling_core.types.doc.ProvResult(
            page_no=pno,
            bbox=...,  # BOTTOMLEFT
        )
        doc.add_text(
            label=DocItemLabel.PAGE_HEADER,  # или CAPTION, PAGE_FOOTER
            text=text,
            prov=prov,
        )

# 3. Export с правильными параметрами
md = doc.export_to_markdown(
    compact_tables=True,                      # чистые таблицы
    image_mode=ImageRefMode.REFERENCED,       # включает caption к рисункам
    traverse_pictures=True,                   # обрабатывает изображения
)

# 4. MD → JSON (без enrich на уровне JSON)
from md_to_json import md_to_document_json
result = md_to_document_json([(pno, md)])    # для одной страницы
# или для всего документа:
result = md_to_document_json(page_md_list)   # list of (page_num, md_text)
```

**Преимущества перед старым конвейером:**
- Не нужен `_docling_doc_to_raw()` (преобразование DoclingDocument → сырой JSON)
- Не нужен enrich на уровне JSON (колонтитулы, подписи — добавляются в DoclingDocument до export)
- Не нужна дедупликация блоков (MD экспорт не дублирует табличные данные)
- Не нужен `JsonStandardizer`/`Normalizer` (если ODO-совместимость не требуется)

## Что нужно сделать

### 1. Enrich на уровне DoclingDocument (приоритет)

Написать функцию `enrich_docling_document(doc, pdf_path)`, которая:
- Открывает PDF через PyMuPDF
- Для каждой страницы находит строки, отсутствующие в Docling
- Добавляет их через `doc.add_text()` с корректным `ProvResult`
- Для строк `Рис.` использует `label=DocItemLabel.CAPTION`
- Для колонтитулов использует `label=DocItemLabel.PAGE_HEADER` / `PAGE_FOOTER`
- Координаты bbox конвертирует Screen → BOTTOMLEFT

### 2. Заменить DoclingParseV2DocumentBackend

`FutureWarning: DoclingParseV2DocumentBackend was removed in docling 2.74.0`

Заменить на `DoclingParseDocumentBackend` во всех файлах:
- `docling_mapper.py`
- `run_range.py`
- `md_to_json.py` (если используется прямой pipeline)

### 3. Разобраться с расхождением строк таблицы

На странице 152 старый Pipeline выдаёт 15 строк таблицы, MD → 14.
Причина: последняя строка таблицы в MD рендерится с многострочным контентом,
который `parse_table()` не захватывает.

**Что делать:**
- Взять `md_p152.md`, найти 15-ю строку
- Понять, почему `split_markdown_blocks()` или `parse_table()` её теряет
- Починить парсер

### 4. Извлечение изображений

Для `PictureItem`:
- `image_mode=ImageRefMode.REFERENCED` — возможно, уже сохраняет изображения
- Если нет — использовать `item.get_image(doc)` в enrich
- Сохранять в папку `{pdf_stem}_images/`
- В JSON писать путь к файлу вместо `<!-- image -->`

### 5. Сравнить метрики на полном документе

Запустить полный прогон (327 стр.) через MD-конвейер и сравнить с текущими метриками:

```bash
python run_range.py --start 1 --end 327 -o output_full_via_docling.json
# → pipeline → enrich → export_to_markdown() → md_to_document_json()
# → evaluate_quality.py output_full_via_docling.json pdf/2-020101-174-1.pdf
```

Сравнить:
- Precision / Recall / F1 / Jaccard
- Количество блоков на страницу (меньше = лучше = нет дублей)
- Проблемные страницы

### 6. Удалить неиспользуемые файлы

После подтверждения, что MD-конвейер работает:

- `layout_analyzer.py`
- `pdfium_mapper.py`
- `main.py` (заменён на `run_range.py`)
- `test_clean_pipeline.py`, `test_direct_pipeline.py`
- `compare_50.py` (заменён на `compare_json.py`)

Из `docling_mapper.py` убрать:
- `_merge_pages` (не используется)
- `_build_via_parse` (не используется)
- Импорт `from layout_analyzer import parse_pdf as layout_parse`

### 7. (Опционально) `generate_picture_images = True`

В `PdfPipelineOptions` включить `generate_picture_images = True`.
Это может улучшить качество извлечения изображений и их caption-текста.

## Критерии готовности

- [ ] `enrich_docling_document()` добавляет подписи Рис. и колонтитулы
- [ ] `md_to_json()` корректно парсит все типы блоков на всём документе (327 стр.)
- [ ] Precision ≥ 0.99, Recall ≥ 0.98, Jaccard ≥ 0.97
- [ ] Блоков на страницу ≤ 6 в среднем (сейчас ~17)
- [ ] Изображения извлечены (не `<!-- image -->`)
- [ ] DoclingParseV2DocumentBackend → DoclingParseDocumentBackend
- [ ] Неиспользуемые файлы удалены
- [ ] `evaluate_quality.py` с Jaccard и multi-strategy sorting включён
