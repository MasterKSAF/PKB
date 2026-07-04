# Первый запуск UI Final вместе с Gateway

Эта инструкция нужна, чтобы другой участник команды мог забрать актуальный `Gateway`, забрать актуальный `UI Final`, развернуть их локально и проверить стыковку.

## Что получится после запуска

- Gateway работает локально на `http://127.0.0.1:8080/api/v1`.
- UI Final работает локально на `http://127.0.0.1:3300`.
- В UI можно выбрать режим `Продуктивный`, войти через Gateway и проверить реальные запросы к Gateway.
- Основной переходник UI к Gateway находится в `UI-UX/UI Final/frontend/src/utils/http.ts`.

## Что установить

- Git for Windows.
- Node.js LTS.
- Python 3.13+.
- Docker Desktop не обязателен для этой проверки, потому что Gateway и UI удобнее запускать в dev-режиме.

## Важно про ветки

Gateway и UI лежат в одном GitHub-репозитории. Основная ветка для локальной проверки и серверной сборки — `develop`.

Если нужно проверить еще не влитые UI-правки, используйте отдельную рабочую ветку только временно. После проверки полезные изменения должны попадать в `develop`.

## 1. Забрать и запустить Gateway

Открыть первый терминал.

```powershell
cd C:\Users\Misha\Documents\GitHub
git clone -b develop https://github.com/NeuronsUII/PKB_neuroassistant.git PKB_gateway_current
cd PKB_gateway_current
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\gateway_service\requirements.txt
pip install -r backend\gateway_service\mocks\requirements.txt
python backend\gateway_service\mocks\gateway.py
```

Проверка Gateway:

```text
http://127.0.0.1:8080/docs
```

Если Swagger открылся, Gateway поднят.

## 2. Забрать и запустить UI Final

Открыть второй терминал.

```powershell
cd C:\Users\Misha\Documents\GitHub
git clone -b develop https://github.com/NeuronsUII/PKB_neuroassistant.git PKB_ui_final_develop
cd "PKB_ui_final_develop\UI-UX\UI Final\frontend"
npm ci
npm run dev -- --host 127.0.0.1 --port 3300 --strictPort
```

Открыть UI:

```text
http://127.0.0.1:3300
```

## 3. Как проверить стыковку

1. На экране входа выбрать `Продуктивный`.
2. Войти под Gateway пользователем `admin@example.com / Admin1234!`, если backend/Auth не выдал другие учетные данные.
3. После авторизации статус должен перейти в `Система онлайн`.
4. Обновить страницу через F5: UI должен остаться внутри приложения и не должен требовать повторный логин, если access/refresh token еще валидны.
5. Во вкладке `Чат` отправить вопрос.
6. Проверить, что появился ответ ассистента с источником.
7. Открыть дерево `Чат -> Мои проекты`: должны появиться проекты Gateway или fallback-группа `Рабочие диалоги`.
8. Во вкладке `База знаний` проверить поиск, разделы, провал в раздел и предпросмотр документа.
9. Во вкладке `Обработка базы знаний` проверить upload/draft/preview/approve/reject/delete, если Gateway и права пользователя позволяют.
10. Во вкладке `История` проверить, что видны chat-сессии Gateway.
11. Во вкладке `QA` проверить метрики.
12. Во вкладке `Администрирование` проверить пользователей, роли и audit.

## Что уже подключено

- Авторизация и профиль: `POST /auth/token`, `GET /auth/me`, `POST /auth/refresh`, `POST /auth/revoke`.
- Проекты чата: `GET /chat/projects`, `POST /chat/projects`, `PUT /chat/projects/{project_id}`, `DELETE /chat/projects/{project_id}`.
- Чат-сессии: `GET /chat/sessions`, `POST /chat/sessions`, `GET /chat/sessions/{id}`, `PUT /chat/sessions/{id}`, `DELETE /chat/sessions/{id}`.
- Сообщения чата: `POST /chat/sessions/{id}/messages`.
- Longpoll ответа: `GET /chat/sessions/{id}/messages/{message_id}?longpoll=15`.
- Оценка ответа: `POST /chat/feedback`.
- Поиск: `POST /text/search`.
- Черновики: `POST /drafts`, `GET /drafts`, `GET /drafts/{id}`, `GET /drafts/{id}/preview`, `POST /drafts/{id}/preview`, `GET /drafts/{id}/preview/status`, `PATCH /drafts/{id}/decide`, `DELETE /drafts/{id}`.
- Документы: `GET /documents`, `GET /documents/queue`, `POST /documents/{id}/reprocess`.
- Источники: `GET /documents/{id}/file`, `GET /documents/{id}/pages/{page}/preview`, `GET /documents/{id}/pages/{page}/content_md`.
- Registry: `GET /registry/documents`, `GET /registry/documents/{doc_id}`, `GET /registry/documents/{doc_id}/sections`, `GET /registry/classifiers/tree`.
- История: `GET /chat/sessions`, fallback `GET /chat/history`.
- QA: `GET /monitor/metrics`.
- Администрирование: `GET /admin/users`, `GET /admin/roles`, `PATCH /admin/users/{id}`, `GET /admin/audit`.

## Что пока не подключено полностью

- Сценарий `Проверка`: исключен из UI Final. В Gateway нет отдельного контракта сверки проектных параметров с требованиями НСИ, интеграция раздела сейчас не планируется.
- `/tasks/*`: если Gateway возвращает ошибку доступа к `orchestrator:8081`, нужно чинить backend/deploy-конфигурацию Gateway и Orchestrator.
- `POST /chat/sessions`: UI отправляет `project_id`, но Gateway может не сохранять связь сессии с проектом в некоторых сборках.
- `POST /chat/feedback`: нужно подтвердить финальный формат `rating`, потому что документация и mock Gateway расходятся.
- `GET /chat/history/export`: Gateway возвращает `url`, но файл по этому URL в mock может отдавать `404`; UI имеет локальный CSV fallback.
- Registry/Classifiers mock-данные нужно синхронизировать, чтобы документы попадали в соответствующие разделы.
- Полный список открытых вопросов: `docs/ui-final-gateway-open-items-2026-06-12.md`.

## Как проверить сборку UI

```powershell
cd "C:\Users\Misha\Documents\GitHub\PKB_ui_final_develop\UI-UX\UI Final\frontend"
npm run lint
npm run build
```

## Как проверить Gateway тестами

В папке Gateway:

```powershell
cd C:\Users\Misha\Documents\GitHub\PKB_gateway_current
.\.venv\Scripts\Activate.ps1
python -m pytest backend\gateway_service\mocks\tests -q
```

Ожидаемый текущий результат: тесты проходят, возможны предупреждения по дублирующимся `system/health` в OpenAPI.
