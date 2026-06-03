# Первый запуск UI Final вместе с Gateway

Эта инструкция нужна, чтобы другой участник команды мог забрать актуальный `Gateway`, забрать актуальный `UI Final`, развернуть их локально и проверить стыковку.

## Что получится после запуска

- Gateway работает локально на `http://127.0.0.1:8081/api/v1`.
- UI Final работает локально на `http://127.0.0.1:3310`.
- В UI можно нажать `Демо-режим`, переключиться в `Система онлайн` и проверить реальные запросы к Gateway.
- Основной переходник UI к Gateway находится в `UI-UX/UI Final/frontend/src/utils/http.ts`.

## Что установить

- Git for Windows.
- Node.js LTS.
- Python 3.13+.
- Docker Desktop не обязателен для этой проверки, потому что Gateway и UI удобнее запускать в dev-режиме.

## Важно про ветки

Gateway и UI лежат в одном GitHub-репозитории, но в разных ветках. Поэтому для одновременного запуска проще клонировать репозиторий в две разные папки:

- `PKB_gateway_current` — ветка `develop_gateway`;
- `PKB_ui_final_gateway_current` — ветка `feature/ui-final-gateway-current`.

## 1. Забрать и запустить Gateway

Открыть первый терминал.

```powershell
cd C:\Users\Misha\Documents\GitHub
git clone -b develop_gateway https://github.com/NeuronsUII/PKB_neuroassistant.git PKB_gateway_current
cd PKB_gateway_current
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\gateway_service\requirements.txt
pip install -r backend\gateway_service\mocks\requirements.txt
python backend\gateway_service\mocks\gateway.py
```

Проверка Gateway:

```text
http://127.0.0.1:8081/docs
```

Если Swagger открылся, Gateway поднят.

## 2. Забрать и запустить UI Final

Открыть второй терминал.

```powershell
cd C:\Users\Misha\Documents\GitHub
git clone -b feature/ui-final-gateway-current https://github.com/NeuronsUII/PKB_neuroassistant.git PKB_ui_final_gateway_current
cd "PKB_ui_final_gateway_current\UI-UX\UI Final\frontend"
npm ci
npm run dev -- --host 127.0.0.1 --port 3310 --strictPort
```

Открыть UI:

```text
http://127.0.0.1:3310
```

## 3. Как проверить стыковку

1. Войти в UI через карточку `Системный администратор`.
2. В правом верхнем углу нажать `Демо-режим`.
3. После первого реального запроса статус должен перейти в `Система онлайн`.
4. Во вкладке `Чат` отправить вопрос.
5. Проверить, что появился ответ ассистента с источником.
6. Открыть дерево `Чат -> Мои проекты`: должны появиться `Диалоги Gateway` и chat-сессии Gateway.
7. Во вкладке `Поиск` выполнить поиск, например `wall thickness`.
8. Во вкладке `База знаний` проверить документы и разделы.
9. Во вкладке `История` проверить, что видны chat-сессии Gateway.
10. Во вкладке `QA` проверить метрики.
11. Во вкладке `Администрирование` проверить пользователей и роли.

## Что уже подключено

- Авторизация и профиль: `POST /auth/token`, `GET /auth/me`.
- Чат-сессии: `GET /chat/sessions`, `POST /chat/sessions`, `GET /chat/sessions/{id}`, `PUT /chat/sessions/{id}`, `DELETE /chat/sessions/{id}`.
- Сообщения чата: `POST /chat/sessions/{id}/messages`.
- Оценка ответа: `POST /chat/feedback`.
- Поиск: `POST /documents/search`.
- Документы: `GET /documents`, `POST /documents`, `GET /documents/queue`, `POST /documents/{id}/reprocess`.
- Источники: `GET /documents/{id}/file`, `GET /documents/{id}/pages/{page}/preview`, `GET /documents/{id}/pages/{page}/text`.
- История: `GET /chat/sessions`, fallback `GET /chat/history`.
- QA: `GET /monitor/metrics`.
- Администрирование: `GET /admin/users`, `PATCH /admin/users/{id}`, `GET /admin/audit`.

## Что пока не подключено полностью

- Вкладка `Проверка`: скрыта из основной навигации и доступна только из `Администрирования` как неиспользуемый сценарий. В Gateway нет отдельного контракта сверки проектных параметров с требованиями НСИ, интеграция раздела сейчас не планируется.
- `Мои проекты`: Gateway отдает chat-сессии, но не отдельную сущность проекта, поэтому проекты пока остаются UI-группировкой. Создание, переименование и удаление проектов не сохраняются в Gateway.
- Расширенная админка справочников: часть API уже есть, но UI пока использует только базовый минимум.

## Как проверить сборку UI

```powershell
cd "C:\Users\Misha\Documents\GitHub\PKB_ui_final_gateway_current\UI-UX\UI Final\frontend"
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
