# Todo: Реализация P1 (10) и P2 (9) тестов из `todo_pipeline_coverage.md`

> Логику не трогаем — только тесты. Цель — выявить дефекты в текущей реализации,
> зафиксировать поведение, покрыть указанные сценарии.

## P1-блок (10 тестов) ✅

- [x] 1. `TestCircuitBreakerOpen` — `tests/test_base_client.py`. CB открыт → mock fallback
- [x] 2. `TestCircuitBreakerPerServiceIsolation` — `tests/test_base_client.py`
- [x] 3. `TestConnectErrorFallback` — `tests/test_base_client.py` (verify tenacity НЕ вызван)
- [x] 4. `TestConnectVsReadTimeout` — `tests/test_base_client.py`
- [x] 5. `TestPoolExhaustion` — `tests/test_base_client.py` (51-й запрос)
- [x] 6. `TestStaleConnectionReuse` — `tests/test_base_client.py`
- [x] 7. `TestIdempotencyCachePersistence` — `tests/orchestrator/test_idempotency_persistence.py`
- [x] 8. `TestReprocessCleanupFailed` — `tests/orchestrator/test_reprocess_cleanup_fail.py`
- [x] 9. `TestRegistryProxyErrors` — `tests/orchestrator/test_registry_proxy_errors.py`
- [x] 10. `TestUserIdMissing` — `tests/api/v1/test_internal_call_user_id_missing.py`

## P2-блок (9 тестов) ✅

- [x] 1. `TestCompensateRagIndex` — `tests/unit/test_saga_compensation.py`
- [x] 2. `TestCompensationIdempotency` — `tests/unit/test_saga_compensation.py`
- [x] 3. `TestPreviewArtifactsTtl` — `tests/orchestrator/test_orphan_data_cleanup.py`
- [x] 4. `TestOrphanMinioCleanup` — `tests/orchestrator/test_orphan_data_cleanup.py`
- [x] 5. `TestDiscardedDraftsGc` — `tests/orchestrator/test_orphan_data_cleanup.py`
- [x] 6. `TestIdempotencyCacheTtl` — `tests/orchestrator/test_idempotency_ttl.py`
- [x] 7. `TestUnknownDraftStatus` — `tests/test_drafts.py`
- [x] 8. `TestTimeoutCascade` — `tests/test_drafts.py`
- [x] 9. `TestAllServicesDisabled` — `tests/test_config.py`

## Финальная проверка
- [x] Все тесты написаны и закоммичены
- [ ] Зафиксировать аномалии в `specificity.md`
- [ ] Исправить 6 падающих тестов (см. ниже)

### Известные падения (6/164 тестов не прошли)
1. `tests/orchestrator/test_reprocess_cleanup_fail.py` (2) — `AsyncMock side_effect` не срабатывает для `_run_async`
2. `tests/orchestrator/test_registry_proxy_errors.py::test_create_draft_registry_5xx_returns_500` — mock-режим не пробрасывает 5xx
3. `tests/unit/test_saga_compensation.py::test_compensate_rag_index_after_its_failure` — Saga compensation не вызывается через on_step_failed
4. `tests/test_drafts.py::TestTimeoutCascade` (2) — `on_step_failed` попадает в OCR-fallback вместо retry
