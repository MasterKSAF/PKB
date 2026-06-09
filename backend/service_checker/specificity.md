# Специфичные архитектурные решения и аномалии

## Зачем этот файл
Фиксируются все аномалии и спорные моменты в проекте (правило 2.3).

## Запрет на редактирование чужих сервисов
Агент не имеет права создавать, изменять или удалять файлы в сервисах, которые не относятся к его задаче. Исключение — только по явному указанию владельца сервиса.

---

## 1. Аномалия: OCR Service не существует — в supervisord запущен Parser Service вместо OCR

**Обнаружено:** 2026-06-09

### Симптом
В отчётах `check_result/` OCR Service (порт 8088) показывал статус ✅, хотя все OCR-эндпоинты возвращают 404.

### Диагностика
В `service_checker/docker/supervisord.conf`:
```ini
[program:ocr]
command=uvicorn app.main:app --host 0.0.0.0 --port 8088 --no-access-log
directory=/app/backend/parser_service
```
Отдельного сервиса `backend/ocr_service/` не существует. На порт 8088 запущен Parser Service.

### Что происходило
1. Supervisor запускает `parser_service/app/main.py` на порту 8088.
2. Parser Service — рабочий FastAPI — стартует успешно.
3. Checker пингует `/api/v1/health`, получает 404, но `404 < 500` → считает сервис живым.
4. Все OCR-эндпоинты возвращают 404.
5. После серии правок checker теперь:
   - Считает 404 с валидным JSON как success (эндпоинт существует, ресурс не найден)
   - Но если ≥2 не-health эндпоинтов вернули 404 — оверрайд: ping_ok=False, success откатывается
   - Статус-колонка в отчёте учитывает ping_ok

### Что исправлено (checker, 2026-06-09)
1. **`api_coverage_test.py:test_service`** — 4xx/5xx с валидным JSON → success, без JSON → fail
2. **`api_coverage_test.py`** — защита all_404: если ≥2 не-health эндпоинтов вернули 404, ping_ok=False, success откатывается
3. **`api_coverage_test.py:generate_report`** — статус-колонка учитывает ping_ok (❌ если ping упал)
4. **`api_coverage_test.py`** — обновлена легенда отчёта
5. **Иконки ping** — `✓/✗` заменены на `✅/❌` для единого стиля

### Тесты
Тесты разбиты на 3 файла в `tests/`:
- `test_success_determination.py` — 6 тестов (200, 404 с/без JSON, 500 с/без JSON)
- `test_override_logic.py` — 3 теста (all_404 с JSON, all_404 без JSON, mixed)
- `test_report_generation.py` — 3 теста (статус-колонка, иконки в отчёте, иконки в консоли)

### Статус
🟡 **Частично исправлено (checker)**
🔴 **Открыто** — OCR Service физически не существует. Требуется создать `backend/ocr_service/` и исправить `supervisord.conf`.
