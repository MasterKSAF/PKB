# План исправлений: проверка Gateway в Docker через recheck.bat

## Выполнено

### Проблема 1: Неверные порты Gateway (8081→8080) и Orchestrator (8000→8081)
Неверные порты были разбросаны по 9 файлам.

**Исправлено:**
- [x] `docker/wait_for_services.py` — Gateway 8081→8080, Orchestrator 8000→8081
- [x] `docker/entrypoint.sh` — табличка портов
- [x] `services/orchestrator.py` — PORT = 8000 → 8081
- [x] `core/docker.py` — DOCKER_SUPERVISOR_SERVICES
- [x] `core/cli.py` — --gateway-url default
- [x] `pipelines/base.py` — _get_service_port
- [x] `tests/test_full_report.py` — MockCoverageResult
- [x] `description.md` — таблица портов
- [x] `README.Docker.md` — curl health port

### Проблема 2: Gateway auth credentials
Gateway Mock использует пароль `admin123`, а checker в auth-эндпоинтах использовал `Admin1234!`.

- [x] `services/gateway.py` — переопределён body для POST /auth/token на GATEWAY_CREDENTIALS

### Проблема 3: Trailing slash → 307 Redirect
Gateway Mock определяет маршруты без слеша (`/documents`), checker стучится со слешем (`/documents/`) → 307.

- [x] `api_coverage_test.py` — включён `follow_redirects=True` в httpx.AsyncClient

## Результаты проверки Gateway

**Было:** Ping ✅ | Passed 45/101 | Failed 34 | Skipped 22
**Стало:** Ping ✅ | **Passed 56/101** | **Failed 35** | **Skipped 10** (+11 passed, -12 skipped)

### Что изменилось
- AUTH: 5/6 → **6/6** ✅ (исправлены credentials)
- Skipped: 22 → **10** (prepare registry проходит, doc_id извлекается)
- Passed: 45 → **56** (за счёт prepare + registry endpoints)

### Остаётся (не проблема checker'а)
- Gateway Mock возвращает ID как **строки** ("rd-4", "sess-85"), документация API — int
- Gateway Mock не реализует часть registry endpoints (/api/v1/registry/...)
- RAG Search не отвечает (известная проблема)

### Аномалия
- [x] Аномалия №18 зафиксирована в `specificity.md`
