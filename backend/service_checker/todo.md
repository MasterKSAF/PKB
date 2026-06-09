# Todo: Починить запуск TEI контейнера + работа с нуля ✅

## Проблема
TEI контейнер падал с "config.json not found". После починки нужно было обеспечить работу "с нуля".

## Корневая причина (две проблемы)
1. **Неверная директория модели** — `prepare_tei_model.py` создавал `tei_model/` в корне `service_checker/`, docker-compose ожидал `docker/tei_model/`
2. **Неверное имя ONNX-файла** — скрипт называл файл `model_quantized.onnx`, TEI ожидает `model.onnx`

Volume path `./tei_model:/data` рабочий, не требует замены на абсолютный.

## Выполнено

### 1. Фикс `docker/prepare_tei_model.py`
- Default target_dir изменён на `docker/tei_model/` (относительно расположения скрипта)
- `ONNX_TARGET`: `model_quantized.onnx` → `model.onnx`
- Docstring обновлён

### 2. Создан `setup.py` — one-command setup
- `python setup.py` — полный цикл: deps → модель TEI → Docker Compose
- `python setup.py --model` — только модель
- `python setup.py --up` / `--down` / `--ps`

### 3. Создан `Makefile` — альтернативный setup (Linux/macOS/Git Bash)
- `make setup` / `make model` / `make up` / `make down` / `make test`

### 4. Документация
- `readme.md` — добавлен раздел "Быстрый старт (с нуля)", исправлена модель (MiniLM → rubert-tiny2)
- `specificity.md` — исправлена #3, добавлена #4
- `prepare_tei_model.py` — docstring обновлён

### 5. Проверка
- TEI контейнер: health → 200 OK, embed → 312-dim вектор
- Docker healthcheck: healthy
- 71/71 unit-тестов пройдено
- Целостность связанных данных подтверждена
