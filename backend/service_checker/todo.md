# TODO — DONE

## 1. ✅ Переименовать БД pkb_neuro → pkb_neuro_check
- [x] Все файлы checker + develop

## 2. ✅ LLM — добавлен LLM_API_URL
- [x] docker-compose.yml (checker + develop)

## 3. ✅ converter-validator — путь /api/v1/registry/classifiers/validate
- [x] converter_validator_service/app/services/registry_client.py

## 4. ✅ Gateway credentials — real mode
- [x] service_checker/services/gateway.py — get_credentials_for_mode

## 5. ✅ Gateway schema — по документации
- [x] /documents/ → data + meta
- [x] /documents/{id}/versions → data.document_id + data.versions
- [x] /documents/queue — orchestrator возвращает правильный формат

## 6. ✅ Gateway prepare — создание документа
- [x] POST /drafts (multipart с PDF) + PATCH /decide + ожидание появления документа
- [x] max_retries/retry_delay в EndpointDef
- [x] retry loop в _execute_endpoint

## 7. ✅ Orchestrator /documents/queue — правильный формат
- [x] orchestrator_service/app/api/v1/endpoints/documents.py

## 8. ✅ Gateway /rag/search — убран transform
- [x] gateway_service/gateway/client.py

## 9. 🔴 Осталось
- Pipeline: _ensure_project до токена (нужен рефакторинг API)
- Gateway: 404 на /documents/* (retry ещё не отработал в прогоне)
- Rag/search body (valid_at) — checker уже передаёт, но RAG Search валидирует строже
