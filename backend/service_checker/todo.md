# TODO: Сменить порты инфраструктурных служб на нестандартные

## Проблема
Стандартные порты PostgreSQL (5432), Redis (6379), MinIO (9000/9001), TEI (8092) 
конфликтуют с другими проектами на машине.

## План

### Блок 1: docker-compose.yml — host ports
- [x] PostgreSQL: `5432` → `15432`
- [x] Redis: `6379` → `16379`
- [x] MinIO: `9000/9001` → `19000/19001`
- [x] TEI: `8092` → `18092`

### Блок 2: core/docker.py
- [x] TEI health check port: `8092` → `18092`

### Блок 3: pipelines/*.py
- [x] `pipelines/base.py`: minio 9000→19000, tei 8092→18092
- [x] `pipelines/document_processing.py`: MINIO_PORT 9000→19000
- [x] `pipelines/multi_document_cross_search.py`: MINIO_PORT 9000→19000

### Блок 4: core/api_coverage_test.py
- [x] MinIO upload URL: `127.0.0.1:9000` → `127.0.0.1:19000`

### Блок 5: services/*.py
- [x] `services/__init__.py`: tei 8092→18092
- [x] `services/tei.py`: PORT 8092→18092

### Блок 6: Проверка
- [x] Пересобрать и перезапустить Docker
- [x] Запустить coverage test — 234/243, всё зелёное
