# Drafts Pages Preview — Спецификация

## 1. Цель

Добавить постраничный просмотр черновиков в формате MD с поддержкой изображений и таблиц.

**Принцип**: данные уже есть в `raw_data` черновика (стандартизированный JSON после парсинга). Нужно:
- Отдать их постранично через API (как у документов: `pages` / `pages/{num}`)
- Во фронтенде сконвертировать блоки страницы в Markdown и отрендерить через `ReactMarkdown` + `remark-gfm`
- Изображения резолвятся фронтендом: `image_key` → `${BASE_URL}/files/${image_key}`

---

## 2. Структура данных

`raw_data` в Draft (JSONB) содержит стандартизированный документ:

```json
{
  "document": {
    "source": { "file_name": "...", "page_count": 3 },
    "pages": [
      { "page": 1, "width": 595, "height": 842 },
      { "page": 2, "width": 595, "height": 842 }
    ],
    "block": [
      { "number": 1, "type": "heading", "page": 1, "content": "ГОСТ 20868-81", "heading_level": 1 },
      { "number": 2, "type": "paragraph", "page": 1, "content": "Настоящий стандарт распространяется..." },
      { "number": 3, "type": "image", "page": 2, "image_key": "<hash>.png", "width": 400, "height": 300 },
      { "number": 4, "type": "table", "page": 2,
        "number_of_rows": 3, "number_of_columns": 2,
        "rows": [
          { "type": "table row", "row_number": 1, "cells": [
            { "type": "table cell", "column_number": 1, "block": [{"content": "A1"}] },
            { "type": "table cell", "column_number": 2, "block": [{"content": "B1"}] }
          ]},
          { "type": "table row", "row_number": 2, "cells": [
            { "type": "table cell", "column_number": 1, "block": [{"content": "A2"}] },
            { "type": "table cell", "column_number": 2, "block": [{"content": "B2"}] }
          ]}
        ]
      },
      { "number": 5, "type": "list", "page": 2, "numbering_style": "bullet",
        "block": [
          { "type": "paragraph", "content": "Пункт 1" },
          { "type": "paragraph", "content": "Пункт 2" }
        ]
      },
      { "number": 6, "type": "formula", "page": 3, "latex": "E = mc^2", "image_key": "<hash>.png" }
    ]
  }
}
```

**Типы блоков**: `paragraph`, `heading`, `image`, `table`, `list`, `formula`, `text_block`, `headerFooter`, `caption`.

---

## 3. API endpoints

### 3.1 Registry Service (`backend/registry_service/api/v1/`)

**Новые CRUD функции** в `crud/draft.py`:

```python
def get_draft_pages_from_raw(draft: Draft) -> list[dict]:
    """Извлечь список страниц из raw_data."""
    raw = draft.raw_data or {}
    doc = raw.get("document", {})
    return doc.get("pages", [])

def get_draft_page_blocks(draft: Draft, page_num: int) -> list[dict]:
    """Извлечь блоки для указанной страницы из raw_data."""
    raw = draft.raw_data or {}
    doc = raw.get("document", {})
    blocks = doc.get("block", [])
    return [b for b in blocks if b.get("page") == page_num]
```

**Новые endpoints** в `routes.py`:

```
GET /registry/drafts/{draft_id}/pages
  → 200: { "data": { "draft_id": int, "pages_total": int, "pages": [...] } }
  → 404: draft not found / no raw_data

GET /registry/drafts/{draft_id}/pages/{page_num}
  → 200: { "data": { "draft_id": int, "page": int, "blocks": [...] } }
  → 404: draft not found / page not found
```

### 3.2 Orchestrator Service (`backend/orchestrator_service/app/`)

**Новые методы** в `services/registry_client.py`:

```python
async def get_draft_pages(self, draft_id: int) -> dict:
    return await self.call("GET", f"/api/v1/registry/drafts/{draft_id}/pages", ...)

async def get_draft_page(self, draft_id: int, page_num: int) -> dict:
    return await self.call("GET", f"/api/v1/registry/drafts/{draft_id}/pages/{page_num}", ...)
```

**Новые endpoints** в `api/v1/endpoints/drafts.py`:

```
GET /drafts/{draft_id}/pages
GET /drafts/{draft_id}/pages/{page_num}
```

Оба проксируют в Registry.

### 3.3 Gateway Mocks (`backend/gateway_service/mocks/handlers/orch_routes.py`)

Добавить mock-хендлеры:
```
GET /api/v1/drafts/{draft_id}/pages
GET /api/v1/drafts/{draft_id}/pages/{page_num}
```

Mock должен возвращать тестовые страницы/блоки.

---

## 4. Frontend

### 4.1 API (`UI-UX/UI Final/frontend/src/utils/http.ts`)

Добавить в `draftsApi`:

```typescript
pages: async (draftId: string) => {
  requireNumericDraftId(draftId, 'pages');
  const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}/pages`));
  return response.data?.data ?? response.data;
},
page: async (draftId: string, pageNum: number) => {
  requireNumericDraftId(draftId, 'page');
  const response = await gatewayRequest<any>(() => apiClient.get(`/drafts/${draftId}/pages/${pageNum}`));
  return response.data?.data ?? response.data;
},
```

### 4.2 Конвертер blocks → Markdown

Новый файл `UI-UX/UI Final/frontend/src/utils/draftBlocksToMd.ts`:

```typescript
export interface DraftBlock {
  number: number;
  type: 'paragraph' | 'heading' | 'image' | 'table' | 'list' | 'formula' | 'text_block' | 'headerFooter' | 'caption';
  page: number;
  content?: string;
  heading_level?: number;
  image_key?: string;
  rows?: TableRow[];
  block?: DraftBlock[];
  numbering_style?: string;
  latex?: string;
  font?: { size?: number; bold?: boolean; italic?: boolean; color?: string };
}

export function blocksToMarkdown(blocks: DraftBlock[], baseUrl: string, draftId: number): string {
  return blocks.map(b => blockToMd(b, baseUrl, draftId)).filter(s => s).join('\n\n');
}

function blockToMd(b: DraftBlock, baseUrl: string, draftId: number): string {
  switch (b.type) {
    case 'heading':
      return `${'#'.repeat(b.heading_level ?? 1)} ${b.content ?? ''}`;
    case 'paragraph':
      return b.content ?? '';
    case 'image':
      return `![Страница ${b.page}](${baseUrl}/files/${b.image_key})`;
    case 'table':
      return tableToMd(b);
    case 'list':
      return listToMd(b);
    case 'formula':
      return b.latex ? `$$\n${b.latex}\n$$` : '';
    case 'caption':
      return `> ${b.content ?? ''}`;
    case 'text_block':
      return (b.block ?? []).map(child => child.content ?? '').join('\n');
    default:
      return b.content ?? '';
  }
}
```

**Таблицы** конвертятся в GFM pipe-таблицы:

```
| Заголовок 1 | Заголовок 2 |
|------------|------------|
| A1         | B1         |
| A2         | B2         |
```

**Списки** в маркированные/нумерованные.

### 4.3 Preview renderer

В `KnowledgeProcessing.tsx`:

Текущие `previewPages` / `buildPreviewPages` / `buildDocumentPreviewText` заменяются на:

1. При открытии превью — фетч `/drafts/{id}/pages` → получаем список страниц
2. При переключении страницы — фетч `/drafts/{id}/pages/{num}` → получаем блоки
3. Конвертируем блоки в MD через `blocksToMarkdown(blocks, BASE_URL, draftId)`
4. Рендерим через `<ReactMarkdown remarkPlugins={[remarkGfm]} />`

**Состояние навигации** сохраняется (текущая страница, всего страниц, кнопки назад/вперёд).

**Изображения**: `image_key` → URL `${BASE_URL}/files/${image_key}` — Gateway проксирует MinIO.

### 4.4 Интеграция с текущим UI

- Большой диалог предпросмотра (previewDialogOpen) — рендерит MD вместо текущих страниц
- Боковая панель (previewPanelOpen) — то же самое
- Поиск по тексту сохраняется (работает по plain-text, извлечённому из MD)
- Кнопка "Скачать" — сохраняет MD-файл вместо TXT

---

## 5. Изменяемые файлы

| Файл | Изменения |
|------|-----------|
| `backend/registry_service/api/v1/crud/draft.py` | + `get_draft_pages_from_raw`, `get_draft_page_blocks` |
| `backend/registry_service/api/v1/routes.py` | + 2 endpoints: `/registry/drafts/{id}/pages`, `/registry/drafts/{id}/pages/{num}` |
| `backend/orchestrator_service/app/services/registry_client.py` | + `get_draft_pages`, `get_draft_page` |
| `backend/orchestrator_service/app/api/v1/endpoints/drafts.py` | + 2 proxy endpoints |
| `backend/gateway_service/mocks/handlers/orch_routes.py` | + 2 mock handlers |
| `UI-UX/UI Final/frontend/src/utils/http.ts` | + `draftsApi.pages`, `draftsApi.page` |
| `UI-UX/UI Final/frontend/src/utils/draftBlocksToMd.ts` | **новый** — конвертер blocks→MD |
| `UI-UX/UI Final/frontend/src/components/KnowledgeProcessing.tsx` | замена preview на MD-рендер |

---

## 6. Обработка краевых случаев

- **raw_data = null/пусто** → возвращать 404 с PAGE_NOT_FOUND
- **page_num вне диапазона** → 404
- **нет блоков на странице** → пустой массив blocks, MD = "(пустая страница)"
- **изображение недоступно (404)** → react-markdown покажет broken image, можно добавить fallback через custom renderer
- **очень большие таблицы** → GFM поддерживает, но на узких экранах можно добавить `white-space: nowrap` + горизонтальный скролл через custom renderer
- **формулы** → `$$latex$$` требует `remark-math` + `rehype-katex` (подключить при необходимости)

---

## 7. Критерии приёмки

- [ ] `GET /drafts/{id}/pages` возвращает список страниц из raw_data
- [ ] `GET /drafts/{id}/pages/{n}` возвращает блоки для n-й страницы
- [ ] Картинки отображаются в превью (URL формируется из image_key + BASE_URL)
- [ ] Таблицы рендерятся корректно (GFM pipe tables)
- [ ] Заголовки, параграфы, списки отображаются
- [ ] Навигация по страницам работает (назад/вперёд)
- [ ] Поиск по тексту работает
- [ ] Скачивание сохраняет MD-файл
- [ ] Mock-режим (демо) тоже работает
