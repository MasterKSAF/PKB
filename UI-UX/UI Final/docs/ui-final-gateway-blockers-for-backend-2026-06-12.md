# UI Final / Gateway: стоперы для backend

Дата проверки: 13.06.2026  
Ветка: `develop`  
Gateway commit: `34ae411`  
UI режим: продуктивный, Gateway `http://127.0.0.1:8081/api/v1`

Ниже только пункты, где Gateway не реализует документированный контракт или возвращает данные в формате, который блокирует корректную работу UI. UI-only ошибки сюда не включены.

| # | Стопер | Факт на Gateway | Почему блокирует UI | Возможное решение |
| --- | --- | --- | --- | --- |
| 1 | `POST /registry/classifiers/import` не принимает документированный CSV/XLSX import | Документация: `multipart/form-data` с `file`, `classifier_system`, `mapping`. Фактически handler читает содержимое файла как JSON. CSV возвращает `500 Internal Server Error`. | Нельзя реализовать загрузку классификаторов из UI по документации. | Реализовать парсинг `.csv/.xlsx` и применение `mapping`; при ошибках возвращать `400 VALIDATION_ERROR` с деталями строк, не `500`. |
| 2 | `POST /registry/terminology/import` не принимает документированный CSV/XLSX import | Документация: `multipart/form-data` аналогично классификаторам. Фактически CSV может падать `500`; устойчивого CSV/XLSX-контракта нет. | Нельзя реализовать импорт терминологии из UI. | Реализовать единый import parser для terminology: `.csv/.xlsx`, `mapping`, построчные ошибки, ответ `{ data: { inserted, updated, errors } }`. |
| 3 | `POST /registry/classifiers/validate` не читает документированное тело | Документация требует `{ "classification": { "mks_oks_code": "47.020" } }`. Gateway читает только top-level `mks_oks_code`/`code`; документированный payload возвращает `NOT_FOUND`. | UI по документации получает неверный результат валидации кода. | Поддержать документированный wrapper `classification.*`. Для обратной совместимости можно временно оставить top-level поля. |
| 4 | `POST /registry/classifiers/pending/{id}/accept` игнорирует тело запроса | Документация: принимает `parent_code`, `full_name`, `admin_comment`, возвращает `status: "mapped"`. Фактически body игнорируется, создается узел из suggested fields, статус `accepted`. | Админ не может вручную задать название, родителя и комментарий при принятии неизвестного кода. | Принять и валидировать body; сохранять `admin_comment`; создавать/обновлять классификатор с `parent_code` и `full_name`; вернуть `pending_id`, `classifier_system`, `code`, `status: "mapped"`, `registry_created`. |
| 5 | `POST /registry/classifiers/pending/{id}/reject` игнорирует `admin_comment` | Документация: body содержит `admin_comment`. Фактически комментарий не используется. | UI может показать поле причины отклонения, но решение не сохраняется. | Принимать body, сохранять `admin_comment`, возвращать `pending_id` и `status: "rejected"`. |
| 6 | `GET /registry/classifiers/pending` не фильтрует по `system` | Документация описывает query `system`. Handler принимает только `status`, `page`, `page_size`. | UI не может корректно фильтровать неизвестные коды по `MKS`, `OKSTU`, `UDC`, `EXTERNAL`. | Добавить query `system` и фильтр по `pending.system`; оставить `status`, `page`, `page_size`. |
| 7 | `registry/terminology.scope` расходится с документацией | Документация и DB-модель: `scope: string[]`. Gateway Pydantic model: `scope: Optional[str]`. Payload со списком дает `422`. | UI не может редактировать несколько областей применения термина по документации. | Привести Gateway к `scope: list[str]`; на переходный период принимать и строку, и массив, нормализуя к массиву в ответе. |
| 8 | `GET /registry/terminology/normalize` возвращает неверный `term_type` для неизвестного термина | Документация: если термин не найден, вернуть `term_type: "unknown"`. Gateway возвращает `term_type: "preferred"`. | UI не может отличить найденный термин от неизвестного и правильно подсветить результат нормализации. | Для not found возвращать `term_type: "unknown"` и исходный `raw_term`; найденные термины возвращать из справочника. |
| 9 | `/api/v1/health` требует авторизацию | Без токена `GET /api/v1/health` возвращает `401`; с токеном `200`. | Если UI должен показывать состояние Gateway до логина или при истекшем токене, health-check не работает как публичный индикатор доступности. | Либо сделать health публичным, либо явно зафиксировать в документации, что health закрытый, и дать отдельный public endpoint типа `/api/v1/ping`. |

## Отдельно: что не является backend-стопером

Эти проблемы видны в UI, но прямые API-вызовы Gateway отвечают корректно, поэтому исправлять нужно на стороне UI:

| # | UI-проблема | Факт |
| --- | --- | --- |
| 1 | В админке отображается `Система офлайн` и ошибка аудита | Прямой `GET /admin/audit` возвращает `200`. |
| 2 | UI показывает `Неизвестные коды (0)` | Прямой `GET /registry/classifiers/pending` возвращает данные. |
| 3 | UI показывает `Терминология (0)` и вкладка не переключается | Прямой `GET /registry/terminology` возвращает данные. |
