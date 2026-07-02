# PKB UI Final Frontend

Актуальное React-приложение интерфейса `AI Assistant PKB`.

## Статус

| Параметр | Значение |
| --- | --- |
| Основная ветка | `develop` |
| Папка приложения | `UI-UX/UI Final/frontend` |
| Локальный порт | `3300` |
| Локальный Gateway | `http://127.0.0.1:8080/api/v1` |
| Стек | React 19, Vite 6, TypeScript, MUI, Zustand, TanStack Query, Axios |
| Режимы | `prod` через Gateway и локальный `demo` |

`frontend-v1` и `frontend-v2` удалены из `develop`. Источник истины по UI - только эта папка.

## Быстрый запуск

```powershell
npm ci
npm run dev -- --host 127.0.0.1 --port 3300 --strictPort
```

Открыть:

```text
http://127.0.0.1:3300
```

Docker:

```powershell
docker compose up --build
```

Если нужен полный пересборочный цикл:

```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

`docker compose up` без `--build` может запустить старый образ и не подтянуть изменения кода.

## Проверка

```powershell
npm run lint
npm run test:run
npm run build
```

Команды из `package.json`:

| Команда | Что делает |
| --- | --- |
| `npm run dev` | Запускает Vite на порту `3300`, host `0.0.0.0`. |
| `npm run lint` | Запускает TypeScript-проверку `tsc --noEmit`. |
| `npm run test:run` | Запускает Vitest один раз. |
| `npm run build` | Собирает production bundle через Vite. |
| `npm run preview` | Запускает Vite preview. |
| `npm run test:coverage` | Запускает Vitest с coverage. |

## Вход и режимы

UI поддерживает два режима:

| Режим | Источник данных | Авторизация |
| --- | --- | --- |
| `demo` | `src/utils/mockData.ts` | Локальный пароль `demo`. |
| `prod` | Gateway/Auth/Registry/Query/Orchestrator | `POST /auth/token`, `GET /auth/me`, refresh token. |

В demo-режиме доступны локальные пользователи:

| Роль | Логин | Пароль | Demo-вкладки |
| --- | --- | --- | --- |
| Пользователь | `a.morozov` | `demo` | Чат, База знаний, История |
| Пользователь | `m.sokolova` | `demo` | Чат, База знаний, История |
| Администратор знаний | `o.volkova` | `demo` | Чат, База знаний, Обработка базы знаний, История |
| Системный администратор | `d.smirnov` | `demo` | Все demo-вкладки |

Продуктивные логины и пароли задаются текущим Gateway/Auth seed и не являются частью frontend-контракта.

## Auth-flow

1. Вход выполняется через `POST /auth/token`.
2. Профиль, роль, permissions и `available_tabs` подтягиваются через `GET /auth/me`.
3. После reload UI восстанавливает продуктивную сессию по сохраненным access/refresh token.
4. При `401 Unauthorized` HTTP-слой вызывает `POST /auth/refresh` и один раз повторяет исходный запрос.
5. Если refresh token истек или невалиден, UI очищает локальную сессию и возвращает пользователя на экран входа.
6. В продуктивном режиме видимые вкладки определяет backend-поле `available_tabs`.
7. Локальная карта ролей используется только в demo-режиме.
8. Переключение prod -> demo -> prod не отзывает продуктивные токены и возвращает исходную prod-сессию.

## Вкладки и доступ

Типы вкладок определены в `src/utils/access.ts`.

| AppTab | UI-раздел |
| --- | --- |
| `chat` | Чат инженера |
| `documents` | База знаний |
| `knowledgeProcessing` | Обработка базы знаний |
| `history` | История |
| `qa` | QA |
| `admin` | Администрирование |
| `search` | Legacy/reserve route, не основной сценарий |

Demo-доступ:

| Роль | AppTab |
| --- | --- |
| `user` | `chat`, `documents`, `history` |
| `knowledgeAdmin` | `chat`, `documents`, `knowledgeProcessing`, `history` |
| `systemAdmin` | `chat`, `documents`, `knowledgeProcessing`, `history`, `qa`, `admin` |

Prod-доступ:

| Gateway tab | AppTab |
| --- | --- |
| `chat` | `chat` |
| `search` | `documents` |
| `knowledge_base` | `documents` |
| `documents` | `knowledgeProcessing` |
| `registry` | `knowledgeProcessing` |
| `knowledge_processing` | `knowledgeProcessing` |
| `history` | `history` |
| `monitor` | `qa` |
| `qa` | `qa` |
| `admin` | `admin` |

Если Gateway не передал `available_tabs`, prod UI показывает controlled empty state `Разделы недоступны` и не подставляет demo-данные.

## Основные экраны

| Экран | Компонент | Что делает |
| --- | --- | --- |
| Вход | `LoginScreen.tsx` | Переключение demo/prod, ввод логина/пароля, запуск auth-flow. |
| Навигация | `ModeSwitcher.tsx` | Левое меню, проекты/чаты, вложенные пункты обработки БЗ, тема, focus mode, видеоинструкция. |
| Чат | `Chat.tsx` | Проекты, дерево чатов, отправка сообщений, longpoll, источники, preview, поиск по текущему чату, feedback. |
| База знаний | `KnowledgeBase.tsx` | Разделы, документы, поиск по базе/разделу, preview и поиск внутри документа. |
| Обработка БЗ | `KnowledgeProcessing.tsx` | Загрузка, очередь, прогресс, черновики, метаданные, raw JSON, preview, решения, журналы. |
| Реестр | `DocumentRegistryPanel.tsx` | Таблица документов, фильтры, версии, история, ошибки, страницы, preview, скачивание, удаление. |
| История | `History.tsx` | Фильтры, поиск, раскрытие сессии, источники, preview, продолжение чата, экспорт. |
| QA | `Monitor.tsx` | Метрики качества, журнал проверки, оценки ответов. |
| Администрирование | `AdminPanel.tsx` | Пользователи, роли, права, audit, журнал обработки. |
| Registry-редакторы | `RegistryEditors.tsx` | Классификаторы, терминология, неизвестные коды. |
| Legacy поиск | `Search.tsx` | Старый/резервный компонент поиска; основной поиск сейчас внутри `База знаний`. |

## Обработка базы знаний

| Зона | Назначение |
| --- | --- |
| `Загрузка` | Выбор файлов, отправка в Gateway, создание черновиков, очередь обработки, прогресс и текущий этап. |
| `Черновики` | Список черновиков, сверка и правка метаданных, raw JSON, классификация, preview, approve/reject/delete. |
| `Реестр` | Принятые документы, поиск, фильтры, preview, версии, история, ошибки, страницы, скачивание и удаление. |
| `Журналы` | События обработки, статусы, задачи и диагностика. |

Загрузка по URL удалена. Поддерживается только прямая файловая загрузка.

## Gateway/API-сценарии

Основной API-слой находится в `src/utils/http.ts`.

| UI-сценарий | Основные endpoints |
| --- | --- |
| Авторизация | `POST /auth/token`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/revoke` |
| Health | `GET /system/health` |
| Чат | `GET/POST /chat/sessions`, `GET/PUT/DELETE /chat/sessions/{id}`, `POST /chat/sessions/{id}/messages`, `GET /chat/sessions/{id}/messages/{message_id}` |
| Проекты чата | `GET/POST /chat/projects`, `PUT/DELETE /chat/projects/{id}` |
| Поиск по БЗ | `POST /text/search` |
| Черновики | `POST /drafts`, `GET /drafts`, `GET /drafts/{id}`, `GET /drafts/{id}/preview`, `PATCH /drafts/{id}/metadata`, `PATCH /drafts/{id}/decide`, `DELETE /drafts/{id}` |
| Task status | `GET /tasks/{task_id}/status`, `GET /drafts/{draft_id}/tasks` |
| Документы | `GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/status`, `history`, `errors`, `parameters`, `pages`, `file`, `versions`, `DELETE /documents/{id}` |
| Страницы | `GET /documents/{id}/pages/{page}/preview`, `GET /documents/{id}/pages/{page}/text` |
| Очередь | `GET /documents/queue` |
| Reprocess | `POST /documents/{id}/reprocess` |
| Registry documents | `GET /registry/documents`, `GET /registry/documents/{id}`, `GET /registry/documents/{id}/sections`, `PATCH /registry/documents/{id}` |
| Classifiers | `GET/POST /registry/classifiers`, tree, pending, accept/reject, validate, import, update/delete by code |
| Terminology | `GET/POST /registry/terminology`, normalize, import, update/delete by id |
| Registry meta | `GET /registry/stats`, `GET /registry/enums` |
| История | собирается из `GET /chat/sessions`, экспорт через `GET /chat/history/export` |
| QA/metrics | `GET /monitor/metrics` |
| Администрирование | `GET /admin/roles`, `GET /admin/users`, `GET /admin/audit`, `PATCH /admin/users/{id}` |
| Feedback | `POST /chat/feedback` |

## Логика данных и утилиты

| Файл | Назначение |
| --- | --- |
| `src/utils/http.ts` | Gateway-first API-слой, axios client, token refresh, mappers, demo/prod branching, controlled error states. |
| `src/utils/mockData.ts` | Demo-пользователи, demo-документы, demo-проекты, demo-чаты, demo-метрики. |
| `src/utils/access.ts` | Роли, labels, permissions, demo/prod доступность вкладок. |
| `src/utils/citations.ts` | Нормализация inline-citation markers и сопоставление источников ответа. |
| `src/utils/errors.ts` | Пользовательские сообщения для backend/API ошибок. |
| `src/utils/downloadPreview.ts` | Открытие и скачивание файлов/preview с учетом gateway/minio ссылок. |
| `src/store/uiStore.ts` | Zustand-состояние: режим, пользователь, роль, вкладка, тема, gateway session/project, auth snapshots. |

## Структура проекта

| Путь | Назначение |
| --- | --- |
| `src/main.tsx` | Точка входа React-приложения. |
| `src/App.tsx` | Главный контейнер: auth restore, темы, роли, доступные вкладки, layout и роутинг экранов. |
| `src/theme.tsx` | Тема MUI, цвета, типографика, светлый/темный режим. |
| `src/index.css` | Базовые CSS-стили, scrollbars, layout, переносы длинного текста. |
| `src/components/` | Экранные компоненты и диалоги. |
| `src/components/__tests__/` | Тесты component-level mappers. |
| `src/store/` | Zustand store и тесты store. |
| `src/utils/` | API, mappers, access, citations, errors, download helpers, demo data. |
| `src/utils/__tests__/` | Тесты access/citations/errors/http contracts. |
| `src/test/setup.ts` | Настройка Vitest/jsdom. |

## Конфигурация

| Файл | Назначение |
| --- | --- |
| `package.json` | Зависимости и npm scripts. |
| `vite.config.ts` | Vite, React, Tailwind plugin и alias. |
| `vitest.config.ts` | Конфигурация Vitest. |
| `Dockerfile` | Production-сборка UI и nginx. |
| `docker-compose.yml` | Локальный Docker-запуск frontend. |
| `nginx.conf` | SPA-раздача через nginx. |
| `.env.example` | Пример переменных окружения. |

Ключевые env-переменные:

```text
VITE_API_BASE_URL=http://127.0.0.1:8080/api/v1
VITE_GATEWAY_AUTO_LOGIN=false
VITE_GATEWAY_USERNAME=admin@example.com
VITE_GATEWAY_PASSWORD=Admin1234!
VITE_VIDEO_GUIDE_URL=/video/ai-assistant-pkb.mp4
```

`VITE_GATEWAY_AUTO_LOGIN=true` допустим только для локальной отладки. В продуктивной сборке пользователь должен входить через экран авторизации.

`VITE_VIDEO_GUIDE_URL` должен указывать на доступный браузеру видеофайл. Если видео недоступно, UI показывает явное состояние отсутствующей видеоинструкции.

## Тесты

Актуальные тестовые группы:

| Файл | Что проверяет |
| --- | --- |
| `src/utils/__tests__/access.test.ts` | Маппинг `available_tabs`, demo/prod доступность вкладок. |
| `src/utils/__tests__/citations.test.ts` | Inline-citation markers и номера видимых ссылок. |
| `src/utils/__tests__/errors.test.ts` | Пользовательские backend/API ошибки. |
| `src/utils/__tests__/httpContracts.test.ts` | Контракты Gateway, upload multipart, task status, chat session guard. |
| `src/store/__tests__/uiStore.test.ts` | Переключение demo/prod, сохранение темы, сессии и профиля. |
| `src/components/__tests__/draftMapper.test.ts` | Отображаемые имена черновиков и нормализация metadata. |

## Текущее состояние

1. UI готов для проверки в demo-режиме и с локальным/серверным Gateway.
2. Основные сценарии подключены к текущим Gateway-контрактам.
3. Поиск документов находится в `База знаний`.
4. Отдельная вкладка `Проверка` исключена до согласованного API-контракта.
5. Registry-редакторы доступны в администрировании при соответствующих правах.
6. В prod-режиме ошибки Gateway должны отображаться явно, без fallback на demo-данные.
7. Известные backend-блокеры фиксируются отдельно и не должны маскироваться frontend-логикой.

## Документация рядом

| Документ | Что внутри |
| --- | --- |
| `../README.md` | Обзор UI Final. |
| `../docs/first-run-ui-final.md` | Запуск UI без Gateway. |
| `../docs/first-run-ui-final-with-gateway.md` | Запуск UI вместе с Gateway. |
| `../docs/ui-final-gateway-docs-adaptation-plan-2026-06-19.md` | План адаптации под Gateway/Registry. |
| `gateway-backend-blockers.md` | Рабочий список backend-блокеров, если актуализирован в ветке. |
