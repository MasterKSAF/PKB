# PKB UI Final Frontend

Актуальное React-приложение интерфейса `AI Assistant PKB`.

## Статус

| Параметр | Значение |
| --- | --- |
| Основная ветка | `develop` |
| Папка приложения | `UI-UX/UI Final/frontend` |
| Локальный порт | `3300` |
| Локальный Gateway | `http://127.0.0.1:8080/api/v1` |
| Стек | React, Vite, TypeScript, MUI, Zustand |
| Режимы | продуктивный через Gateway и demo-режим |

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

Проверка:

```powershell
npm run lint
npm run build
```

## Вход

Продуктивный режим работает через Gateway/Auth. Роль и права должны приходить из профиля пользователя.

Текущий auth-flow:

1. Вход выполняется через `POST /auth/token`.
2. Профиль, роль и permissions подтягиваются через `GET /auth/me`.
3. После обновления страницы UI восстанавливает сессию по сохраненным access/refresh token и не требует повторного логина, если сессия еще валидна.
4. При `401 Unauthorized` общий HTTP-слой вызывает `POST /auth/refresh`, обновляет access token и повторяет исходный запрос один раз.
5. Если refresh token истек или невалиден, UI очищает локальную сессию и возвращает пользователя на экран входа.

Актуальная dev/server-сборка обычно использует:

| Роль | Логин | Пароль |
| --- | --- | --- |
| Системный администратор | `admin@example.com` | `Admin1234!` |

Demo-режим использует локальные профили:

| Роль | Логин | Пароль | Назначение |
| --- | --- | --- | --- |
| Пользователь | `a.morozov` | `demo` | Чат, база знаний, история. |
| Администратор знаний | `o.volkova` | `demo` | База знаний, обработка документов, QA, НСИ. |
| Системный администратор | `d.smirnov` | `demo` | Все вкладки, пользователи, права, системные разделы. |

## Основные экраны

| Экран | Что делает |
| --- | --- |
| `Вход` | Логин/пароль, продуктивный или demo-режим. |
| `Чат` | Проекты, дерево чатов, вопросы, ответы, источники, longpoll, preview, поиск по текущему чату, feedback. |
| `База знаний` | Разделы базы знаний, провал в раздел, документы раздела, поиск по базе или разделу, preview. |
| `Обработка базы знаний` | Вложенные зоны: загрузка, черновики, реестр документов, журналы. |
| `История` | Фильтры, поиск по диалогам, раскрытие чата, продолжение диалога, экспорт. |
| `QA` | Метрики, журнал проверки, оценка ответов. |
| `Администрирование` | Пользователи, роли, права, audit, классификаторы, терминология, неизвестные коды. |

## Обработка базы знаний

Текущая структура:

| Зона | Назначение |
| --- | --- |
| `Загрузка` | Выбор одного или нескольких файлов, создание черновиков, очередь обработки. |
| `Черновики` | Список черновиков, сверка и правка метаданных, raw JSON, классификация, preview, approve/reject/delete. |
| `Реестр` | Принятые документы, поиск, предпросмотр справа, срок действия, меню действий. |
| `Журналы` | События обработки, статусы, задачи и диагностическая информация. |

Загрузка по URL удалена. Поддерживается только прямая файловая загрузка.

## Текущая логика данных

| Файл | Назначение |
| --- | --- |
| `src/utils/http.ts` | Gateway-first HTTP-слой, авторизация, refresh token, восстановление сессии, API-вызовы и controlled fallback/error states. |
| `src/utils/mockData.ts` | Demo-данные для локального режима. |
| `src/store/uiStore.ts` | Zustand-состояние UI: режим, пользователь, вкладки, роли, состояние Gateway. |
| `src/utils/access.ts` | Роли, permissions и доступность вкладок. |

В продуктивном режиме UI не должен молча подменять ответы Gateway demo-данными. Если Gateway не отдает нужный контракт, показываем понятное empty/error-состояние.

## Основные Gateway/API-сценарии

| UI-сценарий | Основные endpoints |
| --- | --- |
| Авторизация | `POST /auth/token`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/revoke` |
| Чат | `GET/POST /chat/sessions`, `POST /chat/sessions/{id}/messages`, longpoll по message id |
| История | `GET /chat/history`, экспорт истории и продолжение диалога |
| Поиск по базе знаний | `POST /text/search`, Registry/Document endpoints |
| Черновики | `POST /drafts`, `GET /drafts`, `GET /drafts/{id}`, preview/status/decide/delete |
| Документы | `GET /documents`, `GET /documents/{id}`, pages/preview/file/status |
| Реестр | `GET /registry/documents`, classifiers, terminology, pending codes |
| Администрирование | `GET /admin/users`, `GET /admin/roles`, `GET /admin/audit` |
| Мониторинг | `GET /monitor/health`, `GET /monitor/metrics`, `/tasks/*` для admin-сценариев |

Подробные расхождения и backend-блокеры ведутся в рабочих документах рядом с UI Final и публикуются после согласования.

## Структура проекта

| Путь | Назначение |
| --- | --- |
| `src/main.tsx` | Точка входа React-приложения. |
| `src/App.tsx` | Главный контейнер: вход, режимы, роли, навигация, рабочая область. |
| `src/theme.tsx` | Тема MUI, цвета, типографика, светлый/темный режим. |
| `src/index.css` | Базовые CSS-стили, scrollbars, layout и визуальные правки. |
| `src/components/LoginScreen.tsx` | Экран входа. |
| `src/components/ModeSwitcher.tsx` | Левая навигация, вложенные пункты, проекты/чаты, режимы. |
| `src/components/Chat.tsx` | Чат инженера и preview источников. |
| `src/components/KnowledgeBase.tsx` | База знаний, разделы, документы, поиск и preview. |
| `src/components/KnowledgeProcessing.tsx` | Загрузка, черновики, реестр и журналы обработки. |
| `src/components/DocumentRegistryPanel.tsx` | Панель реестра документов и preview. |
| `src/components/History.tsx` | История диалогов. |
| `src/components/Monitor.tsx` | QA и метрики. |
| `src/components/AdminPanel.tsx` | Администрирование. |
| `src/components/RegistryEditors.tsx` | Классификаторы, терминология, неизвестные коды. |
| `src/components/SourcePreviewDialog.tsx` | Предпросмотр источников и документов. |
| `src/components/Feedback.tsx` | Оценка ответа ассистента. |
| `src/components/VideoGuideDialog.tsx` | Видеоинструкция. |

## Конфигурация

| Файл | Назначение |
| --- | --- |
| `package.json` | Зависимости и команды. |
| `vite.config.ts` | Vite, React, Tailwind и alias. |
| `Dockerfile` | Production-сборка UI и nginx. |
| `docker-compose.yml` | Локальный Docker-запуск. |
| `nginx.conf` | SPA-раздача через nginx. |
| `.env.example` | Пример переменных окружения. |

Ключевые env-переменные:

```text
VITE_API_BASE_URL=http://127.0.0.1:8080/api/v1
VITE_GATEWAY_AUTO_LOGIN=false
VITE_GATEWAY_USERNAME=admin@example.com
VITE_GATEWAY_PASSWORD=Admin1234!
```

`VITE_GATEWAY_AUTO_LOGIN=true` допустим только для локальной отладки. В продуктивной сборке вход должен выполняться пользователем через экран авторизации.

## Документация рядом

| Документ | Что внутри |
| --- | --- |
| `../README.md` | Общий README папки UI Final. |
| `../docs/first-run-ui-final.md` | Запуск UI без Gateway. |
| `../docs/first-run-ui-final-with-gateway.md` | Запуск UI вместе с Gateway. |
| `../docs/ui-final-gateway-docs-adaptation-plan-2026-06-19.md` | План адаптации под новую документацию Gateway/Registry. |
| `gateway-backend-blockers.md` | Короткий рабочий список стоперов рядом с frontend. |

## Текущее состояние

1. UI готов для демонстрации без backend и для проверки с локальным Gateway.
2. Ключевые сценарии подключены к Gateway-контрактам в текущем объеме.
3. Registry-редакторы классификаторов, терминологии и неизвестных кодов добавлены в администрирование.
4. Обработка базы знаний разделена на загрузку, черновики, реестр и журналы.
5. Авторизация в продуктивном режиме поддерживает refresh token и восстановление после F5/reload.
6. Открытые backend-блокеры зафиксированы отдельно.
7. Проверки: `npm run lint`, `npm run build`.
