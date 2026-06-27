# Integration Service API

Сервис интеграции для PKB Develop. Предоставляет API для загрузки/хранения файлов, экспорта в Meridian и проверки статуса внешних систем.

---

## Структура проекта

```
integration_service/
├── api/v1/
│   ├── endpoints/
│   │   ├── common.py         # Health-check, базовые эндпоинты
│   │   ├── files.py           # Upload / download / delete файлов
│   │   ├── meridian.py         # Экспорт в Meridian
│   │   └── external.py        # Статус внешних систем
│   └── routes.py          # Сборка всех роутов
├── tests/
│   ├── conftest.py         # Фикстуры: БД SQLite in-memory, TestClient, директории
│   ├── test_main.py         # Тест корневого эндпоинта (/\)
│   ├── test_files.py        # Тесты файлового API (через TestClient)
│   ├── test_meridian.py      # Тесты экспорта в Meridian (через TestClient)
│   ├── test_external.py      # Тест статуса внешних систем (через TestClient)
│   └── live_server_check.py  # Docker-зависимые тесты против реального сервера (только через recheck.bat)
├── config.py           # Настройки (БД, директории хранения)
├── main.py             # Точка входа FastAPI
└── readme.md           # Этот файл
```

---

## Запуск

### Локальный сервер

```bash
cd integration_service
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8100
```

### Тесты

#### Локальные тесты (с моками)
Используют `TestClient` и in-memory SQLite. Не требуют внешних зависимостей.

```bash
cd integration_service
pytest tests/ -v --ignore=tests/test_live_api.py
```

#### Docker-зависимые тесты (против реального сервера)
Используют `httpx` и ходят на работающий экземпляр сервиса.
Запускаются только через `recheck.bat`, т.к. требуют Docker.

```bash
# через recheck.bat (сервер из Docker, порт 18085)
service_checker\docker\recheck.bat

# напрямую, если сервер уже запущен вручную
LIVE_SERVER_URL=http://localhost:8100 python -m pytest integration_service/tests/live_server_check.py -v

# против удалённого сервера
LIVE_SERVER_URL=http://195.70.195.203 python -m pytest integration_service/tests/live_server_check.py -v
```

---

## Тесты сервера

### Локальные тесты (`test_files.py`, `test_meridian.py`, `test_external.py`, `test_main.py`)

- **Фикстуры**: `TestClient(app)` + SQLite in-memory + временные директории
- **Скорость**: быстрые, без внешних вызовов
- **Назначение**: проверка логики API, обработки ошибок, граничных случаев

### Docker-зависимые тесты (`live_server_check.py`)

- **Механизм**: `httpx.Client()` напрямую к реальному серверу
- **Сценарии**:
  - `test_live_upload_and_lifecycle` — полный цикл файла: загрузка → info → скачивание → удаление → проверка
  - `test_live_meridian_export` — экспорт документа в Meridian
  - `test_live_external_status` — проверка статуса внешних систем
- **Целевой URL**:
  - По умолчанию: `http://localhost:8100`
  - Через переменную окружения `LIVE_SERVER_URL`: любой адрес (например `http://195.70.195.203`)
- **Предусловие**: работающий экземпляр Integration Service
- **Запуск**: только через `recheck.bat` (не собираются `pytest` по умолчанию, т.к. требуют Docker)
- **Файл переименован** в `live_server_check.py` — не подпадает под шаблон `test_*.py`, поэтому не подхватывается обычным `pytest`
