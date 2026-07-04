# parser_docling — TODO

## Выполнено
- [x] MD-конвейер: DocumentConverter → enrich(DoclingDocument) → export_to_markdown() → md_to_json()
- [x] enrich с гибридной проверкой дублей: bbox overlap + текст подстрока
- [x] Постраничный export (page_no= параметр)
- [x] Старый JSON-конвейер сохранён (--mode json)
- [x] bbox для блоков (из bbox_map по ключу текст+страница)
- [x] Размеры страниц из doc.pages
- [x] quality.per_page заполнен
- [x] generate_picture_images = True
- [x] Парсинг таблиц с многострочным контентом
- [x] Распознавание списков (.1, .2, 1.2.3, - текст)
- [x] Подписи изображений (Рис., Fig., Таблица)
- [x] Группировка коротких параграфов в list (списки сокращений/определений)
- [x] Индивидуальный bbox для каждого элемента списка
- [x] Общий bbox списка (объединение элементов)
- [x] Flattening list-блоков в evaluate_quality.py для корректных метрик
- [x] Полный прогон (327 стр.) — F1=0.993, Jaccard=0.985, ~11 мин
- [x] Чистка кода: удалены неиспользуемые файлы (main, pdfium_mapper, layout_analyzer, compare_50, тесты)
- [x] Обновлён README.md
- [x] Переработан SUMMARY.md с тестовым сценарием

## Осталось (опционально)
- [ ] Доработать quality_metrics.py — учесть enrich и колонтитулы
- [ ] Извлечение изображений (сохранение в файлы вместо image_key)
- [ ] DoclingParseV2DocumentBackend → DoclingParseDocumentBackend
