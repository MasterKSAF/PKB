# DoS — лимит на размер тела запроса (Gateway)

## Задача
Добавить `MaxBodySizeMiddleware` в gateway (main.py), проверяющую
`Content-Length` и возвращающую 413 при превышении лимита.

Лимиты:
- query-пути (/chat/, /text/) — ~66 KB (строгий, для сообщений чата)
- остальные пути — 100 MB (для документов)

## План
- [x] 1. `MAX_BODY_SIZE` (100 MB) + `MAX_BODY_SIZE_QUERY` (~66 KB) + `_QUERY_PATH_PREFIXES`
- [x] 2. Класс `MaxBodySizeMiddleware` с `_get_limit(path)`
- [x] 3. Регистрация middleware — самым внешним (после CORS)
- [x] 4. Тесты (8 шт.): query/не query, превышение/между/в пределах, без тела, без Content-Length
- [x] 5. Запуск тестов — 8 passed
- [x] 6. README — обновлён (MaxBodySize в таблице возможностей)
