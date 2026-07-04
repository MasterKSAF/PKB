# Замена /text → /content_md ✅

## Бэкенд (registry_service)
- [x] Endpoint `content_md` уже существует
- [x] Endpoint `/text` остаётся для обратной совместимости

## Gateway
- [x] Mock handler `GET /api/v1/documents/{doc_id}/pages/{page_num}/content_md` добавлен в `orch_routes.py`
- [x] Production routing не требует изменений (catch-all `pages(?:/.*)?$` уже покрывает)
- [x] Тест роутинга `content_md` добавлен в `test_gateway_routing.py`

## Фронтенд
- [x] Установлены `react-markdown` + `remark-gfm`
- [x] `http.ts`: добавлен метод `pageContentMd()`
- [x] `http.ts`: превью цитат переведено на `/content_md`
- [x] `DocumentRegistryPanel.tsx`: вызов `pageText()` → `pageContentMd()`
- [x] `DocumentRegistryPanel.tsx`: рендеринг страницы через `ReactMarkdown` + `remarkGfm` (с поддержкой таблиц)

## Документация
- [x] frontend/README.md
- [x] first-run-ui-final-with-gateway.md
- [x] ui-final-gateway-current-status-2026-06-03.md
