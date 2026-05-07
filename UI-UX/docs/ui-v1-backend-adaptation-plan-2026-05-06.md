# UI V1: короткий план адаптации под backend API

Дата: 2026-05-06  
Ветка UI: `feature/ui-import-frontend-v1`  
Основа: `develop/docs/api`

## 1. Общий принцип

UI визуально почти не переделываем. Основная работа - заменить mock/demo-данные на реальные API и добавить адаптеры.

Frontend должен ходить во внешние для UI слои:

- `Auth Service` - вход, профиль, роли, права.
- `Orchestrator Service` - документы, поиск, чат, проверка НСИ, preview, QA.
- `Query Service` - чат-сессии, история, feedback.
- `Registry Service` - классификаторы НСИ, терминология, реестр НСИ-документов.

Напрямую в `rag`, `ocr`, `validate` UI не ходит, если backend не попросит отдельно.

## 2. HTTP-слой

Где: `src/utils/http.ts`

Сейчас:

- `/chat`
- `/search`
- `/documents`
- `/checks`
- `/history`
- `/metrics`
- `/feedback`

Сделать:

- добавить `VITE_API_BASE_URL`, вероятно `/api/v1`
- добавить `Authorization: Bearer <token>`
- добавить режимы `mock` и `real`
- сделать адаптеры ответа backend в UI-формат
- поддержать общий wrapper публичного API: `{ success, data, error, meta }`
- все списковые ответы читать через `data`, пагинацию через `meta`
- ошибки показывать из `error.code` и `error.message`

Пока оставить:

- mock fallback, пока backend не отдает реальные данные

## 3. Вход и профиль

Где:

- `src/components/LoginScreen.tsx`
- `src/store/uiStore.ts`
- `src/utils/access.ts`

API:

- `POST /auth/token`
- `GET /auth/me`

Сделать:

- заменить demo-выбор пользователя на логин/пароль
- сохранить `access_token`
- профиль, ФИО, должность, роль, вкладки и права брать из `/auth/me`

Пока оставить:

- demo-вход можно оставить до готовности auth

Спросить:

- финальные роли: только `Администратор/Пользователь` или роли из API `engineer/knowledge_admin/system_admin`

## 4. Роли и вкладки

Где:

- `src/utils/access.ts`
- `src/store/uiStore.ts`
- `src/App.tsx`
- `src/components/ModeSwitcher.tsx`

Сделать:

- вкладки показывать по `available_tabs`
- действия включать/выключать по `permissions`
- не хранить финальные права только во frontend
- учесть новые права: `can_manage_classifiers`, `can_manage_terminology`, `can_manage_registry`

Пока оставить:

- текущую demo-модель ролей, пока нет финального auth

## 5. Чат

Где:

- `src/components/Chat.tsx`
- `src/utils/http.ts`
- `src/store/uiStore.ts`

API:

- `POST /chat`
- позже возможно: `/chat/sessions`

Сейчас UI отправляет:

```json
{ "q": "текст вопроса" }
```

Нужно отправлять:

```json
{
  "question": "текст вопроса",
  "session_id": "chat-001",
  "user_id": "u-001",
  "context": {
    "project_id": "project-17",
    "document_ids": ["doc-001"],
    "nsi_version": "2026"
  }
}
```

Ответ backend:

- `answer_id`
- `status`
- `answer_items[]`
- `answer_items[].citations[]`
- `latency_ms`

Сделать:

- маппить `answer_items[]` в наши нумерованные ответы
- под каждым пунктом оставлять `Страница` и `Документ`
- поддержать статусы `answered`, `needs_clarification`, `source_conflict`

Пока оставить:

- текущий внешний вид чата
- mock-ответы до реального backend

## 6. Чат-сессии и продолжение диалога

Где:

- `Chat.tsx`
- `History.tsx`
- `uiStore.ts`
- `http.ts`

API:

- `POST /chat/sessions`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `POST /chat/sessions/{session_id}/messages`

Сделать:

- добавить активную `session_id`
- добавить сценарий `Новый чат`
- кнопка `Продолжить чат` из истории открывает выбранную сессию в чате

Пока оставить:

- одиночный demo-чат, если backend-сессии еще не готовы

Спросить:

- `/chat` сам создает сессию или UI должен сначала вызвать `/chat/sessions`

## 7. Поиск по текущему чату

Где: `Chat.tsx`

Сделать:

- пока оставить frontend-поиск по загруженным сообщениям

Позже:

- если чат длинный и сообщения подгружаются с сервера, нужен backend-поиск по полной сессии

Спросить:

- нужен ли endpoint поиска внутри одной чат-сессии

## 8. История и поиск по чатам

Где:

- `src/components/History.tsx`
- `src/utils/http.ts`
- `src/store/uiStore.ts`

API:

- `GET /chat/history`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `GET /chat/history/export`

Сделать:

- фильтры отправлять в query backend
- по клику раскрывать диалог из `session_id`
- `Продолжить чат` открывает выбранную сессию
- экспорт учитывать текущие фильтры

Пока оставить:

- текущую таблицу истории и раскрытие диалога

Спросить:

- история должна показывать вопросы или чат-сессии
- администратор видит все чаты или только свои/по правам
- нужен ли отдельный глобальный поиск по чатам

## 9. Feedback

Где:

- `src/components/Feedback.tsx`
- `src/utils/http.ts`

API:

- `POST /chat/feedback`

Нужно отправлять:

```json
{
  "answer_id": "ans-001",
  "user_id": "u-001",
  "useful": true,
  "comment": "Ответ точный",
  "opened_citation_ids": ["cit-001"]
}
```

Сделать:

- привязать feedback к `answer_id`
- передавать открытые источники, если инженер нажимал `Страница` или `Документ`

Пока оставить:

- текущий UI feedback

## 10. Страница и документ

Где:

- `SourcePreviewDialog.tsx`
- `Chat.tsx`
- `Search.tsx`
- `ChecksPanel.tsx`
- `http.ts`

API:

- `GET /documents/{doc_id}/pages/{page_num}/preview`
- `GET /documents/{doc_id}/file`

Сделать:

- `Страница` открывает `page_preview_url`
- `Документ` открывает `document_url`
- если backend вернул PDF/изображение/файл, показывать в правой preview-панели

Пока оставить:

- текущий mock-preview

Спросить:

- как backend будет отдавать DOCX/XLSX/PPTX: preview, файл, PDF-конверсия или iframe URL

## 11. Поиск по базе знаний

Где:

- `Search.tsx`
- `http.ts`

API:

- `GET /documents/search?q=...`
- или `POST /documents/search`

Сделать:

- заменить `/search` на `/documents/search`
- маппить `items[]` в текущие карточки/таблицу поиска
- ссылки брать из `page_preview_url` и `document_url`

Пока оставить:

- внешний вид вкладки

## 12. Реестр документов

Где:

- `DocumentRegistry.tsx`
- `http.ts`

API:

- `GET /documents`
- `POST /documents`
- `GET /documents/{doc_id}/status`
- `POST /documents/{doc_id}/reprocess`
- `GET /documents/queue`
- `GET /documents/{doc_id}/errors`

Сделать:

- список документов брать из `GET /documents`
- верхние метрики брать из `summary`
- загрузку документа привязать к backend
- OCR/переобработку привязать к `reprocess`
- ошибки брать из `/errors`

Пока оставить:

- demo-кнопки, пока backend не готов принимать файлы

Спросить:

- главный endpoint загрузки: `/documents` или `/files/upload`
- как связать загруженный файл из `/documents` с карточкой НСИ-документа из `/registry/documents`

Важно:

- `/documents` - это фактические загруженные файлы, OCR, индексация, очередь обработки.
- `/registry/documents` - это справочник НСИ-документов: название, номер, классификатор, статус, источник, примечания.
- Эти две сущности нельзя смешивать в UI без явной связи от backend.

## 13. Проверка НСИ

Где:

- `ChecksPanel.tsx`
- `http.ts`

API:

- `POST /validate/checks`
- `GET /validate/checks/{check_run_id}/export`

Сделать:

- выбранные документы делить на проектные и НСИ
- отправлять `project_document_ids`, `nsi_document_ids`, `parameters`, `user_id`
- таблицу заполнять из `items[]`
- экспорт брать из `export`
- ссылки `Страница/Документ` брать из `project_source` и `nsi_source`

Пока оставить:

- текущую таблицу и demo-результаты

Спросить:

- как UI определяет проектные документы и НСИ
- какие параметры доступны для выборочной проверки

## 14. QA

Где:

- `Monitor.tsx`
- `http.ts`

API:

- `GET /monitor/metrics`

Сделать:

- `control_metrics` -> контрольные метрики
- `answer_metrics` -> оценка ответов ассистента
- `logs[]` -> журнал проверки

Пока оставить:

- текущий внешний вид QA

## 15. Администрирование

Где:

- `AdminPanel.tsx`
- `uiStore.ts`
- `http.ts`

API:

- `GET /admin/users`
- `POST /admin/users`
- `PATCH /admin/users/{user_id}`
- `GET /admin/roles`
- `GET /admin/audit`
- `GET /registry/classifiers`
- `GET /registry/classifiers/tree`
- `GET /registry/terminology`
- `GET /registry/documents`
- `GET /registry/stats`
- `GET /registry/enums`

Сделать:

- пользователей брать из `/admin/users`
- роли брать из `/admin/roles`
- смену роли отправлять через `PATCH`
- журнал брать из `/admin/audit`
- после сохранения обновлять таблицу
- если права позволяют, добавить управление НСИ-справочниками:
- классификаторы НСИ
- терминология
- реестр документов НСИ
- импорт/экспорт CSV/XLSX

Пока оставить:

- demo-сохранение в UI

Спросить:

- Registry Service показываем отдельной вкладкой, внутри `Реестр` или внутри `Администрирование`
- кто имеет права на классификаторы, терминологию и реестр НСИ
- нужен ли пользователю только просмотр Registry или еще редактирование

## 16. Registry Service / НСИ-справочники

Где:

- вероятно новый блок в `AdminPanel.tsx`
- возможно отдельный будущий компонент `RegistryAdmin.tsx`
- `http.ts`

API:

- `GET /registry/classifiers`
- `GET /registry/classifiers/tree`
- `POST /registry/classifiers`
- `PATCH /registry/classifiers/{code}`
- `DELETE /registry/classifiers/{code}`
- `POST /registry/classifiers/import`
- `GET /registry/terminology`
- `GET /registry/terminology/normalize`
- `POST /registry/terminology`
- `POST /registry/terminology/import`
- `GET /registry/documents`
- `POST /registry/documents`
- `PATCH /registry/documents/{doc_id}/status`
- `GET /registry/documents/export`
- `GET /registry/stats`
- `GET /registry/enums`

Сделать:

- сначала добавить только просмотр: статистика, классификаторы, термины, НСИ-документы
- редактирование и импорт включать только при правах `can_manage_registry`, `can_manage_classifiers`, `can_manage_terminology`
- enum-значения брать из `/registry/enums`, не зашивать их во frontend
- статусы НСИ-документов брать из Registry: `draft`, `active`, `obsolete`, `need_to_buy`, `searching`

Пока оставить:

- не внедрять в основной UI, пока не решим место этого блока
- текущую вкладку `Реестр` оставить под `/documents`, OCR и индекс

Спросить:

- нужен ли Registry Service в MVP UI
- нужен ли полноценный CRUD или только просмотр
- кто отвечает за наполнение классификаторов и терминологии
- должна ли проверка НСИ использовать `/registry/documents` как источник выбора НСИ

## 17. Файлы и загрузка

Где:

- `DocumentRegistry.tsx`
- `ChecksPanel.tsx`
- `SourcePreviewDialog.tsx`
- `http.ts`

API:

- `POST /files/upload`
- `GET /files/{file_id}`
- `GET /files/{file_id}/info`

Сделать:

- если backend выберет `/files/upload`, отправлять `multipart/form-data`
- после загрузки получать `file_id` или `document_id`
- дальше отслеживать обработку документа

Пока оставить:

- загрузку в demo-режиме

## 18. Что пока не трогать

Не менять без необходимости:

- общий layout
- левую навигацию
- правую preview-панель
- кнопки `Страница` и `Документ`
- таблицы поиска, реестра, проверки, истории
- QA-вкладку
- focus mode
- светлую/темную тему

## 19. Приоритеты

### Сначала

1. `authApi`: login, profile, token.
2. `chatApi`: новый формат `/chat`.
3. `previewApi`: реальные `Страница` и `Документ`.
4. `historyApi`: сессии, раскрытие, продолжение чата.

### Потом

1. `searchApi`: `/documents/search`.
2. `feedbackApi`: `/chat/feedback`.
3. `metricsApi`: `/monitor/metrics`.
4. `adminApi`: users, roles, audit.
5. `registryApi`: stats, enums, classifiers, terminology, registry documents.

### После этого

1. `checksApi`: `/validate/checks`.
2. upload/reprocess документов.
3. экспорт истории и проверки.

## 20. Главные вопросы backend-команде

1. UI ходит только в Orchestrator или в несколько сервисов?
2. Какой финальный `BASE_URL` для frontend?
3. Какие финальные роли и права?
4. Как создается чат-сессия?
5. Что считать главным экраном истории: сессии или отдельные вопросы?
6. Как искать по старым чатам?
7. Как отличать проектные документы от НСИ?
8. Какой endpoint загрузки документов главный?
9. Как отдавать DOCX/XLSX/PPTX для preview?
10. Какие поля обязательны для запуска проверки НСИ?
11. Где в UI должен жить Registry Service: отдельная вкладка, `Реестр` или `Администрирование`?
12. Как связываются `/documents` и `/registry/documents`?
13. Какие операции Registry входят в MVP: просмотр, CRUD, импорт, экспорт?

## 21. Короткий вывод

UI V1 оставляем базовой версией. Основная работа дальше - не перерисовка, а подключение реальных API через адаптеры. Самые заметные изменения для пользователя: нормальный вход, реальные роли, чат-сессии, продолжение истории и реальные документы в preview.

Свежий Registry Service добавляет отдельный фронт работ по НСИ-справочникам. Его лучше не смешивать с текущим реестром OCR-документов, пока backend не объяснит связь между загруженными файлами и карточками НСИ-документов.
