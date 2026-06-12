# UI Final: сверка со свежими GitHub docs/api

Дата проверки: 12.06.2026

Источник: `origin/develop`, commit `fe9f0b3`
Папка GitHub: https://github.com/NeuronsUII/PKB_neuroassistant/tree/develop/docs/api

## Короткий вывод

В свежей документации `docs/api` на `develop` есть обновления, которые частично расходятся с текущим UI Final. Самые важные зоны: Auth/Admin пути, формат feedback, основной endpoint поиска, Registry-поля и статусы документов, chat projects.

При этом часть документации конфликтует сама с собой: `auth_service_api.md` уже описывает `/users/*`, `/roles`, `/audit`, а `common_api.md` и Gateway-доки ещё содержат `/admin/*`. Поэтому Auth/Admin пути нельзя менять в UI без подтверждения backend.

## Найденные расхождения

1. Auth/Admin API

   Свежий `auth_service_api.md` описывает:
   - `GET /users/me`
   - `GET /users`
   - `POST /users`
   - `PUT /users/{user_id}`
   - `DELETE /users/{user_id}`
   - `GET /roles`
   - `POST /roles`
   - `GET /audit`

   Текущий UI использует:
   - `GET /auth/me`
   - `GET /admin/users`
   - `GET /admin/audit`
   - `PATCH /admin/users/{user_id}`

   Статус: требует подтверждения backend, потому что документация конфликтует.

2. Feedback

   Свежий `query_service_api.md` для session-формата требует:

   ```json
   {
     "session_id": 1001,
     "message_id": 420004,
     "rating": "positive",
     "comment": "..."
   }
   ```

   Текущий UI отправляет `rating: 5 | 1` и `useful`.

   Статус: требует подтверждения backend. По свежей проверке mock Gateway принимает числовой `rating` и возвращает `422` на строковый `rating`, поэтому UI пока оставлен на работающем числовом формате.

3. Поиск

   Свежая документация описывает основной поиск как:
   - `POST /text/search`

   Текущий UI сначала пробует:
   - `POST /documents/search`

   И только потом fallback:
   - `POST /text/search`

   Статус: можно исправить сразу. `/text/search` должен быть основным endpoint для поиска по базе знаний.

4. Chat projects

   Свежий `query_service_api.md` описывает полноценный CRUD:
   - `POST /chat/projects`
   - `GET /chat/projects`
   - `GET /chat/projects/{project_id}`
   - `PUT /chat/projects/{project_id}`
   - `DELETE /chat/projects/{project_id}`

   Текущий UI уже использует Gateway-first слой `/chat/projects` для списка, создания, переименования и удаления проектов. Сессии по-прежнему дополнительно читаются из `/chat/sessions`, чтобы показать fallback-группу `Рабочие диалоги`, если Gateway не связывает сессии с проектами.

   Статус: частично закрыто в UI. Остается backend-вопрос: должен ли `POST /chat/sessions` реально принимать и сохранять `project_id`.

5. Загрузка сообщений чата

   Документация рекомендует:
   - `GET /chat/sessions/{session_id}/messages/last?limit=20`
   - `GET /chat/sessions/{session_id}/messages?after={message_id}`
   - `GET /chat/sessions/{session_id}/messages?before={message_id}`

   Текущий UI при выборе сессии использует:
   - `GET /chat/sessions/{session_id}`

   Longpoll по конкретному `message_id` уже реализован правильно.

   Статус: не критично, но надо улучшить стартовую загрузку и пагинацию сообщений.

6. Registry: поля документов

   Свежий `registry_service_api.md` добавляет/уточняет поля:
   - `group`
   - `document_type`
   - `classification_status: { mks, okstu, udk, subject_area }`
   - `adoption_date`
   - `effective_from`
   - `replaces`
   - `status_note`

   Текущий UI принимает ключевые поля Registry, включая `group`, `mks_oks_code`, `okstu_code`, `classification_status`, и использует `/registry/documents` как основной источник списка документов.

   Статус: частично закрыто. Дальше нужно проверять на реальных данных, потому что текущие mock Registry/Classifiers не связаны между собой по MKS-коду.

7. Registry: статусы документов

   Свежая статусная модель документов:
   - `created`
   - `pending_index`
   - `indexing`
   - `indexed`
   - `failed`

   Текущий UI ещё частично мапит старые статусы:
   - `approved`
   - `completed`
   - `ready_for_promotion`
   - `uploaded`
   - `parsing`

   Статус: маппинг расширен безопасно. UI принимает старые и новые статусы, чтобы не ломаться на разных версиях Gateway.

8. Registry/classifiers пути

   В документации есть расхождение:
   - `registry_service_api.md`: `/registry/classifiers/tree`
   - `gateway_service_api.md`: `/classifiers/*`

   Текущий UI использует:
   - сначала `/classifiers/tree`
   - затем fallback `/registry/classifiers/tree`

   Статус: совместимость добавлена. Нужно зафиксировать канонический Gateway-путь.

9. Drafts

   Свежая документация подтверждает основной сценарий:
   - `POST /drafts`
   - `GET /drafts`
   - `GET /drafts/{draft_id}`
   - `GET /drafts/{draft_id}/preview`
   - `POST /drafts/{draft_id}/preview`
   - `GET /drafts/{draft_id}/preview/status`
   - `PATCH /drafts/{draft_id}/decide`
   - `DELETE /drafts/{draft_id}`

   Статусы черновиков:
   - `uploaded`
   - `previewing`
   - `ready_for_approve`
   - `approved`
   - `discarded`

   Текущий UI уже поддерживает этот набор, включая совместимость со старыми `preview_ready` и `promoted`.

   Статус: в целом закрыто.

## Что можно исправить сразу

1. Сделать `/text/search` основным endpoint поиска по базе знаний, если backend подтвердит, что именно он должен заменить `/documents/search` в UI Final.

2. Расширить визуальное отображение Registry-полей в карточке/preview документа:
   - `adoption_date`
   - `effective_from`
   - `replaces`
   - `status_note`
   - `successor_doc_id`
   - `predecessor_doc_id`

3. Проверить провал в раздел базы знаний на реальных данных, где `mks_oks_code` документа совпадает с кодом раздела.

## Уже исправлено в UI после этой сверки

1. Добавлен Gateway-first слой `/chat/projects`.
2. Создание chat-сессии из проекта отправляет `project_id`.
3. База знаний переведена на `/registry/documents`.
4. Предпросмотр документа подтягивает `/registry/documents/{doc_id}/sections`.
5. Маппинг статусов документов расширен:
   - `indexed` -> индексирован / готов
   - `indexing`, `pending_index` -> в обработке
   - `created` -> создан / ожидает индексации
   - `failed` -> ошибка

## Что нельзя менять без подтверждения backend

1. Переключать Auth/Admin с `/auth/me` и `/admin/*` на `/users/*`, `/roles`, `/audit`.

2. Переключать классификаторы с `/classifiers/tree` на `/registry/classifiers/tree`.

3. Менять payload `POST /chat/feedback` на строковый `rating`, пока mock Gateway и документация расходятся.

4. Делать отдельный UI для Registry CRUD, если это не подтверждено как задача для UI Final.

## Вопросы backend

1. Какой актуальный Gateway-путь для профиля пользователя:
   - `/auth/me`
   - или `/users/me`?

2. Какой актуальный Gateway-путь для администрирования пользователей:
   - `/admin/users`
   - или `/users`?

3. Какой актуальный Gateway-путь для ролей:
   - `/admin/roles`
   - или `/roles`?

4. Какой актуальный Gateway-путь для аудита:
   - `/admin/audit`
   - или `/audit`?

5. Какой канонический путь классификаторов через Gateway:
   - `/classifiers/tree`
   - или `/registry/classifiers/tree`?

6. Должен ли `POST /chat/sessions` принимать и сохранять `project_id`, чтобы сессии реально попадали внутрь проекта?

7. Должен ли feedback использовать session-формат с `rating: positive/negative/neutral`, или текущий mock-формат с числовым `rating`?

8. Почему `GET /chat/history/export` возвращает `url`, который в mock Gateway отдает `404`?

9. Нужно ли синхронизировать mock Registry/Classifiers так, чтобы документы попадали в разделы по `mks_oks_code`?
