# parser_docling — план сессии

### Сделано
- [x] MD-конвейер: DocumentConverter → enrich(DoclingDocument) → export_to_markdown(params) → md_to_json()
- [x] enrich с гибридной проверкой дублей: bbox overlap + текст подстрока
- [x] Постраничный export (page_no= параметр)
- [x] Старый JSON-конвейер сохранён (--mode json)
- [x] bbox для блоков (из bbox_map по ключу текст+страница)
- [x] Размеры страниц из doc.pages
- [x] quality.per_page заполнен
- [x] generate_picture_images = True
- [x] Парсинг таблиц с многострочным контентом

### Осталось
- [ ] Полный прогон (327 стр.) и оценка метрик
- [ ] Обновить README.md
