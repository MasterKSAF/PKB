# TODO (выполнено)

## 1. Изолировать docker-зависимые тесты ✅
- [x] `test_live_api.py` → `live_server_check.py` (не собирается pytest по умолчанию)
- [x] Убран `pytest.skip` — тесты падают с ConnectError при недоступности сервера

## 2. Добавить запуск в recheck.bat ✅
- [x] Секция 8 в `service_checker/docker/recheck.bat` — запуск live тестов
- [x] LIVE_SERVER_URL по умолчанию `http://localhost:18085` (порт integration в Docker)
- [x] Можно переопределить через внешнюю `LIVE_SERVER_URL`

## 3. Обновить документацию ✅
- [x] `integration_service/readme.md` — уточнено про live_server_check.py и recheck.bat
- [x] `backend/guide.md` — зафиксировано решение об изоляции через переименование
