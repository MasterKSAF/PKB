# Todo: Реализация P1 (10) и P2 (9) тестов из `todo_pipeline_coverage.md`

> Логику не трогаем — только тесты. Цель — выявить дефекты в текущей реализации,
> зафиксировать поведение, покрыть указанные сценарии.

## P1-блок (10 тестов)

- [ ] 1. `TestCircuitBreakerOpen` — `tests/test_base_client.py`. CB открыт → mock fallback
- [ ] 2. `TestCircuitBreakerPerServiceIsolation` — `tests/test_base_client.py`
- [ ] 3. `TestConnectErrorFallback` — `tests/test_base_client.py` (verify tenacity НЕ вызван)
- [ ] 4. `TestConnectVsReadTimeout` — `tests/test_base_client.py`
- [ ] 5. `TestPoolExhaustion` — `tests/test_base_client.py` (51-й запрос)
- [ ] 6. `TestStaleConnectionReuse` — `tests/test_base_client.py`
- [ ] 7. `TestIdempotencyCachePersistence` — `tests/orchestrator/test_idempotency_persistence.py`
- [ ] 8. `TestReprocessCleanupFailed` — `tests/orchestrator/test_reprocess_cleanup_fail.py`
- [ ] 9. `TestRegistryProxyErrors` — `tests/orchestrator/test_registry_proxy_errors.py`
- [ ] 10. `TestUserIdMissing` — `tests/api/v1/test_internal_call_user_id_missing.py`

## P2-блок (9 тестов)

- [ ] 1. `TestCompensateRagIndex` — `tests/unit/test_saga_compensation.py`
- [ ] 2. `TestCompensationIdempotency` — `tests/unit/test_saga_compensation.py`
- [ ] 3. `TestPreviewArtifactsTtl` — `tests/orchestrator/test_orphan_data_cleanup.py`
- [ ] 4. `TestOrphanMinioCleanup` — `tests/orchestrator/test_orphan_data_cleanup.py`
- [ ] 5. `TestDiscardedDraftsGc` — `tests/orchestrator/test_orphan_data_cleanup.py`
- [ ] 6. `TestIdempotencyCacheTtl` — `tests/orchestrator/test_idempotency_ttl.py`
- [ ] 7. `TestUnknownDraftStatus` — `tests/test_drafts.py`
- [ ] 8. `TestTimeoutCascade` — `tests/test_drafts.py`
- [ ] 9. `TestAllServicesDisabled` — `tests/test_config.py`

## Финальная проверка
- [ ] Прогнать новые тесты
- [ ] Зафиксировать аномалии в `specificity.md`
- [ ] Финальный обзор правок
