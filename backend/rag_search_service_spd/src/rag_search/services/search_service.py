import time

from rag_search.models.search import SearchRequest, SearchResponse
from rag_search.repositories.postgres_search_repository import PostgresSearchRepository


class SearchService:
    def __init__(self, repository: PostgresSearchRepository | None = None) -> None:
        self.repository = repository or PostgresSearchRepository()

    async def search(self, request: SearchRequest) -> SearchResponse:
        started = time.perf_counter()
        results = await self.repository.search(request)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        return SearchResponse(
            query=request.query,
            search_type_used=request.search_type,
            results=results,
            total_found=len(results),
            processing_time_ms=elapsed_ms,
            context_expanded=request.expand_context,
        )
