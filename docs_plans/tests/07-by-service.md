# Распределение тестов по backend-сервисам

Каждый внутренний микросервис проксируется через Gateway. Тесты должны проверить, что прокси корректно передаёт запросы/ответы и что RBAC ограничивает доступ.

---

## AUTH Service (`/api/v1/auth/*`, `/api/v1/admin/*`)

Сервис аутентификации и управления пользователями.

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: auth routes` | gateway/tests/test_routing.py | `ALL_METHODS /api/v1/auth/*` и `/api/v1/admin/*` → `"auth"` |
| `proxy: POST /api/v1/auth/token` | gateway/tests/test_proxy.py | Прокси на auth:8082 + передача тела (username/password) |
| `proxy: GET /api/v1/auth/me` | gateway/tests/test_proxy.py | Прокси + проброс Authorization header |
| `proxy: GET/POST /api/v1/admin/*` | gateway/tests/test_proxy.py | Прокси CRUD пользователей/ролей/аудита на auth |
| `proxy: POST /api/v1/auth/refresh` | gateway/tests/test_proxy.py | Прокси refresh токена |
| `proxy: POST /api/v1/auth/revoke` | gateway/tests/test_proxy.py | Прокси revoke токена |
| `proxy: POST /api/v1/auth/validate` | gateway/tests/test_proxy.py | Internal validate |
| `RBAC: /admin/* для system_admin` | gateway/tests/test_rbac.py | Только admin имеет доступ |
| `RBAC: /admin/* для engineer` | gateway/tests/test_rbac.py | engineer → 403 |
| `RBAC: /auth/* без токена` | gateway/tests/test_rbac.py | Публичные эндпоинты |
| `authApi.login/me/refresh/logout` | frontend/utils/__tests__/http-auth.test.ts | Мэпперы аутентификации |
| `AdminPanel: users/roles/audit` | frontend/components/__tests__/AdminPanel.test.tsx | UI администрирования |

---

## Orchestrator Service (`/api/v1/drafts/*`, `/api/v1/documents/*` pipeline, `/api/v1/tasks/*`)

Сервис управления пайплайном обработки документов (черновики, задачи).

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: drafts write` | gateway/tests/test_routing.py | POST/PATCH/DELETE `/api/v1/drafts/*` → `"orchestrator"` |
| `resolve_service: drafts GET numeric` | gateway/tests/test_routing.py | `GET /api/v1/drafts/\d+$` → `"orchestrator"` |
| `resolve_service: documents pipeline` | gateway/tests/test_routing.py | POST reprocess, versions, status, errors, queue, tasks → `"orchestrator"` |
| `resolve_service: tasks` | gateway/tests/test_routing.py | `ALL_METHODS /api/v1/tasks/*` → `"orchestrator"` |
| `resolve_service: POST /documents` | gateway/tests/test_routing.py | Deprecated, но роут существует → orchestrator |
| `proxy: drafts CRUD` | gateway/tests/test_proxy.py | POST/GET/PATCH/DELETE /drafts → orchestrator |
| `proxy: documents pipeline` | gateway/tests/test_proxy.py | Reprocess, versions, status → orchestrator |
| `proxy: tasks` | gateway/tests/test_proxy.py | GET /tasks → orchestrator |
| `RBAC: POST /drafts` | gateway/tests/test_rbac.py | can_upload_documents |
| `RBAC: POST /documents/{id}/reprocess` | gateway/tests/test_rbac.py | Права на управление документами |
| `Drafts CRUD` | orchestrator/tests/orchestrator/test_drafts_crud.py | Полный CRUD |
| `Drafts preview + decide` | orchestrator/tests/orchestrator/test_drafts_preview.py | Preview и decision |
| `Drafts tasks` | orchestrator/tests/orchestrator/test_drafts_tasks.py | Задачи черновиков |
| `Documents pipeline` | orchestrator/tests/orchestrator/test_documents_pipeline.py | Reprocess, versions |
| `Documents status` | orchestrator/tests/orchestrator/test_documents_status.py | Статусы |
| `Draft → Document flow` | orchestrator/tests/integration/test_draft_to_document_flow.py | Полный цикл |
| `draftsApi.*` | frontend/utils/__tests__/http-drafts.test.ts | API вызовы черновиков |
| `documentsApi.*` | frontend/utils/__tests__/http-documents.test.ts | API вызовы документов |
| `KnowledgeProcessing` | frontend/components/__tests__/KnowledgeProcessing.test.tsx | UI загрузки/обработки |

---

## Registry Service (`/api/v1/registry/*`, `/api/v1/documents/*` CRUD, `/api/v1/drafts` GET)

Сервис реестра документов и справочников (классификаторы, терминология).

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: drafts list GET` | gateway/tests/test_routing.py | `GET /api/v1/drafts` (без id) → `"registry"` c path transform |
| `resolve_service: drafts detail GET` | gateway/tests/test_routing.py | `GET /api/v1/drafts/\d+$` (с числовым id) → `"orchestrator"` (детали черновика) |
| `resolve_service: documents CRUD` | gateway/tests/test_routing.py | GET/PUT/PATCH/DELETE `/api/v1/documents/{id}` → `"registry"` c path transform |
| `resolve_service: documents sections/pages/file/history/parameters/versions/succession` | gateway/tests/test_routing.py | GET запросы → `"registry"` |
| `resolve_service: documents search/export/import/check-uniqueness` | gateway/tests/test_routing.py | Спец. операции → `"registry"` |
| `resolve_service: registry direct` | gateway/tests/test_routing.py | `ALL_METHODS /api/v1/registry/*` → `"registry"` без изменений |
| `proxy: registry documents CRUD` | gateway/tests/test_proxy.py | Прокси + path transform (/api/v1/documents → /api/v1/registry/documents) |
| `proxy: registry classifiers` | gateway/tests/test_proxy.py | CRUD классификаторов |
| `proxy: registry terminology` | gateway/tests/test_proxy.py | CRUD терминологии |
| `proxy: registry search` | gateway/tests/test_proxy.py | POST /documents/search → /api/v1/registry/search |
| `proxy: registry drafts list` | gateway/tests/test_proxy.py | GET /drafts → /api/v1/registry/drafts |
| `RBAC: registry documents CRUD` | gateway/tests/test_rbac.py | can_manage_registry |
| `RBAC: registry classifiers CRUD` | gateway/tests/test_rbac.py | can_manage_classifiers |
| `RBAC: registry terminology CRUD` | gateway/tests/test_rbac.py | can_manage_terminology |
| `RBAC: registry search` | gateway/tests/test_rbac.py | knowledge_admin/system_admin |
| `RBAC: DELETE documents/drafts` | gateway/tests/test_rbac.py | Права на manage_classifiers/manage_terminology |
| `registryApi.*` | frontend/utils/__tests__/http-registry.test.ts | API вызовы registry |
| `http-mappers-registry` | frontend/utils/__tests__/http-mappers-registry.test.ts | Мэпперы registry |
| `RegistryEditors` | frontend/components/__tests__/RegistryEditors.test.tsx | UI классификаторов/терминологии |
| `DocumentRegistryPanel` | frontend/components/__tests__/DocumentRegistryPanel.test.tsx | UI реестра документов |

---

## Query Service (`/api/v1/chat/*`, `/api/v1/text/*`)

Сервис чата и текстовых операций (поиск ответов).

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: query routes` | gateway/tests/test_routing.py | `ALL_METHODS /api/v1/chat/*`, `/api/v1/text/*` → `"query"` |
| `proxy: POST /api/v1/chat/send` | gateway/tests/test_proxy.py | Прокси отправки сообщения |
| `proxy: GET/POST /api/v1/chat/sessions` | gateway/tests/test_proxy.py | Прокси сессий |
| `proxy: GET/POST /api/v1/text/*` | gateway/tests/test_proxy.py | Прокси текстовых операций |
| `chatApi.*` | frontend/utils/__tests__/http-chat.test.ts | API вызовы чата |
| `projectsApi.*` | frontend/utils/__tests__/http-projects.test.ts | API проектов |
| `http-mappers-chat` | frontend/utils/__tests__/http-mappers-chat.test.ts | Мэпперы чата |
| `Chat component` | frontend/components/__tests__/Chat.test.tsx | UI чата |
| `History` | frontend/components/__tests__/History.test.tsx | UI истории |
| `ModeSwitcher` | frontend/components/__tests__/ModeSwitcher.test.tsx | UI проектов/сессий |

---

## RAG Search Service (`/api/v1/rag/*`)

Сервис семантического поиска (RAG).

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: rag search` | gateway/tests/test_routing.py | `ALL_METHODS /api/v1/rag/*` → `"rag_search"` c path transform (rag → /api/v1) |
| `proxy: GET/POST /api/v1/rag/*` | gateway/tests/test_proxy.py | Прокси + path transform на rag_search:8091 |
| `searchApi.query` | frontend/utils/__tests__/http-mappers-search.test.ts | API вызовы поиска |
| `http-mappers-search` | frontend/utils/__tests__/http-mappers-search.test.ts | Мэпперы поиска |
| `Search component` | frontend/components/__tests__/Search.test.tsx | UI поиска |
| `KnowledgeBase` | frontend/components/__tests__/KnowledgeBase.test.tsx | UI базы знаний |

---

## Analyse Service (`/api/v1/analyse/*`)

Сервис анализа документов.

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: analyse routes` | gateway/tests/test_routing.py | `ALL_METHODS /api/v1/analyse/*` → `"analyse"` |
| `proxy: GET/POST /api/v1/analyse/*` | gateway/tests/test_proxy.py | Прокси на analyse:8089 |

---

## Внутренние сервисы Gateway

Собственные эндпоинты Gateway (health, diagnostics, metrics, mode).

| Тест | Где | Суть |
|------|-----|------|
| `Gateway health — анонимный` | gateway/tests/test_main_handlers.py | GET /api/v1/health → {"status":"ok"} |
| `Gateway health — admin` | gateway/tests/test_main_handlers.py | GET /api/v1/health → полный ответ |
| `Gateway live/ready` | gateway/tests/test_main_handlers.py | /health/live, /health/ready |
| `Gateway mode` | gateway/tests/test_main_handlers.py | /system/mode |
| `Gateway metrics` | gateway/tests/test_main_handlers.py | /monitor/metrics |
| `Gateway diagnostics` | gateway/tests/test_diagnostics.py | /system/diagnostics |
| `Error handlers` | gateway/tests/test_main_handlers.py | 404/422/500 → унифицированный error format |
| `Metrics мониторинг` | frontend/components/__tests__/Monitor.test.tsx | UI метрик |

---

## Deprecated Integration Service

Снятый с поддержки сервис интеграции.

| Тест | Где | Суть |
|------|-----|------|
| `resolve_service: deprecated integration routes` | gateway/tests/test_routing.py | `/api/v1/meridian/*`, `/api/v1/files/*`, `/api/v1/external/*` → 410 |
| `is_deprecated_integration_route()` | gateway/tests/test_client.py | unit-тест функции |

---

## Матрица покрытия по сервисам

| Сервис | Gateway routing | Gateway proxy | RBAC | Orchestrator API | Frontend API | Frontend UI |
|--------|:---------------:|:-------------:|:----:|:----------------:|:------------:|:-----------:|
| **Auth** | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| **Orchestrator** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Registry** | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| **Query** | ✅ | ✅ | — | — | ✅ | ✅ |
| **RAG Search** | ✅ | ✅ | — | — | ✅ | ✅ |
| **Analyse** | ✅ | ✅ | — | — | — | — |
| **Gateway (собств.)** | — | — | — | — | ✅ | ✅ |
| **Integration (depr.)** | ✅ | — | — | — | — | — |
