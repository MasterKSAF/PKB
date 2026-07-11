# План на сессию

## [in_progress] Исправление ошибки чата
- [done] bbox-string: убран json.dumps() в postgres_chunk_repository.py
- [done] SourceLocator: удалён bbox из response.py/search.py
- [done] Retry: 4xx сразу фейл без retry (rag_client.py)
- [done] Excerpt: VARCHAR(512)→Text + ALTER
- [blocked] Деплой на сервер — нет доступа

## [pending] Исправление отображения таблиц
- [done] get_page_blocks: вызывает render_section_content_to_md
- [done] render_section_content_to_md: читает "block" и "kids"
- [done] hierarchy_builder.py: columns извлекаются из первой строки
- [pending] Проверить, почему парсер хранит таблицы как type="text" вместо "table"
- [blocked] Деплой на сервер — нет доступа

## [pending] Diagnostics timeout
- [done] Таймауты снижены 30→10с/10→5с
