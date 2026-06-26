# Смена портов: +10000 в тестах и docker-файлах

**Маппинг:** 8080→18080, 8081→18081, 8082→18082, 8083→18083, 8084→18084,
8085→18085, 8086→18086, 8087→18087, 8088→18088, 8090→18090, 8091→18091

**НЕ ТРОГАТЬ:** 19000, 19001, 15432, 16379, 18092, 5432, 6379, 80, 9000, 9001, 4317, 4318

## Выполнено

### Тесты (все порты +10000)
- [x] tests/conftest.py
- [x] tests/test_api_coverage_execute_endpoint.py
- [x] tests/test_api_coverage_test_service.py
- [x] tests/test_full_report.py
- [x] tests/test_integration_draft_upload.py
- [x] tests/test_md_parser.py
- [x] tests/test_no_restarts.py
- [x] tests/test_openapi_comparator.py
- [x] tests/test_pipeline_base.py
- [x] tests/test_pipeline_multi_document_cross_search.py
- [x] tests/test_pipeline_runner_run.py
- [x] tests/test_pipeline_runner_run_step.py
- [x] tests/test_service_contracts.py

### Docker (только внешние/хост-порты)
- [x] docker/docker-compose.yml — порты `18081:8081` и т.д. + env URL
- [x] docker/docker-compose-web.yml — порты `18081:8081` и т.д. + env URL
- [x] docker/docker-compose.spd.yml — порты `18081:8081` и т.д.
- [x] docker/create_env.py — SERVICE_URL с новыми портами
- [x] docker/wait_for_services.py — кортежи портов

### Документация (для прохождения md_parser тестов)
- [x] docs/api/*.md — заголовки сервисов, таблицы health, URL
- [x] docs/README.md, docs/architecture/*.md, docs/pipelines/*.md и др.

### Валидация
- [x] 238 тестов проходят, 3 integration падают из-за отсутствия Docker
