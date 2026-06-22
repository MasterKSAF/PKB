from mocks.handlers.auth_routes import router as auth_router
from mocks.handlers.orch_routes import router as orch_router
from mocks.handlers.query_routes import router as query_router
from mocks.handlers.registry_routes import router as registry_router
from mocks.handlers.rag_search_routes import router as rag_search_router

__all__ = ["auth_router", "orch_router", "query_router", "registry_router", "rag_search_router"]
