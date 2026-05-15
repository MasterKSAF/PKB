# UI V1: план адаптации под Gateway и backend API

Дата обновления: 2026-05-15
Ветка UI: `feature/ui-import-frontend-v1`

Основа:

- актуальный UI V1 в `UI-UX/frontend-v1`;
- документация `docs/api`;
- ревью mock-gateway от 2026-05-15, подготовленное Полиной;
- обновление OCR API от 2026-05-15: `GET /ocr/processes`;
- ранее полученные ответы backend-команды на вопросы UI.

## 1. Главное решение

UI V1 должен стыковаться не с отдельными backend-сервисами напрямую, а с единым публичным слоем Gateway.

Целевая схема:

```text
UI V1
  -> Gateway / API v1
    -> Auth Service
    -> Query Service
    -> Orchestrator Service
    -> Registry Service
    -> OCR Service
    -> Validation Service
    -> Monitoring / QA
```

Для frontend это означает:

- один базовый адрес API;
- единый префикс `/api/v1`;
- единый формат ошибок;
- единая авторизация через токен;
- маршрутизация между сервисами остается задачей Gateway/backend.

UI не должен напрямую выбирать между `Auth`, `Query`, `Orchestrator`, `Registry`, `OCR` и другими сервисами. Внутреннее устройство backend может меняться, но публичный контракт для UI должен оставаться стабильным.

## 2. Базовый адрес API

Для mock-gateway:

```text
VITE_API_BASE_URL=http://localhost:8081/api/v1
```

Для стенда заказчика:

```text
VITE_API_BASE_URL=https://{host}/api/v1
```

Что нужно изменить в UI V1:

- убрать жесткую привязку к `http://localhost:8000`;
- все реальные запросы строить от `VITE_API_BASE_URL`;
- не дублировать `/api/v1` в каждом endpoint, если он уже есть в базовом URL;
- оставить mock/demo fallback для демонстрации без backend.

Главный файл для изменения:

- `UI-UX/frontend-v1/src/utils/http.ts`.

## 3. Что backend уже подтвердил или уточнил

### Gateway

В ветке `develop_gateway` есть mock-gateway, который объединяет сервисы на одном порту и эмулирует публичный API.

Подтвержденные свойства gateway:

- единый публичный префикс `/api/v1`;
- CORS включен;
- `Authorization: Bearer <token>` используется для определения пользователя;
- `/auth/me` возвращает пользователя из токена, а не статичную заглушку;
- `/admin/*` уже защищен проверкой роли;
- каждый ответ содержит заголовок `X-Process-Time`;
- для `POST /documents` и `POST /chat` поддерживается `Idempotency-Key`;
- ошибки приведены к единому формату.

### Роли

Backend использует три роли:

| Роль в API | Отображение в UI | Смысл |
|---|---|---|
| `engineer` | Инженер | Чат, поиск, проверка, история |
| `knowledge_admin` | Администратор НСИ | Документы, НСИ, реестр, OCR, QA |
| `system_admin` | Системный администратор | Пользователи, роли, аудит, полный доступ |

UI должен брать доступные вкладки и права не из ручной логики, а из профиля пользователя.

Ожидаемый смысл ответа `GET /auth/me`:

```json
{
  "user_id": "u-001",
  "email": "ivanov@example.com",
  "full_name": "Иванов Сергей Петрович",
  "position": "Инженер-конструктор",
  "role": "engineer",
  "role_title": "Инженер",
  "available_tabs": ["chat", "search", "checks", "history"],
  "permissions": {
    "can_upload_documents": false,
    "can_run_ocr": false,
    "can_manage_users": false,
    "can_manage_classifiers": false,
    "can_manage_terminology": false,
    "can_manage_registry": false
  }
}
```

### Ошибки

Формат ошибок унифицирован:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Документ не найден",
    "details": {}
  }
}
```

UI должен показывать пользователю `message`, а технический `code` использовать для сценариев обработки.

### Пагинация

Для списков backend использует `meta`:

```json
{
  "items": [],
  "meta": {
    "total": 120,
    "page": 1,
    "page_size": 50
  }
}
```

Для Registry возможен формат:

```json
{
  "data": [],
  "meta": {
    "total": 120,
    "page": 1,
    "page_size": 50
  }
}
```

Вывод: в `http.ts` нужен универсальный нормализатор ответа, который умеет читать прямой объект, `items + meta` и `data + meta`.

### Проверка НСИ

Mock-gateway сейчас описывает `POST /validate/checks` как синхронный запрос:

```text
POST /validate/checks -> 200 OK
```

Ответ содержит:

- `check_run_id`;
- `status`;
- `summary`;
- `items[]`;
- `created_at`.

Для MVP считаем синхронный вариант базовым, но на встрече с backend надо уточнить, нужен ли async-режим для тяжелых пакетных проверок.

### Registry и документы

Подтверждено поле `registry_doc_id` в списке документов.

Это важно, потому что в UI нельзя смешивать:

- физический файл в `/documents`;
- карточку НСИ в `/registry/documents`.

Связь между ними должна идти через `registry_doc_id`.

## 4. Что нового появилось 15.05 и что берем в UI-план

### OCR-процессы

В документации OCR Service появился endpoint:

```text
GET /ocr/processes
```

Он возвращает список активных процессов OCR:

```json
{
  "processes": [
    {
      "task_id": "ocr-task-001",
      "version_id": "c4b9f2d3-...",
      "status": "processing",
      "progress_percent": 45,
      "pages_processed": 5,
      "pages_total": 12,
      "engine": "paddleocr",
      "started_at": "2026-05-15T10:00:05Z"
    }
  ]
}
```

Важно: OCR Service в документации указан как внутренний сервис, не предназначенный для прямого вызова из frontend.

Поэтому для UI решение такое:

- UI не вызывает OCR Service напрямую;
- UI получает данные OCR-процессов только через Gateway;
- если Gateway не публикует `/ocr/processes`, нужно согласовать публичный маршрут, например `/documents/ocr/processes` или `/monitor/ocr/processes`.

Где это полезно в интерфейсе:

- вкладка `Реестр`: показать активную очередь OCR и прогресс обработки документов;
- вкладка `Администрирование`: показать процессы обработки для администратора НСИ;
- вкладка `QA`: использовать как техническую метрику нагрузки и качества обработки.

Для MVP достаточно показать:

- количество активных OCR-процессов;
- статус;
- прогресс;
- обработано страниц / всего страниц;
- используемый OCR-движок.

## 5. Что меняем в UI V1

### 5.1 HTTP-слой

Файл:

- `UI-UX/frontend-v1/src/utils/http.ts`.

Сделать:

- добавить `VITE_API_BASE_URL`;
- перевести реальные запросы на Gateway `/api/v1`;
- добавить `Authorization: Bearer <access_token>`;
- поддержать единый формат ошибок `{ error: { code, message, details } }`;
- поддержать пагинацию `items + meta` и `data + meta`;
- добавить обработку `401` и `403`;
- оставить mock fallback для режима без backend;
- добавить возможность читать `X-Process-Time` для QA/диагностики.

### 5.2 Авторизация

Файлы:

- `src/components/LoginScreen.tsx`;
- `src/store/uiStore.ts`;
- `src/utils/access.ts`;
- `src/utils/http.ts`.

Сделать:

- demo-выбор пользователя оставить только для mock-режима;
- для real-режима использовать `POST /auth/token`;
- после входа вызывать `GET /auth/me`;
- хранить `access_token`;
- при выходе очищать токен и профиль пользователя;
- ФИО, должность, роль, вкладки и права брать из backend.

Пример запроса:

```json
{
  "username": "ivanov@example.com",
  "password": "secret123"
}
```

Важно: в mock-gateway используется поле `username`, но фактически туда передается email. На UI надо подписать это как "Email / логин".

### 5.3 Роли, вкладки и кнопки

Файлы:

- `src/utils/access.ts`;
- `src/components/ModeSwitcher.tsx`;
- `src/App.tsx`;
- `src/components/AdminPanel.tsx`;
- `src/components/DocumentRegistry.tsx`.

Сделать:

- вкладки показывать по `available_tabs`;
- кнопки включать/выключать по `permissions`;
- не держать отдельную независимую матрицу ролей во frontend как главный источник прав;
- локальную матрицу оставить только как fallback для demo-режима.

Открытый вопрос к backend:

- нужно ли защищать не только `/admin/*`, но и endpoints для документов, проверки, QA и реестра.

Рекомендация для MVP:

- backend должен проверять права не только на UI-уровне, но и на сервере;
- frontend скрывает недоступные действия, backend дополнительно запрещает прямой вызов.

### 5.4 Чат

Файлы:

- `src/components/Chat.tsx`;
- `src/components/Feedback.tsx`;
- `src/utils/http.ts`;
- `src/store/uiStore.ts`.

Базовый endpoint:

```text
POST /chat
```

Что нужно сделать:

- отправлять вопрос через Gateway;
- хранить активный `session_id`;
- принимать `session_id`, который вернул backend;
- строить нумерованные пункты ответа из `answer_items[]`;
- источники брать из `citations[]`;
- ссылки `Страница` и `Документ` брать из backend-полей;
- статусы ответа показывать спокойными UI-состояниями.

Ожидаемые поля ответа:

- `answer_id`;
- `session_id`;
- `status`;
- `message`;
- `answer_items[]`;
- `citations[]`;
- `latency_ms`.

Открытый вопрос:

- какой финальный формат feedback: текущий UI-формат `useful + comment` или backend-формат `rating + comment + aspects`.

Предварительное решение:

- если backend подтверждает шкалу `rating`, UI надо доработать под более богатую оценку ответа;
- если для MVP оставляем просто "полезно / не полезно", backend должен уметь принять `useful`.

### 5.5 История чатов

Файл:

- `src/components/History.tsx`.

Основные endpoints:

```text
GET /chat/sessions
GET /chat/sessions/{id}
GET /chat/history
GET /chat/history/export
```

Что нужно сделать:

- главным представлением считать список чат-сессий;
- по клику раскрывать полный диалог;
- оставить возможность продолжить выбранный чат;
- плоскую историю использовать как журнал/фильтр;
- экспорт истории отправлять с текущими фильтрами.

Открытые вопросы:

- нужен ли full-text поиск по содержимому всех старых чатов;
- что происходит с текущим активным чатом, когда пользователь нажимает "Продолжить чат" из истории;
- какие чаты видит администратор: только свои, все, по проекту или обезличенную статистику.

### 5.6 Поиск по документам

Файлы:

- `src/components/Search.tsx`;
- `src/utils/http.ts`.

Базовый endpoint:

```text
POST /documents/search
```

Что нужно сделать:

- заменить старый `/search` на поиск через Gateway;
- результаты маппить в текущие карточки и таблицы UI;
- ссылки `Страница` и `Документ` брать из backend;
- поддержать фильтры, которые backend реально отдаст.

Отложить:

- `POST /text/search`;
- `POST /text/ask`.

Причина: эти endpoints сейчас выглядят как низкоуровневые или дополнительные. Для UI V1 базовым сценарием считаем поиск по документам.

### 5.7 Страница и документ

Файлы:

- `src/components/SourcePreviewDialog.tsx`;
- `src/components/Chat.tsx`;
- `src/components/Search.tsx`;
- `src/components/ChecksPanel.tsx`.

Ожидаемые endpoints:

```text
GET /documents/{id}/pages/{num}/preview
GET /documents/{id}/pages/{num}
GET /documents/{id}/file
```

Что нужно сделать:

- кнопка `Страница` открывает конкретную страницу или preview;
- кнопка `Документ` открывает полный документ;
- UI не конвертирует форматы самостоятельно;
- если backend возвращает PDF, изображение или URL, UI показывает это в правой панели.

Открытый вопрос:

- как backend будет отдавать DOCX/XLSX/PPTX: оригиналом, PDF-конверсией, HTML-preview или изображением страницы.

### 5.8 Реестр и документы

Файлы:

- `src/components/DocumentRegistry.tsx`;
- `src/components/AdminPanel.tsx`;
- `src/utils/http.ts`.

Endpoints для физических файлов:

```text
GET /documents
POST /documents
GET /documents/{id}/status
POST /documents/{id}/reprocess
GET /documents/{id}/errors
GET /documents/queue
```

Endpoints для карточек НСИ:

```text
GET /registry/documents
GET /registry/documents/{id}
POST /registry/documents
PUT /registry/documents/{id}
PATCH /registry/documents/{id}/status
DELETE /registry/documents/{id}
GET /registry/documents/export
POST /registry/documents/import
```

Что нужно сделать:

- не смешивать физические файлы и карточки НСИ;
- показывать `registry_doc_id`, если backend вернул связь;
- загрузку и OCR-статусы брать из `/documents`;
- НСИ-метаданные брать из `/registry/documents`;
- действия загрузки, импорта, экспорта и редактирования показывать только по правам.

### 5.9 Очередь OCR

Файлы:

- `src/components/DocumentRegistry.tsx`;
- `src/components/AdminPanel.tsx`;
- `src/components/Monitor.tsx`;
- `src/utils/http.ts`.

Новый backend-сигнал:

```text
GET /ocr/processes
```

Но для UI это должно быть доступно через Gateway.

Что нужно сделать после подтверждения маршрута:

- добавить метод `getOcrProcesses`;
- показать активные процессы обработки;
- показывать прогресс и количество страниц;
- связать `version_id` с документом, если backend вернет нужную связь;
- в QA использовать количество активных/зависших процессов как технический показатель.

Открытый вопрос:

- какой публичный Gateway endpoint использовать для OCR-процессов.

### 5.10 Проверка НСИ

Файл:

- `src/components/ChecksPanel.tsx`.

Базовый endpoint:

```text
POST /validate/checks
```

Текущее решение mock-gateway:

- синхронный ответ `200 OK`;
- полный результат возвращается сразу.

Что нужно сделать:

- отправлять проектные документы и документы НСИ раздельно;
- не отправлять `user_id`, если backend берет пользователя из токена;
- маппить `summary` и `items[]` в текущую таблицу;
- привязать экспорт к `GET /validate/checks/{id}/export`.

Открытый вопрос:

- нужен ли async-режим для больших пакетных проверок и какой порог переключения.

### 5.11 QA

Файл:

- `src/components/Monitor.tsx`.

Endpoint:

```text
GET /monitor/metrics
```

Что нужно сделать:

- оставить текущий UI;
- реальные метрики подключать после подтверждения состава полей;
- добавить OCR-процессы как возможный источник технических метрик;
- feedback инженеров учитывать как источник оценки качества, если backend возвращает такие агрегаты.

### 5.12 Администрирование

Файл:

- `src/components/AdminPanel.tsx`.

Endpoints:

```text
GET /admin/users
POST /admin/users
GET /admin/roles
GET /admin/audit
PATCH /admin/users/{id}
GET /common/enums
```

Что нужно сделать:

- пользователей брать из backend;
- роли брать из backend;
- аудит брать из backend;
- смену роли отправлять на backend;
- настройки классификаторов, терминологии и реестра показывать по правам.

## 6. Что пока не переносим в UI V1

Не берем в работу прямо сейчас:

- `POST /text/ask`;
- `POST /text/search`;
- `POST /chat/sessions/{id}/context`;
- поля качества в `ChatResponse`: `confidence`, `tokens_used`, `is_grounded`;
- полноценный preview DOCX/XLSX/PPTX;
- full-text поиск по содержимому всех старых чатов;
- async-режим проверки НСИ, пока backend не подтвердит необходимость.

Причина: эти функции либо сверх текущего MVP, либо требуют отдельного согласования, либо пока не имеют устойчивого UI-сценария.

## 7. Открытые вопросы для созвона UI + backend

### 1. Gateway и публичный API

Подтвердить, что UI V1 должен ходить только в Gateway:

```text
http://localhost:8081/api/v1
```

И что прямые вызовы отдельных сервисов из UI не нужны.

### 2. Scope RBAC

Сейчас backend защищает `/admin/*`, но UI разграничивает также документы, проверки, QA и реестр.

Нужно решить, какие endpoints backend обязан защищать уже в MVP.

### 3. Feedback

Согласовать формат обратной связи:

- простой UI-формат: `useful + comment`;
- расширенный backend-формат: `rating + comment + aspects`;
- поддержка обоих форматов.

Рекомендация: если backend готов, перейти на `rating`, потому что это полезнее для QA-метрик.

### 4. Проверка НСИ

Синхронный `POST /validate/checks` считаем базовым для MVP.

Нужно уточнить:

- будет ли async-режим;
- какой порог для async;
- как UI узнает прогресс проверки;
- какой endpoint экспорта Excel считать финальным.

### 5. OCR-процессы через Gateway

Нужно подтвердить публичный маршрут для списка OCR-процессов.

Варианты:

- `/ocr/processes`;
- `/documents/ocr/processes`;
- `/monitor/ocr/processes`.

Главное: UI не должен ходить во внутренний OCR Service напрямую.

### 6. Форматы ответа списков

Нужно зафиксировать, где используется:

- прямой объект;
- `items + meta`;
- `data + meta`.

UI может поддержать все три варианта, но backend-команде лучше сократить количество форматов.

### 7. История чатов

Нужно решить:

- есть ли full-text поиск по старым чатам;
- видит ли администратор чужие чаты;
- можно ли продолжать старый чат;
- что происходит с текущим открытым чатом при продолжении старого.

### 8. Office preview

Нужно понять, как будут открываться DOCX/XLSX/PPTX:

- оригинальным файлом;
- PDF-конверсией;
- HTML-preview;
- изображением страницы;
- ссылкой на viewer.

## 8. Backend-only замечания, которые UI учитывает, но не чинит

По ревью mock-gateway от 15.05 остались пункты, которые должна закрывать backend-команда:

- hard-coded `u-001` вместо пользователя из `request.state.user`;
- разные регистры enum-ов: `OK/WARNING/ERROR` против `ok/warning/error`;
- in-memory сессии сбрасываются при перезапуске;
- статические mock-источники в ответах чата;
- местами типы коллекций в Pydantic-моделях описаны слишком общо.

Для UI это означает:

- не строить важную логику на временных mock-данных;
- быть готовыми к смене enum-ов;
- нормализовать статусы на frontend-уровне до финального контракта;
- не считать mock-сессии полноценным постоянным хранилищем.

## 9. Приоритет внедрения

### Этап 1. Gateway-ready HTTP layer

1. Обновить `http.ts` под `VITE_API_BASE_URL`.
2. Перевести пути на `/api/v1`.
3. Добавить токен авторизации.
4. Добавить обработку `401`, `403` и единого формата ошибок.
5. Добавить нормализацию `items/data/meta`.

### Этап 2. Auth и роли

1. Подключить `POST /auth/token`.
2. Подключить `GET /auth/me`.
3. Перевести вкладки и кнопки на `available_tabs` и `permissions`.
4. Оставить локальные роли только для mock-режима.

### Этап 3. Чат и история

1. Подключить `POST /chat`.
2. Сохранять `session_id`.
3. Подключить список сессий.
4. Подключить раскрытие диалога.
5. Сохранить локальный поиск по текущему открытому чату.

### Этап 4. Документы, поиск и preview

1. Подключить `/documents/search`.
2. Подключить открытие страницы.
3. Подключить открытие документа.
4. Разделить `/documents` и `/registry/documents`.

### Этап 5. Проверка НСИ

1. Подключить `POST /validate/checks`.
2. Маппить `summary` и `items[]`.
3. Подключить экспорт результата.
4. Отдельно вернуться к async-режиму, если backend подтвердит необходимость.

### Этап 6. OCR и QA

1. Согласовать публичный endpoint OCR-процессов через Gateway.
2. Добавить отображение активных OCR-процессов.
3. Подключить `/monitor/metrics`.
4. Решить формат feedback и связать его с QA.

## 10. Короткий вывод

UI V1 оставляем базовой рабочей версией, но план адаптации теперь строим вокруг Gateway.

Главное изменение: frontend больше не должен думать, какой внутренний сервис вызывать. Он работает с единым `/api/v1`, а Gateway распределяет запросы дальше.

С учетом ревью Полины от 15.05 и нового `GET /ocr/processes` ближайшие практические шаги такие:

1. Подготовить HTTP-слой UI к Gateway.
2. Подключить авторизацию и роли через backend.
3. Перевести чат, историю и поиск на реальные endpoints.
4. Добавить OCR-процессы в план UI как новый источник статусов обработки.
5. На созвоне закрыть вопросы по RBAC, feedback, проверке НСИ и публичному маршруту OCR-процессов.
