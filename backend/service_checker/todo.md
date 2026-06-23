# Исправление trailing slash в registry

## Проблема
Registry service редиректит 307 при запросах с trailing slash.
Pipeline `registry_lifecycle` и service definition `registry.py` используют URL с `/` в конце — это вызывает 307.

## План
- [x] 1. Исправить `pipelines/registry_lifecycle.py` — убрать trailing slash у всех путей
- [x] 2. Исправить `services/registry.py`:
  - [x] 2a. Убрать trailing slash у коллекционных endpoint-ов
  - [x] 2b. Исправить warning (registry не требует, а редиректит слеши)
- [x] 3. Запустить тесты — pipeline registry_lifecycle: 11/11 ✅
- [x] 4. Актуализировать specificity.md — исправить неверные сведения о trailing slash
- [x] 5. Добавить ориентир в guide.md
- [x] 6. Исправить `pipelines/full_document_lifecycle.py` — убрать trailing slash у registry-путей
- [x] 7. Исправить `pipelines/registry_quarantine.py` — убрать trailing slash у registry-путей
- [x] 8. Проверить full_document_lifecycle: 11/12 (шаг 4 — 403, не связано с trailing slash)
- [x] 9. Проверить registry_quarantine: 10/10 ✅
- [x] 10. Финальный обзор
