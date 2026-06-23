# План для нового агента

## Текущий статус

**Pipeline**: 15/15 ✅ (полностью зелёный)
**API Coverage**: остались 6 skipped в Gateway

| Сервис | Результат |
|--------|-----------|
| Auth | 19/19 ✅ |
| Registry | 50/50 ✅ (Categories — пересоздана таблица) |
| Orchestrator | 35/35 ✅ (починены metadata proxy, reprocess, pipeline) |
| Gateway | 69/75 ⏭️ **6 skipped** |
| Query | — проверить после обновления (UniqueViolation → 409) |
| Остальные | зелёные |

---

## Задачи

### 1. Gateway: 6 skipped

**Причина**: в `services/gateway.py` нет prepare-шагов для `user_id`, `pending_id`, `file_id`.

**Конкретно**:
- **3 эндпоинта** с `{user_id}` — пропущены
- **2 эндпоинта** с `{pending_id}` — пропущены
- **1 эндпоинт** с `{file_id}` — пропущен

**Что сделать** — добавить в `prepare_endpoints` Gateway:
1. `POST /auth/admin/users` — создать пользователя, извлечь `user_id` (если ещё не создан)
2. `POST /registry/classifiers` — создать классификатор → извлечь `pending_id` через `/classifiers/pending`
3. `POST /registry/documents/import` — импорт документа → извлечь `file_id`

**Куда**: `services/gateway.py`, массив `prepare_endpoints` в `get_service_def()`.

**Проверка**: `python -m service_checker docker --action full-report --services gateway --skip-pipelines`

---

### 2. Query — проверить после обновления

Разработчик query сказал, что починил UniqueViolation → 409. Нужно перепроверить:

```
python -m service_checker docker --action full-report --services query --skip-pipelines
```

Ожидается: 27/27 ✅ вместо 26/27.

---

### 3. Финальный прогон

После gateway и query:

```
python -m service_checker docker --action full-report
```

15 pipelines + все API coverage. Обновить `todo.md` и `specificity.md` при необходимости.

---

## Справка по проекту

- **recheck.bat**: `backend/service_checker/docker/recheck.bat` — полный цикл (чистка БД → перезапуск → отчёт). Запускать через `cmd /c recheck.bat`.
- **Быстрые проверки**: `python -m service_checker docker --action full-report --services <name> --skip-pipelines`
- **Checker определение сервисов**: `services/gateway.py`, `services/orchestrator.py` и т.д.
- **Pipeline**: `pipelines/orchestrator_*.py` — починены 3 pipeline (добавлен шаг создания документа в Registry)
- **Orchestrator**: починены metadata proxy (404 от Registry) и reprocess (IntegrityError → 409)
- **Registry Categories**: таблица пересоздана (не хватало колонок description, color, created_at, updated_at)
