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

### Что исправлено (checker, 2026-06-09)
1. **`api_coverage_test.py:test_service`** — 4xx/5xx с валидным JSON → success, без JSON → fail
2. **`api_coverage_test.py`** — защита all_404: если ≥2 не-health эндпоинтов вернули 404, ping_ok=False, success откатывается у **всех** результатов включая health
3. **`api_coverage_test.py:generate_report`** — статус-колонка учитывает ping_ok (❌ если ping упал)
4. **`api_coverage_test.py`** — обновлена легенда отчёта
5. **Иконки ping** — `✓/✗` заменены на `✅/❌` для единого стиля

### Тесты
Тесты разбиты на 3 файла в `tests/` (13 тестов):
- `test_success_determination.py` — 6 тестов (200, 404 с/без JSON, 500 с/без JSON)
- `test_override_logic.py` — 4 теста (all_404 с JSON, all_404 без JSON, all_404 с health, mixed)
- `test_report_generation.py` — 3 теста (статус-колонка, иконки в отчёте, иконки в консоли)

### Статус
🟡 **Частично исправлено (checker)**
🔴 **Открыто** — OCR Service физически не существует. Требуется создать `backend/ocr_service/` и исправить `supervisord.conf`.

---

## 2. Аномалия: Auth Service падал на /auth/refresh — цикл перезапусков

**Обнаружено:** 2026-06-09

### Симптом
В `check_result/errors_*.md` секция `auth-err` раздувалась до 700+ строк. При каждом запуске coverage test:
1. Checker вызывал `POST /auth/refresh`
2. Auth Service падал с `AttributeError: 'NoneType' object has no attribute 'expires_at'`
3. Supervisor перезапускал сервис
4. В лог писалась полная трассировка (~60 строк на цикл)
5. За несколько запусков набиралось 190+ КБ логов

### Диагностика
`auth_service/app/services/auth_service.py:54`:
```python
expires_at = db_token.expires_at
if expires_at.tzinfo is None:  # expires_at может быть None
    expires_at = expires_at.replace(tzinfo=timezone.utc)
```

### Что исправлено
Добавлена проверка `expires_at is None`:
```python
if expires_at is None:
    raise HTTPException(status_code=401, detail='Token has no expiry')
```

### Требование
**Перезапусков сервисов быть не должно.** Supervisor настроен с `autorestart=false` для всех программ. Любой краш сервиса при тестировании — баг в коде сервиса, а не в checker'е.

### Тесты
Проверка интеграционная — `python api_coverage_test.py` показывает `Auth: 16/16`, 0 failed.
Юнит-тест в `auth_service/tests/` не входит в зону ответственности checker.

### Статус
🟢 **Исправлено (auth_service, 2026-06-09)**
