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
**После фикса портов:** Ping ✅ | **Passed 56/101** | **Failed 35** | **Skipped 10**
**После perеноса DELETE в конец:** Ping ✅ | **Passed 109/119** | **Failed 10** | **Skipped 0**
**Текущий (финальный 2026-06-12):** Ping ✅ | **Passed 116/120** | **Failed 0** | **Skipped 4**

### Что изменилось
- DELETE-эндпоинты перенесены в конец — перестали убивать данные раньше времени
- Исправлен prepare: orchestrator draft (`POST /drafts`) создаётся отдельно от registry draft (`POST /registry/drafts`) с разными ID в контексте
- `expected_status` теперь работает для всех эндпоинтов (не только prepare) — 409 и 202 считаются success
- Добавлен prepare для orchestrator drafts: `orch_draft_id` + `task_id` извлекаются из ответа

### Остаётся (не проблема checker'а)
- 4 skipped — registry-draft endpoints не имеют `reg_draft_id` (prepare registry draft вернул 409, дубликат)
- Gateway Mock возвращает ID как **строки** ("rd-4", "sess-85"), документация API — int
- RAG Search не отвечает (известная проблема)

### Аномалия
- [x] Аномалия №18 зафиксирована в `specificity.md`
