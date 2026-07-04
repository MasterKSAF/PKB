# Drafts Pages Preview — реализация бэкенда

- [x] Изучить существующий код (crud/routes/клиенты/mock)
- [x] Registry: CRUD функции `get_draft_pages_from_raw`, `get_draft_page_blocks`
- [x] Registry: endpoints `GET /registry/drafts/{draft_id}/pages` и `GET /registry/drafts/{draft_id}/pages/{page_num}`
- [x] Orchestrator: методы клиента `get_draft_pages`, `get_draft_page`
- [x] Orchestrator: proxy endpoints `GET /drafts/{draft_id}/pages` и `GET /drafts/{draft_id}/pages/{page_num}`
- [x] Gateway: mock handlers для обоих endpoints
- [ ] Тесты (не запускаются — проблема версий FastAPI в окружении, не связана с правками)
