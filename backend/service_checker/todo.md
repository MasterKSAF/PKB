# Рефакторинг: service_checker.py разбит на модули ✅

## Что сделано
`service_checker.py` (2579 строк) разбит на 7 модулей в `core/`:

```
service_checker/
├── __init__.py                  # метка пакета
├── __main__.py                  # entry point (python -m service_checker)
├── service_checker.py           # entry point (25 строк, python service_checker.py)
├── core/
│   ├── __init__.py
│   ├── config.py                # константы, SERVICE_DEFS, пути
│   ├── models.py                # ServiceProcess, Report, ApiCallLog, md_to_html
│   ├── utils.py                 # log_*, log_header, find_available_python
│   ├── services.py              # start/stop/wait/check, WebEmulator, _collect_logs
│   ├── reports.py               # _generate_full_report (сводная таблица)
│   ├── docker.py                # _check_docker, _docker_action, health, coverage, pipeline
│   └── cli.py                   # parse_args, cmd_*, main()
├── pipeline_test.py
├── api_coverage_test.py
├── pipelines/
└── tests/
```

## Проверка
- **84/84 тестов** пройдено
- `python service_checker/service_checker.py` — работает
- `python -m service_checker` — работает (из `backend/`)
- `recheck.bat` — обновлён на `python -m service_checker`
- Docker full-report — создаёт все отчёты (coverage + pipeline + full_report + errors)
