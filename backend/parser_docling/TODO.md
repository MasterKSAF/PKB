# parser_docling — что доделать

## Текущее состояние

Утилита парсит PDF через Docling, выдаёт JSON в той же структуре, что и parser_service (opendataloader).

**Работает:**
- Docling StandardPdfPipeline (layout analysis, таблицы, заголовки, списки)
- JsonStandardizer + Normalizer (копии из parser_service) — идентичная структура JSON
- Quality metrics (копия quality_metrics.py из parser_service) — реальная оценка confidence
- CLI: `python main.py file.pdf --max-pages N -o output.json`
- run_via_api.py — загрузка в MinIO → API parser_service → JSON (сравнение с ODO)

**Не работает:**
- DocumentConverter — падает с "Input document is not valid". Решение: прямой вызов StandardPdfPipeline.execute() с InputDocument + DoclingParseV2DocumentBackend + page_range (работает).
- Изображения не сохраняются (только ссылки image_key в JSON, без реальных файлов)

## Что нужно доделать

### 1. Извлечение изображений
Сейчас PictureItem маппится в блок type=image с image_key, но само изображение не сохраняется. Нужно:
- При парсинге извлекать PictureItem.image (PIL Image)
- Сохранять в папку рядом с JSON
- В JSON записывать путь к файлу вместо image_key

### 2. Тестирование на всём PDF
- Прогнать 2-020101-174-1.pdf на всех 327 страницах
- Замерить время (~1.2 с/стр → ~6.5 мин на весь PDF)
- Сравнить с ODO на 50+ страницах через run_via_api.py
- Проверить на других PDF

### 3. Чистка кода
- layout_analyzer.py — не используется (pipeline работает). Удалить или доработать.
- pdfium_mapper.py — не используется, удалить.
- docling_mapper.py — много кода. Вынести прямой pipeline в отдельный модуль.

### 4. Интеграция с проектом
- Сейчас parser_docling — отдельная утилита. Может заменить opendataloader в parser_service.
- Для интеграции нужно починить DocumentConverter.

## Архитектура

main.py -> docling_mapper.convert_docling_to_standard()
 1. _try_pipeline() — StandardPdfPipeline.execute() (основной)
 2. layout_parse() — layout_analyzer (fallback)
 3. _build_via_parse() — DoclingPdfParser (raw fallback)
 4. docling_to_raw_json() — DoclingDocument -> raw JSON
 5. JsonStandardizer — raw JSON -> стандартная структура
 6. quality_metrics — assess_quality_from_json -> confidence
 7. Normalizer — контейнер {document_info, content, metadata}

## Известные баги

- **DocumentConverter** не работает (не передаёт backend). Решение: прямой вызов pipeline.execute() с InputDocument + DoclingParseV2DocumentBackend.
- **quality_metrics.py** — assess_quality_from_json ожидает файл на диске (формат opendataloader с kids). Нужен временный файл.
