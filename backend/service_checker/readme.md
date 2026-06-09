# PKB Neuroassistant — Service Checker

Утилита для проверки сервисов PKB Neuroassistant.

## Структура

```
service_checker/
├── api_coverage_test.py   # API Coverage Test (real-режим, Docker)
├── service_checker.py     # Запуск/остановка сервисов, health check, эмуляция UI
├── setup_db.py            # Инициализация БД
├── docker/                # Docker-конфигурация (supervisord и т.д.)
├── tests/
│   ├── conftest.py                        # Общие фикстуры
│   ├── test_success_determination.py      # Логика success/fail для статус-кодов
│   ├── test_override_logic.py             # Оверрайд all_404 и ping_ok
│   └── test_report_generation.py          # Формирование отчёта
├── specificity.md         # Аномалии и архитектурные решения
└── readme.md              # Точка входа (этот файл)
```

## Запуск

```bash
# Все тесты
python -m pytest tests/ -v

# По файлам
python -m pytest tests/test_success_determination.py -v
python -m pytest tests/test_override_logic.py -v
python -m pytest tests/test_report_generation.py -v

# Coverage test в Docker
python api_coverage_test.py run-all
```

## Ключевые решения

- **404 с валидным JSON** — success (эндпоинт существует, ресурс не найден)
- **all_404 оверрайд** — если ≥2 не-health эндпоинтов вернули 404, сервис помечается мёртвым (ping_ok=False, success откатывается)
- **4xx/5xx без JSON** — fail
- **Статус-колонка отчёта** — ❌ если ping_ok=False
