from rag_search.models.search import SearchRequest, SearchResultItem


class PostgresSearchRepository:
    """Repository for reading indexed chunks from PostgreSQL.

    Runtime search implementation will be added in the next PR.
    """

    async def search(self, request: SearchRequest) -> list[SearchResultItem]:
        return []
