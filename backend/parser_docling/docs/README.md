# parser_docling

Утилита парсинга PDF через **Docling** с пост-обработкой (enrich, группировка списков, quality).
Выдаёт JSON в структуре, совместимой с `JsonStandardizer` (`parser_service`).

## Структура проекта

```
parser_docling/
├── src/              # библиотечный код
│   ├── docling_mapper.py   # основной пайплайн (Pipeline → enrich → MD → JSON)
│   ├── md_to_json.py       # конвертер Markdown → JSON + группировка списков
│   ├── quality_metrics.py  # эвристическая оценка качества
│   ├── standardizer.py     # стандартизация JSON (JsonStandardizer)
│   └── normalizer.py       # обёртка в контейнер
├── scripts/          # CLI-утилиты
│   ├── run_range.py         # парсинг PDF с диапазоном страниц
│   ├── evaluate_quality.py  # оценка Precision/Recall/F1
│   ├── compare_json.py      # сравнение Docling vs ODO
│   ├── run_via_api.py       # загрузка PDF в MinIO → вызов parser API
│   └── wait_odo.py          # ожидание завершения ODO парсера
├── data/             # результаты парсинга (JSON)
├── docs/             # документация
├── archive/          # устаревший код
├── pdf/              # тестовые PDF
└── requirements.txt
```

## Быстрый старт

```bash
cd backend/parser_docling

# MD-конвейер (основной, рекомендуется)
python scripts/run_range.py --start 1 --end 50 -o data/output.json --mode md

# Оценка качества
python scripts/evaluate_quality.py data/output.json pdf/2-020101-174-1.pdf

# Сравнение с ODO
python scripts/compare_json.py data/output.json data/odo_50.json
```

## Конвейеры

### MD-конвейер (`--mode md`) — основной

```
PDF → DocumentConverter (батчи по 5 стр.) → enrich(DoclingDocument) → export_to_markdown() → md_to_json()
```

- enrich добавляет колонтитулы/подписи, пропущенные Docling
- export_to_markdown с `compact_tables=True`, `ImageRefMode.REFERENCED`
- md_to_json: парсинг Markdown → JSON + группировка списков

### JSON-конвейер (`--mode json`) — устаревший

```
PDF → StandardPdfPipeline → _docling_doc_to_raw() → enrich (JSON) → standardize → normalize
```

## Тестирование и сценарии

### 1. Полный прогон документа

```bash
# Весь документ (327 стр., ~11 мин)
python scripts/run_range.py --start 1 --end 327 -o data/output_full.json --mode md --quiet
```

**Ожидаемые метрики:**
| Метрика | Ожидание |
|---|---|
| Precision | ≥ 0.99 |
| Recall | ≥ 0.97 |
| F1 | ≥ 0.98 |
| Jaccard | ≥ 0.97 |
| Проблемных страниц (sim < 0.5) | ≤ 5% |
| Время | ~11 мин / 327 стр. |

### 2. Списки

**Что распознаётся как list:**
- Нумерованные перечисления: `.1`, `.2`, `.2.1`, `1.2.3` (в т.ч. если Docling их маркирует как `- .1`)
- Списки сокращений/определений (короткие строки ≤120 символов, идущие подряд, с ` - ` в одном из элементов)
- Маркированные списки из Docling: `- текст`

**Когда список НЕ создаётся:**
- Если коротких строк <3 — остаются как отдельные параграфы
- Если элемент длиннее 120 символов — разрывает группу

**Особенности:**
- Каждый элемент списка хранит свой `bounding box` в `items[].bounding box`
- У списка есть общий `bounding box` (объединение bbox всех элементов)
- Тип списка: `list_type: "bullet"` или `"numbered"`

```json
{
  "type": "list",
  "page number": 11,
  "list_type": "bullet",
  "bounding box": [76.6, 59.8, 542.0, 785.6],
  "items": [
    {"content": "АПС - аварийно-предупредительная сигнализация;", "bounding box": [...]},
    {"content": "ВРШ - винт регулируемого шага;", "bounding box": [...]}
  ]
}
```

### 3. Изображения и подписи

- Docling image блоки генерируются как `<!-- image -->`
- Подпись (Рис. / Fig. / Таблица) захватывается со следующей строки → `image.content`
- **НЕ распознаются** мелкие иконки/буллиты (ODO их находит, Docling — нет, но они не несут информации)

```json
{
  "type": "image",
  "page number": 6,
  "content": "Рис. 1.1.1-1 Границы района Арктики 1",
  "image_key": "",
  "bounding box": [253.7, 500.0, 364.8, 518.7]
}
```

### 4. Таблицы

- Распознаются pipe-таблицы (`| ... | ... |`)
- Поддерживаются многострочные ячейки
- Bbox восстанавливается из bbox_map по ключу `('__table__', page_no)`

### 5. Заголовки

- Docling генерирует `#`/`##`/`###` для заголовков
- Распознаёт больше заголовков, чем ODO (многие bold-строки классифицируются как heading)

### 6. Оценка качества

```bash
python scripts/evaluate_quality.py data/output.json pdf/document.pdf [--max-pages N]
```

**Метрики:**
- **Precision**: доля блоков Docling, чей текст найден в сыром PDF
- **Recall**: доля символов сырого PDF, покрытых блоками Docling
- **F1**: гармоническое среднее
- **Jaccard**: word overlap similarity (нечувствителен к порядку слов)
- **Text similarity**: SequenceMatcher (чувствителен к порядку)

**Важно:** Для list-блоков evaluate разворачивает элементы в отдельные блоки с их bbox для корректной сортировки.

### 7. Сравнение с ODO

```bash
python scripts/compare_json.py data/output.json data/odo.json
```

Сравнивает:
- Количество блоков по типам
- Качество (confidence)
- Совпадение структуры по страницам
- Сходство текста

### 8. Известные ограничения

| Ограничение | Причина |
|---|---|
| Quality confidence (0.75) ниже F1 (0.99) | Эвристика не учитывает enrich; штрафует за короткие строки |
| Нет caption-блоков (ODO — 6 шт.) | Подписи встроены в image.content |
| 3 изображения vs 6 в ODO | Docling не видит мелкие иконки/декоративные элементы |
| 459 заголовков vs 29 в ODO | Docling классифицирует bold-строки как heading |
| Документы с 300+ стр. парсятся ~11 мин | Из-за enrich + постраничного MD экспорта |
