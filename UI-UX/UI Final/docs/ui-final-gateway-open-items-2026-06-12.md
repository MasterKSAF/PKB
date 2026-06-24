# UI Final / Gateway: что осталось сделать и уточнить

Дата проверки: 12.06.2026

UI-ветка: `develop`

Свежий Gateway для проверки: `origin/develop`, commit `fe9f0b3` / после fetch `origin/develop` обновлен до актуального состояния репозитория.

Локальные порты проверки:

- UI Final: `http://127.0.0.1:3300`
- Gateway: `http://127.0.0.1:8081/api/v1`

## Что уже закрыто на стороне UI

1. UI работает в двух режимах: `Продуктивный` и `Демо`.
2. В продуктивном режиме вход идет через `POST /auth/token`, профиль подтягивается через `GET /auth/me`.
3. Чат отправляет сообщения через `POST /chat/sessions/{session_id}/messages`.
4. Longpoll ответа подключен через `GET /chat/sessions/{session_id}/messages/{message_id}?longpoll=15`.
5. FSM-статусы чата приведены к документированным статусам: `pending`, `enriching`, `searching`, `generating`, `enriching_citations`, `answered`, `failed`; статус mock Gateway `completed` маппится в `answered`.
6. Дерево проектов чата переведено на Gateway-first слой `/chat/projects`.
7. Создание, переименование и удаление проекта в UI вызывают `POST /chat/projects`, `PUT /chat/projects/{project_id}`, `DELETE /chat/projects/{project_id}`.
8. Создание новой chat-сессии из проекта отправляет `project_id` в `POST /chat/sessions`.
9. База знаний переведена на Gateway-first слой Registry: `GET /registry/documents`, `GET /registry/documents/{doc_id}`, `GET /registry/documents/{doc_id}/sections`.
10. Предпросмотр документа в базе знаний использует секции Registry, если Gateway их отдает.
11. Поиск по базе знаний остался в самой вкладке `База знаний`; можно искать везде или внутри выбранного раздела.
12. Обработка базы знаний использует внешний поток `/drafts/*`: upload, preview, preview status, approve/reject, delete.
13. История поддерживает `GET /chat/history/export`; если Gateway возвращает нерабочую ссылку на файл, UI делает локальный CSV fallback из текущих строк.
14. Роли для администрирования подтягиваются через `GET /admin/roles` с fallback на demo-роли.
15. Классификаторы в UI уже берутся только из `GET /registry/classifiers/tree`; старый fallback на `/classifiers/tree` убран.

## Проверено

1. `npm run lint` — успешно.
2. `npm run build` — успешно, только стандартное предупреждение Vite о крупном chunk.
3. Gateway health на `8081` — `status: ok`, `endpoints_total: 114`.
4. Продуктивный вход в UI через `admin@example.com / admin123` — успешно.
5. Статус UI после входа — `Система онлайн`.
6. Вкладка `База знаний` открывается и получает дерево классификаторов из Gateway.
7. Провал в раздел базы знаний работает; если документов в разделе нет, показывается empty state без падения UI.
8. Дерево чатов показывает `Рабочие диалоги` как fallback, если `/chat/projects` возвращает пустой список.

## Что осталось на стороне UI

1. После перехода Gateway на `categories` вместо `group` обновить навигацию по разделам и фильтры поиска в базе знаний.
2. Проверить сценарий многосвязных категорий: один документ может попадать в несколько разделов.
3. После появления новой схемы убрать старые упоминания `group` из UI-документации.

## Блокеры для UI из-за будущей смены схемы разделов

| # | Область | Что меняется | Почему это важно | Что нужно от backend |
| --- | --- | --- | --- | --- |
| 1 | Схема разделов | `group` остается текущим полем связи, но в следующей версии Gateway его заменят `categories` с множественными связями. | UI уже использует `group` для текущего контракта; при переходе на `categories` потребуется безопасная миграция фильтров и навигации. | Подтвердить схему `categories`, формат множественных связей и период совместимости с `group`. |

## Вопросы к backend по Gateway

1. Когда в Gateway придет новая схема `categories`?
   - Нужен ли переходный период, где `group` остается алиасом.
   - Нужно ли UI поддерживать одновременно `group` и `categories`.

2. Как будет выглядеть многосвязность категорий?
   - Один документ может входить в несколько разделов.
   - Нужен ли новый формат ответа для дерева разделов и фильтра поиска внутри раздела.

## Ветки-кандидаты на удаление

Ничего не удалено. Ниже только рекомендации.

### Можно удалить после подтверждения

Эти ветки созданы нами, уже являются предками `origin/develop` и текущей рабочей ветки:

| Ветка | Где | Почему можно удалить |
| --- | --- | --- |
| `codex-ui-final-docs-readme` | local + `origin/codex-ui-final-docs-readme` | Документационные правки уже вошли в `develop` и текущую UI-ветку. |
| `codex/ui-final-docs-readme` | local + `origin/codex/ui-final-docs-readme` | Дубликат предыдущей docs/readme-ветки, тоже уже вошел в `develop` и текущую UI-ветку. |

Команды после подтверждения:

```powershell
git branch -d codex-ui-final-docs-readme
git branch -d codex/ui-final-docs-readme
git push origin --delete codex-ui-final-docs-readme
git push origin --delete codex/ui-final-docs-readme
```

### Не удалять без отдельной проверки

Эти ветки старые или промежуточные, но не являются предками `origin/develop`, поэтому перед удалением надо проверить, что нужные memo/docs/изменения перенесены:

| Ветка | Где | Причина осторожности |
| --- | --- | --- |
| `feature/ui-final-gateway-current` | local + `origin/feature/ui-final-gateway-current` | Старая основная UI/Gateway-ветка, но не слита в `develop` полностью по git-графу. |
| `feature/ui-final-gateway-spike` | local only | Старый эксперимент Gateway wiring; не предок `develop`; сейчас checkout в worktree `C:/Users/Misha/Documents/GitHub/PKB_neuroassistant`. |
| `feature/ui-import-frontend-v1` | local + `origin/feature/ui-import-frontend-v1` | Содержит memo/материалы `frontend-v1`; не предок `develop`. |
| `ui-v1-meeting-2026-06-09` | local, upstream `origin/feature/ui-import-frontend-v1` | Локальная ветка с memo встречи 09.06; не предок `develop`; сейчас checkout в worktree `C:/Users/Misha/Documents/GitHub/PKB_neuroassistant_ui_v1_memo_0906`. |

## Рекомендация по следующему шагу

1. Передать backend список вопросов выше.
2. Не менять UI-контракты feedback/export/projects до ответа backend, чтобы не сломать уже работающую связку.
3. После ответа backend закрыть оставшиеся пункты небольшими UI-only правками.
4. После проверки — отдельный commit только по UI/docs, без захвата грязных изменений `backend/gateway_service`.
