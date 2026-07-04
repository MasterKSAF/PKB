# Переход на продвинутый MD с картинками для просмотра документов — ВЫПОЛНЕНО

## Backend (registry_service)

### `get_page_blocks_md()` — document.py
- Для image-блоков `content` содержит `![alt](/api/v1/files/{image_key})` (вместо пустой строки)

### `/documents/{id}/pages/{n}/content_md` — routes.py
- Поле `markdown` собирает content блоков (картинки уже встроены в content)

### `/documents/{id}/content_md` — routes.py (новый)
- Весь документ одной MD-строкой со всеми страницами

### `/registry/drafts/{draft_id}/preview` — routes.py
- Передан `files_base_url='/api/v1/files'` для `draft_blocks_to_markdown`

## Gateway
- Добавлен роут `/documents/{id}/content_md` → Registry

## Frontend

### Готовые документы (content_md)
- `utils/markdownBuilder.ts` — сборка content блоков в MD
- `sourceApi.preview()` — использует `markdown` из сервера, режет относительные пути → абсолютные
- `DocumentRegistryPanel.tsx` — ReactMarkdown с `& img` стилями
- `KnowledgeBase.tsx` — ReactMarkdown + fallback
- `Chat.tsx` — ReactMarkdown в превью
- `SourcePreviewDialog.tsx` — ReactMarkdown с картинками

### Черновики (draft/preview)
- `DraftPreview.previewMd` — поле для markdown первых 3 страниц
- `KnowledgeProcessing.tsx` — ReactMarkdown для рендера + resolve URL картинок

### Разрешение URL картинок
- Сервер генерирует `/api/v1/files/{key}`
- Фронтенд режет `/api/v1/files/` → `{VITE_API_BASE_URL}/files/` на всех путях

## Проверка
- TypeScript: `tsc --noEmit` — чисто
- Python: `ast.parse()` — синтаксис корректен
- Тесты не запускались (pre-existing ошибка FastAPI on_startup)
