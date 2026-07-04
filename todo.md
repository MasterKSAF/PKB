# Переход на продвинутый MD с картинками для просмотра документов

## Финальный обзор перед коммитом

### Backend
- [x] `get_page_blocks_md()` — image_key в content как `![alt](/api/v1/files/{key})`
- [x] `/documents/{id}/pages/{n}/content_md` — markdown из content блоков
- [x] `/documents/{id}/content_md` — весь документ одной MD-строкой
- [x] Gateway route для `/documents/{id}/content_md`

### Frontend
- [x] `utils/markdownBuilder.ts` — сборка content блоков
- [x] `sourceApi.preview()` — использует markdown из сервера
- [x] `DocumentRegistryPanel.tsx` — ReactMarkdown с картинками
- [x] `KnowledgeBase.tsx` — ReactMarkdown + fallback
- [x] `Chat.tsx` — ReactMarkdown в превью
- [x] `SourcePreviewDialog.tsx` — ReactMarkdown с картинками
- [x] `draft/preview` — не требует изменений (только метаданные, нет контента)

### Валидация
- [x] TypeScript: `tsc --noEmit` — чисто
- [x] Python: `ast.parse()` — синтаксис корректен
