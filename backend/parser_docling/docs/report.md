# Отчёт: Алгоритмы парсинга PDF в parser_docling

## Общая схема

Проект `parser_docling` реализует замену устаревшему OpenDataLoader (ODO) на современный Docling.
Разработано **два конвейера** на базе Docling, которые преобразуют PDF в стандартизированный JSON.

```
PDF → [Конвейер] → JSON (структура opendataloader)
```

---

## 1. ODO — старый парсер (через Docker API)

**Назначение:** референсный парсер, работающий через parser-service в Docker.

**Команда:** `python run_via_api.py pdf.pdf -o out.json --max-pages 999`

**Алгоритм:**
1. Загрузка PDF в MinIO
2. POST `/api/v1/parser/process` с `mode=full`
3. Внутри контейнера запускается `opendataloader-pdf` с `--hybrid docling-fast`
4. Результат возвращается через `GET /api/v1/parser/process/{id}/result`

**Характеристики:**
- Работает только через Docker (parser-service)
- Использует `opendataloader-pdf` внутри контейнера
- Под капотом — Java/PDFBox + docling-fast (гибридный режим)
- Качество: Precision 0.828, Recall 0.620, F1 0.709 (50 стр)

**Недостатки:**
- Только через API (нет локального запуска)
- Требует MinIO и Redis
- Зависит от Docker-инфраструктуры
- `--hybrid docling-fast` падает на некоторых документах (код 1)

---

## 2. Docling JSON конвейер — старый (локальный)

**Назначение:** локальный парсинг без Docker, полный контроль.

**Файлы:** `docling_mapper.py` (функции `docling_to_raw_json`, `_try_pipeline`, `_docling_doc_to_raw`, `_enrich_empty_blocks`)

**Команда:** `python run_range.py --mode json --start 1 --end N -o out.json`

**Схема работы:**

```
PDF → StandardPdfPipeline (батчи по 5 стр) → DoclingDocument
    → _docling_doc_to_raw (→ kids/raw JSON)
    → _enrich_empty_blocks (PyMuPDF)
        → заполнение пустых блоков
        → добавление пропущенных колонтитулов
        → добавление подписей "Рис."
        → дедупликация дублей таблиц
    → JsonStandardizer → Normalizer → JSON
```

### 2.1. Pipeline (StandardPdfPipeline)

**`_try_pipeline()`** (строки 349-410):
- Создаёт `StandardPdfPipeline` с layout analysis и распознаванием таблиц
- **Батчи по 5 страниц** — чтобы избежать `std::bad_alloc` на больших документах
- Каждый батч выполняется отдельным `pipeline.execute()`, результаты сливаются через `_merge_pages()`
- Параметры: `do_ocr=False`, `do_table_structure=True`, `num_threads=4`
- При ошибке конкретного батча — пропускает, продолжает со следующим

### 2.2. Конвертация DoclingDocument → raw JSON

**`_docling_doc_to_raw()`** (строки 701-764):
- Обходит все `TextItem`, `TableItem`, `PictureItem` через `iterate_items()`
- Каждому элементу присваивает `page number`, `bounding box`, `type`
- Для таблиц: преобразует `TableData` в структуру `rows → cells → kids`
- Координаты конвертирует из BOTTOMLEFT (Docling) в Screen (PyMuPDF)

### 2.3. Обогащение (Enrich) через PyMuPDF

**`_enrich_empty_blocks()`** (строки 442-698) — ключевая функция:

**Шаг 1 — Заполнение пустых блоков:**
- Находит блоки с пустым `content` (часто таблицы с битым bbox)
- Извлекает текст из сырого PDF через PyMuPDF по координатам
- Конвертирует Docling BOTTOMLEFT → Screen координаты
- Если bbox < 20px (битый) — берёт текст всей страницы

**Шаг 2 — Колонтитулы:**
- Для каждой страницы собирает все строки из PyMuPDF
- Сравнивает с текстом Docling (normalized)
- Строки длиной ≥15 символов, отсутствующие в Docling → добавляет как `paragraph`
- Захватывает: название документа, номер страницы, заголовки разделов

**Шаг 3 — Подписи "Рис.":**
- Ищет строки вида "Рис.X.X" длиной 7-30 символов
- Проверяет, что их нет в Docling
- Добавляет как `paragraph`

**Шаг 4 — Дедупликация:**
- Docling часто дублирует содержимое таблиц: один раз как `table.rows`, второй как `paragraph`
- Для каждой страницы собирает все слова из таблиц
- Удаляет параграфы, у которых >70% слов перекрываются с табличными

**Шаг 5 — Заполнение table.content:**
- Если у таблицы пустой `content`, но есть `rows` — собирает текст из ячеек

### 2.4. Стандартизация (через JsonStandardizer + Normalizer)

**`convert_docling_to_standard()`** (строки 803-842):
- Оборачивает enriched JSON в структуру `{document: {source, pages, block}, quality, errors, status}`
- Вычисляет `quality.confidence` через эвристику `quality_metrics.py`
- Включает per-page метрики

---

## 3. Docling MD конвейер — новый (локальный)

**Назначение:** упрощённый конвейер через Markdown — без лишних преобразований.

**Файлы:** `docling_mapper.py` (функция `convert_via_docling_md`), `md_to_json.py`, `enrich_docling_document()`

**Команда:** `python run_range.py --mode md --start 1 --end N -o out.json`

**Схема работы:**

```
PDF → DocumentConverter (батчи по 5 стр) → DoclingDocument
    → enrich_docling_document() (PyMuPDF)
    → export_to_markdown(params) — постранично
    → md_to_document_json() — парсинг Markdown → JSON
    → Простановка bbox из карты enrich
```

### 3.1. DocumentConverter

**`convert_via_docling_md()`** (строки 159-323):
- Использует `DocumentConverter` вместо `StandardPdfPipeline`
- Те же батчи по 5 страниц, та же проблема `std::bad_alloc`
- Параметры: `generate_picture_images=True`, `do_table_structure=True`

### 3.2. Enrich на уровне DoclingDocument

**`enrich_docling_document()`** (строки 29-156):
- В отличие от JSON-конвейера (enrich на уровне сырого JSON), здесь enrich делается **на уровне DoclingDocument**
- Для каждой страницы:
  1. Собирает все текстовые элементы Docling с их bbox
  2. Извлекает строки из PyMuPDF
  3. Сравнивает по координатам (bbox overlap), а не по тексту
  4. Если строка из PDF не перекрывается ни с одним элементом Docling — добавляет через `doc.add_text()`
- Для строк "Рис." — `label=DocItemLabel.CAPTION`
- Для остальных пропущенных — `label=DocItemLabel.PAGE_HEADER` / `PARAGRAPH`
- Возвращает `bbox_map = {(page_no, norm_text): [l, t, r, b]}` для простановки bbox в финальном JSON

**Преимущество:** Оперирует на уровне объектов DoclingDocument, а не сырого JSON. Меньше промежуточных форматов.

### 3.3. Export → Markdown

- Каждая страница экспортируется отдельно через `doc.export_to_markdown(page_no=N, ...)`
- Параметры:
  - `compact_tables=True` — чистые pipe-таблицы без лишних пробелов
  - `image_mode=ImageRefMode.REFERENCED` — включает caption к рисункам
  - `traverse_pictures=True` — обрабатывает изображения
- Результат: `list of (page_no, md_text)`

### 3.4. Markdown → JSON (md_to_json.py)

**`md_to_document_json(page_mds, file_name)`:**
- Парсит Markdown без LLM — только регулярные выражения
- **Заголовки:** `^(#{1,6})\s+(.+)$` → `type: heading, level: N`
- **Таблицы:** `^\|.+\|[\s\S]*?^\|.+\|` → `type: table, rows, cells`
  - Парсит header, separator, body rows
  - Многострочный контент в ячейках (есть перенос строк)
- **Изображения:** `<!-- image -->` или `![...](...)` → `type: image`
- **Параграфы:** всё остальное → `type: paragraph`
- Возвращает полный JSON в структуре opendataloader

### 3.5. Простановка bbox

После md_to_json():
- Для каждого блока ищет bbox в `bbox_map`, собранной во время enrich
- Поиск по нормализованному тексту
- Fallback: substring matching для длинных строк
- Для таблиц — специальный ключ `__table__`

**Проблема:** bbox_map не покрывает все блоки (особенно таблицы и параграфы), часть остаётся без координат.

---

## 4. Сравнение конвейеров

| Характеристика | ODO (Docker API) | Docling JSON | Docling MD |
|---|---|---|---|
| Запуск | Docker только | Локально | Локально |
| Pipeline | opendataloader-pdf | StandardPdfPipeline | DocumentConverter |
| Enrich | — | На уровне JSON (PyMuPDF) | На уровне DoclingDocument |
| Формат | Нативный JSON ODO | kids/raw → standard | Markdown → JSON |
| Дедупликация | — | +70% overlap | (через Docling) |
| Колонтитулы | — | + | + |
| Подписи "Рис." | — | + | + |
| Таблицы | rows | rows+cells | pipe tables |
| Bbox | Есть | Есть | Частично |

### 4.2. Метрики качества (50 страниц)

| Метрика | Docling JSON | ODO |
|---|---|---|
| **Precision** | **0.970** | 0.828 |
| **Recall** | **0.816** | 0.620 |
| **F1** | **0.886** | 0.709 |
| Text similarity | **0.830** | 0.639 |
| Word overlap (Jaccard) | **0.809** | 0.619 |
| Quality confidence | **0.940** | 0.646 |
| Блоков всего | 643 | 436 |
| Проблемных страниц (sim<0.5) | **7** | 16 |

**Сравнение структуры блоков (Docling vs ODO):**

| Тип блока | Docling | ODO | Δ |
|---|---|---|---|
| heading | **91** | 29 | +62 |
| paragraph | **533** | 327 | +206 |
| table | 16 | 16 | 0 |
| image | 3 | **6** | -3 |
| list | 0 | **52** | -52 |

- Совпадение типов блоков по страницам: **63.3%**
- Среднее сходство текста: **66.1%**

### 4.4. Плюсы MD-конвейера

- **Не нужен** `JsonStandardizer` / `Normalizer` (маршрут короче)
- **Нет дублей** таблиц (MD экспорт не дублирует)
- **Не нужен** `_docling_doc_to_raw()` (сложный обход DoclingDocument)
- **Не нужен** enrich на уровне JSON (всё делается в DoclingDocument до export)
- `export_to_markdown()` даёт чистый Markdown без дублирования

### 4.5. Проблемы MD-конвейера

- `DocumentConverter` падает с `std::bad_alloc` на больших диапазонах (batches не спасают)
- Нет bbox для части блоков
- Парсинг таблиц с многострочным контентом нестабилен
- Изображения — только `<!-- image -->`, реальное извлечение не реализовано
- Качество на полном документе не оценено

### 4.6. Плюсы JSON-конвейера

- Стабилен на больших документах
- Bbox проставлены для всех блоков
- Дедупликация работает
- Детальное обогащение (колонтитулы, подписи, таблицы)
- Качество подтверждено (Precision 0.97, Recall 0.82)

---

## 5. Ключевые технические детали

### 5.1. Координаты: BOTTOMLEFT vs Screen

Docling использует BOTTOMLEFT (y растёт вверх), PyMuPDF — Screen (y растёт вниз). Конвертация:

```python
screen_y0 = page_h - max(by0, by1)  # верх
screen_y1 = page_h - min(by0, by1)  # низ
```

### 5.2. Проверка дублей (гибридная)

В `enrich_docling_document()` (MD-конвейер):
- Сначала по bbox overlap (точное совпадение зоны)
- Если bbox не совпал — по тексту (подстрока)

В `_enrich_empty_blocks()` (JSON-конвейер):
- Сначала по bbox
- Fallback: текст всей страницы для битых bbox

### 5.3. Дедупликация таблиц

Только в JSON-конвейере. Собирает все слова из `table.rows` на странице, удаляет параграфы с >70% пересечением. Не удаляет короткие строки (<15 символов) — это номера страниц.

### 5.4. Security scan

Parser-service (Docker) сканирует PDF на безопасность: проверяет MIME, размер, наличие JBIG2Decode (потенциально опасный фильтр).

---

## 6. Статус

| Компонент | Статус |
|---|---|
| Docling JSON pipeline | ✅ Работает, метрики подтверждены |
| Enrich (пустые блоки) | ✅ Работает |
| Колонтитулы | ✅ Работает |
| Подписи "Рис." | ✅ Работает |
| Дедупликация | ✅ Работает |
| Docling MD pipeline | ⚠️ Работает нестабильно (bad_alloc) |
| Enrich (DoclingDocument) | ✅ Работает |
| bbox из enrich | ⚠️ Частично |
| Извлечение изображений | ❌ Не реализовано |
| ODO через Docker API | ⚠️ hybrid падает, fallback без ML |
| Полный прогон (327 стр) | ⚠️ Не проведён |
