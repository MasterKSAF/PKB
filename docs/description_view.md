# Просмотр документов — архитектура

## Общая схема

```
Frontend (React SPA)                  Backend Docker
┌──────────────────┐     HTTP          ┌──────────────────────┐
│ KnowledgeBase    │ ── GET ──────────→ │ Gateway (reverse      │
│  (осн. просмотр) │                   │  proxy + MinIO-proxy) │
│                  │                   │  :8080                │
│ DocumentRegistry │                   └──────┬───────────────┘
│  (реестр)        │                          │
│                  │                          ├──→ Registry (:8084)
│ SourcePreview    │                          │     ─ документы, секции,
│  (диалог)        │                          │       страницы
│                  │                          │
│ Chat / Search    │                          ├──→ MinIO (S3 API)
│  (боковая панель)│                          │     ─ PDF файлы
│                  │                          │     ─ preview-изображения
└──────────────────┘                          │
                                       ┌──────┴───────────────┐
                                       │ Parser  │ Converter- │
                                       │ (:8087) │ Validator  │
                                       │         │ (:8086)    │
                                       └─────────┴────────────┘
```

## Где хранятся данные для просмотра

### 1. PDF-файлы (исходные документы)

| Хранилище | Бакет | Путь |
|-----------|-------|------|
| MinIO | `pkb-documents` (или config.minio_bucket) | `documents/{file_key}` |

**Как формируется file_key:**
- При загрузке черновика → Orchestrator → Parser → сохраняет в MinIO
- file_key = `documents/{draft_id}/{version}/{hash}.pdf`

**Доступ через фронтенд:**
```
documentUrl = /api/v1/files/{file_key}
             ↓
Gateway (minio_proxy.py) → presigned S3 URL → MinIO → StreamingResponse
```

### 2. Preview-изображения страниц

| Хранилище | Бакет | Путь |
|-----------|-------|------|
| MinIO | `pkb-images` (или config.minio_image_bucket) | `previews/{doc_id}/{page_num}.png` |

**Как формируются:**
- Parser генерирует изображения каждой страницы PDF
- Сохраняет в MinIO с префиксом `previews/`

**Доступ через фронтенд:**
```
pagePreviewUrl = /api/v1/files/{image_key}
                 где image_key = previews/{doc_id}/{page_num}.png
                 ↓
Gateway → presigned S3 URL → MinIO → StreamingResponse
```

### 3. Текст страниц (OCR / текстовый слой)

| Хранилище | Таблица | Схема |
|-----------|---------|-------|
| PostgreSQL (Registry) | `registry.document_sections` | JSONB |

**Структура секции (DocumentSection):**
```
id, document_id, clause, title, level, path, page, bbox (JSONB), type, content (JSONB)
```

**Доступ через фронтенд:**
```
GET /documents/{id}/pages/{num}/text → Registry → {full_text, blocks}
```

### 4. Метаданные документа

| Хранилище | Таблица | Схема |
|-----------|---------|-------|
| PostgreSQL (Registry) | `registry.documents` | см. Document model |

Поля: doc_code, title, source_type, era, jurisdiction, issuing_body, mks_oks_code, okstu_code, status, validity_status, valid_from, valid_until, total_versions

### 5. API для просмотра

Все запросы идут через Gateway (:8080). Gateway маршрутизирует:

| Endpoint | Метод | Целевой сервис | Описание |
|----------|-------|----------------|----------|
| `/api/v1/documents/{id}` | GET | Registry | Детали документа |
| `/api/v1/documents/{id}/file` | GET | Registry | file_key + полный текст документа |
| `/api/v1/documents/{id}/pages` | GET | Registry | Список страниц |
| `/api/v1/documents/{id}/pages/{n}/preview` | GET | Registry | image_key для страницы |
| `/api/v1/documents/{id}/pages/{n}/text` | GET | Registry | Текст страницы |
| `/api/v1/documents/{id}/sections` | GET | Registry | Секции документа |
| `/api/v1/documents/{id}/history` | GET | Registry | История изменений |
| `/api/v1/documents/{id}/versions` | GET | Registry | Версии документа |
| `/api/v1/documents/{id}/parameters` | GET | Registry | Параметры/точность |
| `/api/v1/documents/{id}/status` | GET | Orchestrator | Статус обработки |
| `/api/v1/files/{file_key}` | GET | Gateway→MinIO | Сырой файл (PDF/изображение) |

## Что за что отвечает в бэкенде

### Gateway (`gateway_service`)
- **routers.py** — catch-all reverse proxy: маршрутизирует /api/v1/* запросы к сервисам
- **minio_proxy.py** — S3 presigned URL proxy: читает файлы из MinIO и отдаёт клиенту
- **client.py** — таблица ROUTE_TABLE: определяет, какой сервис обрабатывает какой путь

Маршруты к документам трансформируются:
```
/api/v1/documents/{id} → /api/v1/registry/documents/{id}
```

### Registry (`registry_service`)
- Хранит метаданные документов, версии, секции, страницы
- CRUD: `api/v1/crud/document.py`
- Модели: `api/v1/models/document.py` (Document), `document_sections.py` (DocumentSection), `document_versions.py` (DocumentVersion)
- Эндпоинты: `api/v1/routes.py`

### Orchestrator (`orchestrator_service`)
- Пайплайн обработки черновика: загрузка → парсинг → конвертация → approve
- Статус документа, история, ошибки, репроцессинг
- Draft → preview → approve → создание документа в Registry

### Parser (`parser_service`)
- Парсинг PDF: извлечение текста, структуры, изображений
- OCR для сканированных PDF
- Сохранение результатов в MinIO (изображения страниц) и Registry (секции)

### Converter-Validator (`converter_validator_service`)
- Извлечение метаданных (PreviewMetadata): doc_code, title, year, era и т.д.
- Валидация и классификация документа

## Компоненты фронтенда

### KnowledgeBase.tsx (основной просмотр)
- Показывает документы из Registry, сгруппированные по разделам классификатора
- При выборе документа:
  1. `sourceApi.preview(citation, 'document')` → GET /documents/{id}/file → текст + file_key
  2. `sourceApi.preview(citation, 'source')` → GET /pages/1/preview → image_key
  3. Строит страницы: изображение, текст (разбитый по ~80 строк), PDF (iframe)
- Диалог предпросмотра с навигацией по страницам
- Fallback на мета-карточки, если API недоступен

### DocumentRegistryPanel.tsx (реестр)
- Таблица документов с фильтрацией/поиском
- При выборе документа:
  1. `documentsApi.get(id)` → детали
  2. `documentsApi.pages(id)` → список страниц
  3. `documentsApi.pagePreview(id, n)` + `documentsApi.pageText(id, n)` → контент страницы
- Показывает изображение страницы + текст
- Кнопка "Скачать оригинал" — через `/documents/{id}/file`

### SourcePreviewDialog.tsx (диалог источника)
- Показывает источник найденного фрагмента
- Отображает: изображение (pagePreviewUrl), PDF (documentUrl в iframe), текст фрагмента
- Кнопка "Открыть PDF" → открывает documentUrl в новой вкладке

### Chat.tsx (боковая панель)
- Inline preview для цитат в ответах ассистента
- `sourceApi.preview(citation, previewKind)` → отображает текст/ссылку
- Регулируемая ширина, зум, поиск по тексту

## Процесс просмотра документа (sequence)

```
User click → handleOpenPreview()
  │
  ├─ sourceApi.preview('document')
  │   └─ GET /api/v1/documents/{id}/file
  │      └─ Gateway → Registry
  │         └─ response: {file_key, text, content_type, status}
  │
  ├─ sourceApi.preview('source')   (для 1-й страницы)
  │   └─ GET /api/v1/documents/{id}/pages/1/preview
  │      └─ Gateway → Registry
  │         └─ response: {image_key, file_key, ...}
  │
  └─ setPreviewCitation({documentUrl, pagePreviewUrl, text})
       │
       └─ buildPreviewPages()
            ├─ изображение страницы (если pagePreviewUrl есть)
            ├─ текст документа (разбит на страницы)
            ├─ PDF (если documentUrl есть)
            └─ секции Registry (если есть)
```
