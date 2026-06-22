# TODO: Удаление rag_builder_spk + единый источник портов + spk→spd ✅

## 1. Удалить rag_builder_spk
- [x] 1.1 `services/rag_builder_spk.py` — удалён
- [x] 1.2 `services/__init__.py` — SERVICE_KEYS, MODE_PORTS, SERVICE_DEPENDENCIES, SERVICE_REGISTRY, импорт
- [x] 1.3 `core/config.py` — SERVICE_DEFS, SERVICE_DISPLAY_NAMES
- [x] 1.4 `core/api_coverage_test.py` — SERVICES_WITH_REAL, KNOWN_NEW_ENDPOINTS, pre-prepare
- [x] 1.5 `core/cli.py` — spk→spd (флаг, переменные, суффикс)
- [x] 1.6 `specificity.md` — запись #49 переписана
- [x] 1.7 `readme.md` — структура, таблица статусов, SPD описание
- [x] 1.8 `core/docker.py` — err_files добавлен rag_builder_spk.err

## 2. Pipeline: единый источник портов (MODE_PORTS)
- [x] 2.1 `pipelines/base.py` — `run_step()`: приоритет `_get_service_port(step.service)` над `step.port`
- [x] 2.2 Все pipeline шаги автоматически используют MODE_PORTS

## 3. Rename spk→spd
- [x] 3.1 Файлы: `recheck_spk.bat`→`recheck_spd.bat`, `docker-compose.spk.yml`→`docker-compose.spd.yml`, `supervisord.spk.conf`→`supervisord.spd.conf`, `entrypoint.spk.sh`→`entrypoint.spd.sh`
- [x] 3.2 `recheck_spd.bat` — содержимое обновлено (флаги, имена файлов, сообщения)
- [x] 3.3 `docker-compose.spd.yml` — ссылки на .spd файлы, комментарии
- [x] 3.4 `entrypoint.spd.sh` — заголовок
- [x] 3.5 `core/cli.py` — флаг `--spd`, переменная `spd`, суффикс `_spd`, все log-сообщения
- [x] 3.6 `core/docker.py` — комментарии
- [x] 3.7 `core/api_coverage_test.py` — комментарий
- [x] 3.8 `pipelines/base.py` — комментарии
- [x] 3.9 `guide.md`, `readme.md`, `specificity.md` — все упоминания spk→spd
