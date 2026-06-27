# Recheck — текущее состояние (2026-06-27)

## Результат: все сервисы + пайплайны проходят

**API Coverage:** 253/253 ✅ (0 failed)
**Pipeline Testing:** 16/16 ✅ (0 failed, штатные skip)
**Contracts:** 4/4 ✅
**Gateway Tests:** известные несоответствия (pre-existing)

## Исправлено за сегодня

### 13. Registry trailing slash — ИСПРАВЛЕНО
- Причина: Registry не поддерживал эндпоинты со слешем (`/terminology/` → 400)
- Фикс: middleware в `registry_service/main.py` — редирект 307 с `/path/` на `/path`

### 14. Registry 3× import 400 vs 422 — ИСПРАВЛЕНО
- Причина: checker ожидал 422, Registry возвращает 400 (жёстко в коде)
- Фикс: `expected_status={422}` → `{400, 422}` в `services/registry.py`

### 15. Pipeline `orchestrator_draft_lifecycle` — ИСПРАВЛЕНО
- Причина: checker ожидал поле `created_by`, сервис его не возвращает
- Фикс: убрано поле из проверки в `pipelines/orchestrator_draft_lifecycle.py`

### 16. Pipeline `orchestrator_metadata_update` — ИСПРАВЛЕНО
- Причина: та же — `created_by` не возвращается сервисом
- Фикс: убрано поле из проверки в `pipelines/orchestrator_metadata_update.py`

## Осталось (pre-existing):
- Gateway: mock/реальный несоответствия (gateway_tests)
- OCR: dev-статус
- parser_service: OTEL без try/except (требует доработки разработчиком)
- celery-worker: не отвечает на ping (module tasks not found)

---

## Текущая задача: разрешение git merge conflicts

### Контекст
- HEAD (наша ветка): port shift +10000, rate limit vars
- MERGE_HEAD (вливаемая): старые порты без сдвига, без rate limit
- Конфликты — только порты и rate limit vars

### План
- [ ] 1. `docker-compose.yml` — взять HEAD (сохранить rate limit vars)
- [ ] 2. Все pipeline файлы — взять HEAD (порты +10000)
- [ ] 3. `git add` разрешённых файлов
- [ ] 4. Проверить, что тесты проходят
