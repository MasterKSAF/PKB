# Todo — Исправление 9 стоперов Gateway — ВЫПОЛНЕНО ✅

## Результаты

| # | Стопер | Статус | Комментарий |
|---|--------|:------:|-------------|
| 1 | POST /registry/classifiers/import — CSV/XLSX | ✅ | Добавлен парсинг CSV (встроенный csv) и XLSX (openpyxl) с mapping, обратная совместимость с JSON |
| 2 | POST /registry/terminology/import — CSV/XLSX | ✅ | Аналогично классификаторам |
| 3 | POST /registry/classifiers/validate — `classification.*` wrapper | ✅ | Поддержан документированный wrapper + fallback на top-level поля |
| 4 | POST /registry/classifiers/pending/{id}/accept — тело запроса | ✅ | Принимает body (parent_code, full_name, admin_comment), ответ: status "mapped" |
| 5 | POST /registry/classifiers/pending/{id}/reject — admin_comment | ✅ | Принимает body (admin_comment), сохраняет в pending |
| 6 | GET /registry/classifiers/pending — фильтр по system | ✅ | Добавлен query parameter system |
| 7 | terminology.scope: str → list[str] | ✅ | Pydantic-модели принимают Union[str, List[str]], нормализуют к list. Seed-данные обновлены |
| 8 | GET /registry/terminology/normalize — term_type unknown | ✅ | Для not found возвращается term_type: "unknown" |
| 9 | /api/v1/health требует авторизацию | ✅ | Добавлен алиас /api/v1/health (публичный) |

### Сопутствующие изменения
- Добавлен `openpyxl` в requirements.txt
- Обновлены seed-данные (scope как list)
- Обновлены тесты test_api.py и start_service.py под новый формат ответов
- Добавлены 17 новых тестов (TestStopperFixes)

### Валидация
- **487 тестов проходят** (было 470, добавлено 17 новых, 4 обновлено под новый формат)
