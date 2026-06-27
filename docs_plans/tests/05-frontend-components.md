# Frontend — React компоненты

**Директория:** `UI-UX/UI Final/frontend/src/components/__tests__/` (создать новую)

---

## 1. `__tests__/LoginScreen.test.tsx` (~200 строк)

**Компонент:** `LoginScreen.tsx`

**Сценарии:**
- Рендер: отображение полей ввода (логин, пароль), кнопки "Продуктивный"/"Демо", кнопки "Войти"
- Demo mode: переключение на demo → пароль предзаполнен "demo"
- Prod mode: переключение на prod → пароль пустой
- Валидация длины логина: `<3` или `>64` → error helper text
- Валидация длины пароля: `<4` или `>64` → error helper text
- Кнопка "Войти" disabled при пустых полях
- Demo-login: корректный логин + пароль `demo` → вызывает `login(user.id)`
- Demo-login: неверный пароль → Alert с ошибкой
- Demo-login: неизвестный логин → Alert "Не найден demo-профиль"
- Prod-login: успешный запрос `authApi.login()` → `login(profile.id)`
- Prod-login: ошибка API → Alert с сообщением об ошибке
- Enter в поле пароля → вызов `handleLogin()`

---

## 2. `__tests__/Chat.test.tsx` (~300 строк)

**Компонент:** `Chat.tsx`

**Сценарии:**
- Рендер: поле ввода, кнопка отправки, контейнер сообщений
- Отправка сообщения: ввод текста + Send → сообщение появляется в списке
- Отправка пустого сообщения: кнопка disabled
- Отображение статусов: pending, enriching, searching, generating, enriching_citations, answered, failed
- Ответ assistant: content + кнопки источников (sourceButtonSx)
- Цитаты: click по источнику → открытие preview (openPreview)
- Закрытие preview: closePreview → preview скрыт
- Resize preview: перетаскивание border → изменение ширины
- Поиск по сообщениям (chatSearch): фильтр сообщений, подсветка текста
- Навигация по совпадениям: goToSearchMatch → прокрутка к сообщению
- Панель поиска в preview (previewSearch): фильтр, подсветка, навигация
- Ответ с limitation: "out_of_scope" → отображение limitation
- Ответ с limitation: "no_knowledge" → отображение
- Expand/collapse источников (toggleCitations): разворачивание/сворачивание
- Long-poll: незавершённый ответ → вызов waitForGatewayChatMessage
- Ответ с цитатами: countMatches + highlightText подсветка
- Несколько сообщений: корректная прокрутка scrollIntoView

---

## 3. `__tests__/Search.test.tsx` (~300 строк)

**Компонент:** `Search.tsx`

**Сценарии:**
- Рендер: поле поиска, фильтры, контейнер результатов
- Поиск по запросу: ввод текста → вызов searchApi.query → отображение результатов
- Пустой поиск: результаты не загружаются (enabled=false)
- Фильтр по типу: выбор source_type → фильтрация результатов
- Фильтр по версии: выбор version
- Фильтр по секции: toggleSectionFilter → выбор/отмена секции
- Advanced filters: открыть/закрыть панель
- Клик по результату: openDocument → панель preview
- Закрытие preview: closeDocument → панель закрыта
- Preview: загрузка страницы, навигация по страницам
- Preview: поиск текста, подсветка, навигация по совпадениям
- Resize preview: перетаскивание границы
- Дерево секций знаний: загрузка knowledgeSectionsQuery → отображение
- Выбор секции → фильтрация документов по sectionId
- No results: отображение пустого состояния
- Pagination: загрузка следующей страницы

---

## 4. `__tests__/DocumentRegistryPanel.test.tsx` (~350 строк)

**Компонент:** `DocumentRegistryPanel.tsx`

**Сценарии:**
- Рендер: таблица документов, фильтры (search, source, validity, validAt)
- Фильтр search: поиск по названию/коду
- Фильтр source: выбор source_type (GOST, SNIP, TU, STD_ORG, METHODOLOGY)
- Фильтр validity: active/inactive/all
- Фильтр validAt: date picker
- Клик по строке → загрузка detailQuery, versionsQuery, historyQuery, errorsQuery, parametersQuery, pagesQuery
- Панель деталей: отображение полей (title, doc_code, status, source_type, era, validity_status, jurisdiction, issuing_body)
- Chips: отображение summaryChips (status, version, validity, ocr)
- Вкладка версии: таблица версий, выбор для сравнения
- Вкладка история: список изменений
- Вкладка ошибки: список ошибок
- Вкладка параметры: extraction_confidence, parameters
- Preview страниц: навигация, поиск, подсветка
- Скачивание оригинала: handleDownloadOriginal → file API → blob download
- Обновление validity: handleSaveValidity → PATCH /documents/{id}
- Удаление документа: deleteDialog → handleDeleteDocument → DELETE /documents/{id}
- ValidFrom/ValidUntil: date inputs, сохранение
- Demo режим: buildDemoDetail/buildDemoVersions/buildDemoHistory
- Пустой список: отображение "Нет документов"

---

## 5. `__tests__/KnowledgeProcessing.test.tsx` (~400 строк)

**Компонент:** `KnowledgeProcessing.tsx`

**Сценарии:**
- Секции: Upload, Drafts, Registry, Journal
- Upload: выбор файла → создание локального draft
- Upload: загрузка файла → POST /drafts → отображение в списке
- Upload: несколько файлов → batch загрузка
- Upload: ошибка → отображение gatewayErrorMessage
- Список черновиков: gatewayDraftsQuery → отображение, сортировка (status, date, name)
- Сортировка статусов: правильный порядок (ready_for_approve > review_required > ...)
- Выбор черновика → metadata form (title, sourceType, docCode, year, mksOksCode, okstuCode, era, jurisdiction, issuingBody, validFrom, validUntil)
- Metadata review: extracted vs manual значения
- Сохранение metadata: handleSaveDraftMetadata → PATCH /drafts/{id}/metadata
- Сброс metadata: handleResetDraftMetadata → форма очищена
- Запуск preview: handleRunDraftChecks → POST /drafts/{id}/preview + poll status
- Preview completed: отображение preview_metadata, duplicates
- Duplicates: отображение title/reason/similarity
- Approve draft: handleDecision("approve") → PATCH /drafts/{id}/decide
- Reject draft: rejectDialog → handleSubmitReject → PATCH /drafts/{id}/decide
- Удаление draft: handleDeleteDraft → DELETE /drafts/{id}
- Очередь: gatewayQueueQuery → отображение queue
- Журнал: processingAuditQuery → отображение событий
- Raw JSON: buildDraftRawJson → диалог
- Notifications: отображение severity/category/message
- Валидация metadata: validateDraftMetadata → ошибки полей

---

## 6. `__tests__/KnowledgeBase.test.tsx` (~250 строк)

**Компонент:** `KnowledgeBase.tsx`

**Сценарии:**
- Рендер: дерево секций знаний, список документов
- Загрузка секций: knowledgeSectionsQuery → отображение tree
- Выбор секции: handleOpenSection → загрузка документов секции
- Назад к секциям: handleBackToSections
- Поиск по документам: knowledgeSearchQuery → scoped результаты
- Изменение scope поиска: handleSearchScopeChange → section/global
- Выбор документа: клик → documentDetailQuery
- Preview документа: handleOpenPreview → диалог preview
- Preview загрузка: previewLoading, previewError
- Страницы preview: навигация по страницам
- Поиск по preview: подсветка, навигация
- Результаты поиска: клик → handleOpenSearchResult → открытие документа на фрагменте
- Сортировка документов: sortDocuments (date, name, type)
- Пустое состояние секции: "Нет документов"
- Фильтр по классификатору: matchSectionDocuments

---

## 7. `__tests__/History.test.tsx` (~200 строк)

**Компонент:** `History.tsx`

**Сценарии:**
- Рендер: таблица истории, фильтры (query, user, project, topic, status)
- Фильтр query: поиск по тексту чата
- Фильтр user: выбор пользователя
- Фильтр project: выбор проекта
- Фильтр topic: выбор темы
- Фильтр status: выбор статуса
- Развернуть строку: клик → отображение сообщений
- Продолжить чат: кнопка → setActiveTab + загрузка сообщений
- Экспорт CSV: handleExport → downloadBlob с csv
- Экспорт ошибка: exportError → отображение
- Preview источника: handleOpenPreview → диалог
- Сводка: historySlices (total, users, queries, avgRating)

---

## 8. `__tests__/AdminPanel.test.tsx` (~200 строк)

**Компонент:** `AdminPanel.tsx`

**Сценарии:**
- Рендер: таблица пользователей, summaryCard
- Фильтр search: поиск по имени/логину
- Выбор пользователя: selectedUser → форма редактирования
- Изменение роли: handleRoleChange → select role
- Toggle access: handleAccessToggle → включение/отключение permission
- Сброс изменений: handleReset → исходные значения
- Сохранение: handleSave → adminApi.updateUser → addAdminAuditLogItem
- Аудит лог: adminApi.audit → отображение событий
- RBAC: engineer не видит секцию управления (canManageUsers = false)
- RBAC: system_admin видит все секции
- Ошибка загрузки пользователей: adminUsersError → Alert
- Ошибка загрузки аудита: adminAuditError → Alert

---

## 9. `__tests__/RegistryEditors.test.tsx` (~300 строк)

**Компонент:** `RegistryEditors.tsx`

**Сценарии:**
- Рендер: вкладки Classifiers / Terminology
- Classifiers list view: GET /registry/classifiers → таблица
- Classifiers tree view: GET /registry/classifiers/tree → дерево
- Classifiers pending view: GET /registry/classifiers/pending
- Classifiers validate view: форма валидации
- Поиск классификатора: поиск по code/full_name
- Создать классификатор: диалог → POST /registry/classifiers
- Редактировать классификатор: диалог → PUT /registry/classifiers/{id}
- Удалить классификатор: confirm → DELETE /registry/classifiers/{id}
- Accept pending: диалог → PATCH accept с parent_code
- Reject pending: диалог → PATCH reject с admin_comment
- Import классификаторов: POST /registry/classifiers/import
- Terminology list: таблица терминов
- Поиск термина: поиск по raw_term/standard_term
- Создать термин: диалог → POST /registry/terminology
- Редактировать термин: диалог → PUT /registry/terminology/{id}
- Удалить термин: confirm → DELETE /registry/terminology/{id}
- Import терминов: POST /registry/terminology/import
- Normalize термина: GET/POST normalize

---

## 10. `__tests__/Monitor.test.tsx` (~150 строк)

**Компонент:** `Monitor.tsx`

**Сценарии:**
- Рендер: секции "Контрольные метрики", "Оценка ответов", "Журнал проверки"
- Загрузка метрик: metricsApi.dashboard → отображение 4-х плиток
- Контрольные метрики: OCR quality, Search quality, Answers with sources, Avg latency
- Статус OK: значение >= target → chip "в норме"
- Статус WARN: значение < target → chip "ниже цели"
- Метрики ответов: usefulRate, ratedAnswers, flaggedForReview, unresolvedAfterReview
- Журнал: строки с time/text, цвет по уровню (ERROR/WARN/INFO)
- Пустой журнал: "Журнал проверки пуст."
- Helper tooltips: клик по иконке Info → подсказка

---

## 11. `__tests__/Feedback.test.tsx` (~100 строк)

**Компонент:** `Feedback.tsx`

**Сценарии:**
- Рендер: вопрос "Полезен ли был этот ответ?", кнопки thumbs up/down
- Выбор useful: click thumbs up → кнопка активна (success цвет)
- Выбор not useful: click thumbs down → кнопка активна (error цвет)
- Сброс выбора: повторный click → снятие выбора
- Отправка: useful + comment → feedbackApi.send → "Спасибо"
- Отправка без комментария: useful без comment → ok
- Ошибка отправки: API error → Alert с сообщением
- После отправки: скрытие кнопок, отображение благодарности

---

## 12. `__tests__/ModeSwitcher.test.tsx` (~350 строк)

**Компонент:** `ModeSwitcher.tsx`

**Сценарии:**
- Рендер: сайдбар с навигацией (nav items)
- Навигация: клик по Chat → setActiveTab("chat")
- Навигация: клик по Search → setActiveTab("search")
- Навигация: клик по Knowledge Base → setActiveTab("knowledge-base")
- Навигация: клик по Monitoring → setActiveTab("monitoring")
- Навигация: клик по Admin → setActiveTab("admin")
- RBAC: engineer не видит Admin
- Темы: светлая/тёмная
- Дерево проектов: createProject → projectsApi.create → отображение
- Развернуть проект: click → отображение чатов
- Свернуть проект: повторный click
- Создать чат: createThread → chatApi.createSession → отображение
- Переименовать чат: startRename → saveRename → chatApi.updateSession
- Удалить чат: confirmDeleteThread → chatApi.deleteSession
- Переименовать проект: startRenameProject → saveProjectRename → projectsApi.update
- Удалить проект: confirmDeleteProject → projectsApi.delete
- Knowledge Processing секции: загрузка/выбор
- Переключение projects: activeProjectIdSnapshot

---

## 13. `__tests__/SourcePreviewDialog.test.tsx` (~100 строк)

**Компонент:** `SourcePreviewDialog.tsx`

**Сценарии:**
- Открытие: передача preview → диалог отображается
- Закрытие: клик по кнопке закрытия → onClose
- Отображение изображения: pagePreviewUrl → img
- Отображение текста: text → pre-форматированный текст
- Навигация по страницам: prev/next
- Зум: увеличение/уменьшение изображения
- Пустой preview: отображение "Нет данных"

---

## 14. `__tests__/VideoGuideDialog.test.tsx` (~40 строк)

**Компонент:** `VideoGuideDialog.tsx`

**Сценарии:**
- Открытие: передача open=true → диалог отображается
- Закрытие: клик по кнопке закрытия → onClose
- Содержимое: заголовок "Видеоинструкция"
