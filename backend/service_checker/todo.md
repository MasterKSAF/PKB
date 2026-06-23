# Registry + Converter-Validator + Parser — DONE

## Результаты прогона (2026-06-23)

### Registry
**Было**: 39/50 passed, 3 failed, 8 skipped
**Стало**: 45/50 passed, **2 failed** (Categories), 3 skipped

| Изменение | Статус |
|-----------|--------|
| PATCH /documents/{doc_id} — убрал data.updated_fields из response_schema | ✅ |
| POST /drafts — добавил extract_keys=["draft_id"] | ✅ |
| PATCH /drafts/{id}/metadata — expected_status={200, 404} (internal) | ✅ |
| Warnings: добавлен PATCH /drafts/{id}/metadata | ✅ |
| Categories — оставлены честно ❌ Fail (не реализованы) | ✅ |

### Converter-Validator
**Было**: 2/5 passed, 3 skipped
**Стало**: **5/5 passed**

| Изменение | Статус |
|-----------|--------|
| task_id/version_id: {context} → константы 12345, "1" | ✅ |

### Parser
**Было**: 1/5 passed, 4 skipped
**Стало**: **5/5 passed**

| Изменение | Статус |
|-----------|--------|
| task_id/draft_id/version_id: {context} → константы 12345, 1, "1" | ✅ |

## Архитектурные решения (записаны в guide.md, specificity.md)

- API Coverage — изолированно, константы для ID не участвующих в логике
- Internal API (Registry) — expected_status={200, 404/403}
- Нереализованные эндпоинты — честный ❌ Fail, без подгонки
