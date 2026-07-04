Алгоритм парсинга MD-конвейера

### 1. Общая схема

```
PDF → DocumentConverter (батчи по 5 стр.)
    → enrich_docling_document() — PyMuPDF: добавляет пропущенные строки
    → export_to_markdown() — Docling → Markdown
    → split_markdown_blocks() — MD → сырые блоки (text, type)
    → md_to_json_blocks() — сырые блоки → JSON-блоки + группировка списков
    → md_to_document_json() — сборка документа
    → bbox matching — восстановление координат из карты enrich
```

---

### 2. enrich_docling_document (docling_mapper.py)

Открывает PDF через PyMuPDF и для каждой страницы:

1. Собирает полный текст всех элементов Docling по страницам (включая ячейки таблиц)
2. Сохраняет карту `bbox_map[(norm_text, page_no)] → [l, t, r, b]` для всех текстов Docling
3. Для каждой страницы получает все текстовые блоки из PyMuPDF
4. Сверяет строку из PyMuPDF с полным текстом Docling:
   - Если строка уже есть в Docling → пропускает (совпадает текст)
   - Если строки нет → добавляет через `doc.add_text()` с правильным label:
     - `PAGE_HEADER` — если строка в верхних 15% страницы
     - `PAGE_FOOTER` — если в нижних 15%
     - `CAPTION` — если содержит «рис»
     - `PARAGRAPH` — всё остальное
   - Сохраняет bbox добавленной строки в `bbox_map`
5. Возвращает обогащённый `doc` и `bbox_map`

**Важно:** Docling использует `CoordOrigin.BOTTOMLEFT`, PyMuPDF — `TOPLEFT`. При добавлении через `add_text()` bbox передаётся как `TOPLEFT` → внутри Docling конвертирует сам. В `bbox_map` сохраняются координаты уже в TOPLEFT.

---

### 3. split_markdown_blocks (md_to_json.py)

Построчный парсер Markdown без LLM. Определяет тип блока по первой строке:

**Порядок проверки строк:**

1. **Пустая строка** — пропуск
2. **Heading** — `^#{1,6}\s+(.+)$`
3. **Image placeholder** — `<!-- image -->` → проверяет следующую непустую строку на caption (см. п.4)
4. **Image MD** — `![alt](path)`
5. **Table** — строка начинается с `|`, собирает все строки таблицы (включая многострочные ячейки)
6. **Horizontal rule** — `^---+$`
7. **Code block** — обрамлён ` ``` `
8. **List** — см. п.5
9. **Paragraph** — всё остальное до пустой строки или другого типа

---

### 4. Детекция подписи изображения

После `<!-- image -->`:

```python
# Ищем следующую непустую строку
j = i + 1
while j < len(lines) and not lines[j].strip():
    j += 1
```

Если строка начинается с `Рис.`, `Fig.`, `Таблица`, `Table`, `Иллюстрация`, `Illustration` — захватывается как `content` изображения. Строка удаляется из основного потока, чтобы не ушла в параграф.

**Почему не любая заглавная буква:** были ложные срабатывания на обычный текст после картинки.

---

### 5. Детекция списков

**`_is_list_marker(line)`** — определяет, является ли строка элементом списка:

```python
stripped = line.lstrip()

# Маркированный: - text, * text
if re.match(r'^[-*+]\s+', stripped):
    rest = re.sub(r'^[-*+]\s+', '', stripped)
    if re.match(r'^\.?\d', rest):    # после маркера идёт .1 или цифра
        return 'numbered'            # это нумерованный, не маркированный
    return 'bullet'

# Нумерованный: .1, .2.1, 1.2.3, 1), (а), (б)
if re.match(r'^(\.\d+(\.\d+)*|\d+[\.\)]|\([а-яa-z]\))\s+', stripped):
    return 'numbered'
```

**Ключевые паттерны для техдокументации:**
- `.1`, `.2` — подпункты (с точки)
- `.2.1`, `.2.2.1` — вложенные подпункты
- `1.2.3` — полные номера пунктов
- `- .1` — Docling экспортирует .1 как bullet (маркер `-` + `.1`)

**Группировка элементов в один list-блок:**
1. Пустые строки внутри списка **пропускаются** (не разрывают группу)
2. Смена стиля нумерации разрывает:
   - Были `.1`, `.2` (dot-prefix) → встретился `1.2.3` (digit-prefix) → **break**
   - Были `1.2.3` (digit-prefix) → встретился `.1` (dot-prefix) → **break**
3. Параграф без отступа и без маркера → **break**
4. Заголовок/таблица/image → **break**

---

### 6. Группировка коротких параграфов в списки

**Проблема:** Docling разбивает списки определений на отдельные строки:
```
АПС - аварийно-предупредительная сигнализация;
ВРШ - винт регулируемого шага;
...
```
Каждая строка — отдельный параграф.

**Решение:** Буфер коротких параграфов в `md_to_json_blocks()`:

```python
list_buffer = []

def flush_list():
    if len(list_buffer) >= 3:
        all_short = all(len(b['text']) <= 120)
        has_listy = any(_looks_like_list_item(b['text']) for b in list_buffer)
        if all_short and has_listy:
            # → создаём один list-блок
            items = [{'content': b['text']} for b in list_buffer]
            # → сбрасываем буфер
    else:
        # → сбрасываем как обычные параграфы
```

**`_looks_like_list_item(text)`** — эвристика:
- Содержит ` - ` или ` — ` (список определений)
- Заглавная аббревиатура `[А-ЯA-Z]{2,}` длиной 2-10 символов (ВРШ, ГУР, ГЭУ)
- `[IVXLCM]+.` (римские цифры)
- `[а-яa-z])` (буквенные маркеры)

**Условие группировки:** ≥3 коротких (≤120 символов) подряд идущих параграфа, хотя бы один проходит `_looks_like_list_item`.

---

### 7. Восстановление bbox (convert_via_docling_md)

После сборки JSON каждый блок получает bbox из `bbox_map`:

**Для обычных блоков:** ищет точное совпадение текста, потом fuzzy (substring).

**Для list-блоков:**
```python
for item in items:
    b = _match_bbox(pno, item['content'])
    if b:
        item['bounding box'] = b          # индивидуальный bbox элемента
        item_bboxes.append(b)

block['bounding box'] = _merge_bbox(item_bboxes)  # объединённый bbox блока
```

**`_merge_bbox(bboxes)`:**
```python
x0 = min(b[0] for b in bboxes)   # минимальный left
y0 = min(b[1] for b in bboxes)   # минимальный top
x1 = max(b[2] for b in bboxes)   # максимальный right
y1 = max(b[3] for b in bboxes)   # максимальный bottom
```

---

### 8. Оценка качества (evaluate_quality.py)

**`_flatten_blocks()`** — разворачивает list-блоки в отдельные виртуальные блоки:

```python
for b in blocks:
    if b['type'] == 'list':
        for item in b['items']:
            # создаём paragraph с content + bounding box из item
            result.append({
                'type': 'paragraph',
                'content': item['content'],
                'bounding box': item['bounding box']
            })
    else:
        result.append(b)
```

Это нужно, чтобы сортировка по bbox (для SequenceMatcher) корректно расставляла элементы списка по их реальным позициям на странице, а не все в одной точке (по объединённому bbox).
