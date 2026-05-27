# План адаптации UI Final к Gateway

Дата: 2026-05-27  
Ветка: `feature/ui-final`  
Папка интерфейса: `UI-UX/UI Final/frontend`

## Основание

План составлен по текущему UI Final и доступным в локальном репозитории API-документам Gateway/backend:

- `origin/develop:docs/api/orchestrator_service_api.md`;
- `origin/develop:docs/api/query_service_api.md`;
- `origin/develop:docs/api/auth_service_api.md`;
- `origin/develop:docs/api/registry_service_api.md`.

Прямой `git fetch` с GitHub на момент проверки не прошел из-за DNS-ошибки `Could not resolve host: github.com`, поэтому план выровнен по уже полученному remote-снимку репозитория. После восстановления доступа к GitHub нужно повторить `git fetch --all --prune` и сверить изменения.

## Целевая схема интеграции

UI Final не должен ходить напрямую в отдельные внутренние сервисы без договоренности. Базовая публичная точка входа для UI по текущим документам:

```text
https://{host}/api/v1
```

Для локальной проверки Orchestrator/Gateway:

```text
http://127.0.0.1:8081/api/v1
```

В `.env` для frontend:

```text
VITE_API_BASE_URL=http://127.0.0.1:8081/api/v1
```

Важное уточнение по текущим API-документам: чатовые функции описаны в Query Service, и в документе прямо указано, что UI обращается к Query Service напрямую, а Orchestrator не проксирует чат-функции. Это нужно отдельно согласовать с backend-командой, потому что для UI удобнее единая публичная точка входа.

## 1. Общий API-клиент

Где менять:

```text
UI-UX/UI Final/frontend/src/utils/http.ts
```

Что сделать:

1. Вынести базовый URL в `VITE_API_BASE_URL`.
2. Добавить единый обработчик ошибок формата:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден",
    "details": {}
  }
}
```

3. Поддержать списки с `meta` для пагинации.
4. Оставить mock-режим как fallback только для демонстрации.
5. Добавить режим `backend unavailable`: UI должен показывать понятное состояние, а не ломать экран.

## 2. Авторизация и профиль

Текущий UI:

- экран входа;
- логин и пароль;
- быстрые demo-карточки ролей;
- отображение ФИО, должности и роли;
- доступность вкладок по роли.

Нужно подключить:

- `POST /auth/token` - получить access/refresh token;
- `POST /auth/refresh` - обновить access token;
- `POST /auth/revoke` - выход;
- `GET /auth/me` - получить профиль текущего пользователя;
- admin endpoints для пользователей, ролей и аудита.

Что должен получить UI из профиля:

- `user_id`;
- ФИО;
- должность;
- роль;
- права;
- доступные вкладки;
- признак доступа к администрированию;
- признак просмотра чужих чатов.

Открытый вопрос:

```text
Backend возвращает готовые availableTabs/permissions или UI сам мапит role -> permissions?
```

## 3. Чат, проекты и сессии

Текущий UI:

- дерево `Мои проекты` под вкладкой `Чат`;
- вложенные чаты внутри проекта;
- отправка вопроса;
- ответ ассистента;
- источники `Страница` и `Документ`;
- обратная связь;
- поиск по текущему чату.

Целевые endpoints Query Service:

- `POST /chat/sessions` - создать новую сессию;
- `GET /chat/sessions` - получить список сессий;
- `GET /chat/sessions/{session_id}` - получить историю сессии;
- `PUT /chat/sessions/{session_id}` - переименовать/обновить параметры сессии;
- `DELETE /chat/sessions/{session_id}` - удалить сессию;
- `GET /chat/sessions/{session_id}/messages/last?limit=20` - загрузить хвост диалога;
- `GET /chat/sessions/{session_id}/messages?before=...&after=...` - пагинация сообщений;
- `POST /chat/sessions/{session_id}/messages` - отправить вопрос;
- `GET /chat/sessions/{session_id}/messages/{message_id}?longpoll=15` - дождаться ответа;
- `POST /chat/feedback` - отправить оценку ответа.

Статусы сообщения, которые должен понимать UI:

- `pending`;
- `enriching`;
- `searching`;
- `generating`;
- `enriching_citations`;
- `answered`;
- `failed`.

Дополнительно UI должен аккуратно обработать бизнес-состояния:

- источники не найдены;
- вопрос вне базы знаний;
- требуется уточнение;
- конфликт источников.

Открытый вопрос:

```text
Какими статусами backend будет обозначать not_found, out_of_scope, needs_clarification и source_conflict: отдельными message.status или отдельным полем result_type?
```

## 4. Источники ответа, страницы и документы

Query Service задает единые имена полей источников:

- `document_id`;
- `page`;
- `section_id`;
- `excerpt`;
- `content`;
- `clause`;
- `page_preview_url`;
- `document_url`;
- `score`.

UI Final должен:

1. Показывать под ответом ссылки `Страница` и `Документ`.
2. По `page_preview_url` открывать preview страницы.
3. По `document_url` открывать документ.
4. Поддержать zoom и поиск по открытому источнику, если backend отдает текстовый слой.
5. Показывать цитаты из разных документов как нормальный сценарий, а не как исключение.

Gateway/Orchestrator endpoints для документов и страниц:

- `GET /documents/{doc_id}/file`;
- `GET /documents/{doc_id}/pages`;
- `GET /documents/{doc_id}/pages/{page_num}`;
- `GET /documents/{doc_id}/pages/{page_num}/text`;
- `GET /documents/{doc_id}/pages/{page_num}/preview`;
- `GET /documents/{doc_id}/parameters`.

Открытый вопрос:

```text
Какая ссылка считается основной для UI: готовый page_preview_url/document_url из Query Service или отдельная сборка URL на стороне frontend?
```

## 5. Поиск

Текущий UI:

- поисковая строка;
- фильтры;
- разделы базы знаний;
- карточки результатов;
- открытие источника.

Целевые endpoints:

- `POST /text/search` - поиск по произвольному тексту через Query Service;
- `POST /documents/search` - поиск документов через Orchestrator;
- `GET /documents/search` - GET-вариант поиска документов.

Что нужно сделать:

1. Разделить сценарии `поиск фрагментов` и `поиск документов`, если backend сохраняет два разных endpoint.
2. Не подставлять случайный документ при пустой выдаче.
3. Показывать состояние `ничего не найдено`.
4. Сохранять ссылки на страницу и документ в том же стиле, что и в чате.

Открытый вопрос:

```text
Для вкладки `Поиск` backend рекомендует `POST /text/search`, `POST /documents/search` или оба endpoint под разные режимы?
```

## 6. База знаний

Текущий UI:

- вкладка `База знаний`;
- карточки состояния документов;
- разделы базы знаний;
- таблица документов;
- загрузка документа;
- загрузка по ссылке;
- повтор OCR.

Целевые endpoints Orchestrator:

- `POST /documents` - загрузить документ;
- `GET /documents` - список документов;
- `GET /documents/{doc_id}` - карточка документа;
- `GET /documents/{doc_id}/status` - статус обработки;
- `POST /documents/{doc_id}/reprocess` - повторная обработка;
- `GET /documents/queue` - очередь обработки;
- `GET /documents/{doc_id}/errors` - ошибки.

Целевые endpoints Registry:

- `GET /registry/documents`;
- `GET /registry/documents/{doc_id}`;
- `GET /registry/documents/{doc_id}/sections`;
- `POST /registry/documents/check-uniqueness`;
- `GET /registry/stats`;
- `GET /registry/classifiers/tree`.

Что нужно сделать:

1. Для таблицы документов использовать Orchestrator или Registry по согласованному правилу.
2. Для разделов базы знаний использовать классификаторы Registry.
3. Для OCR/индексации показывать статусы из Orchestrator.
4. Для загрузки использовать двухфазный pipeline: загрузка, preview, решение, полная обработка.

## 7. Проверка на соответствие НСИ

Текущий UI:

- выбор одного или нескольких документов;
- запуск проверки;
- таблица результата;
- статусы `OK / WARNING / ERROR`;
- ссылки на страницу и документ;
- экспорт в Excel.

Что нужно от backend:

- endpoint запуска проверки;
- endpoint статуса проверки;
- endpoint получения результата;
- endpoint выгрузки Excel;
- единый формат строки результата.

Минимальная строка результата для UI:

- проект;
- раздел;
- параметр;
- значение в проекте;
- требование НСИ;
- документ НСИ;
- статус;
- комментарий;
- источники.

Открытый вопрос:

```text
Проверка относится к Analyse Service, Orchestrator или отдельному Gateway endpoint? Нужны точные маршруты.
```

## 8. История и поиск по чатам

Текущий UI:

- фильтры истории;
- поиск по чатам;
- раскрытие диалога;
- продолжение старого чата;
- экспорт.

Целевые endpoints Query Service:

- `GET /chat/history`;
- `GET /chat/history/export`;
- `GET /chat/sessions`;
- `GET /chat/sessions/{session_id}`;
- `POST /chat/sessions/{session_id}/export`.

Что нужно сделать:

1. Вкладку `История` подключить к `GET /chat/history`.
2. Продолжение чата делать через открытие существующей `session_id`.
3. Поиск по своим старым чатам делать через query-параметры истории.
4. Администраторский просмотр чужих чатов включать только при наличии права.

Открытый вопрос:

```text
Какие query-параметры поддерживает /chat/history: project_id, user_id, status, text, date_from, date_to?
```

## 9. QA и метрики

Текущий UI:

- контрольные метрики;
- оценка ответов ассистента;
- журнал проверки.

Целевые endpoints:

- `GET /monitor/health`;
- `GET /monitor/metrics`;
- данные feedback через `POST /chat/feedback` и будущую статистику по feedback.

Что нужно сделать:

1. Подключить карточки метрик к `/monitor/metrics`.
2. Отдельно согласовать статистику оценок ответов ассистента.
3. Журнал проверки формировать из истории событий backend или отдельного monitoring endpoint.

Открытый вопрос:

```text
Будет ли /monitor/metrics возвращать именно UI-метрики качества ответов, OCR, поиска и feedback, или это только технические метрики сервисов?
```

## 10. Администрирование

Текущий UI:

- список пользователей;
- роли;
- права;
- сохранение изменений;
- административный журнал;
- журнал обработки.

Целевые endpoints Auth Service:

- `GET /admin/users`;
- `POST /admin/users`;
- `GET /admin/users/{user_id}`;
- `PUT /admin/users/{user_id}`;
- `PATCH /admin/users/{user_id}`;
- `DELETE /admin/users/{user_id}`;
- `GET /admin/roles`;
- `POST /admin/roles`;
- `GET /admin/audit`.

Что нужно сделать:

1. Связать таблицу пользователей с `/admin/users`.
2. Связать список ролей с `/admin/roles`.
3. Сохранять изменения прав через admin endpoint.
4. Отображать audit log из `/admin/audit`.

Открытый вопрос:

```text
Права пользователя хранятся как отдельные permissions или только через role?
```

## 11. Приоритет работ

1. Переключить базовый URL и общий API-клиент.
2. Подключить авторизацию и профиль пользователя.
3. Подключить чатовые сессии и longpoll ответа.
4. Подключить источники, страницы и документы.
5. Подключить историю и продолжение чата.
6. Подключить поиск.
7. Подключить базу знаний.
8. Подключить проверку НСИ.
9. Подключить QA-метрики.
10. Подключить администрирование.

## 12. Что можно оставить mock до финального backend

- часть QA-метрик;
- журнал проверки;
- Excel-экспорт проверки;
- часть административных журналов;
- демонстрационные данные для прав доступа;
- визуальные статусы OCR/индексации, пока нет стабильных live-данных.
